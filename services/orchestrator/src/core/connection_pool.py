"""Advanced connection pooling for HTTP clients, databases, and external services."""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import aiohttp
import ssl
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pools."""
    max_connections: int = 100
    max_connections_per_host: int = 30
    timeout_seconds: int = 30
    keepalive_timeout: int = 30
    enable_ssl: bool = True
    retry_attempts: int = 3
    retry_backoff: float = 1.0
    health_check_interval: int = 60
    connection_lifetime: int = 300  # 5 minutes


@dataclass
class PoolMetrics:
    """Metrics for connection pool monitoring."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    requests_completed: int = 0
    requests_failed: int = 0
    avg_response_time_ms: float = 0.0
    last_health_check: Optional[float] = None
    pool_utilization: float = 0.0
    response_times: List[float] = field(default_factory=list)


class HTTPConnectionPool:
    """Optimized HTTP connection pool with advanced features."""
    
    def __init__(self, 
                 pool_name: str,
                 config: ConnectionPoolConfig,
                 base_url: Optional[str] = None):
        """Initialize HTTP connection pool.
        
        Args:
            pool_name: Name identifier for the pool
            config: Pool configuration
            base_url: Base URL for the service (optional)
        """
        self.pool_name = pool_name
        self.config = config
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.connector: Optional[aiohttp.TCPConnector] = None
        self.metrics = PoolMetrics()
        self._health_check_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        logger.info(f"HTTP pool '{pool_name}' initialized - Max: {config.max_connections}, "
                   f"Per-host: {config.max_connections_per_host}")
    
    async def initialize(self) -> None:
        """Initialize the connection pool."""
        async with self._lock:
            if self.session:
                return  # Already initialized
            
            # Create SSL context
            ssl_context = None
            if self.config.enable_ssl:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = True
                ssl_context.verify_mode = ssl.CERT_REQUIRED
            
            # Create connector with optimized settings
            self.connector = aiohttp.TCPConnector(
                limit=self.config.max_connections,
                limit_per_host=self.config.max_connections_per_host,
                ttl_dns_cache=300,  # 5 minutes DNS cache
                use_dns_cache=True,
                keepalive_timeout=self.config.keepalive_timeout,
                enable_cleanup_closed=True,
                ssl=ssl_context
            )
            
            # Create session with timeout
            timeout = aiohttp.ClientTimeout(
                total=self.config.timeout_seconds,
                connect=10,  # 10 seconds connect timeout
                sock_read=20  # 20 seconds read timeout
            )
            
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'HELIOS-Orchestrator/1.0',
                    'Accept': 'application/json',
                    'Connection': 'keep-alive'
                }
            )
            
            # Start health check task
            if self.config.health_check_interval > 0:
                self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info(f"HTTP pool '{self.pool_name}' initialized successfully")
    
    async def request(self, 
                     method: str, 
                     url: str, 
                     **kwargs) -> aiohttp.ClientResponse:
        """Make HTTP request using the pool."""
        if not self.session:
            await self.initialize()
        
        # Build full URL if base_url is set
        if self.base_url and not url.startswith('http'):
            url = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
        
        start_time = time.time()
        
        for attempt in range(self.config.retry_attempts):
            try:
                self.metrics.active_connections += 1
                
                async with self.session.request(method, url, **kwargs) as response:
                    # Record successful request
                    response_time = time.time() - start_time
                    self._record_request_metrics(response_time, success=True)
                    
                    # Return response for context manager usage
                    return response
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.metrics.active_connections = max(0, self.metrics.active_connections - 1)
                
                if attempt == self.config.retry_attempts - 1:
                    # Last attempt failed
                    response_time = time.time() - start_time
                    self._record_request_metrics(response_time, success=False)
                    logger.error(f"HTTP request failed after {self.config.retry_attempts} attempts: {str(e)}")
                    raise
                
                # Wait before retry with exponential backoff
                wait_time = self.config.retry_backoff * (2 ** attempt)
                await asyncio.sleep(wait_time)
                logger.warning(f"HTTP request attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
            
            finally:
                self.metrics.active_connections = max(0, self.metrics.active_connections - 1)
    
    def _record_request_metrics(self, response_time: float, success: bool) -> None:
        """Record request metrics."""
        if success:
            self.metrics.requests_completed += 1
        else:
            self.metrics.requests_failed += 1
        
        # Track response times (keep last 1000)
        self.metrics.response_times.append(response_time * 1000)  # Convert to ms
        if len(self.metrics.response_times) > 1000:
            self.metrics.response_times.pop(0)
        
        # Calculate average response time
        if self.metrics.response_times:
            self.metrics.avg_response_time_ms = sum(self.metrics.response_times) / len(self.metrics.response_times)
        
        # Calculate pool utilization
        if self.connector:
            total_connections = len(self.connector._conns)
            self.metrics.total_connections = total_connections
            self.metrics.pool_utilization = (total_connections / self.config.max_connections) * 100
    
    async def _health_check_loop(self) -> None:
        """Periodic health check for the connection pool."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                if self.connector:
                    # Clean up closed connections
                    await self.connector._cleanup_closed_transports()
                    
                    # Update metrics
                    self.metrics.last_health_check = time.time()
                    
                    logger.debug(f"Pool '{self.pool_name}' health check - "
                               f"Connections: {self.metrics.total_connections}, "
                               f"Utilization: {self.metrics.pool_utilization:.1f}%")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for pool '{self.pool_name}': {str(e)}")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get connection pool metrics."""
        return {
            "pool_name": self.pool_name,
            "total_connections": self.metrics.total_connections,
            "active_connections": self.metrics.active_connections,
            "requests_completed": self.metrics.requests_completed,
            "requests_failed": self.metrics.requests_failed,
            "avg_response_time_ms": round(self.metrics.avg_response_time_ms, 2),
            "pool_utilization_percent": round(self.metrics.pool_utilization, 1),
            "success_rate": self._calculate_success_rate(),
            "last_health_check": self.metrics.last_health_check,
            "config": {
                "max_connections": self.config.max_connections,
                "max_per_host": self.config.max_connections_per_host,
                "timeout_seconds": self.config.timeout_seconds
            }
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate percentage."""
        total_requests = self.metrics.requests_completed + self.metrics.requests_failed
        if total_requests == 0:
            return 100.0
        return (self.metrics.requests_completed / total_requests) * 100
    
    async def close(self) -> None:
        """Close the connection pool and cleanup resources."""
        logger.info(f"Closing HTTP pool '{self.pool_name}'")
        
        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close session and connector
        if self.session:
            await self.session.close()
        
        if self.connector:
            await self.connector.close()
        
        logger.info(f"HTTP pool '{self.pool_name}' closed")


class ConnectionPoolManager:
    """Central manager for all connection pools."""
    
    def __init__(self):
        """Initialize connection pool manager."""
        self.pools: Dict[str, HTTPConnectionPool] = {}
        self.default_config = ConnectionPoolConfig()
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="pool-mgr")
        
    async def create_pool(self, 
                         pool_name: str, 
                         base_url: Optional[str] = None,
                         config: Optional[ConnectionPoolConfig] = None) -> HTTPConnectionPool:
        """Create a new HTTP connection pool."""
        if pool_name in self.pools:
            logger.warning(f"Pool '{pool_name}' already exists, returning existing pool")
            return self.pools[pool_name]
        
        pool_config = config or self.default_config
        pool = HTTPConnectionPool(pool_name, pool_config, base_url)
        await pool.initialize()
        
        self.pools[pool_name] = pool
        logger.info(f"Created HTTP pool '{pool_name}' for {base_url or 'generic'}")
        
        return pool
    
    def get_pool(self, pool_name: str) -> Optional[HTTPConnectionPool]:
        """Get existing connection pool."""
        return self.pools.get(pool_name)
    
    async def get_or_create_pool(self, 
                                pool_name: str, 
                                base_url: Optional[str] = None,
                                config: Optional[ConnectionPoolConfig] = None) -> HTTPConnectionPool:
        """Get existing pool or create new one."""
        pool = self.get_pool(pool_name)
        if pool:
            return pool
        
        return await self.create_pool(pool_name, base_url, config)
    
    @asynccontextmanager
    async def request(self, 
                     pool_name: str, 
                     method: str, 
                     url: str, 
                     **kwargs):
        """Make HTTP request using specified pool."""
        pool = self.get_pool(pool_name)
        if not pool:
            raise ValueError(f"Pool '{pool_name}' not found. Create it first.")
        
        async with pool.request(method, url, **kwargs) as response:
            yield response
    
    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all pools."""
        metrics = {}
        for pool_name, pool in self.pools.items():
            metrics[pool_name] = await pool.get_metrics()
        
        # Add summary metrics
        total_pools = len(self.pools)
        total_connections = sum(pool.metrics.total_connections for pool in self.pools.values())
        avg_utilization = sum(pool.metrics.pool_utilization for pool in self.pools.values()) / total_pools if total_pools > 0 else 0
        
        metrics["summary"] = {
            "total_pools": total_pools,
            "total_connections": total_connections,
            "avg_utilization_percent": round(avg_utilization, 1)
        }
        
        return metrics
    
    async def close_all_pools(self) -> None:
        """Close all connection pools."""
        logger.info(f"Closing {len(self.pools)} connection pools")
        
        # Close all pools concurrently
        close_tasks = [pool.close() for pool in self.pools.values()]
        await asyncio.gather(*close_tasks, return_exceptions=True)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Clear pools
        self.pools.clear()
        
        logger.info("All connection pools closed")


# Global connection pool manager instance
_global_pool_manager: Optional[ConnectionPoolManager] = None


def get_connection_pool_manager() -> ConnectionPoolManager:
    """Get global connection pool manager instance."""
    global _global_pool_manager
    
    if _global_pool_manager is None:
        _global_pool_manager = ConnectionPoolManager()
    
    return _global_pool_manager


@asynccontextmanager
async def http_request(pool_name: str, method: str, url: str, **kwargs):
    """Convenience function for making HTTP requests with connection pooling."""
    manager = get_connection_pool_manager()
    async with manager.request(pool_name, method, url, **kwargs) as response:
        yield response
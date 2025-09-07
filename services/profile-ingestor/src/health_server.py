"""Lightweight health check server for Profile Ingestor service.

This provides a simple HTTP health endpoint for Docker/Kubernetes health checks
while keeping the main CLI application unchanged.
"""

import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class HealthResponse:
    """Health response data structure."""
    
    def __init__(self, status: str = "healthy", service: str = "profile-ingestor"):
        self.status = status
        self.service = service
        self.version = "1.0.0"
        self.timestamp = time.time()
        self.uptime = time.time() - _start_time
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "service": self.service,
            "version": self.version,
            "timestamp": self.timestamp,
            "uptime_seconds": self.uptime,
            "checks": {
                "spacy_models": self._check_spacy_models(),
                "data_directory": self._check_data_directory(),
                "dependencies": self._check_dependencies()
            }
        }
    
    def _check_spacy_models(self) -> bool:
        """Check if spaCy models are available."""
        try:
            import spacy
            # Try to load the models
            spacy.load("en_core_web_sm")
            spacy.load("fr_core_news_sm")
            return True
        except Exception:
            return False
    
    def _check_data_directory(self) -> bool:
        """Check if data directory exists and is readable."""
        try:
            from pathlib import Path
            data_dir = Path(__file__).parent.parent / "data"
            return data_dir.exists() and data_dir.is_dir()
        except Exception:
            return False
    
    def _check_dependencies(self) -> bool:
        """Check critical dependencies are importable."""
        try:
            import questionary
            import pydantic
            import yaml
            return True
        except ImportError:
            return False


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoints."""
    
    def do_GET(self):
        """Handle GET requests for health endpoints."""
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/health/ready":
            self._handle_ready()
        elif self.path == "/health/live":
            self._handle_live()
        else:
            self._handle_404()
    
    def _handle_health(self):
        """Handle detailed health check."""
        try:
            response = HealthResponse()
            self._send_json_response(200, response.to_dict())
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._send_json_response(503, {"status": "unhealthy", "error": str(e)})
    
    def _handle_ready(self):
        """Handle Kubernetes readiness probe."""
        try:
            response = HealthResponse()
            checks = response.to_dict()["checks"]
            
            if all(checks.values()):
                self._send_json_response(200, {"status": "ready"})
            else:
                self._send_json_response(503, {"status": "not_ready", "failed_checks": 
                                              [k for k, v in checks.items() if not v]})
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            self._send_json_response(503, {"status": "not_ready", "error": str(e)})
    
    def _handle_live(self):
        """Handle Kubernetes liveness probe."""
        self._send_json_response(200, {"status": "alive"})
    
    def _handle_404(self):
        """Handle unknown endpoints."""
        self._send_json_response(404, {"error": "endpoint not found"})
    
    def _send_json_response(self, status_code: int, data: Dict[str, Any]):
        """Send JSON response with proper headers."""
        response_body = json.dumps(data, indent=2).encode('utf-8')
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_body)))
        self.end_headers()
        
        self.wfile.write(response_body)
    
    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        logger.info(format % args)


class HealthServer:
    """Lightweight health check HTTP server."""
    
    def __init__(self, port: int = 8001, host: str = "0.0.0.0"):
        self.port = port
        self.host = host
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the health server in a background thread."""
        try:
            self.server = HTTPServer((self.host, self.port), HealthHandler)
            self.thread = Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            logger.info(f"Health server started on {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start health server: {e}")
            raise
    
    def stop(self):
        """Stop the health server."""
        if self.server:
            self.server.shutdown()
            logger.info("Health server stopped")


# Track service start time
_start_time = time.time()

# Global server instance
_health_server = None


def start_health_server(port: int = 8001, host: str = "0.0.0.0"):
    """Start the global health server."""
    global _health_server
    if _health_server is None:
        _health_server = HealthServer(port, host)
        _health_server.start()


def stop_health_server():
    """Stop the global health server."""
    global _health_server
    if _health_server:
        _health_server.stop()
        _health_server = None


if __name__ == "__main__":
    # For testing the health server standalone
    import sys
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    server = HealthServer(port)
    
    try:
        print(f"Starting health server on port {port}...")
        server.start()
        print("Health server running. Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        import signal
        signal.pause()
        
    except KeyboardInterrupt:
        print("\\nStopping health server...")
        server.stop()
        print("Health server stopped.")
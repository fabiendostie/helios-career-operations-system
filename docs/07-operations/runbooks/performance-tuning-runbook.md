# Performance Tuning Runbook
# Helios Career Operations System

## Document Metadata
- **Version:** 1.0
- **Date:** 2025-09-20
- **Author:** Performance Engineering Team
- **Status:** Production Ready
- **Review Frequency:** Quarterly

---

## 1. Overview

This runbook provides comprehensive performance tuning procedures for the Helios Career Operations System to optimize for 1000+ concurrent users, including capacity planning, bottleneck identification, and optimization strategies.

### 1.1 Performance Targets
```yaml
# performance_targets.yml
targets:
  concurrent_users: 1000+
  response_time:
    p50: 500ms
    p95: 2000ms
    p99: 5000ms
  throughput: 500_requests_per_second
  error_rate: <0.5%
  availability: 99.9%

resource_targets:
  cpu_utilization: <70%
  memory_utilization: <80%
  disk_io: <80%
  network_bandwidth: <70%

scaling_parameters:
  horizontal_scaling_threshold: 70%_cpu_usage
  vertical_scaling_threshold: 85%_memory_usage
  auto_scaling_cooldown: 5_minutes
```

### 1.2 Performance Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│    API Gateway  │────│   Rate Limiter  │
│   (HAProxy)     │    │   (Kong/Nginx)  │    │   (Redis)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Orchestrator  │────│    Strategist   │────│     Analyst     │
│   (3 replicas)  │    │   (2 replicas)  │    │   (2 replicas)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │────│      Redis      │────│   Vector DB     │
│   (Primary +    │    │   (Cluster)     │    │   (Pinecone)    │
│    2 Replicas)  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 2. Performance Baseline and Monitoring

### 2.1 Performance Metrics Collection
```python
# performance_metrics.py
import psutil
import time
import redis
import psycopg2
import requests
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_io: Dict
    network_io: Dict
    response_times: Dict
    throughput: float
    error_rate: float
    active_connections: int

class PerformanceCollector:
    def __init__(self, config: Dict):
        self.config = config
        self.redis_client = redis.Redis(host=config['redis_host'], port=config['redis_port'])

    def collect_system_metrics(self) -> Dict:
        """Collect system-level performance metrics"""
        return {
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_io': dict(psutil.disk_io_counters()._asdict()),
            'network_io': dict(psutil.net_io_counters()._asdict()),
            'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0,
            'process_count': len(psutil.pids())
        }

    def collect_application_metrics(self) -> Dict:
        """Collect application-level performance metrics"""
        services = self.config['services']
        app_metrics = {}

        for service_name, service_config in services.items():
            try:
                # Response time measurement
                start_time = time.time()
                response = requests.get(f"{service_config['url']}/metrics", timeout=10)
                response_time = time.time() - start_time

                if response.status_code == 200:
                    metrics_data = response.json()
                    app_metrics[service_name] = {
                        'response_time': response_time,
                        'status': 'healthy',
                        'request_count': metrics_data.get('requests_total', 0),
                        'error_count': metrics_data.get('errors_total', 0),
                        'active_connections': metrics_data.get('active_connections', 0)
                    }
                else:
                    app_metrics[service_name] = {
                        'response_time': response_time,
                        'status': 'unhealthy',
                        'error': f"HTTP {response.status_code}"
                    }

            except Exception as e:
                app_metrics[service_name] = {
                    'status': 'unreachable',
                    'error': str(e)
                }

        return app_metrics

    def collect_database_metrics(self) -> Dict:
        """Collect database performance metrics"""
        try:
            conn = psycopg2.connect(
                host=self.config['database']['host'],
                port=self.config['database']['port'],
                database=self.config['database']['name'],
                user=self.config['database']['user'],
                password=self.config['database']['password']
            )

            cursor = conn.cursor()

            # Active connections
            cursor.execute("SELECT count(*) FROM pg_stat_activity;")
            active_connections = cursor.fetchone()[0]

            # Slow queries
            cursor.execute("""
                SELECT count(*)
                FROM pg_stat_statements
                WHERE mean_time > 1000;
            """)
            slow_queries = cursor.fetchone()[0] if cursor.fetchone() else 0

            # Cache hit ratio
            cursor.execute("""
                SELECT
                    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
                FROM pg_statio_user_tables;
            """)
            cache_hit_ratio = cursor.fetchone()[0] or 0

            # Database size
            cursor.execute(f"SELECT pg_database_size('{self.config['database']['name']}');")
            db_size = cursor.fetchone()[0]

            conn.close()

            return {
                'active_connections': active_connections,
                'slow_queries': slow_queries,
                'cache_hit_ratio': float(cache_hit_ratio),
                'database_size_bytes': db_size,
                'status': 'healthy'
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def collect_redis_metrics(self) -> Dict:
        """Collect Redis performance metrics"""
        try:
            info = self.redis_client.info()

            return {
                'used_memory': info['used_memory'],
                'used_memory_peak': info['used_memory_peak'],
                'connected_clients': info['connected_clients'],
                'total_commands_processed': info['total_commands_processed'],
                'keyspace_hits': info['keyspace_hits'],
                'keyspace_misses': info['keyspace_misses'],
                'hit_ratio': info['keyspace_hits'] / (info['keyspace_hits'] + info['keyspace_misses']) if (info['keyspace_hits'] + info['keyspace_misses']) > 0 else 0,
                'status': 'healthy'
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def generate_performance_snapshot(self) -> PerformanceMetrics:
        """Generate comprehensive performance snapshot"""
        system_metrics = self.collect_system_metrics()
        app_metrics = self.collect_application_metrics()
        db_metrics = self.collect_database_metrics()
        redis_metrics = self.collect_redis_metrics()

        # Calculate aggregated metrics
        response_times = {
            service: metrics.get('response_time', 0)
            for service, metrics in app_metrics.items()
        }

        total_requests = sum(
            metrics.get('request_count', 0)
            for metrics in app_metrics.values()
        )

        total_errors = sum(
            metrics.get('error_count', 0)
            for metrics in app_metrics.values()
        )

        error_rate = (total_errors / total_requests) * 100 if total_requests > 0 else 0

        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_usage=system_metrics['cpu_usage'],
            memory_usage=system_metrics['memory_usage'],
            disk_io=system_metrics['disk_io'],
            network_io=system_metrics['network_io'],
            response_times=response_times,
            throughput=total_requests / 60,  # requests per minute
            error_rate=error_rate,
            active_connections=db_metrics.get('active_connections', 0)
        )
```

### 2.2 Performance Benchmarking
```bash
#!/bin/bash
# performance_benchmark.sh

echo "📊 Performance Benchmarking for 1000+ Users"

# Configuration
TARGET_USERS=1000
RAMP_UP_TIME=300  # 5 minutes
TEST_DURATION=3600  # 1 hour
RESULTS_DIR="/var/log/performance/benchmark_$(date +%Y%m%d_%H%M%S)"

mkdir -p $RESULTS_DIR

# Step 1: Baseline measurement
echo "🔍 Collecting baseline metrics..."
python scripts/performance/collect_baseline.py --output="$RESULTS_DIR/baseline.json"

# Step 2: Load testing with artillery
echo "🚀 Starting load test with Artillery..."
cat > $RESULTS_DIR/artillery_config.yml << EOF
config:
  target: 'http://localhost:8000'
  phases:
    - duration: $RAMP_UP_TIME
      arrivalRate: 1
      rampTo: $((TARGET_USERS / 60))  # Users per second
    - duration: $TEST_DURATION
      arrivalRate: $((TARGET_USERS / 60))
  processor: "./scripts/performance/custom_functions.js"

scenarios:
  - name: "Profile Processing Workflow"
    weight: 40
    flow:
      - post:
          url: "/api/v1/profiles/upload"
          headers:
            Content-Type: "multipart/form-data"
          formData:
            file: "@test_data/sample_resume.pdf"
      - think: 2
      - get:
          url: "/api/v1/profiles/{{ profileId }}/status"
      - think: 5
      - get:
          url: "/api/v1/profiles/{{ profileId }}/career-paths"

  - name: "Analysis and Optimization"
    weight: 30
    flow:
      - post:
          url: "/api/v1/analysis/resume"
          json:
            profile_id: "{{ profileId }}"
            target_job: "Software Engineer"
      - think: 3
      - get:
          url: "/api/v1/analysis/{{ analysisId }}/results"
      - think: 2
      - post:
          url: "/api/v1/optimization/suggestions"
          json:
            analysis_id: "{{ analysisId }}"

  - name: "Document Generation"
    weight: 20
    flow:
      - post:
          url: "/api/v1/documents/generate"
          json:
            profile_id: "{{ profileId }}"
            template: "ats_optimized"
      - think: 10
      - get:
          url: "/api/v1/documents/{{ documentId }}/download"

  - name: "Health Checks"
    weight: 10
    flow:
      - get:
          url: "/health"
      - get:
          url: "/api/v1/metrics"
EOF

# Run Artillery load test
artillery run $RESULTS_DIR/artillery_config.yml --output $RESULTS_DIR/artillery_results.json

# Step 3: Generate Artillery HTML report
artillery report $RESULTS_DIR/artillery_results.json --output $RESULTS_DIR/artillery_report.html

# Step 4: Continuous monitoring during test
echo "📈 Monitoring system during load test..."
python scripts/performance/continuous_monitor.py \
    --duration=$((RAMP_UP_TIME + TEST_DURATION)) \
    --output="$RESULTS_DIR/system_metrics.json" &

MONITOR_PID=$!

# Step 5: Database performance monitoring
echo "🗄️ Monitoring database performance..."
while [ -f "/tmp/load_test_running" ]; do
    psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
        SELECT
            now() as timestamp,
            count(*) as active_connections,
            avg(duration) as avg_duration
        FROM pg_stat_activity
        WHERE state = 'active';
    " >> $RESULTS_DIR/db_performance.log
    sleep 30
done

# Step 6: Clean up
kill $MONITOR_PID 2>/dev/null || true
rm -f /tmp/load_test_running

echo "✅ Performance benchmark completed"
echo "📄 Results available in: $RESULTS_DIR"
```

---

## 3. Capacity Planning

### 3.1 Resource Capacity Analysis
```python
# capacity_planning.py
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class CapacityMetrics:
    current_users: int
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_usage: float
    response_time_p95: float
    error_rate: float

class CapacityPlanner:
    def __init__(self, historical_data_file: str):
        with open(historical_data_file) as f:
            self.historical_data = json.load(f)
        self.scaling_factors = self.calculate_scaling_factors()

    def calculate_scaling_factors(self) -> Dict:
        """Calculate resource scaling factors based on historical data"""
        # Analyze relationship between user count and resource usage
        user_counts = []
        cpu_usages = []
        memory_usages = []
        response_times = []

        for data_point in self.historical_data:
            user_counts.append(data_point['concurrent_users'])
            cpu_usages.append(data_point['cpu_usage'])
            memory_usages.append(data_point['memory_usage'])
            response_times.append(data_point['response_time_p95'])

        # Linear regression to find scaling factors
        cpu_factor = np.polyfit(user_counts, cpu_usages, 1)[0]
        memory_factor = np.polyfit(user_counts, memory_usages, 1)[0]
        response_time_factor = np.polyfit(user_counts, response_times, 1)[0]

        return {
            'cpu_per_user': cpu_factor,
            'memory_per_user': memory_factor,
            'response_time_per_user': response_time_factor
        }

    def project_capacity_requirements(self, target_users: int) -> Dict:
        """Project resource requirements for target user count"""
        projected_cpu = target_users * self.scaling_factors['cpu_per_user']
        projected_memory = target_users * self.scaling_factors['memory_per_user']
        projected_response_time = target_users * self.scaling_factors['response_time_per_user']

        # Calculate required instances based on per-instance limits
        cpu_instances = max(1, int(projected_cpu / 70))  # 70% CPU limit per instance
        memory_instances = max(1, int(projected_memory / 80))  # 80% memory limit per instance

        required_instances = max(cpu_instances, memory_instances)

        return {
            'target_users': target_users,
            'projected_cpu_usage': projected_cpu,
            'projected_memory_usage': projected_memory,
            'projected_response_time': projected_response_time,
            'required_instances': required_instances,
            'scaling_recommendation': self.get_scaling_recommendation(required_instances)
        }

    def get_scaling_recommendation(self, required_instances: int) -> Dict:
        """Generate scaling recommendations"""
        current_instances = 3  # Current orchestrator instances

        if required_instances > current_instances:
            return {
                'action': 'scale_up',
                'additional_instances': required_instances - current_instances,
                'urgency': 'high' if required_instances > current_instances * 2 else 'medium'
            }
        elif required_instances < current_instances * 0.5:
            return {
                'action': 'scale_down',
                'instances_to_remove': current_instances - required_instances,
                'urgency': 'low'
            }
        else:
            return {
                'action': 'maintain',
                'current_capacity': 'sufficient',
                'urgency': 'none'
            }

    def calculate_database_capacity(self, target_users: int) -> Dict:
        """Calculate database capacity requirements"""
        # Estimate based on user data patterns
        avg_profiles_per_user = 1.2
        avg_career_paths_per_profile = 3
        avg_analysis_results_per_profile = 5

        total_profiles = target_users * avg_profiles_per_user
        total_career_paths = total_profiles * avg_career_paths_per_profile
        total_analysis_results = total_profiles * avg_analysis_results_per_profile

        # Storage estimates (bytes)
        profile_size = 50000  # 50KB per profile
        career_path_size = 10000  # 10KB per career path
        analysis_result_size = 25000  # 25KB per analysis result

        total_storage = (
            total_profiles * profile_size +
            total_career_paths * career_path_size +
            total_analysis_results * analysis_result_size
        )

        # Connection pool sizing
        connections_per_user = 0.1  # Conservative estimate
        required_connections = int(target_users * connections_per_user)

        return {
            'storage_requirements_gb': total_storage / (1024**3),
            'required_connections': required_connections,
            'recommended_pool_size': required_connections * 1.5,  # 50% overhead
            'estimated_iops': target_users * 2,  # 2 IOPS per user
            'backup_storage_gb': (total_storage * 1.3) / (1024**3)  # 30% overhead
        }

    def generate_capacity_plan(self, target_users: int) -> Dict:
        """Generate comprehensive capacity plan"""
        app_capacity = self.project_capacity_requirements(target_users)
        db_capacity = self.calculate_database_capacity(target_users)

        return {
            'capacity_plan_date': datetime.now().isoformat(),
            'target_users': target_users,
            'application_tier': app_capacity,
            'database_tier': db_capacity,
            'infrastructure_recommendations': self.get_infrastructure_recommendations(app_capacity, db_capacity),
            'cost_estimates': self.calculate_cost_estimates(app_capacity, db_capacity)
        }

    def get_infrastructure_recommendations(self, app_capacity: Dict, db_capacity: Dict) -> Dict:
        """Generate infrastructure recommendations"""
        return {
            'compute': {
                'orchestrator_instances': app_capacity['required_instances'],
                'instance_type': 'c5.xlarge',  # 4 vCPU, 8GB RAM
                'auto_scaling': {
                    'min_instances': max(2, app_capacity['required_instances'] // 2),
                    'max_instances': app_capacity['required_instances'] * 2,
                    'scale_up_threshold': '70% CPU',
                    'scale_down_threshold': '30% CPU'
                }
            },
            'database': {
                'primary_instance': 'db.r5.2xlarge',  # 8 vCPU, 64GB RAM
                'read_replicas': 2,
                'storage_type': 'gp3',
                'storage_size_gb': max(100, int(db_capacity['storage_requirements_gb'] * 1.5)),
                'connection_pool_size': db_capacity['recommended_pool_size']
            },
            'cache': {
                'redis_cluster': 'cache.r6g.xlarge',  # 4 vCPU, 32GB RAM
                'cluster_nodes': 3,
                'memory_per_node_gb': 32
            },
            'load_balancer': {
                'type': 'application_load_balancer',
                'health_check_interval': 30,
                'connection_timeout': 60
            }
        }

    def calculate_cost_estimates(self, app_capacity: Dict, db_capacity: Dict) -> Dict:
        """Calculate monthly cost estimates"""
        # AWS pricing estimates (simplified)
        costs = {
            'compute': app_capacity['required_instances'] * 146,  # c5.xlarge monthly cost
            'database': 300,  # db.r5.2xlarge monthly cost
            'database_storage': db_capacity['storage_requirements_gb'] * 0.115,  # GP3 pricing
            'cache': 180,  # cache.r6g.xlarge monthly cost
            'load_balancer': 23,  # ALB monthly cost
            'data_transfer': 50,  # Estimated monthly data transfer
            'backup_storage': db_capacity['backup_storage_gb'] * 0.05  # S3 pricing
        }

        total_monthly = sum(costs.values())

        return {
            'monthly_costs_usd': costs,
            'total_monthly_usd': total_monthly,
            'cost_per_user_monthly': total_monthly / app_capacity['target_users'],
            'annual_cost_usd': total_monthly * 12
        }

# Usage example
historical_data = [
    {'concurrent_users': 100, 'cpu_usage': 25, 'memory_usage': 30, 'response_time_p95': 800},
    {'concurrent_users': 200, 'cpu_usage': 35, 'memory_usage': 45, 'response_time_p95': 1200},
    {'concurrent_users': 500, 'cpu_usage': 55, 'memory_usage': 65, 'response_time_p95': 1800},
    {'concurrent_users': 750, 'cpu_usage': 68, 'memory_usage': 75, 'response_time_p95': 2200}
]

planner = CapacityPlanner('historical_performance.json')
capacity_plan = planner.generate_capacity_plan(1000)
```

---

## 4. Database Optimization

### 4.1 Query Optimization
```sql
-- query_optimization.sql
-- Performance optimization queries for PostgreSQL

-- 1. Identify slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
WHERE mean_time > 1000  -- Queries taking more than 1 second
ORDER BY mean_time DESC
LIMIT 20;

-- 2. Create performance indexes
-- Career profiles search optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_career_profiles_user_skills
ON career_profiles USING GIN (skills_inventory);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_career_profiles_created_at
ON career_profiles (created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_career_profiles_user_id_status
ON career_profiles (user_id, status) WHERE status = 'active';

-- Session management optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_session_states_expires_at
ON session_states (expires_at) WHERE expires_at > NOW();

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_session_states_user_id_active
ON session_states (user_id, last_activity) WHERE status = 'active';

-- Analysis results optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_results_profile_created
ON analysis_results (profile_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_results_score
ON analysis_results (optimization_score) WHERE optimization_score IS NOT NULL;

-- 3. Optimize frequent queries
-- Fast user profile lookup
CREATE OR REPLACE FUNCTION get_user_profile_summary(user_uuid UUID)
RETURNS TABLE (
    profile_id BIGINT,
    skills_count INT,
    experience_years DECIMAL,
    last_updated TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cp.id,
        jsonb_array_length(cp.skills_inventory->'technical') as skills_count,
        EXTRACT(YEAR FROM (cp.updated_at - cp.created_at)) as experience_years,
        cp.updated_at
    FROM career_profiles cp
    WHERE cp.user_id = user_uuid
      AND cp.status = 'active'
    ORDER BY cp.updated_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- 4. Materialized view for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS user_analytics_summary AS
SELECT
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) as profiles_created,
    AVG(jsonb_array_length(skills_inventory->'technical')) as avg_skills,
    COUNT(DISTINCT user_id) as unique_users
FROM career_profiles
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date;

-- Refresh schedule for materialized view
CREATE INDEX ON user_analytics_summary (date);

-- 5. Connection pooling optimization
-- Set optimal connection parameters
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
SELECT pg_reload_conf();
```

### 4.2 Database Performance Monitoring
```bash
#!/bin/bash
# database_performance_monitor.sh

echo "🗄️ Database Performance Monitoring"

DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-helios}
DB_USER=${DB_USER:-helios_user}

# Function to execute PostgreSQL query
execute_query() {
    local query="$1"
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "$query"
}

# Function to monitor database performance
monitor_database_performance() {
    echo "📊 Database Performance Metrics"

    # Connection count
    active_connections=$(execute_query "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")
    total_connections=$(execute_query "SELECT count(*) FROM pg_stat_activity;")
    max_connections=$(execute_query "SHOW max_connections;" | tr -d ' ')

    echo "Connections: $active_connections active, $total_connections total, $max_connections max"

    # Database size
    db_size=$(execute_query "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));")
    echo "Database size: $db_size"

    # Cache hit ratio
    cache_hit_ratio=$(execute_query "
        SELECT round(
            sum(heap_blks_hit) * 100.0 /
            NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0), 2
        )
        FROM pg_statio_user_tables;
    ")
    echo "Cache hit ratio: ${cache_hit_ratio}%"

    # Top 5 largest tables
    echo "Top 5 largest tables:"
    execute_query "
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 5;
    "

    # Slow queries
    echo "Current slow queries (>2 seconds):"
    execute_query "
        SELECT
            now() - pg_stat_activity.query_start AS duration,
            query,
            state
        FROM pg_stat_activity
        WHERE (now() - pg_stat_activity.query_start) > interval '2 seconds'
          AND state = 'active'
          AND query NOT LIKE '%pg_stat_activity%'
        ORDER BY duration DESC;
    "

    # Index usage
    echo "Indexes with low usage:"
    execute_query "
        SELECT
            schemaname,
            tablename,
            indexname,
            idx_tup_read,
            idx_tup_fetch,
            pg_size_pretty(pg_relation_size(indexrelid)) as size
        FROM pg_stat_user_indexes
        WHERE idx_tup_read < 1000
          AND pg_relation_size(indexrelid) > 1048576  -- > 1MB
        ORDER BY pg_relation_size(indexrelid) DESC;
    "
}

# Function to optimize database
optimize_database() {
    echo "🔧 Database Optimization"

    # Update table statistics
    echo "Updating table statistics..."
    execute_query "ANALYZE;"

    # Reindex frequently used tables
    echo "Reindexing career_profiles table..."
    execute_query "REINDEX TABLE career_profiles;"

    echo "Reindexing session_states table..."
    execute_query "REINDEX TABLE session_states;"

    # Vacuum analyze
    echo "Running VACUUM ANALYZE..."
    execute_query "VACUUM ANALYZE;"

    # Update materialized views
    echo "Refreshing materialized views..."
    execute_query "REFRESH MATERIALIZED VIEW CONCURRENTLY user_analytics_summary;"

    echo "✅ Database optimization completed"
}

# Function to check for blocking queries
check_blocking_queries() {
    echo "🔒 Checking for blocking queries..."

    execute_query "
        SELECT
            blocked_locks.pid AS blocked_pid,
            blocked_activity.usename AS blocked_user,
            blocking_locks.pid AS blocking_pid,
            blocking_activity.usename AS blocking_user,
            blocked_activity.query AS blocked_statement,
            blocking_activity.query AS current_statement_in_blocking_process,
            blocked_activity.application_name AS blocked_application,
            blocking_activity.application_name AS blocking_application
        FROM pg_catalog.pg_locks blocked_locks
        JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
        JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
            AND blocking_locks.DATABASE IS NOT DISTINCT FROM blocked_locks.DATABASE
            AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
            AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
            AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
            AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
            AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
            AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
            AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
            AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
            AND blocking_locks.pid != blocked_locks.pid
        JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
        WHERE NOT blocked_locks.GRANTED;
    "
}

# Main execution
case "${1:-monitor}" in
    "monitor")
        monitor_database_performance
        ;;
    "optimize")
        optimize_database
        ;;
    "blocking")
        check_blocking_queries
        ;;
    "all")
        monitor_database_performance
        echo "---"
        check_blocking_queries
        echo "---"
        optimize_database
        ;;
    *)
        echo "Usage: $0 {monitor|optimize|blocking|all}"
        exit 1
        ;;
esac
```

---

## 5. Application-Level Optimization

### 5.1 Caching Strategy
```python
# caching_optimization.py
import redis
import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from functools import wraps

class CacheOptimizer:
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        self.default_ttl = 3600  # 1 hour

    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def cached(self, ttl: int = None, prefix: str = None):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_prefix = prefix or f"func:{func.__name__}"
                cache_key = self.cache_key(cache_prefix, *args, **kwargs)

                # Try to get from cache
                try:
                    cached_result = self.redis_client.get(cache_key)
                    if cached_result:
                        return json.loads(cached_result)
                except Exception as e:
                    print(f"Cache read error: {e}")

                # Execute function and cache result
                result = func(*args, **kwargs)

                try:
                    cache_ttl = ttl or self.default_ttl
                    self.redis_client.setex(
                        cache_key,
                        cache_ttl,
                        json.dumps(result, default=str)
                    )
                except Exception as e:
                    print(f"Cache write error: {e}")

                return result
            return wrapper
        return decorator

    def invalidate_pattern(self, pattern: str):
        """Invalidate all cache keys matching pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                return len(keys)
        except Exception as e:
            print(f"Cache invalidation error: {e}")
        return 0

    def warm_cache(self, cache_config: Dict):
        """Pre-populate cache with frequently accessed data"""
        for cache_item in cache_config['warm_items']:
            try:
                if cache_item['type'] == 'user_profiles':
                    self.warm_user_profiles()
                elif cache_item['type'] == 'skill_mappings':
                    self.warm_skill_mappings()
                elif cache_item['type'] == 'career_paths':
                    self.warm_career_paths()
            except Exception as e:
                print(f"Cache warming error for {cache_item['type']}: {e}")

    @cached(ttl=1800, prefix="user_profile")  # 30 minutes
    def get_user_profile(self, user_id: str) -> Dict:
        """Cached user profile retrieval"""
        # This would typically call the database
        pass

    @cached(ttl=3600, prefix="skill_mapping")  # 1 hour
    def get_skill_mapping(self, skill_name: str) -> Dict:
        """Cached skill mapping retrieval"""
        pass

    @cached(ttl=7200, prefix="career_path")  # 2 hours
    def generate_career_path(self, profile_id: str, target_role: str) -> Dict:
        """Cached career path generation"""
        pass

# Connection pooling optimization
class ConnectionPoolOptimizer:
    def __init__(self):
        self.pool_configs = {
            'postgresql': {
                'min_connections': 10,
                'max_connections': 50,
                'connection_timeout': 30,
                'idle_timeout': 300
            },
            'redis': {
                'max_connections': 20,
                'retry_on_timeout': True,
                'socket_timeout': 5
            }
        }

    def optimize_postgresql_pool(self):
        """Optimize PostgreSQL connection pool"""
        import psycopg2.pool

        return psycopg2.pool.ThreadedConnectionPool(
            minconn=self.pool_configs['postgresql']['min_connections'],
            maxconn=self.pool_configs['postgresql']['max_connections'],
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )

    def optimize_redis_pool(self):
        """Optimize Redis connection pool"""
        return redis.ConnectionPool(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            max_connections=self.pool_configs['redis']['max_connections'],
            retry_on_timeout=self.pool_configs['redis']['retry_on_timeout'],
            socket_timeout=self.pool_configs['redis']['socket_timeout']
        )

# Async processing optimization
import asyncio
import aiohttp

class AsyncOptimizer:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(50)  # Limit concurrent operations

    async def process_batch_profiles(self, profile_ids: list) -> list:
        """Process multiple profiles concurrently"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.process_single_profile(session, profile_id)
                for profile_id in profile_ids
            ]
            return await asyncio.gather(*tasks, return_exceptions=True)

    async def process_single_profile(self, session, profile_id: str):
        """Process single profile with concurrency control"""
        async with self.semaphore:
            try:
                async with session.get(f'/api/profiles/{profile_id}/process') as response:
                    return await response.json()
            except Exception as e:
                return {'error': str(e), 'profile_id': profile_id}
```

### 5.2 API Optimization
```python
# api_optimization.py
from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
import time
import asyncio
from typing import List, Dict
import uvloop

# Performance-optimized FastAPI setup
def create_optimized_app() -> FastAPI:
    app = FastAPI(
        title="Helios Career Operations System",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )

    # Add performance middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Performance monitoring middleware
    @app.middleware("http")
    async def performance_middleware(request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        # Log slow requests
        if process_time > 2.0:
            print(f"Slow request: {request.url} took {process_time:.2f}s")

        return response

    return app

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = create_optimized_app()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Optimized endpoints
@app.post("/api/v1/profiles/batch")
@limiter.limit("10/minute")  # Rate limiting
async def process_profiles_batch(
    profile_requests: List[Dict],
    background_tasks: BackgroundTasks,
    request: Request
):
    """Process multiple profiles with optimization"""

    # Validate request size
    if len(profile_requests) > 50:
        raise HTTPException(400, "Batch size limited to 50 profiles")

    # Process in background for large batches
    if len(profile_requests) > 10:
        task_id = generate_task_id()
        background_tasks.add_task(
            process_large_batch,
            profile_requests,
            task_id
        )
        return {"task_id": task_id, "status": "processing"}

    # Process small batches synchronously
    results = await process_profiles_async(profile_requests)
    return {"results": results, "status": "completed"}

# Response caching
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

@app.get("/api/v1/skills/mapping")
@cache(expire=3600)  # Cache for 1 hour
async def get_skills_mapping():
    """Cached skills mapping endpoint"""
    return await load_skills_mapping()

# Streaming responses for large data
from fastapi.responses import StreamingResponse
import io

@app.get("/api/v1/profiles/{profile_id}/export")
async def export_profile_data(profile_id: str):
    """Stream large profile data"""

    def generate_profile_data():
        # Stream data in chunks
        yield json.dumps({"profile_id": profile_id})
        yield "\n"

        for chunk in get_profile_data_chunks(profile_id):
            yield json.dumps(chunk)
            yield "\n"

    return StreamingResponse(
        generate_profile_data(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f"attachment; filename=profile_{profile_id}.ndjson"}
    )

# Connection pooling for external services
import httpx

class HTTPClientSingleton:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
        return cls._instance

    @property
    def client(self):
        return self._client

# Use uvloop for better async performance
if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=4,
        loop="uvloop",
        http="httptools"
    )
```

---

## 6. Scaling Strategies

### 6.1 Horizontal Scaling
```yaml
# kubernetes_autoscaling.yml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: helios-orchestrator-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: helios-orchestrator
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: helios-strategist-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: helios-strategist
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: queue_length
      target:
        type: AverageValue
        averageValue: "30"

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: helios-analyst-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: helios-analyst
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 85
```

### 6.2 Auto-Scaling Implementation
```python
# auto_scaling_controller.py
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List
import kubernetes
from kubernetes import client, config

class AutoScalingController:
    def __init__(self, config_file: str):
        with open(config_file) as f:
            self.scaling_config = json.load(f)

        # Load Kubernetes config
        config.load_incluster_config()  # For in-cluster
        # config.load_kube_config()  # For local development

        self.apps_v1 = client.AppsV1Api()
        self.metrics_client = client.CustomObjectsApi()

    async def monitor_and_scale(self):
        """Main monitoring and scaling loop"""
        while True:
            try:
                await self.check_scaling_conditions()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"Scaling monitor error: {e}")
                await asyncio.sleep(60)

    async def check_scaling_conditions(self):
        """Check if scaling actions are needed"""
        services = self.scaling_config['services']

        for service_name, service_config in services.items():
            current_metrics = await self.get_service_metrics(service_name)
            scaling_decision = self.evaluate_scaling_decision(
                service_name,
                current_metrics,
                service_config
            )

            if scaling_decision['action'] != 'none':
                await self.execute_scaling_action(service_name, scaling_decision)

    async def get_service_metrics(self, service_name: str) -> Dict:
        """Get current metrics for a service"""
        try:
            # Get deployment info
            deployment = self.apps_v1.read_namespaced_deployment(
                name=f"helios-{service_name}",
                namespace="default"
            )

            current_replicas = deployment.status.ready_replicas or 0

            # Get custom metrics (queue length, response time, etc.)
            custom_metrics = await self.get_custom_metrics(service_name)

            # Get resource metrics from metrics server
            resource_metrics = await self.get_resource_metrics(service_name)

            return {
                'current_replicas': current_replicas,
                'cpu_usage': resource_metrics.get('cpu_usage', 0),
                'memory_usage': resource_metrics.get('memory_usage', 0),
                'queue_length': custom_metrics.get('queue_length', 0),
                'response_time_p95': custom_metrics.get('response_time_p95', 0),
                'error_rate': custom_metrics.get('error_rate', 0)
            }

        except Exception as e:
            print(f"Error getting metrics for {service_name}: {e}")
            return {}

    def evaluate_scaling_decision(self, service_name: str, metrics: Dict, config: Dict) -> Dict:
        """Evaluate whether scaling action is needed"""
        thresholds = config['scaling_thresholds']
        min_replicas = config['min_replicas']
        max_replicas = config['max_replicas']
        current_replicas = metrics.get('current_replicas', min_replicas)

        # Scale up conditions
        scale_up_triggers = []

        if metrics.get('cpu_usage', 0) > thresholds['cpu_scale_up']:
            scale_up_triggers.append(f"CPU usage: {metrics['cpu_usage']}%")

        if metrics.get('memory_usage', 0) > thresholds['memory_scale_up']:
            scale_up_triggers.append(f"Memory usage: {metrics['memory_usage']}%")

        if metrics.get('queue_length', 0) > thresholds['queue_scale_up']:
            scale_up_triggers.append(f"Queue length: {metrics['queue_length']}")

        if metrics.get('response_time_p95', 0) > thresholds['response_time_scale_up']:
            scale_up_triggers.append(f"Response time: {metrics['response_time_p95']}ms")

        # Scale down conditions
        scale_down_triggers = []

        if (metrics.get('cpu_usage', 100) < thresholds['cpu_scale_down'] and
            metrics.get('memory_usage', 100) < thresholds['memory_scale_down'] and
            metrics.get('queue_length', 100) < thresholds['queue_scale_down']):
            scale_down_triggers.append("All metrics below scale-down thresholds")

        # Determine action
        if scale_up_triggers and current_replicas < max_replicas:
            target_replicas = min(max_replicas, current_replicas + config['scale_step'])
            return {
                'action': 'scale_up',
                'target_replicas': target_replicas,
                'current_replicas': current_replicas,
                'triggers': scale_up_triggers
            }
        elif scale_down_triggers and current_replicas > min_replicas:
            target_replicas = max(min_replicas, current_replicas - config['scale_step'])
            return {
                'action': 'scale_down',
                'target_replicas': target_replicas,
                'current_replicas': current_replicas,
                'triggers': scale_down_triggers
            }
        else:
            return {
                'action': 'none',
                'current_replicas': current_replicas,
                'reason': 'No scaling conditions met'
            }

    async def execute_scaling_action(self, service_name: str, decision: Dict):
        """Execute the scaling action"""
        try:
            deployment_name = f"helios-{service_name}"

            # Update deployment replica count
            body = {'spec': {'replicas': decision['target_replicas']}}

            self.apps_v1.patch_namespaced_deployment_scale(
                name=deployment_name,
                namespace="default",
                body=body
            )

            print(f"Scaled {service_name}: {decision['current_replicas']} -> {decision['target_replicas']}")
            print(f"Triggers: {decision['triggers']}")

            # Log scaling event
            await self.log_scaling_event(service_name, decision)

        except Exception as e:
            print(f"Error executing scaling action for {service_name}: {e}")

    async def log_scaling_event(self, service_name: str, decision: Dict):
        """Log scaling event for analysis"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'service': service_name,
            'action': decision['action'],
            'from_replicas': decision['current_replicas'],
            'to_replicas': decision['target_replicas'],
            'triggers': decision['triggers']
        }

        # Store in monitoring system
        print(f"Scaling event: {json.dumps(event)}")

# Configuration example
scaling_config = {
    "services": {
        "orchestrator": {
            "min_replicas": 3,
            "max_replicas": 20,
            "scale_step": 2,
            "scaling_thresholds": {
                "cpu_scale_up": 70,
                "cpu_scale_down": 30,
                "memory_scale_up": 80,
                "memory_scale_down": 40,
                "queue_scale_up": 50,
                "queue_scale_down": 10,
                "response_time_scale_up": 2000,
                "response_time_scale_down": 500
            }
        },
        "strategist": {
            "min_replicas": 2,
            "max_replicas": 10,
            "scale_step": 1,
            "scaling_thresholds": {
                "cpu_scale_up": 80,
                "cpu_scale_down": 40,
                "memory_scale_up": 85,
                "memory_scale_down": 50,
                "queue_scale_up": 30,
                "queue_scale_down": 5,
                "response_time_scale_up": 5000,
                "response_time_scale_down": 2000
            }
        }
    }
}
```

---

## 7. Load Testing and Performance Validation

### 7.1 Comprehensive Load Testing
```bash
#!/bin/bash
# comprehensive_load_test.sh

echo "🚀 Comprehensive Load Testing for 1000+ Users"

# Test configuration
MAX_USERS=1500
RAMP_UP_DURATION=600  # 10 minutes
STEADY_DURATION=1800  # 30 minutes
RAMP_DOWN_DURATION=300  # 5 minutes

RESULTS_DIR="/var/log/performance/load_test_$(date +%Y%m%d_%H%M%S)"
mkdir -p $RESULTS_DIR

# Step 1: Pre-test system check
echo "🔍 Pre-test system check..."
python scripts/performance/pre_test_check.py --output="$RESULTS_DIR/pre_test.json"

# Step 2: Start monitoring
echo "📊 Starting system monitoring..."
python scripts/performance/system_monitor.py \
    --duration=$((RAMP_UP_DURATION + STEADY_DURATION + RAMP_DOWN_DURATION + 300)) \
    --output="$RESULTS_DIR/system_metrics.json" &
MONITOR_PID=$!

# Step 3: K6 load test configuration
cat > $RESULTS_DIR/load_test.js << EOF
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

export let errorRate = new Rate('errors');

export let options = {
  stages: [
    { duration: '${RAMP_UP_DURATION}s', target: $MAX_USERS },
    { duration: '${STEADY_DURATION}s', target: $MAX_USERS },
    { duration: '${RAMP_DOWN_DURATION}s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000', 'p(99)<5000'],
    http_req_failed: ['rate<0.1'],
    errors: ['rate<0.05'],
  },
};

const BASE_URL = 'http://localhost:8000';

export default function() {
  let scenarios = [
    profileUpload,
    careerPathGeneration,
    analysisOptimization,
    documentGeneration
  ];

  // Randomly select scenario
  let scenario = scenarios[Math.floor(Math.random() * scenarios.length)];
  scenario();

  sleep(Math.random() * 3 + 1); // 1-4 second pause
}

function profileUpload() {
  let response = http.post(\`\${BASE_URL}/api/v1/profiles/upload\`, {
    file: http.file(generateRandomProfile(), 'profile.json'),
  });

  let success = check(response, {
    'profile upload status is 200': (r) => r.status === 200,
    'profile upload response time < 5s': (r) => r.timings.duration < 5000,
  });

  errorRate.add(!success);

  if (success && response.json('profile_id')) {
    // Follow-up request
    let profileId = response.json('profile_id');
    sleep(2);

    let statusResponse = http.get(\`\${BASE_URL}/api/v1/profiles/\${profileId}/status\`);
    check(statusResponse, {
      'status check is 200': (r) => r.status === 200,
    });
  }
}

function careerPathGeneration() {
  let profileId = \`test-profile-\${Math.floor(Math.random() * 1000)}\`;

  let response = http.post(\`\${BASE_URL}/api/v1/career-paths/generate\`,
    JSON.stringify({
      profile_id: profileId,
      target_role: 'Software Engineer',
      experience_level: 'mid'
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  let success = check(response, {
    'career path generation status is 200': (r) => r.status === 200,
    'career path response time < 10s': (r) => r.timings.duration < 10000,
  });

  errorRate.add(!success);
}

function analysisOptimization() {
  let response = http.post(\`\${BASE_URL}/api/v1/analysis/optimize\`,
    JSON.stringify({
      resume_text: generateRandomResumeText(),
      target_job_description: 'Senior Software Developer position...'
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  let success = check(response, {
    'analysis optimization status is 200': (r) => r.status === 200,
    'analysis response time < 15s': (r) => r.timings.duration < 15000,
  });

  errorRate.add(!success);
}

function documentGeneration() {
  let response = http.post(\`\${BASE_URL}/api/v1/documents/generate\`,
    JSON.stringify({
      profile_id: \`test-profile-\${Math.floor(Math.random() * 1000)}\`,
      document_type: 'resume',
      template: 'ats_optimized'
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  let success = check(response, {
    'document generation status is 200': (r) => r.status === 200,
    'document response time < 20s': (r) => r.timings.duration < 20000,
  });

  errorRate.add(!success);
}

function generateRandomProfile() {
  return JSON.stringify({
    name: \`Test User \${Math.floor(Math.random() * 10000)}\`,
    skills: ['JavaScript', 'Python', 'React', 'Node.js'],
    experience: Math.floor(Math.random() * 10) + 1
  });
}

function generateRandomResumeText() {
  return 'Experienced software developer with expertise in web technologies...';
}
EOF

# Step 4: Run K6 load test
echo "⚡ Running K6 load test..."
k6 run --out json=$RESULTS_DIR/k6_results.json $RESULTS_DIR/load_test.js

# Step 5: Stop monitoring
kill $MONITOR_PID 2>/dev/null || true

# Step 6: Post-test analysis
echo "📈 Running post-test analysis..."
python scripts/performance/analyze_results.py \
    --k6-results="$RESULTS_DIR/k6_results.json" \
    --system-metrics="$RESULTS_DIR/system_metrics.json" \
    --output="$RESULTS_DIR/analysis_report.json"

# Step 7: Generate HTML report
echo "📄 Generating HTML report..."
python scripts/performance/generate_html_report.py \
    --results-dir="$RESULTS_DIR" \
    --output="$RESULTS_DIR/load_test_report.html"

echo "✅ Load testing completed"
echo "📊 Results available in: $RESULTS_DIR"
echo "🌐 HTML report: $RESULTS_DIR/load_test_report.html"
```

### 7.2 Performance Regression Testing
```python
# performance_regression_test.py
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class PerformanceBaseline:
    test_name: str
    baseline_date: datetime
    response_time_p95: float
    throughput: float
    error_rate: float
    resource_usage: Dict

class PerformanceRegressionTester:
    def __init__(self, baseline_file: str):
        self.baseline_file = baseline_file
        self.baselines = self.load_baselines()
        self.regression_thresholds = {
            'response_time_degradation': 0.20,  # 20% degradation
            'throughput_degradation': 0.15,     # 15% degradation
            'error_rate_increase': 0.05,        # 5% absolute increase
            'resource_usage_increase': 0.25     # 25% increase
        }

    def load_baselines(self) -> Dict[str, PerformanceBaseline]:
        """Load performance baselines from file"""
        try:
            with open(self.baseline_file) as f:
                data = json.load(f)

            baselines = {}
            for test_name, baseline_data in data.items():
                baselines[test_name] = PerformanceBaseline(
                    test_name=test_name,
                    baseline_date=datetime.fromisoformat(baseline_data['baseline_date']),
                    response_time_p95=baseline_data['response_time_p95'],
                    throughput=baseline_data['throughput'],
                    error_rate=baseline_data['error_rate'],
                    resource_usage=baseline_data['resource_usage']
                )
            return baselines
        except FileNotFoundError:
            return {}

    def run_regression_test(self, test_results: Dict) -> Dict:
        """Run regression analysis on test results"""
        regression_report = {
            'test_date': datetime.now().isoformat(),
            'regressions_detected': [],
            'improvements_detected': [],
            'test_results': test_results,
            'overall_status': 'pass'
        }

        for test_name, current_results in test_results.items():
            if test_name in self.baselines:
                regression_analysis = self.analyze_test_regression(
                    test_name,
                    current_results,
                    self.baselines[test_name]
                )

                if regression_analysis['has_regression']:
                    regression_report['regressions_detected'].append(regression_analysis)
                    regression_report['overall_status'] = 'fail'

                if regression_analysis['has_improvement']:
                    regression_report['improvements_detected'].append(regression_analysis)

        return regression_report

    def analyze_test_regression(self, test_name: str, current: Dict, baseline: PerformanceBaseline) -> Dict:
        """Analyze if current test results show regression"""
        analysis = {
            'test_name': test_name,
            'has_regression': False,
            'has_improvement': False,
            'regressions': [],
            'improvements': [],
            'comparison': {}
        }

        # Response time analysis
        response_time_change = (current['response_time_p95'] - baseline.response_time_p95) / baseline.response_time_p95
        analysis['comparison']['response_time_change'] = response_time_change

        if response_time_change > self.regression_thresholds['response_time_degradation']:
            analysis['has_regression'] = True
            analysis['regressions'].append({
                'metric': 'response_time_p95',
                'baseline': baseline.response_time_p95,
                'current': current['response_time_p95'],
                'change_percent': response_time_change * 100,
                'threshold': self.regression_thresholds['response_time_degradation'] * 100
            })
        elif response_time_change < -0.10:  # 10% improvement
            analysis['has_improvement'] = True
            analysis['improvements'].append({
                'metric': 'response_time_p95',
                'improvement_percent': abs(response_time_change) * 100
            })

        # Throughput analysis
        throughput_change = (current['throughput'] - baseline.throughput) / baseline.throughput
        analysis['comparison']['throughput_change'] = throughput_change

        if throughput_change < -self.regression_thresholds['throughput_degradation']:
            analysis['has_regression'] = True
            analysis['regressions'].append({
                'metric': 'throughput',
                'baseline': baseline.throughput,
                'current': current['throughput'],
                'change_percent': throughput_change * 100,
                'threshold': -self.regression_thresholds['throughput_degradation'] * 100
            })
        elif throughput_change > 0.15:  # 15% improvement
            analysis['has_improvement'] = True
            analysis['improvements'].append({
                'metric': 'throughput',
                'improvement_percent': throughput_change * 100
            })

        # Error rate analysis
        error_rate_change = current['error_rate'] - baseline.error_rate
        analysis['comparison']['error_rate_change'] = error_rate_change

        if error_rate_change > self.regression_thresholds['error_rate_increase']:
            analysis['has_regression'] = True
            analysis['regressions'].append({
                'metric': 'error_rate',
                'baseline': baseline.error_rate,
                'current': current['error_rate'],
                'change_absolute': error_rate_change,
                'threshold': self.regression_thresholds['error_rate_increase']
            })

        # Resource usage analysis
        cpu_change = (current['resource_usage']['cpu'] - baseline.resource_usage['cpu']) / baseline.resource_usage['cpu']
        memory_change = (current['resource_usage']['memory'] - baseline.resource_usage['memory']) / baseline.resource_usage['memory']

        if cpu_change > self.regression_thresholds['resource_usage_increase']:
            analysis['has_regression'] = True
            analysis['regressions'].append({
                'metric': 'cpu_usage',
                'baseline': baseline.resource_usage['cpu'],
                'current': current['resource_usage']['cpu'],
                'change_percent': cpu_change * 100,
                'threshold': self.regression_thresholds['resource_usage_increase'] * 100
            })

        if memory_change > self.regression_thresholds['resource_usage_increase']:
            analysis['has_regression'] = True
            analysis['regressions'].append({
                'metric': 'memory_usage',
                'baseline': baseline.resource_usage['memory'],
                'current': current['resource_usage']['memory'],
                'change_percent': memory_change * 100,
                'threshold': self.regression_thresholds['resource_usage_increase'] * 100
            })

        return analysis

    def update_baseline(self, test_name: str, new_results: Dict):
        """Update baseline with new results if they're better"""
        if test_name not in self.baselines:
            # Create new baseline
            self.baselines[test_name] = PerformanceBaseline(
                test_name=test_name,
                baseline_date=datetime.now(),
                response_time_p95=new_results['response_time_p95'],
                throughput=new_results['throughput'],
                error_rate=new_results['error_rate'],
                resource_usage=new_results['resource_usage']
            )
        else:
            # Update baseline if results are significantly better
            current_baseline = self.baselines[test_name]

            should_update = (
                new_results['response_time_p95'] < current_baseline.response_time_p95 * 0.9 and
                new_results['throughput'] > current_baseline.throughput * 1.1 and
                new_results['error_rate'] <= current_baseline.error_rate
            )

            if should_update:
                self.baselines[test_name] = PerformanceBaseline(
                    test_name=test_name,
                    baseline_date=datetime.now(),
                    response_time_p95=new_results['response_time_p95'],
                    throughput=new_results['throughput'],
                    error_rate=new_results['error_rate'],
                    resource_usage=new_results['resource_usage']
                )

                print(f"Updated baseline for {test_name} due to significant improvements")

        self.save_baselines()

    def save_baselines(self):
        """Save baselines to file"""
        data = {}
        for test_name, baseline in self.baselines.items():
            data[test_name] = {
                'baseline_date': baseline.baseline_date.isoformat(),
                'response_time_p95': baseline.response_time_p95,
                'throughput': baseline.throughput,
                'error_rate': baseline.error_rate,
                'resource_usage': baseline.resource_usage
            }

        with open(self.baseline_file, 'w') as f:
            json.dump(data, f, indent=2)

    def generate_regression_report(self, regression_results: Dict) -> str:
        """Generate human-readable regression report"""
        report = f"""
Performance Regression Test Report
=================================

Test Date: {regression_results['test_date']}
Overall Status: {regression_results['overall_status'].upper()}

"""

        if regression_results['regressions_detected']:
            report += "🚨 REGRESSIONS DETECTED:\n"
            report += "=" * 30 + "\n"

            for regression in regression_results['regressions_detected']:
                report += f"\nTest: {regression['test_name']}\n"
                for reg in regression['regressions']:
                    report += f"  - {reg['metric']}: "
                    if 'change_percent' in reg:
                        report += f"{reg['change_percent']:.1f}% degradation "
                        report += f"(threshold: {reg['threshold']:.1f}%)\n"
                    else:
                        report += f"{reg['change_absolute']:.3f} absolute increase "
                        report += f"(threshold: {reg['threshold']:.3f})\n"
                    report += f"    Baseline: {reg['baseline']:.2f}, Current: {reg['current']:.2f}\n"

        if regression_results['improvements_detected']:
            report += "\n✅ IMPROVEMENTS DETECTED:\n"
            report += "=" * 30 + "\n"

            for improvement in regression_results['improvements_detected']:
                report += f"\nTest: {improvement['test_name']}\n"
                for imp in improvement['improvements']:
                    report += f"  - {imp['metric']}: {imp['improvement_percent']:.1f}% improvement\n"

        if not regression_results['regressions_detected'] and not regression_results['improvements_detected']:
            report += "✅ No significant performance changes detected.\n"

        return report

# Example usage
test_results = {
    'profile_upload_1000_users': {
        'response_time_p95': 1850.5,
        'throughput': 245.2,
        'error_rate': 0.008,
        'resource_usage': {'cpu': 68.5, 'memory': 72.1}
    },
    'career_path_generation_1000_users': {
        'response_time_p95': 4200.8,
        'throughput': 85.7,
        'error_rate': 0.012,
        'resource_usage': {'cpu': 75.2, 'memory': 81.3}
    }
}

tester = PerformanceRegressionTester('performance_baselines.json')
regression_report = tester.run_regression_test(test_results)
print(tester.generate_regression_report(regression_report))
```

---

## 8. Success Criteria and KPIs

### 8.1 Performance KPIs Dashboard
```yaml
# performance_kpis.yml
performance_kpis:
  user_experience:
    response_time_p50:
      target: 500ms
      warning: 750ms
      critical: 1000ms

    response_time_p95:
      target: 2000ms
      warning: 3000ms
      critical: 5000ms

    page_load_time:
      target: 3000ms
      warning: 5000ms
      critical: 8000ms

  system_performance:
    throughput:
      target: 500_rps
      warning: 300_rps
      critical: 200_rps

    concurrent_users:
      target: 1000
      maximum: 1500

    error_rate:
      target: 0.1%
      warning: 0.5%
      critical: 1.0%

  resource_utilization:
    cpu_usage:
      target: 60%
      warning: 75%
      critical: 90%

    memory_usage:
      target: 70%
      warning: 85%
      critical: 95%

    disk_io:
      target: 70%
      warning: 85%
      critical: 95%

  business_metrics:
    user_satisfaction:
      target: 95%
      warning: 90%
      critical: 85%

    task_completion_rate:
      target: 98%
      warning: 95%
      critical: 90%

    system_availability:
      target: 99.9%
      warning: 99.5%
      critical: 99.0%

scaling_criteria:
  auto_scale_up:
    cpu_threshold: 70%
    memory_threshold: 80%
    response_time_threshold: 2000ms
    queue_length_threshold: 50

  auto_scale_down:
    cpu_threshold: 30%
    memory_threshold: 40%
    response_time_threshold: 500ms
    queue_length_threshold: 10

  manual_review_triggers:
    sustained_high_load: 30_minutes
    recurring_performance_issues: 3_incidents_per_day
    resource_exhaustion: 95%_utilization
```

---

*This runbook provides comprehensive performance tuning procedures for the Helios Career Operations System, ensuring optimal performance for 1000+ concurrent users with systematic monitoring, optimization, and scaling strategies.*

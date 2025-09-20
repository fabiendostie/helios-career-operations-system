# Monitoring and Alerting Runbook
# Helios Career Operations System

## Document Metadata
- **Version:** 1.0
- **Date:** 2025-09-20
- **Author:** Operations Team
- **Status:** Production Ready
- **Review Frequency:** Weekly

---

## 1. Overview

This runbook provides comprehensive monitoring and alerting procedures for the Helios Career Operations System, including health checks, performance monitoring, and troubleshooting procedures for early detection and resolution of issues.

### 1.1 Monitoring Strategy
- **Proactive Detection:** Early warning systems for potential issues
- **Multi-Layer Monitoring:** Infrastructure, application, and business metrics
- **Automated Response:** Self-healing and auto-scaling capabilities
- **Human-in-the-Loop:** Escalation procedures for complex issues

### 1.2 Monitoring Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │────│     Grafana     │────│   AlertManager  │
│   (Metrics)     │    │   (Dashboard)   │    │   (Alerting)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      ELK        │    │     Jaeger      │    │   StatusPage    │
│   (Logging)     │    │   (Tracing)     │    │ (Public Status) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 2. System Health Monitoring

### 2.1 Health Check Framework
```python
# health_check_framework.py
import asyncio
import aiohttp
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    service_name: str
    endpoint: str
    status: HealthStatus
    response_time: float
    last_check: str
    details: Dict
    dependencies: List[str]

class HealthMonitor:
    def __init__(self, config_file: str):
        with open(config_file) as f:
            self.config = json.load(f)
        self.health_cache = {}

    async def check_service_health(self, service: Dict) -> HealthCheck:
        """Comprehensive health check for a service"""
        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                # Basic health endpoint
                async with session.get(
                    f"{service['url']}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = time.time() - start_time

                    if response.status == 200:
                        health_data = await response.json()

                        # Check dependencies
                        dependency_status = await self.check_dependencies(
                            session, service.get('dependencies', [])
                        )

                        # Determine overall status
                        overall_status = self.calculate_overall_status(
                            health_data, dependency_status
                        )

                        return HealthCheck(
                            service_name=service['name'],
                            endpoint=service['url'],
                            status=overall_status,
                            response_time=response_time,
                            last_check=time.strftime('%Y-%m-%d %H:%M:%S'),
                            details={
                                'health_data': health_data,
                                'dependencies': dependency_status
                            },
                            dependencies=service.get('dependencies', [])
                        )
                    else:
                        return HealthCheck(
                            service_name=service['name'],
                            endpoint=service['url'],
                            status=HealthStatus.UNHEALTHY,
                            response_time=response_time,
                            last_check=time.strftime('%Y-%m-%d %H:%M:%S'),
                            details={'error': f'HTTP {response.status}'},
                            dependencies=service.get('dependencies', [])
                        )

        except Exception as e:
            return HealthCheck(
                service_name=service['name'],
                endpoint=service['url'],
                status=HealthStatus.UNKNOWN,
                response_time=time.time() - start_time,
                last_check=time.strftime('%Y-%m-%d %H:%M:%S'),
                details={'error': str(e)},
                dependencies=service.get('dependencies', [])
            )

    async def check_dependencies(self, session, dependencies: List[str]) -> Dict:
        """Check health of service dependencies"""
        dep_status = {}

        for dep in dependencies:
            if dep in ['postgresql', 'database']:
                dep_status[dep] = await self.check_database_health()
            elif dep in ['redis', 'cache']:
                dep_status[dep] = await self.check_redis_health()
            elif dep in ['ml_models']:
                dep_status[dep] = await self.check_ml_models_health()

        return dep_status

    def calculate_overall_status(self, health_data: Dict, dependency_status: Dict) -> HealthStatus:
        """Calculate overall health status based on service and dependencies"""
        service_healthy = health_data.get('status') == 'healthy'

        # Check if any critical dependencies are unhealthy
        critical_deps_healthy = all(
            status.get('status') == 'healthy'
            for dep, status in dependency_status.items()
            if status.get('critical', True)
        )

        if service_healthy and critical_deps_healthy:
            return HealthStatus.HEALTHY
        elif service_healthy or critical_deps_healthy:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY

# Service configuration
health_config = {
    "services": [
        {
            "name": "profile-ingestor",
            "url": "http://localhost:8080",
            "dependencies": ["filesystem"],
            "critical": True
        },
        {
            "name": "orchestrator",
            "url": "http://localhost:8000",
            "dependencies": ["postgresql", "redis"],
            "critical": True
        },
        {
            "name": "strategist",
            "url": "http://localhost:8001",
            "dependencies": ["ml_models", "postgresql"],
            "critical": False
        },
        {
            "name": "analyst",
            "url": "http://localhost:8002",
            "dependencies": ["ml_models", "postgresql"],
            "critical": False
        }
    ]
}
```

### 2.2 Health Check Procedures
```bash
#!/bin/bash
# comprehensive_health_check.sh

echo "🩺 Comprehensive Health Check"

# Function to check individual service
check_service() {
    local service_name=$1
    local health_url=$2
    local timeout=${3:-10}

    echo "Checking $service_name..."

    # Basic connectivity
    if curl -f -s --max-time $timeout "$health_url" > /dev/null; then
        echo "✅ $service_name: Basic connectivity OK"

        # Detailed health check
        health_response=$(curl -s --max-time $timeout "$health_url")

        # Parse health response
        if echo "$health_response" | jq -r '.status' | grep -q "healthy"; then
            echo "✅ $service_name: Health status HEALTHY"

            # Check response time
            response_time=$(curl -o /dev/null -s -w "%{time_total}" "$health_url")
            if (( $(echo "$response_time < 2.0" | bc -l) )); then
                echo "✅ $service_name: Response time OK (${response_time}s)"
            else
                echo "⚠️ $service_name: Slow response time (${response_time}s)"
            fi
        else
            echo "❌ $service_name: Health status UNHEALTHY"
            echo "Details: $health_response"
        fi
    else
        echo "❌ $service_name: Basic connectivity FAILED"
    fi

    echo "---"
}

# Check all services
check_service "Profile Ingestor" "http://localhost:8080/health"
check_service "Orchestrator" "http://localhost:8000/health"
check_service "Strategist" "http://localhost:8001/health"
check_service "Analyst" "http://localhost:8002/health"

# Infrastructure health checks
echo "🔧 Infrastructure Health Checks"

# Database health
echo "Checking PostgreSQL..."
if pg_isready -h $DB_HOST -p $DB_PORT; then
    echo "✅ PostgreSQL: Connection OK"

    # Check database metrics
    db_connections=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SELECT count(*) FROM pg_stat_activity;")
    echo "📊 PostgreSQL: $db_connections active connections"

    if [ $db_connections -gt 80 ]; then
        echo "⚠️ PostgreSQL: High connection count"
    fi
else
    echo "❌ PostgreSQL: Connection FAILED"
fi

# Redis health
echo "Checking Redis..."
if redis-cli -h $REDIS_HOST -p $REDIS_PORT ping | grep -q PONG; then
    echo "✅ Redis: Connection OK"

    # Check Redis metrics
    redis_memory=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT info memory | grep used_memory_human | cut -d: -f2)
    echo "📊 Redis: $redis_memory memory used"
else
    echo "❌ Redis: Connection FAILED"
fi

# Disk space check
echo "Checking disk space..."
disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $disk_usage -lt 80 ]; then
    echo "✅ Disk space: ${disk_usage}% used"
else
    echo "⚠️ Disk space: ${disk_usage}% used (WARNING)"
fi

echo "🎯 Health check complete"
```

---

## 3. Performance Monitoring

### 3.1 Key Performance Indicators (KPIs)
```yaml
# performance_kpis.yml
kpis:
  response_time:
    target: "<2s"
    warning: ">2s"
    critical: ">5s"

  throughput:
    target: ">100 req/min"
    warning: "<50 req/min"
    critical: "<20 req/min"

  error_rate:
    target: "<1%"
    warning: ">1%"
    critical: ">5%"

  availability:
    target: ">99.5%"
    warning: "<99%"
    critical: "<95%"

  resource_utilization:
    cpu:
      target: "<70%"
      warning: ">70%"
      critical: ">90%"
    memory:
      target: "<80%"
      warning: ">80%"
      critical: ">95%"
    disk:
      target: "<80%"
      warning: ">80%"
      critical: ">95%"
```

### 3.2 Performance Monitoring Scripts
```python
# performance_monitor.py
import psutil
import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List

class PerformanceMonitor:
    def __init__(self):
        self.metrics_history = []
        self.alert_thresholds = self.load_thresholds()

    def load_thresholds(self) -> Dict:
        """Load performance thresholds from configuration"""
        return {
            'response_time': {'warning': 2.0, 'critical': 5.0},
            'cpu_usage': {'warning': 70, 'critical': 90},
            'memory_usage': {'warning': 80, 'critical': 95},
            'error_rate': {'warning': 1, 'critical': 5}
        }

    def collect_system_metrics(self) -> Dict:
        """Collect system-level performance metrics"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0,
            'network_io': dict(psutil.net_io_counters()._asdict()),
            'process_count': len(psutil.pids())
        }

    def collect_application_metrics(self, services: List[Dict]) -> Dict:
        """Collect application-level metrics"""
        app_metrics = {}

        for service in services:
            try:
                # Response time test
                start_time = time.time()
                response = requests.get(f"{service['url']}/metrics", timeout=10)
                response_time = time.time() - start_time

                if response.status_code == 200:
                    metrics_data = response.json()

                    app_metrics[service['name']] = {
                        'response_time': response_time,
                        'status_code': response.status_code,
                        'metrics': metrics_data
                    }
                else:
                    app_metrics[service['name']] = {
                        'response_time': response_time,
                        'status_code': response.status_code,
                        'error': f"HTTP {response.status_code}"
                    }

            except Exception as e:
                app_metrics[service['name']] = {
                    'error': str(e),
                    'status': 'unreachable'
                }

        return app_metrics

    def analyze_performance_trends(self, window_minutes: int = 60) -> Dict:
        """Analyze performance trends over time window"""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)

        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]

        if not recent_metrics:
            return {"error": "No recent metrics available"}

        # Calculate trends
        cpu_trend = self.calculate_trend([m['system']['cpu_percent'] for m in recent_metrics])
        memory_trend = self.calculate_trend([m['system']['memory_percent'] for m in recent_metrics])

        return {
            'window_minutes': window_minutes,
            'samples_count': len(recent_metrics),
            'cpu_trend': cpu_trend,
            'memory_trend': memory_trend,
            'alerts_triggered': self.check_threshold_violations(recent_metrics)
        }

    def calculate_trend(self, values: List[float]) -> Dict:
        """Calculate trend direction and magnitude"""
        if len(values) < 2:
            return {"trend": "insufficient_data"}

        # Simple linear regression
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * v for i, v in enumerate(values))
        x2_sum = sum(i * i for i in range(n))

        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)

        return {
            'trend': 'increasing' if slope > 0.1 else 'decreasing' if slope < -0.1 else 'stable',
            'slope': slope,
            'current_value': values[-1],
            'average_value': sum(values) / len(values)
        }

    def check_threshold_violations(self, metrics: List[Dict]) -> List[Dict]:
        """Check for threshold violations in recent metrics"""
        violations = []

        for metric in metrics[-5:]:  # Check last 5 samples
            system = metric.get('system', {})

            # CPU threshold check
            cpu = system.get('cpu_percent', 0)
            if cpu > self.alert_thresholds['cpu_usage']['critical']:
                violations.append({
                    'metric': 'cpu_usage',
                    'value': cpu,
                    'threshold': self.alert_thresholds['cpu_usage']['critical'],
                    'severity': 'critical',
                    'timestamp': metric['timestamp']
                })
            elif cpu > self.alert_thresholds['cpu_usage']['warning']:
                violations.append({
                    'metric': 'cpu_usage',
                    'value': cpu,
                    'threshold': self.alert_thresholds['cpu_usage']['warning'],
                    'severity': 'warning',
                    'timestamp': metric['timestamp']
                })

            # Memory threshold check
            memory = system.get('memory_percent', 0)
            if memory > self.alert_thresholds['memory_usage']['critical']:
                violations.append({
                    'metric': 'memory_usage',
                    'value': memory,
                    'threshold': self.alert_thresholds['memory_usage']['critical'],
                    'severity': 'critical',
                    'timestamp': metric['timestamp']
                })

        return violations

    def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        current_metrics = self.collect_system_metrics()
        trends = self.analyze_performance_trends()

        return {
            'report_time': datetime.now().isoformat(),
            'current_system_state': current_metrics,
            'performance_trends': trends,
            'recommendations': self.generate_recommendations(current_metrics, trends)
        }

    def generate_recommendations(self, current: Dict, trends: Dict) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []

        if current['cpu_percent'] > 80:
            recommendations.append("Consider scaling up CPU resources or optimizing CPU-intensive processes")

        if current['memory_percent'] > 85:
            recommendations.append("Memory usage is high - investigate memory leaks or increase available memory")

        if trends.get('cpu_trend', {}).get('trend') == 'increasing':
            recommendations.append("CPU usage is trending upward - monitor for potential performance degradation")

        return recommendations
```

---

## 4. Alerting System

### 4.1 Alert Configuration
```yaml
# alerting_config.yml
alerts:
  system_level:
    high_cpu_usage:
      condition: "cpu_usage > 90"
      duration: "5m"
      severity: "critical"
      actions: ["page_oncall", "auto_scale"]

    high_memory_usage:
      condition: "memory_usage > 95"
      duration: "2m"
      severity: "critical"
      actions: ["page_oncall", "restart_services"]

    disk_space_low:
      condition: "disk_usage > 90"
      duration: "1m"
      severity: "warning"
      actions: ["notify_team", "cleanup_logs"]

  service_level:
    service_down:
      condition: "up == 0"
      duration: "30s"
      severity: "critical"
      actions: ["page_oncall", "auto_restart"]

    high_response_time:
      condition: "response_time > 5"
      duration: "2m"
      severity: "warning"
      actions: ["notify_team", "scale_service"]

    high_error_rate:
      condition: "error_rate > 5"
      duration: "1m"
      severity: "critical"
      actions: ["page_oncall", "investigate_logs"]

  business_level:
    user_experience_degraded:
      condition: "user_satisfaction < 0.8"
      duration: "5m"
      severity: "warning"
      actions: ["notify_product_team"]

    revenue_impact:
      condition: "conversion_rate < baseline * 0.9"
      duration: "10m"
      severity: "critical"
      actions: ["page_leadership", "emergency_response"]

notification_channels:
  slack:
    webhook: "https://hooks.slack.com/services/..."
    channels: ["#helios-alerts", "#engineering"]

  email:
    smtp_server: "smtp.company.com"
    recipients: ["oncall@helios.com", "team@helios.com"]

  pagerduty:
    integration_key: "YOUR_PAGERDUTY_KEY"
    escalation_policy: "helios-escalation"

  phone:
    twilio_account: "YOUR_TWILIO_ACCOUNT"
    phone_numbers: ["+1-555-ONCALL"]
```

### 4.2 Alert Manager Implementation
```python
# alert_manager.py
import json
import requests
import smtplib
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class Alert:
    name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    source: str
    metadata: Dict

class AlertManager:
    def __init__(self, config_file: str):
        with open(config_file) as f:
            self.config = json.load(f)
        self.active_alerts = {}
        self.alert_history = []

    def trigger_alert(self, alert: Alert):
        """Trigger an alert and send notifications"""
        alert_key = f"{alert.source}:{alert.name}"

        # Check if this is a new alert or repeat
        if alert_key in self.active_alerts:
            # Update existing alert
            self.active_alerts[alert_key].timestamp = alert.timestamp
        else:
            # New alert
            self.active_alerts[alert_key] = alert
            self.send_notifications(alert)

        # Add to history
        self.alert_history.append(alert)

    def resolve_alert(self, source: str, alert_name: str):
        """Resolve an active alert"""
        alert_key = f"{source}:{alert_name}"

        if alert_key in self.active_alerts:
            resolved_alert = self.active_alerts.pop(alert_key)
            self.send_resolution_notification(resolved_alert)

    def send_notifications(self, alert: Alert):
        """Send alert notifications via configured channels"""
        alert_config = self.config['alerts'].get(alert.name, {})
        actions = alert_config.get('actions', [])

        for action in actions:
            if action == "notify_team":
                self.send_slack_notification(alert)
                self.send_email_notification(alert)
            elif action == "page_oncall":
                self.send_pagerduty_alert(alert)
                self.send_phone_alert(alert)
            elif action == "auto_scale":
                self.trigger_auto_scaling(alert)
            elif action == "auto_restart":
                self.trigger_service_restart(alert)

    def send_slack_notification(self, alert: Alert):
        """Send Slack notification"""
        webhook_url = self.config['notification_channels']['slack']['webhook']

        color = {
            AlertSeverity.INFO: "good",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.CRITICAL: "danger"
        }[alert.severity]

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"🚨 {alert.name}",
                    "text": alert.message,
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value, "short": True},
                        {"title": "Source", "value": alert.source, "short": True},
                        {"title": "Time", "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'), "short": True}
                    ]
                }
            ]
        }

        requests.post(webhook_url, json=payload)

    def send_email_notification(self, alert: Alert):
        """Send email notification"""
        smtp_config = self.config['notification_channels']['email']

        subject = f"[{alert.severity.value.upper()}] Helios Alert: {alert.name}"
        body = f"""
Alert: {alert.name}
Severity: {alert.severity.value}
Source: {alert.source}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Message: {alert.message}

Metadata: {json.dumps(alert.metadata, indent=2)}
        """

        # Send email (implementation depends on SMTP configuration)
        # smtp_send_email(smtp_config, subject, body)

    def send_pagerduty_alert(self, alert: Alert):
        """Send PagerDuty alert"""
        pd_config = self.config['notification_channels']['pagerduty']

        payload = {
            "routing_key": pd_config['integration_key'],
            "event_action": "trigger",
            "payload": {
                "summary": f"{alert.name}: {alert.message}",
                "source": alert.source,
                "severity": alert.severity.value,
                "timestamp": alert.timestamp.isoformat(),
                "custom_details": alert.metadata
            }
        }

        requests.post('https://events.pagerduty.com/v2/enqueue', json=payload)

    def generate_alert_report(self, hours: int = 24) -> Dict:
        """Generate alert summary report"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_alerts = [
            a for a in self.alert_history
            if a.timestamp > cutoff_time
        ]

        severity_counts = {
            AlertSeverity.INFO: 0,
            AlertSeverity.WARNING: 0,
            AlertSeverity.CRITICAL: 0
        }

        for alert in recent_alerts:
            severity_counts[alert.severity] += 1

        return {
            'report_period_hours': hours,
            'total_alerts': len(recent_alerts),
            'alerts_by_severity': {k.value: v for k, v in severity_counts.items()},
            'active_alerts_count': len(self.active_alerts),
            'top_alert_sources': self.get_top_alert_sources(recent_alerts),
            'alert_frequency_trend': self.calculate_alert_frequency_trend(recent_alerts)
        }

    def get_top_alert_sources(self, alerts: List[Alert]) -> List[Dict]:
        """Get top alert sources by frequency"""
        source_counts = {}
        for alert in alerts:
            source_counts[alert.source] = source_counts.get(alert.source, 0) + 1

        return [
            {"source": source, "count": count}
            for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
```

---

## 5. Log Monitoring and Analysis

### 5.1 Log Aggregation Setup
```bash
#!/bin/bash
# setup_log_monitoring.sh

echo "📋 Setting up Log Monitoring"

# Step 1: Configure Elasticsearch
echo "Configuring Elasticsearch..."
docker run -d \
    --name elasticsearch \
    -p 9200:9200 \
    -p 9300:9300 \
    -e "discovery.type=single-node" \
    -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
    elasticsearch:7.17.0

# Step 2: Configure Logstash
echo "Configuring Logstash..."
cat > logstash.conf << EOF
input {
  beats {
    port => 5044
  }
  file {
    path => "/var/log/helios/*.log"
    start_position => "beginning"
    codec => "json"
  }
}

filter {
  if [fields][service] {
    mutate {
      add_field => { "service_name" => "%{[fields][service]}" }
    }
  }

  # Parse application logs
  if [service_name] == "orchestrator" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}" }
    }
  }

  # Extract error patterns
  if [level] == "ERROR" {
    grok {
      match => { "message" => ".*Exception: %{GREEDYDATA:error_message}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "helios-logs-%{+YYYY.MM.dd}"
  }
}
EOF

docker run -d \
    --name logstash \
    -p 5044:5044 \
    -v $(pwd)/logstash.conf:/usr/share/logstash/pipeline/logstash.conf \
    logstash:7.17.0

# Step 3: Configure Kibana
echo "Configuring Kibana..."
docker run -d \
    --name kibana \
    -p 5601:5601 \
    -e "ELASTICSEARCH_HOSTS=http://localhost:9200" \
    kibana:7.17.0

# Step 4: Configure Filebeat for each service
echo "Configuring Filebeat..."
cat > filebeat.yml << EOF
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/helios/orchestrator/*.log
  fields:
    service: orchestrator
  fields_under_root: true

- type: log
  enabled: true
  paths:
    - /var/log/helios/strategist/*.log
  fields:
    service: strategist
  fields_under_root: true

- type: log
  enabled: true
  paths:
    - /var/log/helios/analyst/*.log
  fields:
    service: analyst
  fields_under_root: true

output.logstash:
  hosts: ["localhost:5044"]

processors:
  - add_host_metadata:
      when.not.contains.tags: forwarded
EOF

echo "✅ Log monitoring setup complete"
echo "📊 Kibana dashboard available at: http://localhost:5601"
```

### 5.2 Log Analysis Scripts
```python
# log_analyzer.py
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

class LogAnalyzer:
    def __init__(self, log_patterns_file: str):
        with open(log_patterns_file) as f:
            self.patterns = json.load(f)
        self.error_patterns = self.compile_patterns()

    def compile_patterns(self) -> Dict:
        """Compile regex patterns for log analysis"""
        compiled = {}
        for category, patterns in self.patterns.items():
            compiled[category] = [re.compile(pattern) for pattern in patterns]
        return compiled

    def analyze_log_file(self, log_file: str, hours_back: int = 24) -> Dict:
        """Analyze log file for errors, warnings, and patterns"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)

        analysis = {
            'total_lines': 0,
            'error_count': 0,
            'warning_count': 0,
            'error_patterns': defaultdict(int),
            'performance_issues': [],
            'security_events': [],
            'unusual_activities': []
        }

        with open(log_file, 'r') as f:
            for line in f:
                analysis['total_lines'] += 1

                try:
                    # Parse log line (assuming JSON format)
                    log_entry = json.loads(line)
                    timestamp = datetime.fromisoformat(log_entry.get('timestamp', ''))

                    if timestamp < cutoff_time:
                        continue

                    level = log_entry.get('level', '').upper()
                    message = log_entry.get('message', '')

                    # Count log levels
                    if level == 'ERROR':
                        analysis['error_count'] += 1
                    elif level == 'WARNING':
                        analysis['warning_count'] += 1

                    # Pattern matching
                    self.match_patterns(message, analysis)

                except (json.JSONDecodeError, ValueError):
                    # Handle non-JSON log lines
                    self.analyze_plain_text_log(line, analysis)

        return analysis

    def match_patterns(self, message: str, analysis: Dict):
        """Match log message against known patterns"""
        # Error patterns
        for pattern in self.error_patterns.get('errors', []):
            if pattern.search(message):
                analysis['error_patterns'][pattern.pattern] += 1

        # Performance patterns
        for pattern in self.error_patterns.get('performance', []):
            match = pattern.search(message)
            if match:
                analysis['performance_issues'].append({
                    'pattern': pattern.pattern,
                    'message': message,
                    'details': match.groupdict()
                })

        # Security patterns
        for pattern in self.error_patterns.get('security', []):
            if pattern.search(message):
                analysis['security_events'].append({
                    'pattern': pattern.pattern,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                })

    def generate_log_summary(self, analysis: Dict) -> str:
        """Generate human-readable log analysis summary"""
        summary = f"""
Log Analysis Summary
===================

Total log entries analyzed: {analysis['total_lines']}
Error entries: {analysis['error_count']}
Warning entries: {analysis['warning_count']}
Error rate: {(analysis['error_count'] / max(analysis['total_lines'], 1)) * 100:.2f}%

Top Error Patterns:
"""

        for pattern, count in sorted(analysis['error_patterns'].items(),
                                   key=lambda x: x[1], reverse=True)[:5]:
            summary += f"  - {pattern}: {count} occurrences\n"

        if analysis['performance_issues']:
            summary += f"\nPerformance Issues: {len(analysis['performance_issues'])} detected\n"

        if analysis['security_events']:
            summary += f"\nSecurity Events: {len(analysis['security_events'])} detected\n"

        return summary

    def detect_anomalies(self, current_analysis: Dict, baseline_analysis: Dict) -> List[Dict]:
        """Detect anomalies by comparing with baseline"""
        anomalies = []

        # Error rate anomaly
        current_error_rate = current_analysis['error_count'] / max(current_analysis['total_lines'], 1)
        baseline_error_rate = baseline_analysis['error_count'] / max(baseline_analysis['total_lines'], 1)

        if current_error_rate > baseline_error_rate * 2:
            anomalies.append({
                'type': 'error_rate_spike',
                'current_rate': current_error_rate,
                'baseline_rate': baseline_error_rate,
                'severity': 'high' if current_error_rate > baseline_error_rate * 5 else 'medium'
            })

        # New error patterns
        current_patterns = set(current_analysis['error_patterns'].keys())
        baseline_patterns = set(baseline_analysis['error_patterns'].keys())
        new_patterns = current_patterns - baseline_patterns

        if new_patterns:
            anomalies.append({
                'type': 'new_error_patterns',
                'patterns': list(new_patterns),
                'severity': 'medium'
            })

        return anomalies

# Log patterns configuration
log_patterns = {
    "errors": [
        r"Exception.*?:",
        r"ERROR.*?database.*?connection",
        r"TimeoutError",
        r"ConnectionRefusedError",
        r"Memory.*?error",
        r"OutOfMemory"
    ],
    "performance": [
        r"slow query.*?(\d+)ms",
        r"response time.*?(\d+\.\d+)s",
        r"high CPU.*?(\d+)%",
        r"memory usage.*?(\d+)%"
    ],
    "security": [
        r"authentication.*?failed",
        r"unauthorized.*?access",
        r"suspicious.*?activity",
        r"brute.*?force",
        r"injection.*?attempt"
    ]
}
```

---

## 6. Troubleshooting Procedures

### 6.1 Incident Response Workflow
```bash
#!/bin/bash
# incident_response.sh

echo "🚨 Incident Response Workflow"

INCIDENT_TYPE=${1:-unknown}
SEVERITY=${2:-medium}

echo "Incident Type: $INCIDENT_TYPE"
echo "Severity: $SEVERITY"

# Step 1: Immediate response
case $SEVERITY in
    "critical")
        echo "🚨 CRITICAL INCIDENT - Immediate response required"

        # Page on-call team
        python scripts/alerting/page_oncall.py --message="Critical incident: $INCIDENT_TYPE"

        # Enable maintenance mode if needed
        if [ "$INCIDENT_TYPE" == "service_down" ]; then
            echo "Enabling maintenance mode..."
            export HELIOS_MAINTENANCE_MODE=true
            redis-cli SET "feature_flag:HELIOS_MAINTENANCE_MODE" "true"
        fi
        ;;
    "high")
        echo "⚠️ HIGH SEVERITY - Escalated response"
        python scripts/alerting/notify_team.py --message="High severity incident: $INCIDENT_TYPE"
        ;;
    "medium")
        echo "📢 MEDIUM SEVERITY - Standard response"
        python scripts/alerting/notify_team.py --message="Incident detected: $INCIDENT_TYPE"
        ;;
esac

# Step 2: Gather information
echo "📊 Gathering incident information..."

# System status
echo "=== System Status ===" > incident_report.txt
date >> incident_report.txt
echo "" >> incident_report.txt

# Service health
echo "=== Service Health ===" >> incident_report.txt
python scripts/monitoring/check_all_services.py >> incident_report.txt

# Resource usage
echo "=== Resource Usage ===" >> incident_report.txt
top -bn1 | head -20 >> incident_report.txt

# Recent logs
echo "=== Recent Error Logs ===" >> incident_report.txt
grep -i error /var/log/helios/*.log | tail -50 >> incident_report.txt

# Step 3: Initial diagnosis
echo "🔍 Running initial diagnosis..."

case $INCIDENT_TYPE in
    "high_response_time")
        python scripts/diagnosis/diagnose_performance.py >> incident_report.txt
        ;;
    "service_down")
        python scripts/diagnosis/diagnose_service_failure.py >> incident_report.txt
        ;;
    "database_issues")
        python scripts/diagnosis/diagnose_database.py >> incident_report.txt
        ;;
    "high_error_rate")
        python scripts/diagnosis/diagnose_errors.py >> incident_report.txt
        ;;
esac

# Step 4: Escalation if needed
if [ "$SEVERITY" == "critical" ]; then
    echo "📞 Escalating to senior team..."
    python scripts/alerting/escalate_incident.py --report=incident_report.txt
fi

echo "✅ Initial incident response complete"
echo "📄 Report saved to: incident_report.txt"
```

### 6.2 Common Issue Diagnostics
```python
# diagnostic_tools.py
import subprocess
import psutil
import requests
import json
from datetime import datetime
from typing import Dict, List

class DiagnosticTools:
    def __init__(self):
        self.services = {
            'orchestrator': 'http://localhost:8000',
            'strategist': 'http://localhost:8001',
            'analyst': 'http://localhost:8002',
            'profile_ingestor': 'http://localhost:8080'
        }

    def diagnose_high_response_time(self) -> Dict:
        """Diagnose high response time issues"""
        diagnosis = {
            'timestamp': datetime.now().isoformat(),
            'issue': 'high_response_time',
            'findings': []
        }

        # Check system resources
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent

        if cpu_usage > 80:
            diagnosis['findings'].append({
                'type': 'high_cpu',
                'value': cpu_usage,
                'recommendation': 'Investigate CPU-intensive processes or scale resources'
            })

        if memory_usage > 85:
            diagnosis['findings'].append({
                'type': 'high_memory',
                'value': memory_usage,
                'recommendation': 'Check for memory leaks or increase available memory'
            })

        # Check database performance
        db_diagnosis = self.check_database_performance()
        if db_diagnosis:
            diagnosis['findings'].append(db_diagnosis)

        # Check individual service response times
        for service_name, base_url in self.services.items():
            response_time = self.measure_response_time(f"{base_url}/health")
            if response_time > 2.0:
                diagnosis['findings'].append({
                    'type': 'slow_service',
                    'service': service_name,
                    'response_time': response_time,
                    'recommendation': f'Investigate {service_name} performance'
                })

        return diagnosis

    def diagnose_service_failure(self, service_name: str) -> Dict:
        """Diagnose service failure issues"""
        diagnosis = {
            'timestamp': datetime.now().isoformat(),
            'issue': 'service_failure',
            'service': service_name,
            'findings': []
        }

        # Check if service process is running
        if not self.is_process_running(service_name):
            diagnosis['findings'].append({
                'type': 'process_not_running',
                'recommendation': 'Restart the service process'
            })

        # Check port availability
        service_url = self.services.get(service_name)
        if service_url and not self.is_port_open(service_url):
            diagnosis['findings'].append({
                'type': 'port_not_accessible',
                'recommendation': 'Check network configuration and firewall rules'
            })

        # Check dependencies
        dependency_status = self.check_service_dependencies(service_name)
        if dependency_status['failed_dependencies']:
            diagnosis['findings'].append({
                'type': 'dependency_failure',
                'failed_dependencies': dependency_status['failed_dependencies'],
                'recommendation': 'Fix dependency issues before restarting service'
            })

        # Check recent logs for errors
        recent_errors = self.get_recent_service_errors(service_name)
        if recent_errors:
            diagnosis['findings'].append({
                'type': 'error_logs',
                'errors': recent_errors[:5],  # Top 5 recent errors
                'recommendation': 'Investigate error patterns in logs'
            })

        return diagnosis

    def diagnose_database_issues(self) -> Dict:
        """Diagnose database-related issues"""
        diagnosis = {
            'timestamp': datetime.now().isoformat(),
            'issue': 'database_issues',
            'findings': []
        }

        # Check database connectivity
        if not self.test_database_connection():
            diagnosis['findings'].append({
                'type': 'connection_failure',
                'recommendation': 'Check database server status and network connectivity'
            })
            return diagnosis

        # Check connection pool status
        pool_status = self.check_connection_pool()
        if pool_status['utilization'] > 90:
            diagnosis['findings'].append({
                'type': 'connection_pool_exhausted',
                'utilization': pool_status['utilization'],
                'recommendation': 'Increase connection pool size or investigate connection leaks'
            })

        # Check slow queries
        slow_queries = self.get_slow_queries()
        if slow_queries:
            diagnosis['findings'].append({
                'type': 'slow_queries',
                'count': len(slow_queries),
                'queries': slow_queries[:3],
                'recommendation': 'Optimize slow queries or add indexes'
            })

        # Check database size and growth
        db_size = self.get_database_size()
        if db_size['growth_rate'] > 10:  # 10% growth in recent period
            diagnosis['findings'].append({
                'type': 'rapid_growth',
                'growth_rate': db_size['growth_rate'],
                'recommendation': 'Investigate data growth and implement archiving if needed'
            })

        return diagnosis

    def measure_response_time(self, url: str, timeout: int = 10) -> float:
        """Measure response time for a given URL"""
        try:
            start_time = datetime.now()
            response = requests.get(url, timeout=timeout)
            end_time = datetime.now()
            return (end_time - start_time).total_seconds()
        except Exception:
            return float('inf')

    def is_process_running(self, service_name: str) -> bool:
        """Check if service process is running"""
        try:
            # This is a simplified check - in production, use proper process management
            result = subprocess.run(['pgrep', '-f', service_name],
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def is_port_open(self, url: str) -> bool:
        """Check if service port is accessible"""
        try:
            response = requests.get(f"{url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def check_service_dependencies(self, service_name: str) -> Dict:
        """Check service dependencies"""
        dependencies = {
            'orchestrator': ['postgresql', 'redis'],
            'strategist': ['postgresql'],
            'analyst': ['postgresql'],
            'profile_ingestor': []
        }

        service_deps = dependencies.get(service_name, [])
        failed_deps = []

        for dep in service_deps:
            if dep == 'postgresql' and not self.test_database_connection():
                failed_deps.append('postgresql')
            elif dep == 'redis' and not self.test_redis_connection():
                failed_deps.append('redis')

        return {
            'total_dependencies': len(service_deps),
            'failed_dependencies': failed_deps,
            'health_status': 'unhealthy' if failed_deps else 'healthy'
        }

    def test_database_connection(self) -> bool:
        """Test database connectivity"""
        try:
            # Simplified database test
            result = subprocess.run(['pg_isready', '-h', 'localhost'],
                                  capture_output=True)
            return result.returncode == 0
        except Exception:
            return False

    def test_redis_connection(self) -> bool:
        """Test Redis connectivity"""
        try:
            result = subprocess.run(['redis-cli', 'ping'],
                                  capture_output=True, text=True)
            return 'PONG' in result.stdout
        except Exception:
            return False

    def generate_diagnostic_report(self, issue_type: str, **kwargs) -> str:
        """Generate comprehensive diagnostic report"""
        if issue_type == 'high_response_time':
            diagnosis = self.diagnose_high_response_time()
        elif issue_type == 'service_failure':
            service_name = kwargs.get('service_name', 'unknown')
            diagnosis = self.diagnose_service_failure(service_name)
        elif issue_type == 'database_issues':
            diagnosis = self.diagnose_database_issues()
        else:
            return f"Unknown issue type: {issue_type}"

        # Format report
        report = f"""
Diagnostic Report
================

Issue: {diagnosis['issue']}
Timestamp: {diagnosis['timestamp']}

Findings:
---------
"""

        for i, finding in enumerate(diagnosis['findings'], 1):
            report += f"{i}. {finding['type'].replace('_', ' ').title()}\n"
            if 'value' in finding:
                report += f"   Value: {finding['value']}\n"
            if 'service' in finding:
                report += f"   Service: {finding['service']}\n"
            report += f"   Recommendation: {finding['recommendation']}\n\n"

        if not diagnosis['findings']:
            report += "No specific issues detected. Manual investigation may be required.\n"

        return report
```

---

## 7. Performance Baselines and SLAs

### 7.1 Service Level Agreements (SLAs)
```yaml
# sla_definitions.yml
slas:
  availability:
    target: 99.5%
    measurement_period: monthly
    consequences:
      below_99: "service_credit_5_percent"
      below_95: "service_credit_10_percent"

  response_time:
    p95_target: 2.0s
    p99_target: 5.0s
    measurement_period: hourly

  error_rate:
    target: "<1%"
    measurement_period: hourly
    alert_threshold: 5%

  throughput:
    minimum: 100_requests_per_minute
    target: 500_requests_per_minute
    measurement_period: hourly

service_specific_slas:
  profile_ingestor:
    processing_time: 30s_per_document
    accuracy: 95%_data_extraction

  orchestrator:
    session_management: 99.9%_session_persistence
    routing_latency: 50ms_p95

  strategist:
    career_path_generation: 10s_p95
    recommendation_quality: 80%_user_satisfaction

  analyst:
    analysis_pipeline: 60s_p95
    optimization_improvement: 15%_average_score_increase
```

### 7.2 Baseline Performance Monitoring
```python
# baseline_monitor.py
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class PerformanceBaseline:
    metric_name: str
    baseline_value: float
    measurement_period: str
    confidence_interval: tuple
    last_updated: datetime

class BaselineMonitor:
    def __init__(self, baseline_file: str):
        self.baseline_file = baseline_file
        self.baselines = self.load_baselines()

    def load_baselines(self) -> Dict[str, PerformanceBaseline]:
        """Load performance baselines from file"""
        try:
            with open(self.baseline_file) as f:
                data = json.load(f)

            baselines = {}
            for metric, baseline_data in data.items():
                baselines[metric] = PerformanceBaseline(
                    metric_name=metric,
                    baseline_value=baseline_data['baseline_value'],
                    measurement_period=baseline_data['measurement_period'],
                    confidence_interval=tuple(baseline_data['confidence_interval']),
                    last_updated=datetime.fromisoformat(baseline_data['last_updated'])
                )
            return baselines
        except FileNotFoundError:
            return {}

    def establish_baseline(self, metric_name: str, measurements: List[float],
                          period: str = 'daily') -> PerformanceBaseline:
        """Establish baseline from historical measurements"""
        if len(measurements) < 10:
            raise ValueError("Need at least 10 measurements to establish baseline")

        # Remove outliers (values beyond 2 standard deviations)
        mean = statistics.mean(measurements)
        stdev = statistics.stdev(measurements)
        filtered_measurements = [
            m for m in measurements
            if abs(m - mean) <= 2 * stdev
        ]

        # Calculate baseline metrics
        baseline_value = statistics.median(filtered_measurements)
        p25 = statistics.quantiles(filtered_measurements, n=4)[0]
        p75 = statistics.quantiles(filtered_measurements, n=4)[2]

        baseline = PerformanceBaseline(
            metric_name=metric_name,
            baseline_value=baseline_value,
            measurement_period=period,
            confidence_interval=(p25, p75),
            last_updated=datetime.now()
        )

        self.baselines[metric_name] = baseline
        self.save_baselines()

        return baseline

    def check_deviation(self, metric_name: str, current_value: float) -> Dict:
        """Check if current value deviates significantly from baseline"""
        if metric_name not in self.baselines:
            return {'status': 'no_baseline', 'message': 'No baseline established'}

        baseline = self.baselines[metric_name]
        baseline_value = baseline.baseline_value
        ci_lower, ci_upper = baseline.confidence_interval

        # Calculate deviation percentage
        deviation_percent = ((current_value - baseline_value) / baseline_value) * 100

        # Determine status
        if ci_lower <= current_value <= ci_upper:
            status = 'normal'
            severity = 'info'
        elif current_value < ci_lower:
            status = 'below_baseline'
            severity = 'warning' if deviation_percent < -20 else 'critical'
        else:  # current_value > ci_upper
            status = 'above_baseline'
            severity = 'warning' if deviation_percent < 50 else 'critical'

        return {
            'status': status,
            'severity': severity,
            'deviation_percent': deviation_percent,
            'current_value': current_value,
            'baseline_value': baseline_value,
            'confidence_interval': baseline.confidence_interval,
            'recommendation': self.get_recommendation(status, deviation_percent)
        }

    def get_recommendation(self, status: str, deviation_percent: float) -> str:
        """Get recommendation based on deviation status"""
        if status == 'normal':
            return "Performance within normal range"
        elif status == 'below_baseline':
            if deviation_percent < -50:
                return "Significant performance improvement - investigate changes"
            else:
                return "Performance better than baseline - monitor for consistency"
        else:  # above_baseline
            if deviation_percent > 100:
                return "Critical performance degradation - immediate investigation required"
            elif deviation_percent > 50:
                return "Significant performance degradation - investigate and optimize"
            else:
                return "Performance slightly worse than baseline - monitor trend"

    def update_baseline(self, metric_name: str, recent_measurements: List[float]):
        """Update existing baseline with recent measurements"""
        if metric_name not in self.baselines:
            self.establish_baseline(metric_name, recent_measurements)
            return

        # Use exponential smoothing to update baseline
        current_baseline = self.baselines[metric_name]
        new_median = statistics.median(recent_measurements)

        # Weight: 80% current baseline, 20% new measurements
        updated_value = (0.8 * current_baseline.baseline_value) + (0.2 * new_median)

        # Update confidence interval
        all_values = recent_measurements[-50:]  # Use last 50 measurements
        if len(all_values) >= 10:
            p25 = statistics.quantiles(all_values, n=4)[0]
            p75 = statistics.quantiles(all_values, n=4)[2]
            updated_ci = (p25, p75)
        else:
            updated_ci = current_baseline.confidence_interval

        self.baselines[metric_name] = PerformanceBaseline(
            metric_name=metric_name,
            baseline_value=updated_value,
            measurement_period=current_baseline.measurement_period,
            confidence_interval=updated_ci,
            last_updated=datetime.now()
        )

        self.save_baselines()

    def save_baselines(self):
        """Save baselines to file"""
        data = {}
        for metric, baseline in self.baselines.items():
            data[metric] = {
                'baseline_value': baseline.baseline_value,
                'measurement_period': baseline.measurement_period,
                'confidence_interval': baseline.confidence_interval,
                'last_updated': baseline.last_updated.isoformat()
            }

        with open(self.baseline_file, 'w') as f:
            json.dump(data, f, indent=2)

    def generate_baseline_report(self) -> str:
        """Generate baseline performance report"""
        report = "Performance Baseline Report\n"
        report += "=" * 30 + "\n\n"

        for metric, baseline in self.baselines.items():
            report += f"Metric: {metric}\n"
            report += f"  Baseline Value: {baseline.baseline_value:.2f}\n"
            report += f"  Confidence Interval: {baseline.confidence_interval[0]:.2f} - {baseline.confidence_interval[1]:.2f}\n"
            report += f"  Last Updated: {baseline.last_updated.strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"  Measurement Period: {baseline.measurement_period}\n\n"

        return report
```

---

## 8. Contact Information and Escalation

### 8.1 On-Call Rotation
```yaml
# oncall_rotation.yml
oncall_schedule:
  primary:
    week_1: "alice@helios.com"
    week_2: "bob@helios.com"
    week_3: "charlie@helios.com"
    week_4: "diana@helios.com"

  secondary:
    week_1: "eve@helios.com"
    week_2: "frank@helios.com"
    week_3: "grace@helios.com"
    week_4: "henry@helios.com"

escalation_matrix:
  level_1:  # 0-15 minutes
    responders: ["primary_oncall"]
    notification_methods: ["pagerduty", "phone"]
    auto_escalate_after: 15

  level_2:  # 15-30 minutes
    responders: ["primary_oncall", "secondary_oncall", "team_lead"]
    notification_methods: ["pagerduty", "phone", "slack"]
    auto_escalate_after: 30

  level_3:  # 30+ minutes
    responders: ["engineering_manager", "cto"]
    notification_methods: ["pagerduty", "phone", "slack", "email"]

contact_information:
  primary_oncall:
    phone: "+1-555-PRIMARY"
    slack: "@primary-oncall"
    pagerduty: "primary-oncall@helios.pagerduty.com"

  team_lead:
    phone: "+1-555-TEAMLEAD"
    slack: "@team-lead"
    email: "team-lead@helios.com"

  engineering_manager:
    phone: "+1-555-ENGMGR"
    slack: "@eng-manager"
    email: "eng-manager@helios.com"
```

---

*This runbook provides comprehensive monitoring and alerting procedures for the Helios Career Operations System, ensuring proactive detection and rapid response to issues with minimal user impact.*

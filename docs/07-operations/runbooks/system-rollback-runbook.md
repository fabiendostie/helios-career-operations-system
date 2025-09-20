# System-Wide Rollback Runbook
# Helios Career Operations System

## Document Metadata
- **Version:** 1.0
- **Date:** 2025-09-20
- **Author:** Operations Team
- **Status:** Production Ready
- **Review Frequency:** Monthly

---

## 1. Overview

This runbook provides comprehensive procedures for system-wide rollbacks using feature flags, versioning, and graceful degradation strategies to ensure minimal user impact during rollback operations.

### 1.1 Rollback Strategy
- **Feature Flag Based:** Immediate toggles without code deployment
- **Version-Based:** Rollback to previous stable releases
- **Service-Level:** Individual service rollbacks while maintaining system function
- **Data-Safe:** Zero data loss during rollback operations

### 1.2 Rollback Triggers
- **Critical System Failure:** >50% service availability loss
- **Data Integrity Issues:** Data corruption or loss detected
- **Security Incidents:** Critical vulnerability exploitation
- **Performance Degradation:** >3x response time increase
- **User Impact:** >25% user-reported issues

---

## 2. Feature Flag Management

### 2.1 Core Feature Flags
```yaml
# Feature flags configuration
feature_flags:
  system_level:
    HELIOS_ORCHESTRATOR_ENABLED: true
    HELIOS_USE_NEW_DATABASE: true
    HELIOS_ML_SERVICES_ENABLED: true
    HELIOS_MAINTENANCE_MODE: false
    HELIOS_RATE_LIMITING_ENABLED: true

  service_level:
    HELIOS_STRATEGIST_ENABLED: true
    HELIOS_ANALYST_ENABLED: true
    HELIOS_ARCHITECT_ENABLED: true
    HELIOS_EDITOR_ENABLED: true
    HELIOS_PROFILE_INGESTOR_STANDALONE: false

  feature_level:
    HELIOS_NLP_PROCESSING: true
    HELIOS_EMBEDDINGS_GENERATION: true
    HELIOS_CAREER_PATH_ML: true
    HELIOS_ATS_OPTIMIZATION: true
    HELIOS_DOCUMENT_GENERATION: true
```

### 2.2 Feature Flag Rollback Procedures
```bash
#!/bin/bash
# feature_flag_rollback.sh

echo "🚩 Feature Flag Rollback Procedures"

# Function to update feature flag
update_feature_flag() {
    local flag_name=$1
    local flag_value=$2
    local environment=${3:-production}

    echo "Updating $flag_name to $flag_value in $environment"

    # Update in configuration service
    curl -X POST "http://config-service:8080/flags/$flag_name" \
         -H "Content-Type: application/json" \
         -d "{\"value\": $flag_value, \"environment\": \"$environment\"}"

    # Update in Redis cache
    redis-cli SET "feature_flag:$flag_name" "$flag_value"
    redis-cli EXPIRE "feature_flag:$flag_name" 3600

    echo "✅ $flag_name updated to $flag_value"
}

# Emergency rollback to safe mode
emergency_safe_mode() {
    echo "🚨 EMERGENCY: Activating Safe Mode"

    update_feature_flag "HELIOS_MAINTENANCE_MODE" "true"
    update_feature_flag "HELIOS_ML_SERVICES_ENABLED" "false"
    update_feature_flag "HELIOS_USE_NEW_DATABASE" "false"
    update_feature_flag "HELIOS_ORCHESTRATOR_ENABLED" "false"
    update_feature_flag "HELIOS_PROFILE_INGESTOR_STANDALONE" "true"

    echo "✅ System in safe mode - only Profile Ingestor operational"
}

# Gradual feature restoration
gradual_restoration() {
    echo "🔄 Gradual Feature Restoration"

    # Step 1: Enable orchestrator
    update_feature_flag "HELIOS_ORCHESTRATOR_ENABLED" "true"
    sleep 30

    # Step 2: Enable database
    update_feature_flag "HELIOS_USE_NEW_DATABASE" "true"
    sleep 30

    # Step 3: Enable ML services
    update_feature_flag "HELIOS_ML_SERVICES_ENABLED" "true"
    sleep 30

    # Step 4: Exit maintenance mode
    update_feature_flag "HELIOS_MAINTENANCE_MODE" "false"

    echo "✅ Gradual restoration complete"
}
```

---

## 3. Version-Based Rollback

### 3.1 Service Version Management
```yaml
# service_versions.yml
services:
  orchestrator:
    current: "v2.1.0"
    previous: "v2.0.3"
    stable: "v2.0.0"

  strategist:
    current: "v1.3.0"
    previous: "v1.2.1"
    stable: "v1.2.0"

  analyst:
    current: "v1.4.0"
    previous: "v1.3.2"
    stable: "v1.3.0"

  profile_ingestor:
    current: "v1.1.0"
    previous: "v1.0.5"
    stable: "v1.0.0"  # Production ready
```

### 3.2 Version Rollback Procedures
```bash
#!/bin/bash
# version_rollback.sh

echo "📦 Version-Based Rollback"

# Function to rollback service to previous version
rollback_service_version() {
    local service_name=$1
    local target_version=$2
    local rollback_type=${3:-previous}  # previous, stable, specific

    echo "Rolling back $service_name to $target_version"

    # Stop current service
    docker-compose stop $service_name

    # Update image tag
    sed -i "s|${service_name}:.*|${service_name}:${target_version}|g" docker-compose.yml

    # Start with new version
    docker-compose up -d $service_name

    # Wait for service to be ready
    sleep 30

    # Verify service health
    local health_url="http://localhost:$(get_service_port $service_name)/health"
    if curl -f -s $health_url > /dev/null; then
        echo "✅ $service_name rollback successful to $target_version"
    else
        echo "❌ $service_name rollback failed"
        return 1
    fi
}

# Emergency rollback to stable versions
emergency_version_rollback() {
    echo "🚨 EMERGENCY: Rolling back all services to stable versions"

    # Read stable versions from configuration
    eval $(python -c "
import yaml
with open('config/service_versions.yml') as f:
    versions = yaml.safe_load(f)
for service, ver_info in versions['services'].items():
    print(f'{service}_stable={ver_info[\"stable\"]}')
")

    # Rollback each service
    rollback_service_version "orchestrator" "$orchestrator_stable" "stable"
    rollback_service_version "strategist" "$strategist_stable" "stable"
    rollback_service_version "analyst" "$analyst_stable" "stable"

    # Profile Ingestor is stable - no rollback needed
    echo "✅ Profile Ingestor already on stable version"

    echo "✅ Emergency version rollback complete"
}

# Selective service rollback
selective_service_rollback() {
    local service_name=$1
    local rollback_type=${2:-previous}

    echo "🎯 Selective rollback: $service_name ($rollback_type)"

    # Get target version
    local target_version=$(python -c "
import yaml
with open('config/service_versions.yml') as f:
    versions = yaml.safe_load(f)
print(versions['services']['$service_name']['$rollback_type'])
")

    rollback_service_version "$service_name" "$target_version" "$rollback_type"

    echo "✅ Selective rollback complete for $service_name"
}
```

---

## 4. Service-Level Rollback Procedures

### 4.1 Orchestrator Rollback
```bash
#!/bin/bash
# orchestrator_rollback.sh

echo "🎭 Orchestrator Service Rollback"

# Step 1: Enable maintenance mode
echo "Enabling maintenance mode..."
export HELIOS_MAINTENANCE_MODE=true
redis-cli SET "feature_flag:HELIOS_MAINTENANCE_MODE" "true"

# Step 2: Gracefully drain connections
echo "Draining active connections..."
sleep 30  # Allow current requests to complete

# Step 3: Stop orchestrator
echo "Stopping orchestrator service..."
docker-compose stop orchestrator

# Step 4: Switch to direct service routing
echo "Switching to direct service routing..."
export HELIOS_ORCHESTRATOR_ENABLED=false
redis-cli SET "feature_flag:HELIOS_ORCHESTRATOR_ENABLED" "false"

# Step 5: Start services in standalone mode
echo "Starting services in standalone mode..."
docker-compose up -d strategist analyst

# Step 6: Verify service connectivity
echo "Verifying service connectivity..."
curl -f http://localhost:8001/health || echo "⚠️ Strategist health check failed"
curl -f http://localhost:8002/health || echo "⚠️ Analyst health check failed"

# Step 7: Update load balancer configuration
echo "Updating load balancer configuration..."
python scripts/rollback/update_load_balancer.py --mode=direct

# Step 8: Exit maintenance mode
echo "Exiting maintenance mode..."
export HELIOS_MAINTENANCE_MODE=false
redis-cli SET "feature_flag:HELIOS_MAINTENANCE_MODE" "false"

echo "✅ Orchestrator rollback complete - Services running in standalone mode"
```

### 4.2 ML Services Rollback (Strategist/Analyst)
```bash
#!/bin/bash
# ml_services_rollback.sh

echo "🤖 ML Services Rollback"

# Function to rollback ML service
rollback_ml_service() {
    local service_name=$1
    local fallback_mode=$2

    echo "Rolling back $service_name to $fallback_mode mode"

    # Stop ML service
    docker-compose stop $service_name

    # Enable fallback mode
    export "HELIOS_${service_name^^}_ENABLED"=false
    export "HELIOS_USE_${fallback_mode^^}_${service_name^^}"=true

    # Start fallback service
    python "services/$service_name/fallback/${fallback_mode}_${service_name}.py" &

    echo "✅ $service_name rolled back to $fallback_mode mode"
}

# Strategist rollback to rule-based
echo "Rolling back Strategist to rule-based career paths..."
rollback_ml_service "strategist" "rule_based"

# Analyst rollback to basic analysis
echo "Rolling back Analyst to basic analysis..."
rollback_ml_service "analyst" "basic"

# Verify fallback services
echo "Verifying fallback services..."
curl -f http://localhost:8001/health || echo "⚠️ Strategist fallback health check failed"
curl -f http://localhost:8002/health || echo "⚠️ Analyst fallback health check failed"

echo "✅ ML services rollback complete - Using fallback implementations"
```

### 4.3 Database Rollback
```bash
#!/bin/bash
# database_rollback.sh

echo "🗄️ Database Rollback"

# Step 1: Enable dual-write mode
echo "Enabling dual-write mode..."
export HELIOS_DUAL_WRITE_MODE=true
redis-cli SET "feature_flag:HELIOS_DUAL_WRITE_MODE" "true"

# Step 2: Validate JSON data integrity
echo "Validating JSON data integrity..."
python scripts/validation/validate_json_integrity.py

# Step 3: Switch read traffic to JSON
echo "Switching read traffic to JSON files..."
export HELIOS_USE_NEW_DATABASE=false
redis-cli SET "feature_flag:HELIOS_USE_NEW_DATABASE" "false"

# Step 4: Stop write traffic to PostgreSQL
echo "Stopping write traffic to PostgreSQL..."
export HELIOS_POSTGRESQL_WRITES_ENABLED=false

# Step 5: Verify JSON-only operation
echo "Verifying JSON-only operation..."
python scripts/testing/test_json_operations.py

# Step 6: Backup PostgreSQL state
echo "Backing up PostgreSQL state..."
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -f "backup/postgresql_rollback_$(date +%Y%m%d_%H%M%S).sql"

echo "✅ Database rollback complete - Operating on JSON files"
```

---

## 5. Graceful Degradation Strategies

### 5.1 Progressive Degradation Levels
```yaml
# degradation_levels.yml
degradation_levels:
  level_0:  # Full functionality
    description: "All services operational"
    services: [orchestrator, strategist, analyst, architect, editor, profile_ingestor]
    features: [ml_processing, ai_optimization, document_generation]

  level_1:  # Reduced ML functionality
    description: "Limited ML processing"
    services: [orchestrator, strategist, analyst, profile_ingestor]
    features: [basic_processing, template_generation]
    disabled: [architect, editor, advanced_ml]

  level_2:  # Core services only
    description: "Core services operational"
    services: [orchestrator, profile_ingestor]
    features: [basic_processing, data_extraction]
    disabled: [strategist, analyst, architect, editor]

  level_3:  # Profile Ingestor only
    description: "Minimal functionality"
    services: [profile_ingestor]
    features: [data_extraction, basic_parsing]
    disabled: [all_ml_services, orchestration]

  level_4:  # Emergency safe mode
    description: "Read-only emergency mode"
    services: []
    features: [status_page, health_checks]
    disabled: [all_processing]
```

### 5.2 Degradation Implementation
```bash
#!/bin/bash
# graceful_degradation.sh

echo "📉 Graceful Degradation Implementation"

# Function to apply degradation level
apply_degradation_level() {
    local level=$1

    echo "Applying degradation level $level"

    case $level in
        1)
            echo "Level 1: Reducing ML functionality"
            update_feature_flag "HELIOS_ARCHITECT_ENABLED" "false"
            update_feature_flag "HELIOS_EDITOR_ENABLED" "false"
            update_feature_flag "HELIOS_ADVANCED_ML_ENABLED" "false"
            ;;
        2)
            echo "Level 2: Core services only"
            update_feature_flag "HELIOS_STRATEGIST_ENABLED" "false"
            update_feature_flag "HELIOS_ANALYST_ENABLED" "false"
            update_feature_flag "HELIOS_ARCHITECT_ENABLED" "false"
            update_feature_flag "HELIOS_EDITOR_ENABLED" "false"
            ;;
        3)
            echo "Level 3: Profile Ingestor only"
            update_feature_flag "HELIOS_ORCHESTRATOR_ENABLED" "false"
            update_feature_flag "HELIOS_PROFILE_INGESTOR_STANDALONE" "true"
            docker-compose stop orchestrator strategist analyst architect editor
            ;;
        4)
            echo "Level 4: Emergency safe mode"
            update_feature_flag "HELIOS_MAINTENANCE_MODE" "true"
            docker-compose stop orchestrator strategist analyst architect editor
            python scripts/emergency/start_status_page.py &
            ;;
    esac

    echo "✅ Degradation level $level applied"
}

# Monitor system health and auto-degrade
auto_degradation_monitor() {
    echo "🔍 Starting auto-degradation monitor"

    while true; do
        # Check system health metrics
        error_rate=$(python scripts/monitoring/get_error_rate.py)
        response_time=$(python scripts/monitoring/get_avg_response_time.py)
        service_availability=$(python scripts/monitoring/get_service_availability.py)

        # Apply degradation based on metrics
        if (( $(echo "$error_rate > 25" | bc -l) )); then
            apply_degradation_level 1
        elif (( $(echo "$error_rate > 50" | bc -l) )); then
            apply_degradation_level 2
        elif (( $(echo "$service_availability < 50" | bc -l) )); then
            apply_degradation_level 3
        fi

        sleep 30  # Check every 30 seconds
    done
}
```

---

## 6. Communication and User Experience

### 6.1 User Communication Templates
```yaml
# communication_templates.yml
rollback_notifications:
  maintenance_mode:
    title: "🔧 Helios Maintenance Mode"
    message: |
      We're performing emergency maintenance to ensure optimal performance.

      Available Services:
      - Profile data extraction ✅
      - Basic resume processing ✅

      Temporarily Unavailable:
      - Career path generation ⏸️
      - Market analysis ⏸️
      - Document optimization ⏸️

      Estimated completion: 30 minutes
      We'll notify you when all services are restored.

  degraded_service:
    title: "⚠️ Helios Service Degradation"
    message: |
      We're experiencing technical difficulties and have temporarily
      reduced some advanced features to maintain core functionality.

      What's Still Working:
      - Resume processing and data extraction
      - Basic career guidance
      - Account management

      What's Temporarily Limited:
      - AI-powered career recommendations
      - Advanced document optimization
      - Market analysis features

      We're working to restore full functionality.

  service_restored:
    title: "✅ Helios Services Restored"
    message: |
      All Helios services have been successfully restored!

      You now have access to:
      - Full AI-powered career recommendations
      - Advanced document optimization
      - Comprehensive market analysis
      - All premium features

      Thank you for your patience during the maintenance.
```

### 6.2 Status Page Integration
```python
# status_page_integration.py
import requests
import json
from datetime import datetime

class StatusPageManager:
    def __init__(self, api_key, page_id):
        self.api_key = api_key
        self.page_id = page_id
        self.base_url = "https://api.statuspage.io/v1"

    def create_incident(self, title, message, impact="minor"):
        """Create incident on status page during rollback"""
        data = {
            "incident": {
                "name": title,
                "status": "investigating",
                "impact_override": impact,
                "body": message
            }
        }

        response = requests.post(
            f"{self.base_url}/pages/{self.page_id}/incidents",
            headers={"Authorization": f"OAuth {self.api_key}"},
            json=data
        )
        return response.json()

    def update_component_status(self, component_name, status):
        """Update individual service status"""
        components = {
            "orchestrator": "comp_orchestrator_123",
            "strategist": "comp_strategist_456",
            "analyst": "comp_analyst_789"
        }

        component_id = components.get(component_name)
        if component_id:
            data = {"component": {"status": status}}
            requests.patch(
                f"{self.base_url}/pages/{self.page_id}/components/{component_id}",
                headers={"Authorization": f"OAuth {self.api_key}"},
                json=data
            )

    def rollback_notification_flow(self, rollback_type):
        """Complete notification flow for rollback"""
        if rollback_type == "emergency":
            incident = self.create_incident(
                "Emergency Maintenance - Helios Services",
                "We've initiated emergency maintenance procedures. Core functionality remains available.",
                impact="major"
            )

            # Update component statuses
            self.update_component_status("strategist", "under_maintenance")
            self.update_component_status("analyst", "under_maintenance")

        elif rollback_type == "planned":
            incident = self.create_incident(
                "Planned Service Rollback",
                "We're rolling back recent changes to ensure optimal performance.",
                impact="minor"
            )

# Usage during rollback
status_manager = StatusPageManager(api_key=os.getenv("STATUS_PAGE_API_KEY"),
                                 page_id=os.getenv("STATUS_PAGE_ID"))
status_manager.rollback_notification_flow("emergency")
```

---

## 7. Monitoring During Rollback

### 7.1 Rollback Monitoring Dashboard
```yaml
# rollback_monitoring.yml
monitoring:
  real_time_metrics:
    - rollback_progress_percentage
    - active_user_sessions
    - error_rate_during_rollback
    - service_recovery_time
    - data_consistency_status
    - user_impact_assessment

  alerting_rules:
    rollback_failure:
      condition: "rollback_progress_percentage < 50 AND time_elapsed > 600"
      severity: critical
      action: "escalate to senior engineer"

    data_inconsistency:
      condition: "data_consistency_status != 'consistent'"
      severity: high
      action: "pause rollback, investigate immediately"

    user_impact_high:
      condition: "active_user_sessions < 50% AND error_rate > 10%"
      severity: medium
      action: "prioritize user communication"

  dashboards:
    rollback_overview:
      panels:
        - rollback_timeline
        - service_status_grid
        - user_impact_metrics
        - error_rate_trends
        - performance_comparison
```

### 7.2 Health Monitoring Scripts
```bash
#!/bin/bash
# rollback_health_monitor.sh

echo "🩺 Rollback Health Monitoring"

# Function to check service health during rollback
monitor_service_health() {
    local service_name=$1
    local expected_status=$2  # up, down, degraded

    echo "Monitoring $service_name (expected: $expected_status)"

    while true; do
        health_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$(get_port $service_name)/health")

        case $expected_status in
            "up")
                if [ "$health_status" = "200" ]; then
                    echo "✅ $service_name: HEALTHY"
                else
                    echo "❌ $service_name: UNHEALTHY (HTTP $health_status)"
                    alert_unhealthy_service "$service_name" "$health_status"
                fi
                ;;
            "down")
                if [ "$health_status" = "000" ] || [ "$health_status" = "404" ]; then
                    echo "✅ $service_name: DOWN (as expected)"
                else
                    echo "⚠️ $service_name: Should be down but responding (HTTP $health_status)"
                fi
                ;;
        esac

        sleep 10
    done
}

# Monitor data consistency during rollback
monitor_data_consistency() {
    echo "🔍 Monitoring data consistency during rollback"

    while true; do
        # Check JSON vs PostgreSQL consistency
        consistency_status=$(python scripts/monitoring/check_data_consistency.py)

        if [ "$consistency_status" = "consistent" ]; then
            echo "✅ Data consistency: OK"
        else
            echo "❌ Data consistency: ISSUES DETECTED"
            alert_data_inconsistency "$consistency_status"
        fi

        sleep 30
    done
}

# Monitor user impact
monitor_user_impact() {
    echo "👥 Monitoring user impact during rollback"

    baseline_sessions=$(redis-cli GET "baseline:active_sessions")

    while true; do
        current_sessions=$(redis-cli SCARD "active_sessions")
        session_impact=$((100 - (current_sessions * 100 / baseline_sessions)))

        error_rate=$(python scripts/monitoring/get_current_error_rate.py)

        echo "📊 User Impact: ${session_impact}% session reduction, ${error_rate}% error rate"

        # Alert if impact is too high
        if [ "$session_impact" -gt 75 ] || [ "$error_rate" -gt 25 ]; then
            alert_high_user_impact "$session_impact" "$error_rate"
        fi

        sleep 60
    done
}

# Start monitoring processes
monitor_service_health "profile_ingestor" "up" &
monitor_data_consistency &
monitor_user_impact &

echo "✅ Rollback monitoring started"
```

---

## 8. Post-Rollback Procedures

### 8.1 System Validation
```bash
#!/bin/bash
# post_rollback_validation.sh

echo "✅ Post-Rollback System Validation"

# Step 1: Verify all services are in expected state
echo "Verifying service states..."
python scripts/validation/verify_rollback_state.py

# Step 2: Run integration tests
echo "Running integration tests..."
pytest tests/integration/ --rollback-mode

# Step 3: Validate user workflows
echo "Validating user workflows..."
python scripts/validation/test_user_workflows.py

# Step 4: Check data integrity
echo "Checking data integrity..."
python scripts/validation/comprehensive_data_check.py

# Step 5: Performance baseline comparison
echo "Comparing performance to baseline..."
python scripts/validation/performance_comparison.py --baseline=pre_rollback

# Step 6: Generate rollback report
echo "Generating rollback report..."
python scripts/reporting/generate_rollback_report.py

echo "✅ Post-rollback validation complete"
```

### 8.2 Incident Analysis
```python
# incident_analysis.py
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class RollbackIncident:
    timestamp: datetime
    trigger: str
    services_affected: List[str]
    rollback_type: str
    duration_minutes: int
    user_impact: Dict[str, float]
    data_loss: bool
    resolution_actions: List[str]

class IncidentAnalyzer:
    def __init__(self):
        self.incidents = []

    def analyze_rollback(self, rollback_data):
        """Analyze rollback incident for lessons learned"""
        incident = RollbackIncident(
            timestamp=rollback_data['start_time'],
            trigger=rollback_data['trigger'],
            services_affected=rollback_data['affected_services'],
            rollback_type=rollback_data['rollback_type'],
            duration_minutes=rollback_data['duration'],
            user_impact=rollback_data['user_metrics'],
            data_loss=rollback_data['data_loss'],
            resolution_actions=rollback_data['actions_taken']
        )

        self.incidents.append(incident)
        return self.generate_analysis_report(incident)

    def generate_analysis_report(self, incident):
        """Generate comprehensive incident analysis"""
        report = {
            "incident_summary": {
                "trigger": incident.trigger,
                "duration": f"{incident.duration_minutes} minutes",
                "severity": self.calculate_severity(incident),
                "user_impact": incident.user_impact
            },
            "lessons_learned": self.extract_lessons(incident),
            "improvement_recommendations": self.generate_recommendations(incident),
            "prevention_strategies": self.suggest_prevention(incident)
        }

        return report

    def calculate_severity(self, incident):
        """Calculate incident severity based on impact"""
        if incident.data_loss:
            return "CRITICAL"
        elif incident.duration_minutes > 60:
            return "HIGH"
        elif incident.user_impact.get('session_loss', 0) > 50:
            return "MEDIUM"
        else:
            return "LOW"

# Usage
analyzer = IncidentAnalyzer()
rollback_report = analyzer.analyze_rollback({
    'start_time': datetime.now(),
    'trigger': 'database_migration_failure',
    'affected_services': ['strategist', 'analyst'],
    'rollback_type': 'emergency',
    'duration': 15,
    'user_metrics': {'session_loss': 25, 'error_rate': 5},
    'data_loss': False,
    'actions_taken': ['feature_flags_disabled', 'services_restarted', 'fallback_activated']
})
```

---

## 9. Recovery Planning

### 9.1 Recovery Strategies
```bash
#!/bin/bash
# recovery_planning.sh

echo "🔄 Recovery Planning After Rollback"

# Function to plan service recovery
plan_service_recovery() {
    local failed_service=$1
    local failure_cause=$2

    echo "Planning recovery for $failed_service (cause: $failure_cause)"

    case $failure_cause in
        "dependency_failure")
            echo "Recovery plan: Update dependencies, test in staging"
            python scripts/recovery/plan_dependency_recovery.py --service=$failed_service
            ;;
        "configuration_error")
            echo "Recovery plan: Validate configuration, gradual rollout"
            python scripts/recovery/plan_config_recovery.py --service=$failed_service
            ;;
        "performance_degradation")
            echo "Recovery plan: Performance optimization, load testing"
            python scripts/recovery/plan_performance_recovery.py --service=$failed_service
            ;;
        "data_corruption")
            echo "Recovery plan: Data validation, integrity checks"
            python scripts/recovery/plan_data_recovery.py --service=$failed_service
            ;;
    esac
}

# Create recovery timeline
create_recovery_timeline() {
    echo "📅 Creating Recovery Timeline"

    cat > recovery_timeline.md << EOF
# Recovery Timeline

## Immediate Actions (0-1 hour)
- [ ] Root cause analysis complete
- [ ] Fix developed and tested in staging
- [ ] Recovery plan approved by team lead

## Short-term Recovery (1-4 hours)
- [ ] Deploy fix to staging environment
- [ ] Run comprehensive test suite
- [ ] Validate fix effectiveness
- [ ] Prepare production deployment

## Production Recovery (4-8 hours)
- [ ] Deploy fix to production with feature flags
- [ ] Gradual traffic ramp-up
- [ ] Monitor key metrics
- [ ] Full service restoration

## Post-Recovery (8-24 hours)
- [ ] System stability verification
- [ ] Performance optimization
- [ ] Documentation updates
- [ ] Team retrospective
EOF

    echo "✅ Recovery timeline created"
}

# Execute recovery plan
execute_recovery() {
    local recovery_type=$1

    echo "🚀 Executing $recovery_type recovery"

    case $recovery_type in
        "feature_flag")
            echo "Enabling features gradually..."
            ./scripts/recovery/gradual_feature_restoration.sh
            ;;
        "service_restart")
            echo "Restarting services with fixes..."
            ./scripts/recovery/service_restart_recovery.sh
            ;;
        "database_repair")
            echo "Repairing database issues..."
            ./scripts/recovery/database_repair_recovery.sh
            ;;
    esac
}
```

---

## 10. Success Criteria and Sign-off

### 10.1 Rollback Success Criteria
```yaml
# rollback_success_criteria.yml
success_criteria:
  technical:
    - all_critical_services_operational: true
    - data_integrity_maintained: true
    - zero_data_loss: true
    - performance_within_baseline: ">90%"
    - error_rate_acceptable: "<5%"
    - rollback_time_met: true  # <5min emergency, <30min planned

  business:
    - user_functionality_restored: true
    - customer_impact_minimized: true
    - sla_requirements_met: true
    - business_continuity_maintained: true

  operational:
    - monitoring_functional: true
    - alerting_operational: true
    - backup_systems_verified: true
    - documentation_updated: true
```

### 10.2 Sign-off Procedures
```bash
#!/bin/bash
# rollback_signoff.sh

echo "✍️ Rollback Sign-off Procedures"

# Generate sign-off checklist
generate_signoff_checklist() {
    cat > rollback_signoff_checklist.md << EOF
# Rollback Sign-off Checklist

## Technical Validation
- [ ] All services responding to health checks
- [ ] Database integrity verified
- [ ] No data loss confirmed
- [ ] Performance metrics within acceptable range
- [ ] Error rates below threshold
- [ ] Security measures intact

## Business Validation
- [ ] Critical user workflows functional
- [ ] Customer-facing features operational
- [ ] Revenue-generating processes working
- [ ] Support team notified of status

## Operational Validation
- [ ] Monitoring and alerting functional
- [ ] Backup systems verified
- [ ] Documentation updated
- [ ] Team debriefing scheduled

## Approvals Required
- [ ] Technical Lead: ________________
- [ ] Operations Manager: ____________
- [ ] Product Owner: ________________
- [ ] On-call Engineer: _____________

## Final Sign-off
- [ ] System Ready for Production: ___________
- [ ] Rollback Officially Complete: __________

Date: ___________  Time: ___________
EOF

    echo "✅ Sign-off checklist generated"
}

# Automated validation for sign-off
automated_signoff_validation() {
    echo "🤖 Running automated sign-off validation"

    # Technical checks
    python scripts/validation/automated_health_check.py
    python scripts/validation/automated_performance_check.py
    python scripts/validation/automated_security_check.py

    # Generate validation report
    python scripts/validation/generate_signoff_report.py

    echo "✅ Automated validation complete - Review report before manual sign-off"
}

# Execute sign-off process
generate_signoff_checklist
automated_signoff_validation

echo "📋 Rollback ready for manual sign-off - Review checklist and validation report"
```

---

## 11. Contacts and Escalation

### 11.1 Emergency Contacts
```yaml
# emergency_contacts.yml
contacts:
  primary_on_call:
    name: "Operations Engineer"
    phone: "+1-555-OPS-CALL"
    email: "ops-oncall@helios.com"
    slack: "@ops-oncall"

  technical_lead:
    name: "Senior Engineering Lead"
    phone: "+1-555-TECH-LEAD"
    email: "tech-lead@helios.com"
    slack: "@tech-lead"

  product_owner:
    name: "Product Owner"
    phone: "+1-555-PRODUCT"
    email: "product@helios.com"
    slack: "@product-owner"

  management:
    name: "Engineering Director"
    phone: "+1-555-ENG-DIR"
    email: "engineering-director@helios.com"
    slack: "@eng-director"

escalation_matrix:
  level_1:  # 0-15 minutes
    responders: ["primary_on_call"]
    auto_escalate: 15

  level_2:  # 15-30 minutes
    responders: ["primary_on_call", "technical_lead"]
    auto_escalate: 30

  level_3:  # 30+ minutes
    responders: ["primary_on_call", "technical_lead", "product_owner", "management"]
```

---

*This runbook ensures safe, efficient system-wide rollbacks with minimal user impact and comprehensive recovery procedures for the Helios Career Operations System.*

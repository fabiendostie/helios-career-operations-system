# Service Deployment Runbook
# Helios Career Operations System

## Document Metadata
- **Version:** 1.0
- **Date:** 2025-09-20
- **Author:** DevOps Team
- **Status:** Production Ready
- **Review Frequency:** Monthly

---

## 1. Overview

This runbook provides comprehensive procedures for deploying individual services in the Helios Career Operations System, including validation, monitoring, and rollback procedures for each service.

### 1.1 Service Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Orchestrator  │────│    Strategist   │────│     Analyst     │
│     (Core)      │    │   (ML/Career)   │    │   (NLP/Opt)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Architect   │    │   Profile       │    │     Editor      │
│  (Doc Gen)      │    │   Ingestor      │    │  (Text Opt)     │
│   [PENDING]     │    │  (COMPLETED)    │    │   [PENDING]     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 1.2 Deployment Prerequisites
- [ ] Docker/Kubernetes cluster access
- [ ] CI/CD pipeline configured
- [ ] Environment variables configured
- [ ] Database connections validated
- [ ] Monitoring tools configured
- [ ] Rollback procedures tested

---

## 2. Profile Ingestor Service (COMPLETED)

### 2.1 Deployment Status
- **Status:** ✅ Production Ready
- **Tests:** 208/208 passing (100%)
- **Dependencies:** Python 3.13.1, spaCy, NLP models
- **Deployment Type:** Standalone service

### 2.2 Deployment Procedure
```bash
#!/bin/bash
# deploy_profile_ingestor.sh

echo "📦 Deploying Profile Ingestor Service"

# Step 1: Pre-deployment validation
echo "Running pre-deployment validation..."
cd services/profile-ingestor

# Validate environment
python -c "import sys; print(f'Python version: {sys.version}')"
python -c "import spacy; print(f'spaCy version: {spacy.__version__}')"

# Run test suite
echo "Running test suite..."
python -m pytest --tb=short -v
if [ $? -ne 0 ]; then
    echo "❌ Tests failed - deployment cancelled"
    exit 1
fi
echo "✅ All tests passed"

# Step 2: Check dependencies
echo "Checking dependencies..."
pip check
python -m spacy validate

# Download required models if missing
python -m spacy download en_core_web_sm --quiet
python -m spacy download fr_core_news_sm --quiet

# Step 3: Build deployment package
echo "Building deployment package..."
pip freeze > requirements_deployed.txt

# Step 4: Deploy service
echo "Deploying Profile Ingestor..."
# For Docker deployment
docker build -t helios-profile-ingestor:latest .
docker tag helios-profile-ingestor:latest helios-profile-ingestor:$(date +%Y%m%d-%H%M%S)

# Step 5: Start service
echo "Starting service..."
docker run -d \
    --name helios-profile-ingestor \
    -p 8080:8080 \
    -v $(pwd)/output:/app/output \
    -v $(pwd)/data:/app/data \
    -e HELIOS_LOG_LEVEL=INFO \
    helios-profile-ingestor:latest

# Step 6: Health check
echo "Performing health check..."
sleep 10
curl -f http://localhost:8080/health || exit 1

echo "✅ Profile Ingestor deployment successful"
```

### 2.3 Post-Deployment Validation
```bash
#!/bin/bash
# validate_profile_ingestor.sh

echo "🔍 Profile Ingestor Post-Deployment Validation"

# Test basic functionality
echo "Testing basic functionality..."
python -c "
from src.resume_extractor.main import process_resume
print('✅ Import successful')
"

# Test processing pipeline
echo "Testing processing pipeline..."
python scripts/testing/test_pipeline_integration.py

# Validate output format
echo "Validating output format..."
python scripts/validation/validate_output_schema.py

# Performance baseline
echo "Running performance baseline..."
python scripts/testing/performance_baseline.py

echo "✅ Profile Ingestor validation complete"
```

---

## 3. Orchestrator Service

### 3.1 Deployment Status
- **Status:** ✅ Operational
- **Dependencies:** FastAPI, Redis, PostgreSQL
- **Deployment Type:** Microservice with state management

### 3.2 Deployment Procedure
```bash
#!/bin/bash
# deploy_orchestrator.sh

echo "🎭 Deploying Orchestrator Service"

# Step 1: Environment preparation
echo "Preparing environment..."
cd services/orchestrator

# Validate configuration
python -c "
import yaml
with open('config/production.yml') as f:
    config = yaml.safe_load(f)
print('✅ Configuration valid')
"

# Check database connectivity
echo "Checking database connectivity..."
python -c "
import psycopg2
import os
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
print('✅ Database connection successful')
conn.close()
"

# Check Redis connectivity
echo "Checking Redis connectivity..."
redis-cli -h $REDIS_HOST -p $REDIS_PORT ping || exit 1

# Step 2: Build and test
echo "Building service..."
pip install -r requirements.txt
python -m pytest tests/ --tb=short

# Step 3: Database migrations
echo "Running database migrations..."
python scripts/migrate.py --environment=production

# Step 4: Deploy with feature flags
echo "Deploying with feature flags..."
export HELIOS_ORCHESTRATOR_ENABLED=true
export HELIOS_GRACEFUL_SHUTDOWN=true
export HELIOS_HEALTH_CHECK_INTERVAL=30

# Build Docker image
docker build -t helios-orchestrator:latest .
docker tag helios-orchestrator:latest helios-orchestrator:$(date +%Y%m%d-%H%M%S)

# Step 5: Deploy to Kubernetes
echo "Deploying to Kubernetes..."
kubectl apply -f k8s/orchestrator-deployment.yml
kubectl apply -f k8s/orchestrator-service.yml

# Step 6: Wait for deployment
echo "Waiting for deployment to complete..."
kubectl wait --for=condition=available --timeout=300s deployment/helios-orchestrator

# Step 7: Health verification
echo "Verifying deployment health..."
kubectl get pods -l app=helios-orchestrator
curl -f http://orchestrator.helios.local/health || exit 1

echo "✅ Orchestrator deployment successful"
```

### 3.3 Blue-Green Deployment
```bash
#!/bin/bash
# blue_green_orchestrator.sh

echo "🔄 Blue-Green Deployment for Orchestrator"

# Step 1: Deploy to green environment
echo "Deploying to green environment..."
kubectl apply -f k8s/orchestrator-green-deployment.yml

# Step 2: Wait for green deployment
kubectl wait --for=condition=available --timeout=300s deployment/helios-orchestrator-green

# Step 3: Run smoke tests on green
echo "Running smoke tests on green environment..."
python tests/smoke/test_orchestrator_green.py

# Step 4: Switch traffic to green
echo "Switching traffic to green..."
kubectl patch service helios-orchestrator -p '{"spec":{"selector":{"version":"green"}}}'

# Step 5: Monitor for issues
echo "Monitoring for 5 minutes..."
sleep 300

# Check error rates
error_rate=$(python scripts/monitoring/get_error_rate.py --service=orchestrator --duration=5m)
if (( $(echo "$error_rate > 5" | bc -l) )); then
    echo "❌ High error rate detected - rolling back"
    kubectl patch service helios-orchestrator -p '{"spec":{"selector":{"version":"blue"}}}'
    exit 1
fi

# Step 6: Cleanup blue environment
echo "Cleaning up blue environment..."
kubectl delete deployment helios-orchestrator-blue

echo "✅ Blue-green deployment successful"
```

---

## 4. Strategist Service

### 4.1 Deployment Status
- **Status:** ✅ Operational
- **Dependencies:** ML models, sentence-transformers, scikit-learn
- **Deployment Type:** ML microservice with model loading

### 4.2 Deployment Procedure
```bash
#!/bin/bash
# deploy_strategist.sh

echo "🤖 Deploying Strategist Service"

# Step 1: Model preparation
echo "Preparing ML models..."
cd services/strategist

# Download and validate models
python scripts/download_models.py --models=all
python scripts/validate_models.py

# Step 2: Environment setup
echo "Setting up environment..."
pip install -r requirements.txt

# Verify GPU availability (if applicable)
python -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU count: {torch.cuda.device_count()}')
"

# Step 3: Model warming
echo "Warming up models..."
python scripts/warm_models.py

# Step 4: Integration tests
echo "Running integration tests..."
python -m pytest tests/integration/ --tb=short

# Step 5: Deploy service
echo "Deploying Strategist service..."
docker build -t helios-strategist:latest .

# Use GPU runtime if available
if docker info | grep -q nvidia; then
    GPU_FLAG="--runtime=nvidia"
else
    GPU_FLAG=""
fi

docker run -d \
    --name helios-strategist \
    -p 8001:8001 \
    $GPU_FLAG \
    -v $(pwd)/models:/app/models \
    -e HELIOS_MODEL_CACHE_DIR=/app/models \
    -e HELIOS_STRATEGIST_WORKERS=4 \
    helios-strategist:latest

# Step 6: Health and readiness checks
echo "Performing health checks..."
sleep 30  # Allow time for model loading

# Health check
curl -f http://localhost:8001/health || exit 1

# Readiness check (models loaded)
curl -f http://localhost:8001/ready || exit 1

# Step 7: Performance validation
echo "Running performance validation..."
python tests/performance/test_strategist_performance.py

echo "✅ Strategist deployment successful"
```

### 4.3 Model Update Procedure
```bash
#!/bin/bash
# update_strategist_models.sh

echo "🔄 Updating Strategist Models"

# Step 1: Download new models to staging
echo "Downloading new models..."
mkdir -p models/staging
python scripts/download_models.py --target=models/staging --version=latest

# Step 2: Validate new models
echo "Validating new models..."
python scripts/validate_models.py --model-path=models/staging

# Step 3: A/B test new models
echo "Running A/B test..."
export HELIOS_STRATEGIST_AB_TEST=true
export HELIOS_STRATEGIST_MODEL_A=models/current
export HELIOS_STRATEGIST_MODEL_B=models/staging

python tests/ab_testing/test_model_performance.py

# Step 4: Switch to new models if performance is better
if python scripts/compare_model_performance.py --threshold=0.05; then
    echo "New models perform better - switching..."
    mv models/current models/backup
    mv models/staging models/current

    # Restart service with new models
    docker restart helios-strategist

    echo "✅ Model update successful"
else
    echo "⚠️ New models don't meet performance threshold - keeping current models"
    rm -rf models/staging
fi
```

---

## 5. Analyst Service

### 5.1 Deployment Status
- **Status:** ✅ Operational
- **Dependencies:** spaCy, NLP models, analysis pipeline
- **Deployment Type:** NLP microservice with 6-step pipeline

### 5.2 Deployment Procedure
```bash
#!/bin/bash
# deploy_analyst.sh

echo "📊 Deploying Analyst Service"

# Step 1: NLP model preparation
echo "Preparing NLP models..."
cd services/analyst

# Download spaCy models
python -m spacy download en_core_web_sm
python -m spacy download fr_core_news_sm

# Validate model loading
python -c "
import spacy
nlp_en = spacy.load('en_core_web_sm')
nlp_fr = spacy.load('fr_core_news_sm')
print('✅ NLP models loaded successfully')
"

# Step 2: Pipeline validation
echo "Validating analysis pipeline..."
python scripts/validate_pipeline.py --all-steps

# Step 3: Performance testing
echo "Running performance tests..."
python tests/performance/test_pipeline_performance.py

# Step 4: Deploy service
echo "Deploying Analyst service..."
docker build -t helios-analyst:latest .

docker run -d \
    --name helios-analyst \
    -p 8002:8002 \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/models:/app/models \
    -e HELIOS_ANALYST_PIPELINE_WORKERS=6 \
    -e HELIOS_ANALYST_BATCH_SIZE=32 \
    helios-analyst:latest

# Step 5: Pipeline health check
echo "Checking pipeline health..."
sleep 20

# Test each pipeline step
for step in extract transform analyze optimize score validate; do
    echo "Testing $step step..."
    curl -f "http://localhost:8002/pipeline/$step/health" || exit 1
done

# Step 6: End-to-end pipeline test
echo "Running end-to-end pipeline test..."
python tests/integration/test_full_pipeline.py

echo "✅ Analyst deployment successful"
```

### 5.3 Pipeline Configuration
```yaml
# analyst_pipeline_config.yml
pipeline:
  steps:
    1_extract:
      name: "Content Extraction"
      timeout: 30
      retries: 3

    2_transform:
      name: "Data Transformation"
      timeout: 45
      retries: 2

    3_analyze:
      name: "NLP Analysis"
      timeout: 60
      retries: 2

    4_optimize:
      name: "Content Optimization"
      timeout: 90
      retries: 1

    5_score:
      name: "ATS Scoring"
      timeout: 30
      retries: 3

    6_validate:
      name: "Output Validation"
      timeout: 15
      retries: 2

  monitoring:
    health_check_interval: 30
    performance_threshold: 0.95
    error_rate_threshold: 0.05
```

---

## 6. Architect Service (PENDING)

### 6.1 Planned Deployment
- **Status:** ⏳ Development Phase
- **Expected:** Q1 2025
- **Dependencies:** Document generation, templates, AI models

### 6.2 Deployment Preparation
```bash
#!/bin/bash
# prepare_architect_deployment.sh

echo "🏗️ Preparing Architect Service Deployment"

# Step 1: Template validation
echo "Validating document templates..."
cd services/architect
python scripts/validate_templates.py

# Step 2: AI model preparation
echo "Preparing AI models for document generation..."
python scripts/download_generation_models.py

# Step 3: Integration testing framework
echo "Setting up integration testing..."
python -m pytest tests/integration/ --collect-only

echo "✅ Architect deployment preparation complete"
echo "⏳ Awaiting service implementation completion"
```

---

## 7. Editor Service (PENDING)

### 7.1 Planned Deployment
- **Status:** ⏳ Development Phase
- **Expected:** Q1 2025
- **Dependencies:** Text optimization, NLP, quality metrics

### 7.2 Deployment Preparation
```bash
#!/bin/bash
# prepare_editor_deployment.sh

echo "✏️ Preparing Editor Service Deployment"

# Step 1: Text optimization models
echo "Preparing text optimization models..."
cd services/editor
python scripts/download_optimization_models.py

# Step 2: Quality metrics framework
echo "Setting up quality metrics..."
python scripts/setup_quality_metrics.py

echo "✅ Editor deployment preparation complete"
echo "⏳ Awaiting service implementation completion"
```

---

## 8. Multi-Service Deployment

### 8.1 Orchestrated Deployment
```bash
#!/bin/bash
# deploy_all_services.sh

echo "🚀 Multi-Service Deployment"

# Define deployment order (dependencies first)
SERVICES=("profile-ingestor" "orchestrator" "strategist" "analyst")

# Step 1: Pre-deployment validation
echo "Running pre-deployment validation..."
for service in "${SERVICES[@]}"; do
    echo "Validating $service..."
    cd "services/$service"
    python scripts/validate_deployment.py || exit 1
    cd ../..
done

# Step 2: Deploy services in order
for service in "${SERVICES[@]}"; do
    echo "Deploying $service..."
    ./scripts/deployment/deploy_$service.sh

    # Wait for service to be ready
    sleep 30

    # Health check
    python scripts/health_check.py --service=$service || exit 1

    echo "✅ $service deployed successfully"
done

# Step 3: Integration validation
echo "Running integration validation..."
python tests/integration/test_multi_service.py

# Step 4: Load balancer configuration
echo "Configuring load balancer..."
python scripts/configure_load_balancer.py --services="${SERVICES[*]}"

echo "✅ Multi-service deployment complete"
```

### 8.2 Canary Deployment
```bash
#!/bin/bash
# canary_deployment.sh

echo "🐤 Canary Deployment"

SERVICE=${1:-orchestrator}
CANARY_PERCENTAGE=${2:-10}

echo "Deploying $SERVICE with $CANARY_PERCENTAGE% traffic"

# Step 1: Deploy canary version
echo "Deploying canary version..."
kubectl apply -f k8s/$SERVICE-canary-deployment.yml

# Step 2: Configure traffic splitting
echo "Configuring traffic splitting..."
kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: $SERVICE-canary
spec:
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: $SERVICE
        subset: canary
  - route:
    - destination:
        host: $SERVICE
        subset: stable
      weight: $((100 - CANARY_PERCENTAGE))
    - destination:
        host: $SERVICE
        subset: canary
      weight: $CANARY_PERCENTAGE
EOF

# Step 3: Monitor canary performance
echo "Monitoring canary performance..."
python scripts/monitoring/monitor_canary.py --service=$SERVICE --duration=600

# Step 4: Promote or rollback based on metrics
if python scripts/analysis/evaluate_canary.py --service=$SERVICE; then
    echo "✅ Canary deployment successful - promoting to production"
    kubectl apply -f k8s/$SERVICE-production-deployment.yml
    kubectl delete -f k8s/$SERVICE-canary-deployment.yml
else
    echo "❌ Canary deployment failed - rolling back"
    kubectl delete -f k8s/$SERVICE-canary-deployment.yml
    exit 1
fi
```

---

## 9. Monitoring and Health Checks

### 9.1 Service Health Monitoring
```python
# health_monitoring.py
import requests
import time
import logging
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class ServiceHealth:
    name: str
    url: str
    status: str
    response_time: float
    last_check: str

class HealthMonitor:
    def __init__(self, services: List[Dict]):
        self.services = services
        self.health_status = {}

    def check_service_health(self, service: Dict) -> ServiceHealth:
        """Check individual service health"""
        start_time = time.time()

        try:
            response = requests.get(
                f"{service['url']}/health",
                timeout=10
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                status = "healthy"
            else:
                status = "unhealthy"

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            status = "unreachable"
            logging.error(f"Health check failed for {service['name']}: {e}")

        return ServiceHealth(
            name=service['name'],
            url=service['url'],
            status=status,
            response_time=response_time,
            last_check=time.strftime('%Y-%m-%d %H:%M:%S')
        )

    def monitor_all_services(self):
        """Monitor all services continuously"""
        while True:
            for service in self.services:
                health = self.check_service_health(service)
                self.health_status[service['name']] = health

                if health.status != "healthy":
                    self.alert_unhealthy_service(health)

            time.sleep(30)  # Check every 30 seconds

    def alert_unhealthy_service(self, health: ServiceHealth):
        """Alert on unhealthy service"""
        logging.warning(f"Service {health.name} is {health.status}")
        # Send alert to monitoring system
        # self.send_alert(health)

# Configuration
services = [
    {"name": "profile-ingestor", "url": "http://localhost:8080"},
    {"name": "orchestrator", "url": "http://localhost:8000"},
    {"name": "strategist", "url": "http://localhost:8001"},
    {"name": "analyst", "url": "http://localhost:8002"}
]

monitor = HealthMonitor(services)
monitor.monitor_all_services()
```

### 9.2 Deployment Health Dashboard
```yaml
# deployment_dashboard.yml
dashboard:
  name: "Helios Service Deployment Health"
  panels:
    - title: "Service Status"
      type: "status_grid"
      services:
        - profile_ingestor
        - orchestrator
        - strategist
        - analyst

    - title: "Deployment Metrics"
      type: "metrics"
      metrics:
        - deployment_success_rate
        - rollback_frequency
        - average_deployment_time
        - service_uptime

    - title: "Health Check Trends"
      type: "time_series"
      metrics:
        - response_time_trend
        - error_rate_trend
        - availability_percentage

    - title: "Recent Deployments"
      type: "table"
      columns:
        - service_name
        - version
        - deployment_time
        - status
        - rollback_count
```

---

## 10. Troubleshooting Guide

### 10.1 Common Deployment Issues

#### Issue: Service Fails to Start
```bash
# Troubleshooting service startup failures

# Check container logs
docker logs helios-orchestrator --tail=50

# Check resource usage
docker stats helios-orchestrator

# Verify environment variables
docker exec helios-orchestrator env | grep HELIOS

# Check dependencies
docker exec helios-orchestrator pip check

# Test configuration
docker exec helios-orchestrator python -c "
import yaml
with open('config/production.yml') as f:
    config = yaml.safe_load(f)
    print('Config valid')
"
```

#### Issue: Health Checks Failing
```bash
# Troubleshooting health check failures

# Direct health check
curl -v http://localhost:8000/health

# Check database connectivity
python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    print('✅ Database connection OK')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"

# Check Redis connectivity
redis-cli -h $REDIS_HOST -p $REDIS_PORT ping

# Review application logs
tail -f logs/application.log | grep ERROR
```

#### Issue: Performance Degradation
```bash
# Troubleshooting performance issues

# Check resource utilization
top -p $(pgrep -f helios-orchestrator)

# Monitor memory usage
python scripts/monitoring/memory_profiler.py --service=orchestrator

# Check slow queries
python scripts/monitoring/slow_query_analyzer.py

# Profile API endpoints
python scripts/profiling/api_profiler.py --duration=300
```

---

## 11. Rollback Procedures

### 11.1 Service-Specific Rollback
```bash
#!/bin/bash
# service_rollback.sh

SERVICE=$1
ROLLBACK_TYPE=${2:-previous}  # previous, stable, version

echo "🔄 Rolling back $SERVICE ($ROLLBACK_TYPE)"

case $ROLLBACK_TYPE in
    "previous")
        TARGET_VERSION=$(git describe --tags --abbrev=0 HEAD~1)
        ;;
    "stable")
        TARGET_VERSION=$(cat config/stable_versions.txt | grep $SERVICE | cut -d: -f2)
        ;;
    "version")
        TARGET_VERSION=$3
        ;;
esac

echo "Rolling back $SERVICE to $TARGET_VERSION"

# Stop current service
docker stop helios-$SERVICE

# Deploy previous version
docker run -d \
    --name helios-$SERVICE \
    -p $(get_service_port $SERVICE):$(get_service_port $SERVICE) \
    helios-$SERVICE:$TARGET_VERSION

# Health check
sleep 30
curl -f http://localhost:$(get_service_port $SERVICE)/health || exit 1

echo "✅ $SERVICE rollback successful to $TARGET_VERSION"
```

---

## 12. Success Criteria

### 12.1 Deployment Success Criteria
- [ ] All services start successfully
- [ ] Health checks pass for all services
- [ ] Integration tests pass
- [ ] Performance within 10% of baseline
- [ ] Zero critical errors in logs
- [ ] User functionality unaffected

### 12.2 Service-Specific Criteria

#### Profile Ingestor
- [ ] All 208 tests passing
- [ ] NLP models loaded correctly
- [ ] Processing pipeline functional
- [ ] Output schema validation passes

#### Orchestrator
- [ ] Database migrations complete
- [ ] Session management operational
- [ ] Service routing functional
- [ ] Feature flags responding

#### Strategist
- [ ] ML models loaded and warmed
- [ ] Career path generation working
- [ ] Performance benchmarks met
- [ ] GPU utilization optimal (if applicable)

#### Analyst
- [ ] 6-step pipeline operational
- [ ] NLP models functional
- [ ] ATS optimization working
- [ ] Analysis quality maintained

---

*This runbook ensures reliable, repeatable deployments for all Helios Career Operations System services with comprehensive validation and rollback procedures.*

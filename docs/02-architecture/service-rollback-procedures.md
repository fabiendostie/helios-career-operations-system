# Service Rollback Procedures
# Helios Career Operations System

## Document Metadata
- **Version:** 1.0
- **Date:** 2025-09-08
- **Author:** Operations Team
- **Status:** Production Ready

---

## 1. Emergency Rollback Overview

This document defines immediate rollback procedures for each Helios service to ensure rapid recovery from deployment issues or service failures.

### 1.1 Rollback Philosophy
- **Speed First**: Restore service within 5 minutes
- **Data Safety**: No data loss during rollback
- **Graceful Degradation**: Maintain partial functionality
- **Clear Communication**: Notify users of service status

### 1.2 Rollback Triggers
- Service fails to start after deployment
- Import errors or dependency failures
- Performance degradation >50% from baseline
- Test suite pass rate <80%
- Critical security vulnerability discovered

---

## 2. Service-Specific Rollback Procedures

### 2.1 Profile Ingestor Service (PRODUCTION READY)

**Status**: ✅ Stable - 208/208 tests passing (100%)

#### Immediate Rollback
```bash
# Profile Ingestor runs independently - minimal rollback needed
cd services/profile-ingestor

# Revert to previous version
git checkout HEAD~1

# Verify functionality
python -m pytest --tb=no -q
python -c "import src.resume_extractor.main; print('✅ Import successful')"

# Restart service
python -m src.resume_extractor.main
```

#### Partial Rollback (Feature-Specific)
```bash
# Disable specific features via environment variables
export HELIOS_SPACY_ENABLED=false           # Disable NLP processing
export HELIOS_BILINGUAL_SUPPORT=false       # Disable French support
export HELIOS_ADVANCED_PARSING=false        # Disable complex parsing
export HELIOS_INTERACTIVE_MODE=false        # Disable UI interactions

# Restart with reduced functionality
python -m src.resume_extractor.main --safe-mode
```

#### Data Recovery
```bash
# Profile Ingestor data recovery
cp services/profile-ingestor/output/.backup_*.json services/profile-ingestor/output/
python scripts/recovery/restore_profile_data.py --from-backup
```

---

### 2.2 Orchestrator Service (OPERATIONAL)

**Status**: ✅ Operational - All imports successful

#### Emergency Rollback
```bash
# Stop orchestrator immediately
docker-compose stop orchestrator

# Revert to JSON-only mode (bypass orchestrator)
export HELIOS_ORCHESTRATOR_ENABLED=false
export HELIOS_USE_LEGACY_MODE=true

# Direct routing to Profile Ingestor
cd services/profile-ingestor
python -m src.resume_extractor.main --standalone

echo "✅ Rolled back to standalone Profile Ingestor mode"
```

#### Service-Level Rollback
```bash
# Rollback orchestrator to previous version
cd services/orchestrator
git checkout HEAD~1

# Install previous dependencies
pip install -r requirements.txt

# Verify rollback
python -c "from src.main import app; print('✅ Orchestrator rollback successful')"

# Restart with feature flags
export HELIOS_ORCHESTRATOR_SAFE_MODE=true
docker-compose up -d orchestrator
```

#### Session Recovery
```bash
# Recover session state from Redis
python scripts/recovery/recover_sessions.py --from-redis
python scripts/recovery/migrate_sessions_to_json.py  # Fallback to file-based
```

---

### 2.3 Strategist Service (OPERATIONAL)

**Status**: ✅ Operational - ML models loaded

#### Emergency Rollback
```bash
# Disable strategist service
docker-compose stop strategist
export HELIOS_STRATEGIST_ENABLED=false

# Fallback to rule-based career paths
export HELIOS_USE_RULE_BASED_PATHS=true
python services/strategist/fallback/rule_based_strategist.py

echo "✅ Strategist disabled, using rule-based fallback"
```

#### ML Model Rollback
```bash
# Rollback to previous ML model version
cd services/strategist

# Clear current models
rm -rf ~/.cache/torch/sentence_transformers/
rm -rf models/

# Reinstall previous model version
pip install sentence-transformers==2.7.0  # Previous stable version
python -c "import sentence_transformers; sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')"

# Restart service
docker-compose up -d strategist
```

#### Data Fallback
```bash
# Use cached career paths instead of generating new ones
export HELIOS_STRATEGIST_USE_CACHE=true
export HELIOS_STRATEGIST_CACHE_ONLY=true

# Copy previous successful career paths
cp data/career_paths_backup/*.json data/career_paths/
```

---

### 2.4 Analyst Service (OPERATIONAL)

**Status**: ✅ Operational - NLP models loaded, 6-step pipeline functional

#### Emergency Rollback
```bash
# Disable analyst service
docker-compose stop analyst
export HELIOS_ANALYST_ENABLED=false

# Fallback to basic analysis
export HELIOS_USE_BASIC_ANALYSIS=true
python services/analyst/fallback/basic_analyzer.py

echo "✅ Analyst disabled, using basic analysis fallback"
```

#### NLP Model Rollback
```bash
# Rollback NLP models
cd services/analyst

# Clear current models
python -m spacy uninstall en_core_web_sm
rm -rf ~/.cache/torch/sentence_transformers/

# Reinstall stable versions
python -m spacy download en_core_web_sm==3.7.1
pip install sentence-transformers==2.7.0

# Verify models
python -c "import spacy; spacy.load('en_core_web_sm'); print('✅ spaCy model loaded')"
python -c "import sentence_transformers; sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2'); print('✅ Sentence transformers loaded')"
```

#### Pipeline Rollback
```bash
# Disable complex pipeline steps
export HELIOS_ANALYST_SKIP_NER=true              # Skip Named Entity Recognition
export HELIOS_ANALYST_SKIP_EMBEDDINGS=true       # Skip embedding generation
export HELIOS_ANALYST_SKIP_MARKET_SIM=true       # Skip market simulation
export HELIOS_ANALYST_USE_SIMPLE_ATS=true        # Use simple ATS scoring

# Use basic 3-step pipeline instead of 6-step
export HELIOS_ANALYST_PIPELINE_MODE=basic
docker-compose up -d analyst
```

---

### 2.5 Architect Service (PENDING)

**Status**: ⏳ Pending Implementation

#### Planned Rollback Procedures
```bash
# When implemented, rollback procedures will include:
# - Fallback to template-based document generation
# - Disable AI-powered content creation
# - Use cached document templates
# - Rollback to manual document assembly
```

---

### 2.6 Editor Service (PENDING)

**Status**: ⏳ Pending Implementation

#### Planned Rollback Procedures
```bash
# When implemented, rollback procedures will include:
# - Disable AI-powered text optimization
# - Use pattern-based text improvements
# - Fallback to manual editing mode
# - Apply preset transformations only
```

---

## 3. System-Wide Rollback Procedures

### 3.1 Complete System Rollback
```bash
#!/bin/bash
# complete_system_rollback.sh

echo "🚨 EMERGENCY: Complete Helios System Rollback"

# Stop all services
docker-compose down

# Disable all feature flags
export HELIOS_ORCHESTRATOR_ENABLED=false
export HELIOS_STRATEGIST_ENABLED=false
export HELIOS_ANALYST_ENABLED=false
export HELIOS_ARCHITECT_ENABLED=false
export HELIOS_EDITOR_ENABLED=false

# Revert to Profile Ingestor only
cd services/profile-ingestor
python -m src.resume_extractor.main --safe-mode

echo "✅ System rolled back to Profile Ingestor safe mode"
echo "⚠️  All advanced features disabled"
echo "📞 Contact support team for recovery assistance"
```

### 3.2 Gradual Service Restoration
```bash
#!/bin/bash
# gradual_restoration.sh

echo "🔄 Gradual Service Restoration"

# Step 1: Restore Orchestrator
export HELIOS_ORCHESTRATOR_ENABLED=true
docker-compose up -d orchestrator
sleep 30
curl -f http://localhost:8000/health || exit 1

# Step 2: Restore Strategist
export HELIOS_STRATEGIST_ENABLED=true
docker-compose up -d strategist
sleep 30
curl -f http://localhost:8001/health || exit 1

# Step 3: Restore Analyst
export HELIOS_ANALYST_ENABLED=true
docker-compose up -d analyst
sleep 30
curl -f http://localhost:8002/health || exit 1

echo "✅ Core services restored successfully"
```

---

## 4. Monitoring During Rollback

### 4.1 Health Checks
```bash
# Service health verification script
check_service_health() {
    local service_name=$1
    local health_url=$2

    echo "Checking $service_name health..."
    if curl -f -s $health_url > /dev/null 2>&1; then
        echo "✅ $service_name: HEALTHY"
        return 0
    else
        echo "❌ $service_name: UNHEALTHY"
        return 1
    fi
}

# Check all services
check_service_health "Profile Ingestor" "http://localhost:8080/health"
check_service_health "Orchestrator" "http://localhost:8000/health"
check_service_health "Strategist" "http://localhost:8001/health"
check_service_health "Analyst" "http://localhost:8002/health"
```

### 4.2 Rollback Verification
```bash
# Verify rollback success
verify_rollback() {
    echo "🔍 Verifying rollback success..."

    # Check service versions
    python -c "import services.orchestrator.src.main as orch; print(f'Orchestrator: {orch.__version__}')"
    python -c "import services.strategist.src.main as strat; print(f'Strategist: {strat.__version__}')"

    # Check functionality
    cd services/profile-ingestor
    python -m pytest --tb=no -q | grep "passed"

    # Check data integrity
    python scripts/verification/check_data_integrity.py

    echo "✅ Rollback verification complete"
}
```

---

## 5. Communication Templates

### 5.1 User Notification
```yaml
emergency_rollback:
  subject: "🚨 Helios Service Emergency Rollback"
  message: |
    We've detected issues with the Helios system and have initiated an emergency rollback.

    Current Status:
    - Profile Ingestor: ✅ Available (safe mode)
    - Advanced Features: ⏸️ Temporarily disabled

    Expected Resolution: Within 30 minutes
    We'll notify you when all services are restored.

planned_rollback:
  subject: "🔄 Helios Service Rollback - Planned Maintenance"
  message: |
    We're rolling back recent changes to ensure optimal performance.

    Services Affected:
    - Career Path Generation (Strategist)
    - Market Analysis (Analyst)

    Core functionality remains available.
    Estimated completion: 15 minutes
```

### 5.2 Internal Team Alerts
```yaml
rollback_alert:
  channels: ["#helios-alerts", "#engineering"]
  message: |
    🚨 HELIOS ROLLBACK INITIATED

    Trigger: {rollback_trigger}
    Services Affected: {affected_services}
    Rollback Initiated By: {operator}

    Actions Taken:
    - Services stopped
    - Fallback mode enabled
    - Data integrity verified

    Next Steps:
    - Monitor service health
    - Investigate root cause
    - Plan restoration
```

---

## 6. Post-Rollback Procedures

### 6.1 Root Cause Analysis
```bash
# Collect rollback diagnostics
collect_rollback_diagnostics() {
    echo "📊 Collecting rollback diagnostics..."

    # Service logs
    docker-compose logs orchestrator > logs/rollback_orchestrator.log
    docker-compose logs strategist > logs/rollback_strategist.log
    docker-compose logs analyst > logs/rollback_analyst.log

    # System metrics
    python scripts/diagnostics/collect_metrics.py --rollback-mode

    # Error analysis
    python scripts/diagnostics/analyze_errors.py --since-rollback

    echo "✅ Diagnostics collected in logs/"
}
```

### 6.2 Service Restoration Planning
```bash
# Plan service restoration
plan_restoration() {
    echo "📋 Planning service restoration..."

    # Analyze failure cause
    python scripts/analysis/analyze_failure.py

    # Generate restoration plan
    python scripts/planning/generate_restoration_plan.py

    # Test restoration in staging
    ./scripts/testing/test_restoration_plan.sh

    echo "✅ Restoration plan generated"
}
```

---

## 7. Rollback Testing

### 7.1 Regular Rollback Drills
```bash
#!/bin/bash
# rollback_drill.sh - Run monthly rollback drill

echo "🎯 Starting rollback drill..."

# Simulate service failure
docker-compose stop strategist

# Execute rollback procedures
source scripts/rollback/strategist_rollback.sh

# Verify functionality
python scripts/testing/verify_rollback_success.py

# Restore services
docker-compose up -d strategist

echo "✅ Rollback drill completed successfully"
```

### 7.2 Rollback Time Measurement
```bash
# Measure rollback performance
measure_rollback_time() {
    local start_time=$(date +%s)

    # Execute rollback
    ./scripts/rollback/emergency_rollback.sh

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo "⏱️  Rollback completed in $duration seconds"

    # Record metrics
    echo "$duration" >> metrics/rollback_times.log
}
```

---

## 8. Rollback Success Criteria

### 8.1 Service-Level Success
- [ ] Service starts successfully
- [ ] All imports functional
- [ ] Health checks pass
- [ ] Core functionality available
- [ ] Performance within 90% of baseline

### 8.2 System-Level Success
- [ ] No data loss
- [ ] User sessions preserved
- [ ] Critical workflows operational
- [ ] Error rate <1%
- [ ] Response times <2x baseline

### 8.3 Business-Level Success
- [ ] Users can complete core tasks
- [ ] No service degradation >30 minutes
- [ ] Customer impact minimized
- [ ] SLA requirements met

---

*This document ensures rapid, safe rollback procedures for all Helios services with zero data loss and minimal downtime.*

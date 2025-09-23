# Rollback Procedures
# Helios Career Operations System

## Document Metadata
- **Version:** 1.0
- **Date:** 2025-01-06
- **Author:** Operations Team
- **Status:** Active
- **Category:** Brownfield Risk Management

---

## 1. Overview

This document defines comprehensive rollback procedures for each service in the Helios Career Operations System. These procedures ensure system stability during brownfield integration with the existing `resume_extractor` module.

## 2. Rollback Strategy Framework

### 2.1 General Principles
- **Zero Data Loss**: All rollbacks must preserve user data
- **Minimal Downtime**: Target <5 minute rollback execution
- **Automated Recovery**: Scripted rollback procedures
- **Version Control**: Git-based code rollback
- **Database Snapshots**: Point-in-time recovery capability
- **Service Independence**: Individual service rollback without full system impact

### 2.2 Rollback Triggers
| Severity | Trigger Condition | Response Time | Authority |
|----------|------------------|---------------|-----------|
| Critical | >50% error rate | Immediate | Auto-rollback |
| High | >25% error rate | 5 minutes | DevOps approval |
| Medium | Performance degradation >2x | 15 minutes | Team lead approval |
| Low | Non-critical feature issues | Next maintenance | Product owner |

---

## 3. Service-Specific Rollback Procedures

### 3.1 Story 1.1: Profile Ingestor Service

#### Pre-Rollback Checklist
- [ ] Backup current Master Career Database JSON files
- [ ] Save in-progress user sessions
- [ ] Export skill mapping configurations
- [ ] Document current service version

#### Rollback Script
```bash
#!/bin/bash
# Profile Ingestor Rollback Script

SERVICE="profile-ingestor"
BACKUP_DIR="/backup/profile-ingestor/$(date +%Y%m%d_%H%M%S)"

# Step 1: Create backup
mkdir -p $BACKUP_DIR
cp -r services/profile-ingestor/output/* $BACKUP_DIR/
cp services/profile-ingestor/data/skill_map.json $BACKUP_DIR/

# Step 2: Stop current service
docker-compose -f services/profile-ingestor/docker-compose.yml down

# Step 3: Revert to previous version
git checkout HEAD~1 -- services/profile-ingestor/

# Step 4: Restore previous dependencies
cd services/profile-ingestor/
pip install -r requirements.txt.backup

# Step 5: Restart service with previous version
docker-compose up -d

# Step 6: Validate rollback
python tests/test_pipeline.py --smoke-test
```

#### Post-Rollback Validation
- [ ] Verify resume parsing functionality
- [ ] Test bilingual processing (EN/FR)
- [ ] Confirm skill mapping accuracy
- [ ] Check output JSON schema compliance

#### Data Recovery
```sql
-- Restore user profiles from backup
COPY user_profiles FROM '/backup/profile-ingestor/latest/master_career_database.json'
WITH (FORMAT json);
```

---

### 3.2 Story 2.1: HELIOS Orchestrator

#### Pre-Rollback Checklist
- [ ] Export active session states from Redis
- [ ] Backup SQLite sessions.db
- [ ] Save command history logs
- [ ] Document API version

#### Rollback Script
```bash
#!/bin/bash
# Orchestrator Rollback Script

SERVICE="orchestrator"
REDIS_BACKUP="/backup/redis/$(date +%Y%m%d_%H%M%S).rdb"

# Step 1: Backup session data
redis-cli --rdb $REDIS_BACKUP
sqlite3 services/orchestrator/sessions.db ".backup /backup/orchestrator/sessions.db"

# Step 2: Preserve active sessions
python scripts/export_active_sessions.py > /backup/active_sessions.json

# Step 3: Stop orchestrator
docker-compose -f services/orchestrator/docker-compose.yml down

# Step 4: Rollback code
git checkout $(git log --format="%H" -n 2 | tail -1) -- services/orchestrator/

# Step 5: Restore previous configuration
cp /backup/orchestrator/config.yaml.prev services/orchestrator/src/core/config.yaml

# Step 6: Restart with feature flags disabled
export FEATURE_FLAGS="legacy_mode=true,new_commands=false"
docker-compose up -d

# Step 7: Restore session continuity
python scripts/restore_sessions.py /backup/active_sessions.json
```

#### Session Continuity Plan
```python
# Session restoration script
import json
import redis
from sqlalchemy import create_engine

def restore_sessions(backup_file):
    """Restore user sessions after rollback"""
    with open(backup_file) as f:
        sessions = json.load(f)

    r = redis.Redis(host='localhost', port=6379)
    for session in sessions:
        r.hset(f"session:{session['id']}", mapping=session)

    # Update database
    engine = create_engine('sqlite:///sessions.db')
    # ... restoration logic
```

---

### 3.3 Story 2.2: Strategist Service

#### Pre-Rollback Checklist
- [ ] Backup role taxonomy database
- [ ] Export ML model versions
- [ ] Save career path generation history
- [ ] Document skill vector cache

#### Rollback Script
```bash
#!/bin/bash
# Strategist Rollback Script

SERVICE="strategist"
MODEL_BACKUP="/backup/models/strategist/$(date +%Y%m%d_%H%M%S)"

# Step 1: Backup ML models and data
mkdir -p $MODEL_BACKUP
cp -r services/strategist/src/data/* $MODEL_BACKUP/
redis-cli --raw dump "skill_vectors:*" > $MODEL_BACKUP/vectors.dump

# Step 2: Tag current version
git tag -a "rollback-point-$(date +%Y%m%d)" -m "Pre-rollback checkpoint"

# Step 3: Stop service gracefully
curl -X POST http://localhost:8002/shutdown?graceful=true
sleep 5

# Step 4: Rollback to stable version
STABLE_VERSION=$(cat /deployments/strategist/stable_version.txt)
git checkout $STABLE_VERSION -- services/strategist/

# Step 5: Restore compatible models
cp $MODEL_BACKUP/../stable/* services/strategist/models/

# Step 6: Clear incompatible cache
redis-cli FLUSHDB

# Step 7: Restart service
docker-compose up -d strategist

# Step 8: Warm up cache
python scripts/warmup_strategist.py
```

#### Model Compatibility Matrix
| Service Version | Model Version | Compatibility |
|----------------|---------------|---------------|
| v2.2.0 | sentence-bert-v2 | ✅ Full |
| v2.1.0 | sentence-bert-v1 | ⚠️ Partial |
| v1.0.0 | word2vec | ❌ Incompatible |

---

### 3.4 Story 2.3: Analyst Service

#### Pre-Rollback Checklist
- [ ] Export market analysis cache
- [ ] Backup ATS scoring algorithms
- [ ] Save compensation database state
- [ ] Document NER model versions

#### Rollback Script
```bash
#!/bin/bash
# Analyst Rollback Script

SERVICE="analyst"
NLP_BACKUP="/backup/nlp/analyst/$(date +%Y%m%d_%H%M%S)"

# Step 1: Preserve analysis results
mkdir -p $NLP_BACKUP
mongodump --db analyst --collection analysis_results --out $NLP_BACKUP

# Step 2: Stop service with queue drain
curl -X POST http://localhost:8003/drain_queue
timeout 30 docker-compose stop analyst

# Step 3: Version rollback
git checkout HEAD~1 -- services/analyst/
git checkout HEAD~1 -- services/analyst/src/data/

# Step 4: Downgrade spaCy models if needed
python -m spacy download en_core_web_sm==3.4.0
python -m spacy download fr_core_news_sm==3.4.0

# Step 5: Restart with compatibility mode
export ANALYST_MODE="compatibility"
docker-compose up -d analyst

# Step 6: Replay failed analyses
python scripts/replay_analyses.py --from=$NLP_BACKUP
```

---

## 4. Database Migration Rollback

### 4.1 PostgreSQL Rollback Strategy

```sql
-- Pre-migration backup
pg_dump helios_prod > /backup/db/helios_prod_$(date +%Y%m%d).sql

-- Create restore point
SELECT pg_create_restore_point('pre_migration_2_3');

-- Rollback to restore point if needed
SELECT pg_switch_wal();
RESTORE DATABASE helios_prod TO RESTORE POINT 'pre_migration_2_3';
```

### 4.2 Migration Version Control
```python
# Alembic migration rollback
alembic downgrade -1  # Rollback one version
alembic downgrade base  # Full rollback
alembic history  # View migration history
```

---

## 5. Feature Flag Implementation

### 5.1 Feature Flag Configuration
```yaml
# feature_flags.yaml
flags:
  profile_ingestor:
    new_nlp_pipeline: false
    enhanced_validation: false

  orchestrator:
    new_command_parser: false
    async_processing: true

  strategist:
    ml_v2_models: false
    expanded_taxonomy: false

  analyst:
    advanced_ner: false
    market_api_v2: false
```

### 5.2 Runtime Flag Control
```python
# Feature flag manager
class FeatureFlagManager:
    def __init__(self):
        self.flags = self.load_flags()

    def is_enabled(self, feature: str) -> bool:
        return self.flags.get(feature, False)

    def toggle(self, feature: str, enabled: bool):
        self.flags[feature] = enabled
        self.persist_flags()

    def rollback_all(self):
        """Disable all experimental features"""
        for feature in self.flags:
            self.flags[feature] = False
        self.persist_flags()
```

---

## 6. Monitoring During Rollback

### 6.1 Key Metrics to Monitor
```yaml
monitoring:
  error_rates:
    threshold: 10%
    window: 5m

  response_times:
    p50: 200ms
    p95: 1000ms
    p99: 5000ms

  service_health:
    cpu_usage: <80%
    memory_usage: <90%
    disk_io: <1000 iops
```

### 6.2 Rollback Dashboard
```python
# Grafana dashboard configuration
dashboards:
  - name: "Rollback Monitor"
    panels:
      - title: "Service Status"
        query: "up{service=~'helios-.*'}"
      - title: "Error Rates"
        query: "rate(errors_total[5m])"
      - title: "Rollback Events"
        query: "rollback_triggered_total"
```

---

## 7. Communication Plan

### 7.1 Internal Communication
| Event | Channel | Recipients | Template |
|-------|---------|------------|----------|
| Rollback Initiated | Slack #incidents | DevOps, Dev Team | ROLLBACK_STARTED |
| Rollback Complete | Email + Slack | All Stakeholders | ROLLBACK_SUCCESS |
| Rollback Failed | PagerDuty | On-call Engineer | ROLLBACK_FAILED |

### 7.2 User Communication
```javascript
// User notification service
const notifyUsers = async (rollbackType) => {
  const message = {
    'partial': 'Some features temporarily unavailable',
    'full': 'System maintenance in progress',
    'complete': 'Service restored successfully'
  };

  await broadcastToActiveSessions(message[rollbackType]);
};
```

---

## 8. Testing Rollback Procedures

### 8.1 Rollback Drill Schedule
- **Weekly**: Component-level rollback tests
- **Monthly**: Full service rollback simulation
- **Quarterly**: Disaster recovery exercise

### 8.2 Rollback Test Script
```bash
#!/bin/bash
# Automated rollback testing

# Test each service rollback
for service in profile-ingestor orchestrator strategist analyst; do
  echo "Testing rollback for $service"

  # Deploy canary version
  ./deploy_canary.sh $service

  # Inject failure
  ./inject_failure.sh $service

  # Trigger rollback
  ./rollback.sh $service

  # Validate recovery
  ./validate_service.sh $service
done
```

---

## 9. Post-Rollback Analysis

### 9.1 Root Cause Analysis Template
```markdown
## Incident Report
- **Date**: [YYYY-MM-DD]
- **Service**: [Service Name]
- **Duration**: [Time]
- **Impact**: [User Impact]

### Timeline
- T+0: Issue detected
- T+X: Rollback initiated
- T+Y: Service restored

### Root Cause
[Detailed analysis]

### Lessons Learned
[Improvements identified]

### Action Items
- [ ] Fix identified issue
- [ ] Update rollback procedures
- [ ] Improve monitoring
```

---

## 10. Approval Matrix

| Rollback Type | Approval Required | Time Limit |
|---------------|------------------|------------|
| Automated (Critical) | None - Auto-execute | Immediate |
| Service-level | DevOps Lead | 5 minutes |
| Multi-service | Engineering Manager | 10 minutes |
| Full System | CTO | 15 minutes |

---

## Document Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| DevOps Lead | | | |
| Engineering Manager | | | |
| Security Officer | | | |
| CTO | | | |

---

*End of Rollback Procedures v1.0*

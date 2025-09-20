# Database Migration Procedures
# Helios Career Operations System

## Document Metadata
- **Version:** 1.0
- **Date:** 2025-09-08
- **Author:** Architecture Team
- **Status:** Production Ready

---

## 1. Brownfield Integration Overview

The Helios system operates as a **brownfield enhancement** to the existing `resume_extractor` module. This document defines safe database migration procedures that preserve existing functionality while adding new capabilities.

### 1.1 Migration Philosophy
- **Zero-Downtime**: All migrations must support concurrent operation
- **Backward Compatibility**: Existing functionality preserved throughout
- **Rollback Ready**: Every migration has a verified rollback path
- **Data Integrity**: No data loss during transitions

---

## 2. Database Architecture Changes

### 2.1 Current State (Profile Ingestor)
```
├── Master Career Database (JSON Files)
│   ├── master_career_database.json
│   └── timestamped backups
├── spaCy Model Cache
│   └── en_core_web_sm, fr_core_news_sm
```

### 2.2 Target State (Full System)
```
PostgreSQL Primary:
├── users (session management)
├── career_profiles (normalized from JSON)
├── session_states (orchestrator)
├── career_paths (strategist outputs)
├── analysis_reports (analyst outputs)
├── generated_documents (architect outputs)

Redis Cache:
├── active_sessions
├── ml_model_cache
├── api_response_cache

Vector Database (Pinecone/Weaviate):
├── skill_embeddings
├── job_description_vectors
├── career_similarity_index
```

---

## 3. Migration Procedures

### 3.1 Phase 1: Database Infrastructure Setup
```bash
# 1. Create PostgreSQL schemas (non-destructive)
python scripts/migration/01_create_schemas.py

# 2. Setup Redis instance (separate from existing)
docker run -d --name helios-redis -p 6380:6379 redis:alpine

# 3. Initialize Vector DB (new service)
python scripts/migration/02_setup_vector_db.py
```

**Rollback**: Drop new schemas, stop new containers
**Verification**: `python scripts/migration/verify_infrastructure.py`

### 3.2 Phase 2: Data Migration (Existing → New)
```bash
# 1. Migrate existing JSON data to PostgreSQL (READ-ONLY)
python scripts/migration/03_migrate_career_data.py --dry-run
python scripts/migration/03_migrate_career_data.py --execute

# 2. Generate embeddings for existing profiles
python scripts/migration/04_generate_embeddings.py

# 3. Verify data integrity
python scripts/migration/05_verify_migration.py
```

**Safety Measures**:
- Original JSON files remain untouched
- Migration runs in transaction with automatic rollback on error
- Checksum validation after each step

**Rollback**: 
```bash
python scripts/migration/rollback_phase2.py
```

### 3.3 Phase 3: Service Integration
```bash
# 1. Deploy new services with feature flags (OFF)
docker-compose up -d orchestrator strategist analyst

# 2. Enable orchestrator with existing profile ingestor
export HELIOS_ORCHESTRATOR_ENABLED=true
export HELIOS_USE_NEW_DATABASE=false  # Still use JSON

# 3. Gradual cutover
export HELIOS_USE_NEW_DATABASE=true   # Switch to PostgreSQL
```

**Feature Flags**:
- `HELIOS_ORCHESTRATOR_ENABLED`: Route through new orchestrator
- `HELIOS_USE_NEW_DATABASE`: Use PostgreSQL vs JSON files
- `HELIOS_ML_SERVICES_ENABLED`: Enable Strategist/Analyst

**Rollback**:
```bash
# Immediate rollback to JSON-only mode
export HELIOS_USE_NEW_DATABASE=false
export HELIOS_ORCHESTRATOR_ENABLED=false
```

---

## 4. Rollback Procedures

### 4.1 Emergency Rollback (< 5 minutes)
```bash
# 1. Disable new services immediately
export HELIOS_ORCHESTRATOR_ENABLED=false
export HELIOS_USE_NEW_DATABASE=false

# 2. Restart profile ingestor in standalone mode
cd services/profile-ingestor
python -m src.resume_extractor.main

# 3. Verify existing functionality
pytest tests/ --tb=short
```

### 4.2 Planned Rollback (Complete System)
```bash
# 1. Backup current state
python scripts/migration/backup_current_state.py

# 2. Graceful service shutdown
docker-compose down orchestrator strategist analyst

# 3. Restore original JSON-only operation
python scripts/migration/restore_original_state.py

# 4. Verify complete rollback
python scripts/migration/verify_rollback.py
```

### 4.3 Partial Rollback (Service-Specific)
```bash
# Rollback specific service while keeping others
docker-compose stop strategist
export HELIOS_STRATEGIST_ENABLED=false

# Or rollback to previous version
docker-compose up -d strategist:previous
```

---

## 5. Data Integrity Safeguards

### 5.1 Pre-Migration Validation
```python
# Check existing data completeness
def validate_existing_data():
    json_files = glob.glob("services/profile-ingestor/output/*.json")
    for file in json_files:
        validate_json_schema(file)
        verify_data_completeness(file)
```

### 5.2 Migration Checksums
```python
# Ensure no data loss during migration
def generate_migration_checksums():
    original_checksum = hash_json_files()
    migrated_checksum = hash_postgresql_data()
    assert original_checksum == migrated_checksum
```

### 5.3 Continuous Validation
```python
# Real-time data integrity monitoring
def continuous_validation():
    compare_json_vs_postgresql()
    validate_embedding_consistency()
    check_session_state_integrity()
```

---

## 6. Testing Strategy

### 6.1 Migration Testing
```bash
# 1. Test on copy of production data
python scripts/migration/test_migration.py --dataset=production_copy

# 2. Verify all services work with migrated data
pytest services/orchestrator/tests/
pytest services/strategist/tests/
pytest services/analyst/tests/

# 3. End-to-end testing
python scripts/e2e/test_full_system.py
```

### 6.2 Rollback Testing
```bash
# Test every rollback procedure
python scripts/migration/test_rollback_emergency.py
python scripts/migration/test_rollback_planned.py
python scripts/migration/test_rollback_partial.py
```

### 6.3 Load Testing
```bash
# Ensure migration doesn't impact performance
python scripts/load_testing/test_migration_performance.py
```

---

## 7. Monitoring During Migration

### 7.1 Key Metrics
- **Data Consistency**: JSON ↔ PostgreSQL comparison
- **Service Health**: All services responding
- **Performance Impact**: Response times during migration
- **Error Rates**: Failed operations during transition

### 7.2 Alerting Thresholds
```yaml
alerts:
  data_inconsistency: 
    threshold: 0%  # Zero tolerance for data loss
  service_downtime:
    threshold: 30s  # Maximum acceptable downtime
  migration_failure_rate:
    threshold: 1%   # Maximum failed operations
```

### 7.3 Dashboard Metrics
```yaml
metrics:
  - migration_progress_percentage
  - data_validation_status
  - service_health_status  
  - rollback_readiness_status
  - performance_impact_percentage
```

---

## 8. Communication Plan

### 8.1 Pre-Migration
- [ ] Notify users of enhancement window
- [ ] Prepare rollback communication
- [ ] Set up monitoring alerts

### 8.2 During Migration  
- [ ] Real-time status updates
- [ ] Progress notifications
- [ ] Issue escalation procedures

### 8.3 Post-Migration
- [ ] Success confirmation
- [ ] Performance impact summary
- [ ] Next steps communication

---

## 9. Migration Scripts

### 9.1 Core Migration Scripts
```
scripts/migration/
├── 01_create_schemas.py        # Database schema creation
├── 02_setup_vector_db.py       # Vector database initialization
├── 03_migrate_career_data.py   # JSON → PostgreSQL migration
├── 04_generate_embeddings.py   # ML embeddings generation
├── 05_verify_migration.py      # Data integrity validation
├── rollback_phase2.py          # Emergency rollback
├── backup_current_state.py     # State backup
└── verify_rollback.py          # Rollback validation
```

### 9.2 Testing Scripts
```
scripts/e2e/
├── test_full_system.py         # End-to-end testing
├── test_migration_performance.py # Performance validation
└── test_rollback_procedures.py # Rollback testing
```

---

## 10. Success Criteria

### 10.1 Migration Success
- [ ] All existing functionality preserved
- [ ] New services operational
- [ ] Zero data loss
- [ ] Performance within 10% of baseline
- [ ] All tests passing

### 10.2 Rollback Success
- [ ] System restored to pre-migration state
- [ ] All original functionality working
- [ ] Zero additional data loss
- [ ] Rollback completed within SLA

---

## 11. Post-Migration Cleanup

### 11.1 Deprecation Timeline
- **Week 1**: Dual operation (JSON + PostgreSQL)
- **Week 2**: PostgreSQL primary, JSON backup
- **Week 4**: JSON files archived
- **Week 8**: JSON files removed (after verification)

### 11.2 Cleanup Tasks
```bash
# After successful migration and validation period
python scripts/cleanup/archive_json_files.py
python scripts/cleanup/remove_deprecated_code.py
python scripts/cleanup/update_documentation.py
```

---

*This document ensures safe, reversible database migration procedures for the Helios brownfield enhancement.*
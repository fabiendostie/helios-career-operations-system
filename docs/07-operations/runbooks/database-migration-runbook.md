# Database Migration Runbook
# Helios Career Operations System

## Document Metadata
- **Version:** 1.0
- **Date:** 2025-09-20
- **Author:** Operations Team
- **Status:** Production Ready
- **Review Frequency:** Monthly

---

## 1. Overview

This runbook provides step-by-step procedures for database migrations in the Helios Career Operations System, including validation checks, rollback procedures, and disaster recovery.

### 1.1 Prerequisites
- [ ] PostgreSQL 15+ installed and configured
- [ ] Redis 7+ installed and configured
- [ ] Vector database (Pinecone/Weaviate) credentials
- [ ] Backup storage access (AWS S3/Azure Blob)
- [ ] Database admin credentials
- [ ] Migration scripts validated in staging

### 1.2 Required Permissions
- [ ] Database admin access (CREATE/DROP/ALTER privileges)
- [ ] File system write access to backup locations
- [ ] Docker/Kubernetes deployment permissions
- [ ] Monitoring dashboard access

---

## 2. Pre-Migration Checklist

### 2.1 Environment Validation
```bash
#!/bin/bash
# pre_migration_validation.sh

echo "🔍 Pre-Migration Validation Checklist"

# Check database connectivity
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT version();" || exit 1
echo "✅ PostgreSQL connectivity verified"

# Check Redis connectivity
redis-cli -h $REDIS_HOST -p $REDIS_PORT ping || exit 1
echo "✅ Redis connectivity verified"

# Check disk space (minimum 50GB free)
available_space=$(df -BG /var/lib/postgresql/data | awk 'NR==2 {print $4}' | sed 's/G//')
if [ $available_space -lt 50 ]; then
    echo "❌ Insufficient disk space: ${available_space}GB available, 50GB required"
    exit 1
fi
echo "✅ Disk space sufficient: ${available_space}GB available"

# Check backup storage access
aws s3 ls s3://$BACKUP_BUCKET/ > /dev/null || exit 1
echo "✅ Backup storage accessible"

# Verify migration scripts exist
for script in 01_create_schemas.py 02_migrate_data.py 03_verify_migration.py; do
    if [ ! -f "scripts/migration/$script" ]; then
        echo "❌ Missing migration script: $script"
        exit 1
    fi
done
echo "✅ All migration scripts present"

echo "🎯 Pre-migration validation complete"
```

### 2.2 Data Backup
```bash
#!/bin/bash
# create_pre_migration_backup.sh

BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/helios_migration_$BACKUP_TIMESTAMP"

echo "💾 Creating pre-migration backup..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup PostgreSQL database
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -f "$BACKUP_DIR/postgresql_backup.sql"
echo "✅ PostgreSQL backup created"

# Backup Redis data
redis-cli -h $REDIS_HOST -p $REDIS_PORT --rdb "$BACKUP_DIR/redis_backup.rdb"
echo "✅ Redis backup created"

# Backup JSON files from Profile Ingestor
cp -r services/profile-ingestor/output/ "$BACKUP_DIR/json_backup/"
echo "✅ JSON files backed up"

# Backup configuration files
cp -r bmad-core/ "$BACKUP_DIR/config_backup/"
echo "✅ Configuration files backed up"

# Create backup manifest
cat > "$BACKUP_DIR/backup_manifest.txt" << EOF
Backup Timestamp: $BACKUP_TIMESTAMP
PostgreSQL Backup: postgresql_backup.sql
Redis Backup: redis_backup.rdb
JSON Backup: json_backup/
Config Backup: config_backup/
EOF

# Upload to cloud storage
aws s3 cp $BACKUP_DIR s3://$BACKUP_BUCKET/migrations/ --recursive
echo "✅ Backup uploaded to cloud storage"

echo "🎯 Pre-migration backup complete: $BACKUP_DIR"
```

---

## 3. Migration Procedures

### 3.1 Phase 1: Infrastructure Setup
```bash
#!/bin/bash
# phase1_infrastructure_setup.sh

echo "🏗️  Phase 1: Infrastructure Setup"

# Step 1: Create PostgreSQL schemas
echo "Creating PostgreSQL schemas..."
python scripts/migration/01_create_schemas.py --dry-run
echo "Review schema creation plan above. Continue? (y/n)"
read -r confirmation
if [ "$confirmation" != "y" ]; then
    echo "❌ Migration cancelled"
    exit 1
fi

python scripts/migration/01_create_schemas.py --execute
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL schemas created"
else
    echo "❌ Schema creation failed"
    exit 1
fi

# Step 2: Setup Redis instance
echo "Setting up Redis instance..."
docker run -d --name helios-redis-migration \
    -p 6380:6379 \
    -v helios-redis-data:/data \
    redis:7-alpine

# Wait for Redis to start
sleep 10
redis-cli -h localhost -p 6380 ping || exit 1
echo "✅ Redis instance ready"

# Step 3: Initialize Vector Database
echo "Initializing Vector Database..."
python scripts/migration/02_setup_vector_db.py --environment=production
if [ $? -eq 0 ]; then
    echo "✅ Vector Database initialized"
else
    echo "❌ Vector Database setup failed"
    exit 1
fi

# Step 4: Verify infrastructure
echo "Verifying infrastructure..."
python scripts/migration/verify_infrastructure.py
if [ $? -eq 0 ]; then
    echo "✅ Infrastructure verification passed"
else
    echo "❌ Infrastructure verification failed"
    exit 1
fi

echo "🎯 Phase 1 complete: Infrastructure ready"
```

### 3.2 Phase 2: Data Migration
```bash
#!/bin/bash
# phase2_data_migration.sh

echo "📊 Phase 2: Data Migration"

# Step 1: Pre-migration validation
echo "Running pre-migration validation..."
python scripts/migration/validate_source_data.py
if [ $? -ne 0 ]; then
    echo "❌ Source data validation failed"
    exit 1
fi
echo "✅ Source data validation passed"

# Step 2: Dry run migration
echo "Performing dry run migration..."
python scripts/migration/03_migrate_career_data.py \
    --dry-run \
    --source-path=services/profile-ingestor/output/ \
    --target-db=postgresql://...

if [ $? -ne 0 ]; then
    echo "❌ Dry run migration failed"
    exit 1
fi
echo "✅ Dry run successful"

# Step 3: Execute migration with progress tracking
echo "Executing data migration..."
python scripts/migration/03_migrate_career_data.py \
    --execute \
    --source-path=services/profile-ingestor/output/ \
    --target-db=postgresql://... \
    --progress-file=/tmp/migration_progress.json

if [ $? -ne 0 ]; then
    echo "❌ Data migration failed"
    echo "🔄 Initiating rollback..."
    python scripts/migration/rollback_phase2.py
    exit 1
fi
echo "✅ Data migration completed"

# Step 4: Generate embeddings
echo "Generating embeddings for migrated data..."
python scripts/migration/04_generate_embeddings.py \
    --batch-size=100 \
    --progress-file=/tmp/embedding_progress.json

if [ $? -ne 0 ]; then
    echo "❌ Embedding generation failed"
    exit 1
fi
echo "✅ Embeddings generated"

# Step 5: Verify migration integrity
echo "Verifying migration integrity..."
python scripts/migration/05_verify_migration.py \
    --source-path=services/profile-ingestor/output/ \
    --target-db=postgresql://...

if [ $? -ne 0 ]; then
    echo "❌ Migration verification failed"
    exit 1
fi
echo "✅ Migration verification passed"

echo "🎯 Phase 2 complete: Data migration successful"
```

### 3.3 Phase 3: Service Integration
```bash
#!/bin/bash
# phase3_service_integration.sh

echo "🔗 Phase 3: Service Integration"

# Step 1: Deploy services with feature flags disabled
echo "Deploying services with feature flags disabled..."
export HELIOS_ORCHESTRATOR_ENABLED=false
export HELIOS_USE_NEW_DATABASE=false
export HELIOS_ML_SERVICES_ENABLED=false

docker-compose up -d orchestrator strategist analyst
sleep 30

# Verify services are running
for service in orchestrator strategist analyst; do
    if ! docker-compose ps $service | grep -q "Up"; then
        echo "❌ Service $service failed to start"
        exit 1
    fi
done
echo "✅ All services deployed"

# Step 2: Enable orchestrator with JSON backend
echo "Enabling orchestrator with JSON backend..."
export HELIOS_ORCHESTRATOR_ENABLED=true
export HELIOS_USE_NEW_DATABASE=false

# Wait for orchestrator to initialize
sleep 15

# Test orchestrator with existing data
curl -f http://localhost:8000/health || exit 1
echo "✅ Orchestrator operational with JSON backend"

# Step 3: Gradual cutover to PostgreSQL
echo "Switching to PostgreSQL backend..."
export HELIOS_USE_NEW_DATABASE=true

# Wait for database connection to initialize
sleep 10

# Test with migrated data
curl -f http://localhost:8000/api/profiles/health || exit 1
echo "✅ PostgreSQL backend operational"

# Step 4: Enable ML services
echo "Enabling ML services..."
export HELIOS_ML_SERVICES_ENABLED=true

# Restart services to pick up new configuration
docker-compose restart strategist analyst
sleep 30

# Verify ML services
curl -f http://localhost:8001/health || exit 1  # Strategist
curl -f http://localhost:8002/health || exit 1  # Analyst
echo "✅ ML services operational"

echo "🎯 Phase 3 complete: Service integration successful"
```

---

## 4. Validation and Testing

### 4.1 Data Integrity Verification
```bash
#!/bin/bash
# verify_data_integrity.sh

echo "🔍 Data Integrity Verification"

# Compare record counts
echo "Comparing record counts..."
python scripts/validation/compare_record_counts.py \
    --source=json \
    --target=postgresql

# Validate data checksums
echo "Validating data checksums..."
python scripts/validation/validate_checksums.py \
    --source-path=services/profile-ingestor/output/ \
    --target-db=postgresql://...

# Verify relationships
echo "Verifying data relationships..."
python scripts/validation/verify_relationships.py

# Test data queries
echo "Testing data queries..."
python scripts/validation/test_data_queries.py

echo "✅ Data integrity verification complete"
```

### 4.2 Performance Testing
```bash
#!/bin/bash
# performance_testing.sh

echo "⚡ Performance Testing"

# Baseline performance test
echo "Running baseline performance test..."
python scripts/testing/performance_baseline.py \
    --queries=100 \
    --concurrent-users=10

# Load testing with migrated data
echo "Running load test with migrated data..."
python scripts/testing/load_test_migration.py \
    --duration=300 \
    --users=50 \
    --ramp-up=30

# Memory usage monitoring
echo "Monitoring memory usage..."
python scripts/testing/monitor_memory.py \
    --duration=60 \
    --interval=5

echo "✅ Performance testing complete"
```

---

## 5. Rollback Procedures

### 5.1 Emergency Rollback (< 5 minutes)
```bash
#!/bin/bash
# emergency_rollback.sh

echo "🚨 EMERGENCY ROLLBACK INITIATED"

# Step 1: Immediately disable new database
export HELIOS_USE_NEW_DATABASE=false
export HELIOS_ORCHESTRATOR_ENABLED=false

# Step 2: Stop all new services
docker-compose stop orchestrator strategist analyst

# Step 3: Restart Profile Ingestor in standalone mode
cd services/profile-ingestor
python -m src.resume_extractor.main --standalone &

# Step 4: Verify rollback
sleep 10
curl -f http://localhost:8080/health || echo "❌ Profile Ingestor health check failed"

# Step 5: Test basic functionality
python -c "from src.resume_extractor.main import process_resume; print('✅ Basic functionality operational')" || exit 1

echo "✅ Emergency rollback complete - System restored to JSON-only mode"
echo "⚠️  Investigation required - Check logs in logs/migration_emergency.log"
```

### 5.2 Planned Rollback
```bash
#!/bin/bash
# planned_rollback.sh

echo "🔄 Planned Migration Rollback"

# Step 1: Create rollback backup
ROLLBACK_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "Creating rollback backup..."
python scripts/migration/create_rollback_backup.py --timestamp=$ROLLBACK_TIMESTAMP

# Step 2: Gracefully stop services
echo "Stopping services gracefully..."
export HELIOS_MAINTENANCE_MODE=true
sleep 30  # Allow current requests to complete

docker-compose down orchestrator strategist analyst

# Step 3: Rollback database changes
echo "Rolling back database changes..."
python scripts/migration/rollback_database.py --confirm

# Step 4: Restore Redis state
echo "Restoring Redis state..."
redis-cli -h $REDIS_HOST -p $REDIS_PORT FLUSHALL
redis-cli -h $REDIS_HOST -p $REDIS_PORT --rdb /backup/redis_pre_migration.rdb

# Step 5: Restore original configuration
echo "Restoring original configuration..."
cp /backup/config_pre_migration/* bmad-core/ -r

# Step 6: Restart in original mode
echo "Restarting in original mode..."
cd services/profile-ingestor
python -m src.resume_extractor.main

# Step 7: Verify rollback
echo "Verifying rollback..."
python scripts/migration/verify_rollback.py

echo "✅ Planned rollback complete"
```

---

## 6. Monitoring and Alerting

### 6.1 Migration Monitoring Dashboard
```yaml
# migration_monitoring.yml
monitoring:
  metrics:
    - migration_progress_percentage
    - data_validation_errors
    - service_health_status
    - database_connection_pool
    - memory_usage_trend
    - query_response_times

  alerts:
    migration_failure:
      condition: "migration_progress_percentage == 0 AND time_elapsed > 300"
      severity: critical
      action: "trigger emergency rollback"

    data_validation_error:
      condition: "data_validation_errors > 0"
      severity: high
      action: "pause migration, investigate"

    performance_degradation:
      condition: "query_response_times > 2x baseline"
      severity: medium
      action: "scale resources, monitor"
```

### 6.2 Health Check Procedures
```bash
#!/bin/bash
# health_check_migration.sh

echo "🩺 Migration Health Check"

# Database connectivity
check_database_health() {
    echo "Checking database health..."
    psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM pg_stat_activity;" > /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Database: HEALTHY"
    else
        echo "❌ Database: UNHEALTHY"
        return 1
    fi
}

# Redis connectivity
check_redis_health() {
    echo "Checking Redis health..."
    redis_response=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT ping 2>/dev/null)
    if [ "$redis_response" = "PONG" ]; then
        echo "✅ Redis: HEALTHY"
    else
        echo "❌ Redis: UNHEALTHY"
        return 1
    fi
}

# Service health
check_service_health() {
    local service_name=$1
    local health_url=$2

    echo "Checking $service_name health..."
    response=$(curl -s -o /dev/null -w "%{http_code}" $health_url)
    if [ "$response" = "200" ]; then
        echo "✅ $service_name: HEALTHY"
    else
        echo "❌ $service_name: UNHEALTHY (HTTP $response)"
        return 1
    fi
}

# Run all health checks
check_database_health
check_redis_health
check_service_health "Orchestrator" "http://localhost:8000/health"
check_service_health "Strategist" "http://localhost:8001/health"
check_service_health "Analyst" "http://localhost:8002/health"

echo "🎯 Health check complete"
```

---

## 7. Troubleshooting Guide

### 7.1 Common Issues

#### Issue: Migration Script Fails
**Symptoms:** Migration script exits with error code
**Diagnosis:**
```bash
# Check migration logs
tail -f logs/migration.log

# Verify database connectivity
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;"

# Check disk space
df -h
```

**Resolution:**
```bash
# Fix common issues
# 1. Insufficient permissions
GRANT ALL PRIVILEGES ON DATABASE helios TO migration_user;

# 2. Disk space
# Extend volume or clean up old files

# 3. Network connectivity
# Check firewall rules and DNS resolution

# Retry migration
python scripts/migration/03_migrate_career_data.py --resume-from-checkpoint
```

#### Issue: Service Won't Start After Migration
**Symptoms:** Docker container exits immediately
**Diagnosis:**
```bash
# Check container logs
docker-compose logs orchestrator

# Check configuration
python -c "import yaml; print(yaml.safe_load(open('bmad-core/core-config.yaml')))"

# Verify dependencies
pip check
```

**Resolution:**
```bash
# Common fixes
# 1. Environment variables
export DATABASE_URL="postgresql://..."
export REDIS_URL="redis://..."

# 2. Dependency conflicts
pip install --force-reinstall -r requirements.txt

# 3. Configuration errors
cp bmad-core/core-config.yaml.backup bmad-core/core-config.yaml

# Restart service
docker-compose up -d orchestrator
```

### 7.2 Performance Issues

#### Issue: Slow Query Performance
**Diagnosis:**
```sql
-- Check slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_tup_read DESC;
```

**Resolution:**
```sql
-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_career_profiles_user_id ON career_profiles(user_id);
CREATE INDEX CONCURRENTLY idx_session_states_created_at ON session_states(created_at);

-- Update table statistics
ANALYZE career_profiles;
ANALYZE session_states;
```

---

## 8. Post-Migration Procedures

### 8.1 Cleanup Tasks
```bash
#!/bin/bash
# post_migration_cleanup.sh

echo "🧹 Post-Migration Cleanup"

# Wait for stabilization period (24 hours)
echo "Waiting for stabilization period..."
sleep 3600  # In production, this would be 24 hours

# Verify system stability
python scripts/monitoring/verify_stability.py --duration=24h

# Archive old JSON files
echo "Archiving old JSON files..."
mkdir -p /archive/json_files_$(date +%Y%m%d)
mv services/profile-ingestor/output/*.json /archive/json_files_$(date +%Y%m%d)/

# Remove temporary migration files
echo "Cleaning up temporary files..."
rm -rf /tmp/migration_*
rm -rf /tmp/embedding_*

# Update documentation
echo "Updating documentation..."
python scripts/docs/update_migration_status.py --status=completed

echo "✅ Post-migration cleanup complete"
```

### 8.2 Performance Optimization
```bash
#!/bin/bash
# optimize_post_migration.sh

echo "⚡ Post-Migration Optimization"

# Analyze database statistics
echo "Analyzing database statistics..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "ANALYZE;"

# Optimize query performance
echo "Optimizing query performance..."
python scripts/optimization/optimize_queries.py

# Configure connection pooling
echo "Configuring connection pooling..."
python scripts/optimization/configure_connection_pool.py

# Tune cache settings
echo "Tuning cache settings..."
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET maxmemory 4gb

echo "✅ Performance optimization complete"
```

---

## 9. Success Criteria

### 9.1 Migration Success Criteria
- [ ] All data migrated without loss (100% checksum match)
- [ ] All services operational and responding to health checks
- [ ] Performance within 10% of baseline metrics
- [ ] All tests passing (>95% pass rate)
- [ ] Zero critical errors in logs
- [ ] User functionality unaffected

### 9.2 Rollback Success Criteria
- [ ] System restored to pre-migration state
- [ ] All original functionality operational
- [ ] Zero additional data loss during rollback
- [ ] Rollback completed within 5 minutes (emergency) or 30 minutes (planned)
- [ ] All services responding normally
- [ ] Users can resume normal operations

---

## 10. Contacts and Escalation

### 10.1 Team Contacts
- **Database Administrator:** dba@helios.com
- **DevOps Engineer:** devops@helios.com
- **Product Owner:** po@helios.com
- **On-Call Engineer:** +1-555-ON-CALL

### 10.2 Escalation Matrix
- **Level 1:** Migration team resolves within 30 minutes
- **Level 2:** Senior DBA involvement, escalate within 1 hour
- **Level 3:** CTO notification, immediate response required

---

*This runbook ensures safe, reliable database migrations for the Helios Career Operations System with comprehensive validation and rollback procedures.*

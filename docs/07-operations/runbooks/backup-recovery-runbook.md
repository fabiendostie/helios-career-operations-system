# Backup and Recovery Runbook
# Helios Career Operations System

## Document Metadata
- **Version:** 1.0
- **Date:** 2025-09-20
- **Author:** Operations Team
- **Status:** Production Ready
- **Review Frequency:** Monthly

---

## 1. Overview

This runbook provides comprehensive backup and disaster recovery procedures for the Helios Career Operations System, ensuring data protection and business continuity with minimal downtime during recovery operations.

### 1.1 Backup Strategy
- **3-2-1 Rule:** 3 copies of data, 2 different media types, 1 offsite
- **RPO (Recovery Point Objective):** 1 hour maximum data loss
- **RTO (Recovery Time Objective):** 4 hours maximum downtime
- **Automated Backups:** Daily full, hourly incrementals
- **Retention Policy:** 30 daily, 12 monthly, 7 yearly backups

### 1.2 Data Classification
```yaml
# data_classification.yml
data_types:
  critical:
    - user_profiles
    - career_data
    - session_states
    - configuration_data
    backup_frequency: hourly
    retention: 90_days

  important:
    - application_logs
    - ml_model_outputs
    - analysis_results
    backup_frequency: daily
    retention: 30_days

  non_critical:
    - temporary_files
    - cache_data
    - development_artifacts
    backup_frequency: weekly
    retention: 7_days
```

---

## 2. Backup Infrastructure

### 2.1 Backup Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │────│   Backup Agent  │────│   AWS S3        │
│   (Primary DB)  │    │   (Local)       │    │   (Offsite)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Redis       │────│   File System   │────│   Azure Blob    │
│   (Cache/State) │    │   (Local Copy)  │    │   (DR Site)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   JSON Files    │────│   Restic        │────│   Google Cloud  │
│   (Profile Data)│    │   (Backup Tool) │    │   (Archive)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2.2 Backup Tools and Configuration
```bash
#!/bin/bash
# setup_backup_infrastructure.sh

echo "🔧 Setting up Backup Infrastructure"

# Step 1: Install backup tools
echo "Installing backup tools..."
apt-get update
apt-get install -y postgresql-client-15 redis-tools restic rclone

# Step 2: Configure Restic repositories
echo "Configuring Restic repositories..."

# Local repository
export RESTIC_REPOSITORY="/backup/local"
export RESTIC_PASSWORD_FILE="/etc/restic/password"
restic init

# S3 repository (offsite)
export RESTIC_REPOSITORY="s3:s3.amazonaws.com/helios-backups"
export AWS_ACCESS_KEY_ID="$BACKUP_AWS_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$BACKUP_AWS_SECRET_KEY"
restic init

# Azure repository (DR site)
export RESTIC_REPOSITORY="azure:helios-dr-backups"
export AZURE_ACCOUNT_NAME="$BACKUP_AZURE_ACCOUNT"
export AZURE_ACCOUNT_KEY="$BACKUP_AZURE_KEY"
restic init

# Step 3: Configure rclone for cloud sync
echo "Configuring rclone..."
cat > /etc/rclone/rclone.conf << EOF
[aws_s3]
type = s3
provider = AWS
access_key_id = $BACKUP_AWS_ACCESS_KEY
secret_access_key = $BACKUP_AWS_SECRET_KEY
region = us-east-1

[azure_blob]
type = azureblob
account = $BACKUP_AZURE_ACCOUNT
key = $BACKUP_AZURE_KEY

[gcp_storage]
type = google cloud storage
project_number = $BACKUP_GCP_PROJECT
service_account_file = /etc/gcp/service-account.json
EOF

# Step 4: Setup backup directories
mkdir -p /backup/staging
mkdir -p /backup/archive
mkdir -p /backup/restore
chmod 700 /backup

# Step 5: Create backup user and permissions
useradd -r -s /bin/false backup-user
chown -R backup-user:backup-user /backup

echo "✅ Backup infrastructure setup complete"
```

---

## 3. Database Backup Procedures

### 3.1 PostgreSQL Backup
```bash
#!/bin/bash
# postgresql_backup.sh

echo "🗄️ PostgreSQL Backup Procedure"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/staging/postgresql"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Step 1: Full database backup
echo "Creating full database backup..."
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
    --format=custom \
    --compress=9 \
    --verbose \
    --file="$BACKUP_DIR/helios_full_${TIMESTAMP}.dump"

if [ $? -eq 0 ]; then
    echo "✅ Full backup completed: helios_full_${TIMESTAMP}.dump"
else
    echo "❌ Full backup failed"
    exit 1
fi

# Step 2: Schema-only backup (for quick restore testing)
echo "Creating schema-only backup..."
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
    --schema-only \
    --format=plain \
    --file="$BACKUP_DIR/helios_schema_${TIMESTAMP}.sql"

# Step 3: Table-specific backups for critical data
echo "Creating table-specific backups..."
critical_tables=("users" "career_profiles" "session_states" "ml_model_data")

for table in "${critical_tables[@]}"; do
    pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
        --table=$table \
        --data-only \
        --format=custom \
        --file="$BACKUP_DIR/${table}_${TIMESTAMP}.dump"
    echo "✅ Table backup completed: $table"
done

# Step 4: Verify backup integrity
echo "Verifying backup integrity..."
pg_restore --list "$BACKUP_DIR/helios_full_${TIMESTAMP}.dump" > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Backup integrity verification passed"
else
    echo "❌ Backup integrity verification failed"
    exit 1
fi

# Step 5: Generate backup manifest
cat > "$BACKUP_DIR/backup_manifest_${TIMESTAMP}.json" << EOF
{
    "timestamp": "$TIMESTAMP",
    "backup_type": "postgresql_full",
    "database": "$DB_NAME",
    "host": "$DB_HOST",
    "files": {
        "full_backup": "helios_full_${TIMESTAMP}.dump",
        "schema_backup": "helios_schema_${TIMESTAMP}.sql",
        "table_backups": [
            $(printf '"%s_'${TIMESTAMP}'.dump",' "${critical_tables[@]}" | sed 's/,$//')
        ]
    },
    "size_bytes": $(du -b "$BACKUP_DIR/helios_full_${TIMESTAMP}.dump" | cut -f1),
    "compression": "gzip",
    "encryption": "none",
    "checksum": "$(sha256sum "$BACKUP_DIR/helios_full_${TIMESTAMP}.dump" | cut -d' ' -f1)"
}
EOF

# Step 6: Upload to cloud storage
echo "Uploading to cloud storage..."
restic -r $RESTIC_REPOSITORY backup $BACKUP_DIR

# Step 7: Cleanup old local backups
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "*.dump" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.sql" -mtime +$RETENTION_DAYS -delete

echo "🎯 PostgreSQL backup completed successfully"
```

### 3.2 Redis Backup
```bash
#!/bin/bash
# redis_backup.sh

echo "💾 Redis Backup Procedure"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/staging/redis"
REDIS_DATA_DIR="/var/lib/redis"

mkdir -p $BACKUP_DIR

# Step 1: Create Redis snapshot
echo "Creating Redis snapshot..."
redis-cli -h $REDIS_HOST -p $REDIS_PORT BGSAVE

# Wait for background save to complete
while [ $(redis-cli -h $REDIS_HOST -p $REDIS_PORT LASTSAVE) -eq $(redis-cli -h $REDIS_HOST -p $REDIS_PORT LASTSAVE) ]; do
    sleep 1
done

echo "✅ Redis snapshot completed"

# Step 2: Copy RDB file
echo "Copying RDB file..."
cp $REDIS_DATA_DIR/dump.rdb "$BACKUP_DIR/redis_${TIMESTAMP}.rdb"

# Step 3: Export Redis configuration
echo "Exporting Redis configuration..."
redis-cli -h $REDIS_HOST -p $REDIS_PORT CONFIG GET "*" > "$BACKUP_DIR/redis_config_${TIMESTAMP}.txt"

# Step 4: Create compressed archive
echo "Creating compressed archive..."
tar -czf "$BACKUP_DIR/redis_backup_${TIMESTAMP}.tar.gz" \
    -C $BACKUP_DIR \
    "redis_${TIMESTAMP}.rdb" \
    "redis_config_${TIMESTAMP}.txt"

# Step 5: Upload to cloud storage
restic -r $RESTIC_REPOSITORY backup "$BACKUP_DIR/redis_backup_${TIMESTAMP}.tar.gz"

echo "✅ Redis backup completed"
```

---

## 4. Application Data Backup

### 4.1 Profile Ingestor Data Backup
```bash
#!/bin/bash
# profile_data_backup.sh

echo "📊 Profile Ingestor Data Backup"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/staging/profile_data"
SOURCE_DIR="services/profile-ingestor/output"

mkdir -p $BACKUP_DIR

# Step 1: Sync current data
echo "Syncing profile data..."
rsync -av --delete "$SOURCE_DIR/" "$BACKUP_DIR/current/"

# Step 2: Create timestamped snapshot
echo "Creating timestamped snapshot..."
cp -r "$BACKUP_DIR/current" "$BACKUP_DIR/snapshot_$TIMESTAMP"

# Step 3: Validate JSON files
echo "Validating JSON files..."
validation_errors=0

for json_file in "$BACKUP_DIR/snapshot_$TIMESTAMP"/*.json; do
    if [ -f "$json_file" ]; then
        if ! python -m json.tool "$json_file" > /dev/null 2>&1; then
            echo "❌ Invalid JSON: $json_file"
            validation_errors=$((validation_errors + 1))
        fi
    fi
done

if [ $validation_errors -eq 0 ]; then
    echo "✅ All JSON files validated successfully"
else
    echo "⚠️ $validation_errors JSON validation errors found"
fi

# Step 4: Generate data summary
echo "Generating data summary..."
python3 << EOF
import json
import os
from datetime import datetime

data_summary = {
    "timestamp": "$TIMESTAMP",
    "backup_type": "profile_data",
    "file_count": 0,
    "total_profiles": 0,
    "total_size_bytes": 0,
    "files": []
}

snapshot_dir = "$BACKUP_DIR/snapshot_$TIMESTAMP"
for filename in os.listdir(snapshot_dir):
    if filename.endswith('.json'):
        filepath = os.path.join(snapshot_dir, filename)
        file_size = os.path.getsize(filepath)
        data_summary["total_size_bytes"] += file_size
        data_summary["file_count"] += 1

        try:
            with open(filepath) as f:
                data = json.load(f)
                profile_count = len(data.get('work_experience', []))
                data_summary["total_profiles"] += profile_count

                data_summary["files"].append({
                    "filename": filename,
                    "size_bytes": file_size,
                    "profile_count": profile_count
                })
        except Exception as e:
            print(f"Error processing {filename}: {e}")

with open(f"$BACKUP_DIR/data_summary_$TIMESTAMP.json", "w") as f:
    json.dump(data_summary, f, indent=2)

print(f"Data summary: {data_summary['file_count']} files, {data_summary['total_profiles']} profiles")
EOF

# Step 5: Create encrypted archive
echo "Creating encrypted archive..."
tar -czf "$BACKUP_DIR/profile_data_${TIMESTAMP}.tar.gz" \
    -C "$BACKUP_DIR" \
    "snapshot_$TIMESTAMP" \
    "data_summary_$TIMESTAMP.json"

# Encrypt the archive
gpg --symmetric --cipher-algo AES256 \
    --passphrase-file /etc/backup/encryption_key \
    "$BACKUP_DIR/profile_data_${TIMESTAMP}.tar.gz"

# Step 6: Upload to multiple cloud providers
echo "Uploading to cloud storage..."
rclone copy "$BACKUP_DIR/profile_data_${TIMESTAMP}.tar.gz.gpg" aws_s3:helios-backups/profile-data/
rclone copy "$BACKUP_DIR/profile_data_${TIMESTAMP}.tar.gz.gpg" azure_blob:helios-backups/profile-data/
rclone copy "$BACKUP_DIR/profile_data_${TIMESTAMP}.tar.gz.gpg" gcp_storage:helios-backups/profile-data/

echo "✅ Profile data backup completed"
```

### 4.2 ML Models and Configuration Backup
```bash
#!/bin/bash
# ml_models_backup.sh

echo "🤖 ML Models and Configuration Backup"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/staging/ml_models"

mkdir -p $BACKUP_DIR

# Step 1: Backup ML model files
echo "Backing up ML model files..."
services=("strategist" "analyst")

for service in "${services[@]}"; do
    service_dir="services/$service"

    if [ -d "$service_dir/models" ]; then
        echo "Backing up $service models..."

        # Create service-specific backup directory
        mkdir -p "$BACKUP_DIR/$service"

        # Copy model files
        rsync -av "$service_dir/models/" "$BACKUP_DIR/$service/models/"

        # Copy configuration
        cp "$service_dir/config/"*.yml "$BACKUP_DIR/$service/" 2>/dev/null || true
        cp "$service_dir/requirements.txt" "$BACKUP_DIR/$service/" 2>/dev/null || true

        # Generate model manifest
        python3 << EOF
import os
import json
import hashlib
from datetime import datetime

def get_file_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

manifest = {
    "service": "$service",
    "timestamp": "$TIMESTAMP",
    "models": []
}

models_dir = "$BACKUP_DIR/$service/models"
if os.path.exists(models_dir):
    for root, dirs, files in os.walk(models_dir):
        for file in files:
            filepath = os.path.join(root, file)
            relative_path = os.path.relpath(filepath, models_dir)

            manifest["models"].append({
                "path": relative_path,
                "size_bytes": os.path.getsize(filepath),
                "hash": get_file_hash(filepath),
                "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
            })

with open(f"$BACKUP_DIR/$service/model_manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
EOF

        echo "✅ $service models backed up"
    else
        echo "⚠️ No models directory found for $service"
    fi
done

# Step 2: Backup BMAD configuration
echo "Backing up BMAD configuration..."
cp -r bmad-core/ "$BACKUP_DIR/bmad-core/"

# Step 3: Create versioned archive
echo "Creating versioned archive..."
tar -czf "$BACKUP_DIR/ml_models_${TIMESTAMP}.tar.gz" \
    -C "$BACKUP_DIR" \
    strategist/ analyst/ bmad-core/

# Step 4: Upload to cloud storage
rclone copy "$BACKUP_DIR/ml_models_${TIMESTAMP}.tar.gz" aws_s3:helios-backups/ml-models/

echo "✅ ML models backup completed"
```

---

## 5. Automated Backup Scheduling

### 5.1 Backup Cron Jobs
```bash
#!/bin/bash
# setup_backup_schedule.sh

echo "⏰ Setting up Backup Schedule"

# Create backup user crontab
cat > /tmp/backup_crontab << EOF
# Helios Backup Schedule
# Format: minute hour day month dayofweek command

# Database backups
0 */6 * * * /opt/helios/scripts/backup/postgresql_backup.sh >> /var/log/backup/postgresql.log 2>&1
15 */6 * * * /opt/helios/scripts/backup/redis_backup.sh >> /var/log/backup/redis.log 2>&1

# Application data backups
30 2 * * * /opt/helios/scripts/backup/profile_data_backup.sh >> /var/log/backup/profile_data.log 2>&1
45 3 * * * /opt/helios/scripts/backup/ml_models_backup.sh >> /var/log/backup/ml_models.log 2>&1

# Configuration backups
0 4 * * * /opt/helios/scripts/backup/configuration_backup.sh >> /var/log/backup/configuration.log 2>&1

# Log backups
0 5 * * * /opt/helios/scripts/backup/logs_backup.sh >> /var/log/backup/logs_backup.log 2>&1

# Backup verification and cleanup
30 6 * * * /opt/helios/scripts/backup/verify_backups.sh >> /var/log/backup/verification.log 2>&1
0 7 * * * /opt/helios/scripts/backup/cleanup_old_backups.sh >> /var/log/backup/cleanup.log 2>&1

# Weekly backup reports
0 8 * * 1 /opt/helios/scripts/backup/generate_backup_report.sh >> /var/log/backup/reports.log 2>&1
EOF

# Install crontab for backup user
crontab -u backup-user /tmp/backup_crontab
rm /tmp/backup_crontab

# Create log directory
mkdir -p /var/log/backup
chown backup-user:backup-user /var/log/backup

echo "✅ Backup schedule configured"
```

### 5.2 Backup Monitoring and Alerts
```python
# backup_monitor.py
import os
import json
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class BackupMonitor:
    def __init__(self, config_file):
        with open(config_file) as f:
            self.config = json.load(f)
        self.backup_dir = self.config['backup_directory']
        self.alert_thresholds = self.config['alert_thresholds']

    def check_backup_health(self):
        """Check health of all backup operations"""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'services': {},
            'alerts': []
        }

        # Check each backup type
        backup_types = ['postgresql', 'redis', 'profile_data', 'ml_models']

        for backup_type in backup_types:
            service_health = self.check_service_backup(backup_type)
            health_report['services'][backup_type] = service_health

            if service_health['status'] != 'healthy':
                health_report['overall_status'] = 'degraded'
                health_report['alerts'].append({
                    'service': backup_type,
                    'issue': service_health['issue'],
                    'severity': service_health['severity']
                })

        return health_report

    def check_service_backup(self, backup_type):
        """Check backup health for specific service"""
        backup_path = os.path.join(self.backup_dir, 'staging', backup_type)

        if not os.path.exists(backup_path):
            return {
                'status': 'unhealthy',
                'issue': 'backup_directory_missing',
                'severity': 'critical'
            }

        # Check for recent backups
        recent_cutoff = datetime.now() - timedelta(hours=self.alert_thresholds['max_age_hours'])
        recent_backups = []

        for filename in os.listdir(backup_path):
            filepath = os.path.join(backup_path, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time > recent_cutoff:
                    recent_backups.append({
                        'filename': filename,
                        'timestamp': file_time,
                        'size_bytes': os.path.getsize(filepath)
                    })

        if not recent_backups:
            return {
                'status': 'unhealthy',
                'issue': 'no_recent_backups',
                'severity': 'critical',
                'last_backup': self.get_last_backup_time(backup_path)
            }

        # Check backup sizes
        latest_backup = max(recent_backups, key=lambda x: x['timestamp'])
        min_size = self.alert_thresholds.get(f'{backup_type}_min_size_bytes', 1024)

        if latest_backup['size_bytes'] < min_size:
            return {
                'status': 'degraded',
                'issue': 'backup_too_small',
                'severity': 'warning',
                'actual_size': latest_backup['size_bytes'],
                'expected_min': min_size
            }

        return {
            'status': 'healthy',
            'latest_backup': latest_backup,
            'backup_count': len(recent_backups)
        }

    def get_last_backup_time(self, backup_path):
        """Get timestamp of last backup in directory"""
        files = [f for f in os.listdir(backup_path) if os.path.isfile(os.path.join(backup_path, f))]
        if not files:
            return None

        latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(backup_path, x)))
        return datetime.fromtimestamp(os.path.getmtime(os.path.join(backup_path, latest_file)))

    def send_alert(self, health_report):
        """Send alert if backup issues detected"""
        if health_report['overall_status'] == 'healthy':
            return

        alert_message = self.format_alert_message(health_report)

        # Send email alert
        self.send_email_alert(alert_message)

        # Send Slack alert
        self.send_slack_alert(alert_message)

    def format_alert_message(self, health_report):
        """Format alert message"""
        message = f"🚨 Backup Health Alert - {health_report['overall_status'].upper()}\n\n"
        message += f"Timestamp: {health_report['timestamp']}\n\n"

        message += "Issues Detected:\n"
        for alert in health_report['alerts']:
            message += f"- {alert['service']}: {alert['issue']} (Severity: {alert['severity']})\n"

        message += "\nService Status:\n"
        for service, status in health_report['services'].items():
            message += f"- {service}: {status['status']}\n"

        return message

    def generate_backup_report(self):
        """Generate comprehensive backup report"""
        report = {
            'report_date': datetime.now().isoformat(),
            'backup_summary': self.get_backup_summary(),
            'storage_usage': self.get_storage_usage(),
            'recent_operations': self.get_recent_operations(),
            'recommendations': self.get_recommendations()
        }

        return report

    def get_backup_summary(self):
        """Get summary of all backups"""
        summary = {}
        backup_types = ['postgresql', 'redis', 'profile_data', 'ml_models']

        for backup_type in backup_types:
            backup_path = os.path.join(self.backup_dir, 'staging', backup_type)

            if os.path.exists(backup_path):
                files = [f for f in os.listdir(backup_path) if os.path.isfile(os.path.join(backup_path, f))]
                total_size = sum(os.path.getsize(os.path.join(backup_path, f)) for f in files)

                summary[backup_type] = {
                    'file_count': len(files),
                    'total_size_bytes': total_size,
                    'latest_backup': self.get_last_backup_time(backup_path)
                }
            else:
                summary[backup_type] = {
                    'file_count': 0,
                    'total_size_bytes': 0,
                    'latest_backup': None
                }

        return summary

# Configuration example
backup_config = {
    "backup_directory": "/backup",
    "alert_thresholds": {
        "max_age_hours": 25,
        "postgresql_min_size_bytes": 1048576,  # 1MB
        "redis_min_size_bytes": 102400,       # 100KB
        "profile_data_min_size_bytes": 10485760,  # 10MB
        "ml_models_min_size_bytes": 104857600     # 100MB
    },
    "email_config": {
        "smtp_server": "smtp.company.com",
        "smtp_port": 587,
        "username": "backup-alerts@helios.com",
        "recipients": ["ops@helios.com", "backup-team@helios.com"]
    }
}
```

---

## 6. Disaster Recovery Procedures

### 6.1 Complete System Recovery
```bash
#!/bin/bash
# disaster_recovery.sh

echo "🔄 Disaster Recovery Procedure"

RECOVERY_TYPE=${1:-full}  # full, partial, database_only
BACKUP_TIMESTAMP=${2:-latest}

echo "Recovery Type: $RECOVERY_TYPE"
echo "Backup Timestamp: $BACKUP_TIMESTAMP"

# Step 1: Environment preparation
echo "Preparing recovery environment..."

# Stop all services
docker-compose down

# Create recovery workspace
mkdir -p /recovery/workspace
cd /recovery/workspace

# Step 2: Download backups
echo "Downloading backups from cloud storage..."

case $RECOVERY_TYPE in
    "full")
        echo "Downloading all backup types..."
        rclone copy aws_s3:helios-backups/postgresql/ ./postgresql/
        rclone copy aws_s3:helios-backups/redis/ ./redis/
        rclone copy aws_s3:helios-backups/profile-data/ ./profile-data/
        rclone copy aws_s3:helios-backups/ml-models/ ./ml-models/
        ;;
    "database_only")
        echo "Downloading database backups only..."
        rclone copy aws_s3:helios-backups/postgresql/ ./postgresql/
        rclone copy aws_s3:helios-backups/redis/ ./redis/
        ;;
    "partial")
        echo "Downloading critical backups..."
        rclone copy aws_s3:helios-backups/postgresql/ ./postgresql/
        rclone copy aws_s3:helios-backups/profile-data/ ./profile-data/
        ;;
esac

# Step 3: Verify backup integrity
echo "Verifying backup integrity..."
./scripts/recovery/verify_backup_integrity.sh

if [ $? -ne 0 ]; then
    echo "❌ Backup integrity verification failed"
    echo "Attempting recovery from secondary backup location..."

    # Try Azure backup
    rclone copy azure_blob:helios-backups/ ./backup-secondary/
    ./scripts/recovery/verify_backup_integrity.sh ./backup-secondary/

    if [ $? -ne 0 ]; then
        echo "❌ Secondary backup also failed verification"
        exit 1
    fi

    echo "✅ Using secondary backup for recovery"
    mv ./backup-secondary/* ./
fi

# Step 4: Database recovery
if [ "$RECOVERY_TYPE" != "partial" ] || [ "$RECOVERY_TYPE" == "database_only" ]; then
    echo "Recovering PostgreSQL database..."
    ./scripts/recovery/recover_postgresql.sh $BACKUP_TIMESTAMP

    echo "Recovering Redis cache..."
    ./scripts/recovery/recover_redis.sh $BACKUP_TIMESTAMP
fi

# Step 5: Application data recovery
if [ "$RECOVERY_TYPE" == "full" ] || [ "$RECOVERY_TYPE" == "partial" ]; then
    echo "Recovering profile ingestor data..."
    ./scripts/recovery/recover_profile_data.sh $BACKUP_TIMESTAMP

    if [ "$RECOVERY_TYPE" == "full" ]; then
        echo "Recovering ML models..."
        ./scripts/recovery/recover_ml_models.sh $BACKUP_TIMESTAMP
    fi
fi

# Step 6: Configuration recovery
echo "Recovering configuration..."
./scripts/recovery/recover_configuration.sh $BACKUP_TIMESTAMP

# Step 7: Service startup and validation
echo "Starting services..."
docker-compose up -d

# Wait for services to initialize
sleep 60

# Step 8: Post-recovery validation
echo "Performing post-recovery validation..."
./scripts/recovery/validate_recovery.sh

if [ $? -eq 0 ]; then
    echo "✅ Disaster recovery completed successfully"

    # Generate recovery report
    ./scripts/recovery/generate_recovery_report.sh

    # Send success notification
    python scripts/notifications/send_recovery_success.py
else
    echo "❌ Recovery validation failed"
    echo "Manual intervention required"
    exit 1
fi
```

### 6.2 Database-Specific Recovery
```bash
#!/bin/bash
# recover_postgresql.sh

BACKUP_TIMESTAMP=${1:-latest}
RECOVERY_DIR="/recovery/workspace/postgresql"

echo "🗄️ PostgreSQL Recovery Procedure"

# Step 1: Find backup files
if [ "$BACKUP_TIMESTAMP" == "latest" ]; then
    BACKUP_FILE=$(ls -t $RECOVERY_DIR/helios_full_*.dump | head -1)
else
    BACKUP_FILE="$RECOVERY_DIR/helios_full_${BACKUP_TIMESTAMP}.dump"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Using backup file: $BACKUP_FILE"

# Step 2: Stop PostgreSQL if running
docker stop helios-postgresql 2>/dev/null || true

# Step 3: Start fresh PostgreSQL instance
echo "Starting fresh PostgreSQL instance..."
docker run -d \
    --name helios-postgresql-recovery \
    -e POSTGRES_DB=$DB_NAME \
    -e POSTGRES_USER=$DB_USER \
    -e POSTGRES_PASSWORD=$DB_PASSWORD \
    -p 5432:5432 \
    postgres:15

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until docker exec helios-postgresql-recovery pg_isready -U $DB_USER -d $DB_NAME; do
    sleep 2
done

# Step 4: Drop existing database and recreate
echo "Recreating database..."
docker exec helios-postgresql-recovery psql -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker exec helios-postgresql-recovery psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;"

# Step 5: Restore from backup
echo "Restoring database from backup..."
docker exec -i helios-postgresql-recovery pg_restore \
    -U $DB_USER \
    -d $DB_NAME \
    --verbose \
    --clean \
    --if-exists \
    < "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL restore completed successfully"
else
    echo "❌ PostgreSQL restore failed"
    exit 1
fi

# Step 6: Verify restore
echo "Verifying restore..."
TABLE_COUNT=$(docker exec helios-postgresql-recovery psql -U $DB_USER -d $DB_NAME -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")

if [ $TABLE_COUNT -gt 0 ]; then
    echo "✅ Database restore verified - $TABLE_COUNT tables restored"
else
    echo "❌ Database restore verification failed"
    exit 1
fi

# Step 7: Update configuration to use restored database
echo "Updating database configuration..."
export RESTORED_DB_HOST=$(docker inspect helios-postgresql-recovery --format '{{.NetworkSettings.IPAddress}}')

echo "✅ PostgreSQL recovery completed"
echo "Database available at: $RESTORED_DB_HOST:5432"
```

### 6.3 Recovery Validation
```python
# recovery_validator.py
import psycopg2
import redis
import json
import os
import requests
from datetime import datetime
from typing import Dict, List

class RecoveryValidator:
    def __init__(self, config_file: str):
        with open(config_file) as f:
            self.config = json.load(f)

    def validate_full_recovery(self) -> Dict:
        """Validate complete system recovery"""
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'success',
            'validations': {}
        }

        # Database validation
        db_result = self.validate_database_recovery()
        validation_results['validations']['database'] = db_result

        # Cache validation
        cache_result = self.validate_cache_recovery()
        validation_results['validations']['cache'] = cache_result

        # Application data validation
        app_data_result = self.validate_application_data()
        validation_results['validations']['application_data'] = app_data_result

        # Service validation
        service_result = self.validate_services()
        validation_results['validations']['services'] = service_result

        # Configuration validation
        config_result = self.validate_configuration()
        validation_results['validations']['configuration'] = config_result

        # Determine overall status
        failed_validations = [
            name for name, result in validation_results['validations'].items()
            if result['status'] != 'success'
        ]

        if failed_validations:
            validation_results['overall_status'] = 'failed'
            validation_results['failed_components'] = failed_validations

        return validation_results

    def validate_database_recovery(self) -> Dict:
        """Validate database recovery"""
        try:
            conn = psycopg2.connect(
                host=self.config['database']['host'],
                port=self.config['database']['port'],
                database=self.config['database']['name'],
                user=self.config['database']['user'],
                password=self.config['database']['password']
            )

            cursor = conn.cursor()

            # Check table existence
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = self.config['expected_tables']
            missing_tables = set(expected_tables) - set(tables)

            if missing_tables:
                return {
                    'status': 'failed',
                    'error': f'Missing tables: {list(missing_tables)}',
                    'tables_found': len(tables),
                    'tables_expected': len(expected_tables)
                }

            # Check data integrity
            data_integrity_checks = []
            for table in ['users', 'career_profiles', 'session_states']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                data_integrity_checks.append({
                    'table': table,
                    'record_count': count
                })

            conn.close()

            return {
                'status': 'success',
                'tables_recovered': len(tables),
                'data_integrity': data_integrity_checks
            }

        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }

    def validate_cache_recovery(self) -> Dict:
        """Validate Redis cache recovery"""
        try:
            r = redis.Redis(
                host=self.config['redis']['host'],
                port=self.config['redis']['port'],
                decode_responses=True
            )

            # Test basic connectivity
            if not r.ping():
                return {
                    'status': 'failed',
                    'error': 'Redis ping failed'
                }

            # Check key count
            key_count = r.dbsize()

            # Test basic operations
            test_key = 'recovery_test'
            r.set(test_key, 'test_value', ex=60)

            if r.get(test_key) != 'test_value':
                return {
                    'status': 'failed',
                    'error': 'Redis read/write test failed'
                }

            r.delete(test_key)

            return {
                'status': 'success',
                'key_count': key_count,
                'read_write_test': 'passed'
            }

        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }

    def validate_application_data(self) -> Dict:
        """Validate application data recovery"""
        profile_data_path = self.config['application_data']['profile_ingestor_path']

        if not os.path.exists(profile_data_path):
            return {
                'status': 'failed',
                'error': f'Profile data directory not found: {profile_data_path}'
            }

        # Count JSON files
        json_files = [f for f in os.listdir(profile_data_path) if f.endswith('.json')]

        # Validate JSON structure
        valid_files = 0
        invalid_files = []

        for json_file in json_files:
            file_path = os.path.join(profile_data_path, json_file)
            try:
                with open(file_path) as f:
                    data = json.load(f)

                # Basic structure validation
                if 'work_experience' in data and 'skills_inventory' in data:
                    valid_files += 1
                else:
                    invalid_files.append(json_file)

            except json.JSONDecodeError:
                invalid_files.append(json_file)

        if invalid_files:
            return {
                'status': 'failed',
                'error': f'Invalid JSON files: {invalid_files}',
                'valid_files': valid_files,
                'invalid_files': len(invalid_files)
            }

        return {
            'status': 'success',
            'json_files_recovered': len(json_files),
            'valid_files': valid_files
        }

    def validate_services(self) -> Dict:
        """Validate service recovery"""
        services = self.config['services']
        service_results = {}

        for service_name, service_config in services.items():
            try:
                health_url = f"{service_config['url']}/health"
                response = requests.get(health_url, timeout=10)

                if response.status_code == 200:
                    service_results[service_name] = {
                        'status': 'healthy',
                        'response_time': response.elapsed.total_seconds()
                    }
                else:
                    service_results[service_name] = {
                        'status': 'unhealthy',
                        'http_status': response.status_code
                    }

            except Exception as e:
                service_results[service_name] = {
                    'status': 'unreachable',
                    'error': str(e)
                }

        # Determine overall service status
        unhealthy_services = [
            name for name, result in service_results.items()
            if result['status'] != 'healthy'
        ]

        if unhealthy_services:
            return {
                'status': 'failed',
                'unhealthy_services': unhealthy_services,
                'service_details': service_results
            }

        return {
            'status': 'success',
            'healthy_services': len(service_results),
            'service_details': service_results
        }

    def validate_configuration(self) -> Dict:
        """Validate configuration recovery"""
        config_paths = self.config['configuration_paths']
        missing_configs = []

        for config_path in config_paths:
            if not os.path.exists(config_path):
                missing_configs.append(config_path)

        if missing_configs:
            return {
                'status': 'failed',
                'missing_configurations': missing_configs
            }

        return {
            'status': 'success',
            'configurations_recovered': len(config_paths)
        }

    def generate_validation_report(self, validation_results: Dict) -> str:
        """Generate human-readable validation report"""
        report = f"""
Recovery Validation Report
=========================

Overall Status: {validation_results['overall_status'].upper()}
Validation Time: {validation_results['timestamp']}

Component Status:
-----------------
"""

        for component, result in validation_results['validations'].items():
            status_icon = "✅" if result['status'] == 'success' else "❌"
            report += f"{status_icon} {component.replace('_', ' ').title()}: {result['status']}\n"

            if result['status'] != 'success' and 'error' in result:
                report += f"   Error: {result['error']}\n"

        if validation_results['overall_status'] == 'failed':
            report += f"\nFailed Components: {', '.join(validation_results['failed_components'])}\n"
            report += "\nManual intervention may be required for failed components.\n"
        else:
            report += "\n✅ All components recovered successfully!\n"

        return report

# Validation configuration
validation_config = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "helios",
        "user": "helios_user",
        "password": "helios_password"
    },
    "redis": {
        "host": "localhost",
        "port": 6379
    },
    "application_data": {
        "profile_ingestor_path": "services/profile-ingestor/output"
    },
    "services": {
        "orchestrator": {"url": "http://localhost:8000"},
        "strategist": {"url": "http://localhost:8001"},
        "analyst": {"url": "http://localhost:8002"},
        "profile_ingestor": {"url": "http://localhost:8080"}
    },
    "expected_tables": [
        "users", "career_profiles", "session_states", "career_paths",
        "analysis_reports", "ml_model_data"
    ],
    "configuration_paths": [
        "bmad-core/core-config.yaml",
        "docker-compose.yml",
        "services/orchestrator/config/production.yml"
    ]
}
```

---

## 7. RTO/RPO Compliance

### 7.1 Recovery Time Objective (RTO) Procedures
```yaml
# rto_procedures.yml
rto_targets:
  critical_services: 4_hours
  important_services: 8_hours
  non_critical_services: 24_hours

recovery_procedures:
  emergency_recovery:  # Target: 1 hour
    - enable_maintenance_mode: 5_minutes
    - download_critical_backups: 15_minutes
    - restore_database: 20_minutes
    - start_core_services: 10_minutes
    - validate_functionality: 10_minutes

  standard_recovery:  # Target: 4 hours
    - prepare_environment: 30_minutes
    - download_all_backups: 60_minutes
    - restore_databases: 90_minutes
    - restore_application_data: 60_minutes
    - start_all_services: 30_minutes
    - full_validation: 30_minutes

  complete_recovery:  # Target: 8 hours
    - infrastructure_setup: 120_minutes
    - download_backups: 90_minutes
    - restore_databases: 120_minutes
    - restore_application_data: 90_minutes
    - restore_ml_models: 60_minutes
    - start_services: 45_minutes
    - comprehensive_testing: 75_minutes
```

### 7.2 Recovery Point Objective (RPO) Monitoring
```bash
#!/bin/bash
# rpo_monitor.sh

echo "📊 RPO Compliance Monitoring"

RPO_TARGET_MINUTES=60  # 1 hour RPO target
CURRENT_TIME=$(date +%s)

# Function to check backup freshness
check_backup_freshness() {
    local backup_type=$1
    local backup_dir="/backup/staging/$backup_type"

    if [ ! -d "$backup_dir" ]; then
        echo "❌ $backup_type: Backup directory missing"
        return 1
    fi

    # Find most recent backup
    latest_backup=$(find "$backup_dir" -type f -name "*.dump" -o -name "*.tar.gz" -o -name "*.rdb" | xargs ls -t | head -1)

    if [ -z "$latest_backup" ]; then
        echo "❌ $backup_type: No backups found"
        return 1
    fi

    # Calculate age of latest backup
    backup_time=$(stat -c %Y "$latest_backup")
    age_minutes=$(( (CURRENT_TIME - backup_time) / 60 ))

    if [ $age_minutes -le $RPO_TARGET_MINUTES ]; then
        echo "✅ $backup_type: RPO compliant (${age_minutes}m old)"
        return 0
    else
        echo "⚠️ $backup_type: RPO violation (${age_minutes}m old, target: ${RPO_TARGET_MINUTES}m)"
        return 1
    fi
}

# Check all backup types
backup_types=("postgresql" "redis" "profile_data" "ml_models")
rpo_violations=0

for backup_type in "${backup_types[@]}"; do
    if ! check_backup_freshness "$backup_type"; then
        rpo_violations=$((rpo_violations + 1))
    fi
done

# Generate RPO compliance report
cat > "/var/log/backup/rpo_compliance_$(date +%Y%m%d_%H%M%S).log" << EOF
RPO Compliance Report
====================

Check Time: $(date)
RPO Target: $RPO_TARGET_MINUTES minutes
Total Backup Types: ${#backup_types[@]}
RPO Violations: $rpo_violations

$(for backup_type in "${backup_types[@]}"; do
    check_backup_freshness "$backup_type"
done)

Overall RPO Status: $([ $rpo_violations -eq 0 ] && echo "COMPLIANT" || echo "NON-COMPLIANT")
EOF

# Alert if RPO violations detected
if [ $rpo_violations -gt 0 ]; then
    echo "🚨 RPO violations detected - sending alert"
    python scripts/alerting/send_rpo_violation_alert.py --violations=$rpo_violations
fi

echo "✅ RPO monitoring complete"
```

---

*This runbook ensures comprehensive backup and disaster recovery capabilities for the Helios Career Operations System, meeting enterprise-grade data protection and business continuity requirements.*

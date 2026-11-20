#!/bin/bash
# PostgreSQL Database Backup Script for Gofer Exam
# Bash version for Linux/Render production
#
# Usage:
#   ./backup_database.sh                    # Uses environment variables
#   ./backup_database.sh /path/to/backups   # Custom backup directory
#   BACKUP_RETENTION_DAYS=7 ./backup_database.sh  # Keep backups for 7 days

set -e  # Exit on error

# Configuration from environment or defaults
DB_NAME="${DATABASE_NAME:-gofer_exam_db}"
DB_USER="${DATABASE_USER:-gofer_exam_user}"
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
BACKUP_DIR="${1:-${BACKUP_DIR:-/tmp/db_backups}}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# For Render, DATABASE_URL is typically provided
if [ -n "$DATABASE_URL" ]; then
    echo "Using DATABASE_URL from environment"
    # Parse DATABASE_URL if needed (pg_dump can use it directly)
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate timestamped filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_backup_${TIMESTAMP}.dump"
LOG_FILE="$BACKUP_DIR/${DB_NAME}_backup_${TIMESTAMP}.log"

echo "========================================"
echo "Gofer Exam Database Backup Script"
echo "========================================"
echo ""
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST"
echo "Backup file: $BACKUP_FILE"
echo ""

# Start logging
{
    echo "Gofer Exam Database Backup Log"
    echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Database: $DB_NAME"
    echo "User: $DB_USER"
    echo "Host: $DB_HOST:$DB_PORT"
    echo "Backup file: $BACKUP_FILE"
    echo ""
} > "$LOG_FILE"

# Check if pg_dump is available
if ! command -v pg_dump &> /dev/null; then
    echo "ERROR: pg_dump not found in PATH" >&2
    echo "ERROR: pg_dump not found" >> "$LOG_FILE"
    exit 1
fi

PG_VERSION=$(pg_dump --version)
echo "pg_dump found: $PG_VERSION"
echo "pg_dump version: $PG_VERSION" >> "$LOG_FILE"

# Perform backup
echo ""
echo "Creating backup..."
START_TIME=$(date +%s)

if [ -n "$DATABASE_URL" ]; then
    # Use DATABASE_URL directly (Render/production)
    if pg_dump "$DATABASE_URL" -F c -b -v -f "$BACKUP_FILE" 2>> "$LOG_FILE"; then
        BACKUP_SUCCESS=true
    else
        BACKUP_SUCCESS=false
    fi
else
    # Use individual connection parameters (local development)
    if PGPASSWORD="$PGPASSWORD" pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -F c -b -v -f "$BACKUP_FILE" 2>> "$LOG_FILE"; then
        BACKUP_SUCCESS=true
    else
        BACKUP_SUCCESS=false
    fi
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ "$BACKUP_SUCCESS" = true ]; then
    echo "Backup completed successfully!"
    echo "Duration: ${DURATION} seconds"
    
    {
        echo "Backup started: $(date -d @$START_TIME '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r $START_TIME '+%Y-%m-%d %H:%M:%S')"
        echo "Backup completed: $(date -d @$END_TIME '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r $END_TIME '+%Y-%m-%d %H:%M:%S')"
        echo "Duration: ${DURATION} seconds"
    } >> "$LOG_FILE"
    
    # Get backup file size
    if [ -f "$BACKUP_FILE" ]; then
        FILE_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE")
        FILE_SIZE_MB=$(echo "scale=2; $FILE_SIZE / 1048576" | bc)
        echo "Backup size: ${FILE_SIZE_MB} MB ($FILE_SIZE bytes)"
        echo "Backup size: ${FILE_SIZE_MB} MB ($FILE_SIZE bytes)" >> "$LOG_FILE"
        
        # Calculate SHA-256 hash
        echo ""
        echo "Calculating SHA-256 hash..."
        if command -v sha256sum &> /dev/null; then
            HASH=$(sha256sum "$BACKUP_FILE" | awk '{print $1}')
        elif command -v shasum &> /dev/null; then
            HASH=$(shasum -a 256 "$BACKUP_FILE" | awk '{print $1}')
        else
            echo "WARNING: sha256sum not available, skipping hash"
            HASH="N/A"
        fi
        
        if [ "$HASH" != "N/A" ]; then
            echo "SHA-256: $HASH"
            echo "SHA-256: $HASH" >> "$LOG_FILE"
            echo "$HASH" > "${BACKUP_FILE}.sha256"
            echo "Hash saved to: ${BACKUP_FILE}.sha256"
        fi
    fi
else
    echo "ERROR: Backup failed" >&2
    echo "ERROR: Backup failed" >> "$LOG_FILE"
    exit 1
fi

# Verify backup integrity
echo ""
echo "Verifying backup integrity..."

if pg_restore --list "$BACKUP_FILE" > /dev/null 2>> "$LOG_FILE"; then
    TABLE_COUNT=$(pg_restore --list "$BACKUP_FILE" 2>/dev/null | grep -c "TABLE DATA" || echo "0")
    echo "Backup verification passed!"
    echo "Tables found in backup: $TABLE_COUNT"
    echo "Backup verification: PASSED" >> "$LOG_FILE"
    echo "Tables in backup: $TABLE_COUNT" >> "$LOG_FILE"
else
    echo "WARNING: Backup verification failed" >&2
    echo "Backup verification: FAILED" >> "$LOG_FILE"
fi

# Clean up old backups (retention policy)
echo ""
echo "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."
DELETED_COUNT=0

find "$BACKUP_DIR" -name "${DB_NAME}_backup_*.dump" -type f -mtime +${RETENTION_DAYS} -print | while read -r OLD_BACKUP; do
    echo "Deleting old backup: $(basename "$OLD_BACKUP")"
    rm -f "$OLD_BACKUP"
    rm -f "${OLD_BACKUP}.sha256"
    rm -f "${OLD_BACKUP%.dump}.log"
    DELETED_COUNT=$((DELETED_COUNT + 1))
done

if [ "$DELETED_COUNT" -gt 0 ]; then
    echo "Deleted $DELETED_COUNT old backup(s)"
    echo "Deleted $DELETED_COUNT old backup(s)" >> "$LOG_FILE"
else
    echo "No old backups to delete"
fi

# Final log entry
echo "" >> "$LOG_FILE"
echo "Backup completed successfully." >> "$LOG_FILE"

echo ""
echo "========================================"
echo "Backup Summary"
echo "========================================"
echo "Backup file: $BACKUP_FILE"
echo "Log file: $LOG_FILE"
echo ""
echo "To restore this backup, run:"
echo "  pg_restore -d \$DATABASE_URL -c $BACKUP_FILE"
echo "  # OR"
echo "  pg_restore -U $DB_USER -d $DB_NAME -c $BACKUP_FILE"
echo ""

# List recent backups
echo "Recent backups in $BACKUP_DIR:"
ls -lht "$BACKUP_DIR"/*.dump 2>/dev/null | head -5 || echo "  (none)"

exit 0

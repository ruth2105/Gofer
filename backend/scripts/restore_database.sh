#!/bin/bash
# PostgreSQL Database Restore Script for Gofer Exam
# Bash version for Linux/production
#
# Usage:
#   ./restore_database.sh /path/to/backup.dump           # Restore from backup
#   ./restore_database.sh /path/to/backup.dump --verify  # Verify backup first
#   ./restore_database.sh /path/to/backup.dump --dry-run # Show what would be restored

set -e  # Exit on error

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file> [--verify] [--dry-run]" >&2
    echo ""
    echo "Options:"
    echo "  --verify   Verify backup integrity before restoring"
    echo "  --dry-run  List backup contents without restoring"
    exit 1
fi

BACKUP_FILE="$1"
VERIFY_FIRST=false
DRY_RUN=false

# Parse options
shift
while [ $# -gt 0 ]; do
    case "$1" in
        --verify)
            VERIFY_FIRST=true
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
    shift
done

# Configuration
DB_NAME="${DATABASE_NAME:-gofer_exam_db}"
DB_USER="${DATABASE_USER:-gofer_exam_user}"
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"

echo "========================================"
echo "Gofer Exam Database Restore Script"
echo "========================================"
echo ""
echo "Database: $DB_NAME"
echo "Backup file: $BACKUP_FILE"
echo ""

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE" >&2
    exit 1
fi

# Check if pg_restore is available
if ! command -v pg_restore &> /dev/null; then
    echo "ERROR: pg_restore not found in PATH" >&2
    exit 1
fi

# Verify backup file integrity
echo "Verifying backup file integrity..."

if ! pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1; then
    echo "ERROR: Backup file is corrupted or invalid" >&2
    exit 1
fi

TABLE_COUNT=$(pg_restore --list "$BACKUP_FILE" 2>/dev/null | grep -c "TABLE DATA" || echo "0")
echo "Backup file is valid"
echo "Tables in backup: $TABLE_COUNT"

# Verify SHA-256 hash if available
if [ -f "${BACKUP_FILE}.sha256" ]; then
    echo ""
    echo "Verifying SHA-256 hash..."
    STORED_HASH=$(cat "${BACKUP_FILE}.sha256")
    
    if command -v sha256sum &> /dev/null; then
        COMPUTED_HASH=$(sha256sum "$BACKUP_FILE" | awk '{print $1}')
    elif command -v shasum &> /dev/null; then
        COMPUTED_HASH=$(shasum -a 256 "$BACKUP_FILE" | awk '{print $1}')
    else
        echo "WARNING: sha256sum not available, skipping hash verification"
        COMPUTED_HASH="N/A"
    fi
    
    if [ "$COMPUTED_HASH" != "N/A" ]; then
        if [ "$STORED_HASH" = "$COMPUTED_HASH" ]; then
            echo "Hash verification passed!"
        else
            echo "ERROR: Hash mismatch!" >&2
            echo "Stored:   $STORED_HASH" >&2
            echo "Computed: $COMPUTED_HASH" >&2
            exit 1
        fi
    fi
fi

# If dry-run, just list contents and exit
if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "========================================" 
    echo "Backup Contents (Dry Run)"
    echo "========================================"
    pg_restore --list "$BACKUP_FILE" 2>/dev/null
    echo ""
    echo "Dry run complete. No restore performed."
    exit 0
fi

# Exit if only verification was requested
if [ "$VERIFY_FIRST" = true ]; then
    echo ""
    echo "Verification complete. Use without --verify to restore."
    exit 0
fi

# Warning and confirmation
echo ""
echo "========================================"
echo "WARNING"
echo "========================================"
echo "This will DROP and recreate all tables in the database."
echo "All existing data will be LOST."
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRMATION

if [ "$CONFIRMATION" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Perform restore
echo ""
echo "Restoring database..."
START_TIME=$(date +%s)

if [ -n "$DATABASE_URL" ]; then
    # Use DATABASE_URL (Render/production)
    if pg_restore -d "$DATABASE_URL" --clean --if-exists --no-owner --no-acl --verbose "$BACKUP_FILE" 2>&1; then
        RESTORE_SUCCESS=true
    else
        RESTORE_SUCCESS=false
    fi
else
    # Use individual connection parameters (local)
    if PGPASSWORD="$PGPASSWORD" pg_restore -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" --clean --if-exists --no-owner --no-acl --verbose "$BACKUP_FILE" 2>&1; then
        RESTORE_SUCCESS=true
    else
        RESTORE_SUCCESS=false
    fi
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ "$RESTORE_SUCCESS" = true ]; then
    echo ""
    echo "========================================" 
    echo "Restore completed successfully!"
    echo "========================================"
    echo "Duration: ${DURATION} seconds"
    echo ""
    echo "Next steps:"
    echo "  1. Verify database content"
    echo "  2. Run migrations if schema changed: python manage.py migrate"
    echo "  3. Test application functionality"
else
    echo ""
    echo "ERROR: Restore failed" >&2
    echo "Check the error messages above for details" >&2
    exit 1
fi

exit 0

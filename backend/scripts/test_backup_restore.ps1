# Test script to verify backup and restore procedures
# Creates a test database, backs it up, restores to a new database, and verifies

param(
    [switch]$CleanupAfter = $true
)

$ErrorActionPreference = "Stop"

$TestDbName = "gofer_exam_test_backup_$(Get-Date -Format 'yyyyMMddHHmmss')"
$BackupDir = Join-Path $PSScriptRoot "..\backups\test"
$DbUser = "gofer_exam_user"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backup/Restore Test Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test database: $TestDbName" -ForegroundColor Yellow
Write-Host "Backup directory: $BackupDir" -ForegroundColor Yellow
Write-Host ""

# Create test backup directory
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

try {
    # Step 1: Create test database
    Write-Host "[1/6] Creating test database..." -ForegroundColor Yellow
    psql -U postgres -c "CREATE DATABASE $TestDbName;" 2>&1 | Out-Null
    psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $TestDbName TO $DbUser;" 2>&1 | Out-Null
    Write-Host "      Test database created" -ForegroundColor Green
    
    # Step 2: Create test schema and data
    Write-Host "[2/6] Creating test tables and data..." -ForegroundColor Yellow
    $TestSql = @"
CREATE TABLE test_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE test_documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES test_users(id),
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO test_users (email) VALUES 
    ('user1@example.com'),
    ('user2@example.com'),
    ('user3@example.com');

INSERT INTO test_documents (user_id, title) VALUES
    (1, 'Document 1'),
    (1, 'Document 2'),
    (2, 'Document 3');
"@
    
    $TestSql | psql -U $DbUser -d $TestDbName 2>&1 | Out-Null
    
    # Verify data was inserted
    $UserCount = psql -U $DbUser -d $TestDbName -t -c "SELECT COUNT(*) FROM test_users;" 2>&1
    $DocCount = psql -U $DbUser -d $TestDbName -t -c "SELECT COUNT(*) FROM test_documents;" 2>&1
    
    Write-Host "      Created 2 tables with $($UserCount.Trim()) users and $($DocCount.Trim()) documents" -ForegroundColor Green
    
    # Step 3: Backup test database
    Write-Host "[3/6] Creating backup..." -ForegroundColor Yellow
    $BackupFile = Join-Path $BackupDir "${TestDbName}.dump"
    
    pg_dump -U $DbUser -d $TestDbName -F c -f $BackupFile 2>&1 | Out-Null
    
    if (Test-Path $BackupFile) {
        $BackupSize = (Get-Item $BackupFile).Length
        Write-Host "      Backup created: $([math]::Round($BackupSize / 1KB, 2)) KB" -ForegroundColor Green
    } else {
        throw "Backup file was not created"
    }
    
    # Step 4: Verify backup integrity
    Write-Host "[4/6] Verifying backup integrity..." -ForegroundColor Yellow
    $VerifyOutput = pg_restore --list $BackupFile 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $TableDataCount = ($VerifyOutput | Select-String "TABLE DATA").Count
        Write-Host "      Backup verified: $TableDataCount table data entries" -ForegroundColor Green
    } else {
        throw "Backup verification failed"
    }
    
    # Step 5: Restore to new database
    Write-Host "[5/6] Restoring to new database..." -ForegroundColor Yellow
    $RestoreDbName = "${TestDbName}_restored"
    
    psql -U postgres -c "CREATE DATABASE $RestoreDbName;" 2>&1 | Out-Null
    psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $RestoreDbName TO $DbUser;" 2>&1 | Out-Null
    
    pg_restore -U $DbUser -d $RestoreDbName -c --if-exists $BackupFile 2>&1 | Out-Null
    
    Write-Host "      Database restored" -ForegroundColor Green
    
    # Step 6: Verify restored data
    Write-Host "[6/6] Verifying restored data..." -ForegroundColor Yellow
    
    $RestoredUserCount = psql -U $DbUser -d $RestoreDbName -t -c "SELECT COUNT(*) FROM test_users;" 2>&1
    $RestoredDocCount = psql -U $DbUser -d $RestoreDbName -t -c "SELECT COUNT(*) FROM test_documents;" 2>&1
    
    if ($RestoredUserCount.Trim() -eq $UserCount.Trim() -and $RestoredDocCount.Trim() -eq $DocCount.Trim()) {
        Write-Host "      Data verification passed!" -ForegroundColor Green
        Write-Host "      Users: $($UserCount.Trim()) -> $($RestoredUserCount.Trim())" -ForegroundColor Green
        Write-Host "      Documents: $($DocCount.Trim()) -> $($RestoredDocCount.Trim())" -ForegroundColor Green
    } else {
        throw "Data mismatch after restore"
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "TEST PASSED" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Backup and restore procedures are working correctly" -ForegroundColor Green
    
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "TEST FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
} finally {
    # Cleanup
    if ($CleanupAfter) {
        Write-Host ""
        Write-Host "Cleaning up test databases..." -ForegroundColor Yellow
        
        try {
            psql -U postgres -c "DROP DATABASE IF EXISTS $TestDbName;" 2>&1 | Out-Null
            Write-Host "  Dropped: $TestDbName" -ForegroundColor Gray
        } catch {}
        
        try {
            psql -U postgres -c "DROP DATABASE IF EXISTS ${RestoreDbName};" 2>&1 | Out-Null
            Write-Host "  Dropped: $RestoreDbName" -ForegroundColor Gray
        } catch {}
        
        Write-Host "Cleanup complete" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Test databases preserved for inspection:" -ForegroundColor Yellow
        Write-Host "  - $TestDbName" -ForegroundColor Gray
        Write-Host "  - $RestoreDbName" -ForegroundColor Gray
    }
}

exit 0

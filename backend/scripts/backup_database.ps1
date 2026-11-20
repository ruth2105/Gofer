# PostgreSQL Database Backup Script for Gofer Exam
# PowerShell version for Windows development
# 
# Usage:
#   .\backup_database.ps1                          # Interactive (prompts for password)
#   .\backup_database.ps1 -Automated              # Non-interactive (uses PGPASSWORD env var)
#   .\backup_database.ps1 -BackupDir "C:\backups" # Custom backup directory

param(
    [string]$BackupDir = "",
    [switch]$Automated = $false,
    [switch]$Verify = $true
)

# Configuration
$DbName = "gofer_exam"
$DbUser = "gofer_exam_user"
$DbHost = "localhost"
$DbPort = "5432"

# Determine backup directory
if ($BackupDir -eq "") {
    $BackupDir = Join-Path $PSScriptRoot "..\backups"
}

# Create backup directory if it doesn't exist
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Write-Host "Created backup directory: $BackupDir" -ForegroundColor Green
}

# Generate timestamped filename
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = Join-Path $BackupDir "${DbName}_backup_${Timestamp}.dump"
$LogFile = Join-Path $BackupDir "${DbName}_backup_${Timestamp}.log"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Gofer Exam Database Backup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Database: $DbName"
Write-Host "User: $DbUser"
Write-Host "Host: ${DbHost}:${DbPort}"
Write-Host "Backup file: $BackupFile"
Write-Host ""

# Start logging
$LogContent = @"
Gofer Exam Database Backup Log
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Database: $DbName
User: $DbUser
Host: ${DbHost}:${DbPort}
Backup file: $BackupFile

"@

# Check if pg_dump is available
try {
    $pgDumpVersion = pg_dump --version 2>&1
    Write-Host "pg_dump found: $pgDumpVersion" -ForegroundColor Green
    $LogContent += "pg_dump version: $pgDumpVersion`n"
} catch {
    Write-Host "ERROR: pg_dump not found in PATH" -ForegroundColor Red
    Write-Host "Please ensure PostgreSQL bin directory is in your PATH" -ForegroundColor Red
    $LogContent += "ERROR: pg_dump not found in PATH`n"
    $LogContent | Out-File -FilePath $LogFile -Encoding UTF8
    exit 1
}

# Set password environment variable if automated
if ($Automated) {
    if (-not $env:PGPASSWORD) {
        Write-Host "ERROR: PGPASSWORD environment variable not set" -ForegroundColor Red
        Write-Host "For automated backups, set PGPASSWORD before running" -ForegroundColor Yellow
        $LogContent += "ERROR: PGPASSWORD not set for automated mode`n"
        $LogContent | Out-File -FilePath $LogFile -Encoding UTF8
        exit 1
    }
    Write-Host "Using PGPASSWORD from environment" -ForegroundColor Yellow
}

# Perform backup
Write-Host ""
Write-Host "Creating backup..." -ForegroundColor Yellow
$StartTime = Get-Date

try {
    # pg_dump with custom format for compression and selective restore
    $pgDumpArgs = @(
        "-U", $DbUser,
        "-h", $DbHost,
        "-p", $DbPort,
        "-d", $DbName,
        "-F", "c",           # Custom format (compressed)
        "-b",                # Include large objects
        "-v",                # Verbose
        "-f", $BackupFile
    )
    
    $process = Start-Process -FilePath "pg_dump" -ArgumentList $pgDumpArgs -NoNewWindow -Wait -PassThru -RedirectStandardError ($LogFile + ".err")
    
    if ($process.ExitCode -eq 0) {
        $EndTime = Get-Date
        $Duration = ($EndTime - $StartTime).TotalSeconds
        
        Write-Host "Backup completed successfully!" -ForegroundColor Green
        Write-Host "Duration: $([math]::Round($Duration, 2)) seconds" -ForegroundColor Green
        
        $LogContent += "Backup started: $($StartTime.ToString('yyyy-MM-dd HH:mm:ss'))`n"
        $LogContent += "Backup completed: $($EndTime.ToString('yyyy-MM-dd HH:mm:ss'))`n"
        $LogContent += "Duration: $([math]::Round($Duration, 2)) seconds`n"
        
        # Get backup file size
        if (Test-Path $BackupFile) {
            $FileSize = (Get-Item $BackupFile).Length
            $FileSizeMB = [math]::Round($FileSize / 1MB, 2)
            Write-Host "Backup size: $FileSizeMB MB ($FileSize bytes)" -ForegroundColor Green
            $LogContent += "Backup size: $FileSizeMB MB ($FileSize bytes)`n"
            
            # Calculate SHA-256 hash for integrity verification
            Write-Host ""
            Write-Host "Calculating SHA-256 hash..." -ForegroundColor Yellow
            $Hash = Get-FileHash -Path $BackupFile -Algorithm SHA256
            Write-Host "SHA-256: $($Hash.Hash)" -ForegroundColor Cyan
            $LogContent += "SHA-256: $($Hash.Hash)`n"
            
            # Save hash to separate file
            $HashFile = $BackupFile + ".sha256"
            $Hash.Hash | Out-File -FilePath $HashFile -Encoding ASCII -NoNewline
            Write-Host "Hash saved to: $HashFile" -ForegroundColor Green
        }
    } else {
        Write-Host "ERROR: Backup failed with exit code $($process.ExitCode)" -ForegroundColor Red
        $LogContent += "ERROR: Backup failed with exit code $($process.ExitCode)`n"
        
        # Read error output if available
        if (Test-Path ($LogFile + ".err")) {
            $ErrorOutput = Get-Content ($LogFile + ".err") -Raw
            Write-Host "Error output:" -ForegroundColor Red
            Write-Host $ErrorOutput -ForegroundColor Red
            $LogContent += "Error output:`n$ErrorOutput`n"
        }
        
        $LogContent | Out-File -FilePath $LogFile -Encoding UTF8
        exit 1
    }
} catch {
    Write-Host "ERROR: Exception during backup: $_" -ForegroundColor Red
    $LogContent += "ERROR: Exception during backup: $_`n"
    $LogContent | Out-File -FilePath $LogFile -Encoding UTF8
    exit 1
}

# Verify backup integrity
if ($Verify) {
    Write-Host ""
    Write-Host "Verifying backup integrity..." -ForegroundColor Yellow
    
    try {
        # Use pg_restore --list to verify backup file structure
        $pgRestoreArgs = @(
            "--list",
            $BackupFile
        )
        
        $process = Start-Process -FilePath "pg_restore" -ArgumentList $pgRestoreArgs -NoNewWindow -Wait -PassThru -RedirectStandardOutput ($LogFile + ".list") -RedirectStandardError ($LogFile + ".list.err")
        
        if ($process.ExitCode -eq 0) {
            # Count tables/objects in backup
            $ListContent = Get-Content ($LogFile + ".list")
            $TableCount = ($ListContent | Where-Object { $_ -match "TABLE DATA" }).Count
            
            Write-Host "Backup verification passed!" -ForegroundColor Green
            Write-Host "Tables found in backup: $TableCount" -ForegroundColor Green
            $LogContent += "`nBackup verification: PASSED`n"
            $LogContent += "Tables in backup: $TableCount`n"
            
            # Clean up verification files
            Remove-Item ($LogFile + ".list") -ErrorAction SilentlyContinue
            Remove-Item ($LogFile + ".list.err") -ErrorAction SilentlyContinue
        } else {
            Write-Host "WARNING: Backup verification failed" -ForegroundColor Yellow
            Write-Host "The backup file may be corrupted" -ForegroundColor Yellow
            $LogContent += "`nBackup verification: FAILED`n"
            
            if (Test-Path ($LogFile + ".list.err")) {
                $VerifyError = Get-Content ($LogFile + ".list.err") -Raw
                Write-Host "Verification error: $VerifyError" -ForegroundColor Red
                $LogContent += "Verification error: $VerifyError`n"
            }
        }
    } catch {
        Write-Host "WARNING: Could not verify backup: $_" -ForegroundColor Yellow
        $LogContent += "`nBackup verification: ERROR - $_`n"
    }
}

# Clean up error file if empty
if (Test-Path ($LogFile + ".err")) {
    $ErrorContent = Get-Content ($LogFile + ".err") -Raw
    if ([string]::IsNullOrWhiteSpace($ErrorContent)) {
        Remove-Item ($LogFile + ".err") -ErrorAction SilentlyContinue
    }
}

# Save log file
$LogContent += "`nBackup completed successfully.`n"
$LogContent | Out-File -FilePath $LogFile -Encoding UTF8

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backup Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backup file: $BackupFile" -ForegroundColor Green
Write-Host "Log file: $LogFile" -ForegroundColor Green
Write-Host ""
Write-Host "To restore this backup, run:" -ForegroundColor Yellow
Write-Host "  pg_restore -U $DbUser -d $DbName -c $BackupFile" -ForegroundColor Cyan
Write-Host ""

# List recent backups
Write-Host "Recent backups in $BackupDir :" -ForegroundColor Yellow
Get-ChildItem -Path $BackupDir -Filter "*.dump" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | ForEach-Object {
    $SizeMB = [math]::Round($_.Length / 1MB, 2)
    Write-Host "  $($_.Name) - $SizeMB MB - $($_.LastWriteTime.ToString('yyyy-MM-dd HH:mm'))"
}

exit 0

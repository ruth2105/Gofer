# Quick test summary script
$modules = @('accounts', 'scholarships', 'opportunities', 'applications', 'students', 'common', 'consultations', 'notifications', 'documents')
$totalTests = 0
$totalPassed = 0
$totalFailed = 0

Write-Host "`n=== Gofer Exam Test Summary ===`n" -ForegroundColor Cyan

foreach ($module in $modules) {
    Write-Host "Testing apps.$module..." -NoNewline
    $output = python manage.py test "apps.$module.tests" --keepdb 2>&1 | Out-String
    
    if ($output -match 'Ran (\d+) test') {
        $count = [int]$matches[1]
        $totalTests += $count
        
        if ($output -match 'OK') {
            Write-Host " $count PASS" -ForegroundColor Green
            $totalPassed += $count
        } elseif ($output -match 'FAILED \(failures=(\d+)\)') {
            $failures = [int]$matches[1]
            $passed = $count - $failures
            Write-Host " $passed PASS, $failures FAIL" -ForegroundColor Yellow
            $totalPassed += $passed
            $totalFailed += $failures
        } elseif ($output -match 'Found 0 test') {
            Write-Host " 0 tests found" -ForegroundColor Gray
        } else {
            Write-Host " ERROR" -ForegroundColor Red
        }
    } else {
        Write-Host " Could not parse results" -ForegroundColor Red
    }
}

Write-Host "`n=== TOTAL: $totalTests tests ===" -ForegroundColor Cyan
Write-Host "PASSED: $totalPassed" -ForegroundColor Green
if ($totalFailed -gt 0) {
    Write-Host "FAILED: $totalFailed" -ForegroundColor Red
}

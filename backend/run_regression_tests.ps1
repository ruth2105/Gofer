# Comprehensive Backend Regression Test Suite
# Runs all test modules and records results

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$resultsDir = "test_results_$timestamp"
New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "GOFER EXAM - REGRESSION TEST SUITE" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "Results will be saved to: $resultsDir" -ForegroundColor Cyan
Write-Host ""

$testModules = @(
    @{Name="Accounts"; Path="apps.accounts.tests"},
    @{Name="Scholarships"; Path="apps.scholarships.tests"},
    @{Name="Opportunities"; Path="apps.opportunities.tests"},
    @{Name="Applications"; Path="apps.applications.tests"},
    @{Name="Students"; Path="apps.students.tests"},
    @{Name="Common/Permissions"; Path="apps.common.tests"},
    @{Name="Consultations"; Path="apps.consultations.tests"},
    @{Name="Documents"; Path="apps.documents.tests"},
    @{Name="Notifications"; Path="apps.notifications.tests"}
)

$results = @()

foreach ($module in $testModules) {
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "Testing: $($module.Name)" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    
    $outputFile = "$resultsDir/$($module.Name.Replace('/', '_'))_output.txt"
    
    $startTime = Get-Date
    
    # Run tests and capture output
    $testOutput = python manage.py test $($module.Path) --keepdb --verbosity=2 2>&1 | Tee-Object -FilePath $outputFile
    $exitCode = $LASTEXITCODE
    
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    # Parse results
    $passed = $false
    $testCount = 0
    $errorCount = 0
    $failureCount = 0
    
    foreach ($line in $testOutput) {
        if ($line -match "Ran (\d+) test") {
            $testCount = [int]$matches[1]
        }
        if ($line -match "OK") {
            $passed = $true
        }
        if ($line -match "FAILED.*failures=(\d+)") {
            $failureCount = [int]$matches[1]
        }
        if ($line -match "errors=(\d+)") {
            $errorCount = [int]$matches[1]
        }
    }
    
    $status = if ($exitCode -eq 0 -and $passed) { "PASS" } else { "FAIL" }
    $color = if ($status -eq "PASS") { "Green" } else { "Red" }
    
    Write-Host ""
    Write-Host "Module: $($module.Name)" -ForegroundColor White
    Write-Host "Status: $status" -ForegroundColor $color
    Write-Host "Tests Run: $testCount" -ForegroundColor White
    Write-Host "Duration: $([math]::Round($duration, 2))s" -ForegroundColor White
    if ($failureCount -gt 0) {
        Write-Host "Failures: $failureCount" -ForegroundColor Red
    }
    if ($errorCount -gt 0) {
        Write-Host "Errors: $errorCount" -ForegroundColor Red
    }
    Write-Host ""
    
    $results += @{
        Module = $module.Name
        Path = $module.Path
        Status = $status
        TestCount = $testCount
        Failures = $failureCount
        Errors = $errorCount
        Duration = [math]::Round($duration, 2)
        ExitCode = $exitCode
        OutputFile = $outputFile
    }
}

# Run full test suite
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Running Full Test Suite" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$fullOutputFile = "$resultsDir/full_suite_output.txt"
$startTime = Get-Date

$fullOutput = python manage.py test --keepdb --verbosity=2 2>&1 | Tee-Object -FilePath $fullOutputFile
$fullExitCode = $LASTEXITCODE

$endTime = Get-Date
$fullDuration = ($endTime - $startTime).TotalSeconds

$fullTestCount = 0
$fullPassed = $false

foreach ($line in $fullOutput) {
    if ($line -match "Ran (\d+) test") {
        $fullTestCount = [int]$matches[1]
    }
    if ($line -match "OK") {
        $fullPassed = $true
    }
}

$fullStatus = if ($fullExitCode -eq 0 -and $fullPassed) { "PASS" } else { "FAIL" }
$fullColor = if ($fullStatus -eq "PASS") { "Green" } else { "Red" }

Write-Host ""
Write-Host "Full Suite Status: $fullStatus" -ForegroundColor $fullColor
Write-Host "Total Tests: $fullTestCount" -ForegroundColor White
Write-Host "Duration: $([math]::Round($fullDuration, 2))s" -ForegroundColor White
Write-Host ""

$results += @{
    Module = "FULL SUITE"
    Path = "all"
    Status = $fullStatus
    TestCount = $fullTestCount
    Failures = 0
    Errors = 0
    Duration = [math]::Round($fullDuration, 2)
    ExitCode = $fullExitCode
    OutputFile = $fullOutputFile
}

# Summary
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "TEST SUMMARY" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

$passedModules = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$failedModules = ($results | Where-Object { $_.Status -eq "FAIL" }).Count
$totalModules = $results.Count

Write-Host "Total Modules: $totalModules" -ForegroundColor White
Write-Host "Passed: $passedModules" -ForegroundColor Green
Write-Host "Failed: $failedModules" -ForegroundColor Red
Write-Host ""

Write-Host "Module Results:" -ForegroundColor White
foreach ($result in $results) {
    $color = if ($result.Status -eq "PASS") { "Green" } else { "Red" }
    $symbol = if ($result.Status -eq "PASS") { "[PASS]" } else { "[FAIL]" }
    Write-Host "$symbol $($result.Module): $($result.TestCount) tests in $($result.Duration)s" -ForegroundColor $color
}

# Save summary
$results | ConvertTo-Json -Depth 5 | Out-File "$resultsDir/summary.json"
Write-Host ""
Write-Host "Summary saved to: $resultsDir/summary.json" -ForegroundColor Cyan

if ($failedModules -eq 0) {
    Write-Host ""
    Write-Host "[SUCCESS] ALL TESTS PASSED" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "[FAILURE] SOME TESTS FAILED" -ForegroundColor Red
    Write-Host "Check output files in $resultsDir/ for details" -ForegroundColor Yellow
    exit 1
}

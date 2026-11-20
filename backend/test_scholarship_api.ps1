# Test Scholarship Public API
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SCHOLARSHIP API VERIFICATION TEST" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Test 1: List all scholarships
Write-Host "`n[TEST 1] List All Scholarships" -ForegroundColor Yellow
$response = curl.exe -s "http://localhost:8000/api/v1/scholarships/" | ConvertFrom-Json
Write-Host "Count: $($response.count)" -ForegroundColor Green
Write-Host "Results: $($response.results.Count)" -ForegroundColor Green
$response.results | ForEach-Object {
    Write-Host "  - $($_.name) ($($_.provider))" -ForegroundColor White
}

# Test 2: Pagination
Write-Host "`n[TEST 2] Pagination (page_size=2)" -ForegroundColor Yellow
$response = curl.exe -s "http://localhost:8000/api/v1/scholarships/?page_size=2" | ConvertFrom-Json
Write-Host "Count: $($response.count)" -ForegroundColor Green
Write-Host "Results on page: $($response.results.Count)" -ForegroundColor Green
Write-Host "Next: $($response.next -ne $null)" -ForegroundColor Green

# Test 3: Filter by level
Write-Host "`n[TEST 3] Filter by Level (UNDERGRADUATE)" -ForegroundColor Yellow
$response = curl.exe -s "http://localhost:8000/api/v1/scholarships/?level=UNDERGRADUATE" | ConvertFrom-Json
Write-Host "Count: $($response.count)" -ForegroundColor Green
$response.results | ForEach-Object {
    Write-Host "  - $($_.name) (Level: $($_.level))" -ForegroundColor White
}

# Test 4: Filter by type
Write-Host "`n[TEST 4] Filter by Type (MERIT)" -ForegroundColor Yellow
$response = curl.exe -s "http://localhost:8000/api/v1/scholarships/?type=MERIT" | ConvertFrom-Json
Write-Host "Count: $($response.count)" -ForegroundColor Green
$response.results | ForEach-Object {
    Write-Host "  - $($_.name) (Type: $($_.type))" -ForegroundColor White
}

# Test 5: Search
Write-Host "`n[TEST 5] Search (query=Foundation)" -ForegroundColor Yellow
$response = curl.exe -s "http://localhost:8000/api/v1/scholarships/?search=Foundation" | ConvertFrom-Json
Write-Host "Count: $($response.count)" -ForegroundColor Green
$response.results | ForEach-Object {
    Write-Host "  - $($_.name) ($($_.provider))" -ForegroundColor White
}

# Test 6: Get single scholarship details
Write-Host "`n[TEST 6] Get Scholarship Details" -ForegroundColor Yellow
$listResponse = curl.exe -s "http://localhost:8000/api/v1/scholarships/" | ConvertFrom-Json
if ($listResponse.results.Count -gt 0) {
    $slug = $listResponse.results[0].slug
    Write-Host "Fetching: $slug" -ForegroundColor Cyan
    $detail = curl.exe -s "http://localhost:8000/api/v1/scholarships/$slug/" | ConvertFrom-Json
    Write-Host "Name: $($detail.name)" -ForegroundColor Green
    Write-Host "Provider: $($detail.provider)" -ForegroundColor Green
    Write-Host "Amount: $($detail.amount)" -ForegroundColor Green
    Write-Host "Level: $($detail.level)" -ForegroundColor Green
    Write-Host "Deadline: $($detail.application_deadline)" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ALL TESTS COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

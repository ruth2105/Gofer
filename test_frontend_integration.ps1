# Frontend-Backend Integration Test Script
# Tests that frontend can communicate with backend APIs

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "GOFER EXAM - Frontend Integration Tests" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$backendUrl = "http://localhost:8000"
$frontendUrl = "http://localhost:3000"
$passed = 0
$failed = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200
    )
    
    Write-Host "Testing: $Name..." -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host " [PASS]" -ForegroundColor Green
            return $true
        } else {
            Write-Host " [FAIL] Expected $ExpectedStatus, got $($response.StatusCode)" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host " [FAIL] $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-CorsHeaders {
    param(
        [string]$Url
    )
    
    Write-Host "Testing: CORS headers..." -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method OPTIONS -Headers @{
            "Origin" = $frontendUrl
            "Access-Control-Request-Method" = "POST"
        } -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        
        $headers = $response.Headers
        $allowOrigin = $headers["Access-Control-Allow-Origin"]
        $allowCredentials = $headers["Access-Control-Allow-Credentials"]
        
        if ($allowOrigin -like "*localhost:3000*" -and $allowCredentials -eq "true") {
            Write-Host " [PASS]" -ForegroundColor Green
            return $true
        } else {
            Write-Host " [FAIL] CORS not configured correctly" -ForegroundColor Red
            Write-Host "        Allow-Origin: $allowOrigin" -ForegroundColor Yellow
            Write-Host "        Allow-Credentials: $allowCredentials" -ForegroundColor Yellow
            return $false
        }
    }
    catch {
        Write-Host " [FAIL] $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-CsrfToken {
    Write-Host "Testing: CSRF token endpoint..." -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri "$backendUrl/api/v1/auth/csrf/" -Method GET -SessionVariable session -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        
        if ($response.StatusCode -eq 200 -and $session.Cookies.GetCookies($backendUrl).Count -gt 0) {
            Write-Host " [PASS]" -ForegroundColor Green
            return $true
        } else {
            Write-Host " [FAIL] CSRF cookie not set" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host " [FAIL] $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Test 1: Backend Server Running
Write-Host "`n[1] Backend Server Tests" -ForegroundColor Yellow
Write-Host "=" * 40

if (Test-Endpoint "Backend health check" "$backendUrl/api/v1/health/") {
    $script:passed++
} else {
    $script:failed++
    Write-Host "`n  ERROR: Backend server not responding!" -ForegroundColor Red
    Write-Host "  Start it with: cd backend; python manage.py runserver 8000`n" -ForegroundColor Yellow
}

if (Test-Endpoint "Backend API root" "$backendUrl/api/v1/") {
    $script:passed++
} else {
    $script:failed++
}

# Test 2: Frontend Server Running
Write-Host "`n[2] Frontend Server Tests" -ForegroundColor Yellow
Write-Host "=" * 40

if (Test-Endpoint "Frontend homepage" "$frontendUrl/") {
    $script:passed++
} else {
    $script:failed++
    Write-Host "`n  ERROR: Frontend server not responding!" -ForegroundColor Red
    Write-Host "  Start it with: npm run dev`n" -ForegroundColor Yellow
}

# Test 3: Authentication Endpoints
Write-Host "`n[3] Authentication API Tests" -ForegroundColor Yellow
Write-Host "=" * 40

if (Test-CsrfToken) {
    $script:passed++
} else {
    $script:failed++
}

if (Test-Endpoint "Registration endpoint" "$backendUrl/api/v1/auth/register/" 405) {
    $script:passed++
    Write-Host "        (405 expected for GET, endpoint exists)" -ForegroundColor Gray
} else {
    $script:failed++
}

if (Test-Endpoint "Login endpoint" "$backendUrl/api/v1/auth/login/" 405) {
    $script:passed++
    Write-Host "        (405 expected for GET, endpoint exists)" -ForegroundColor Gray
} else {
    $script:failed++
}

if (Test-Endpoint "Password reset endpoint" "$backendUrl/api/v1/auth/password/reset/" 405) {
    $script:passed++
    Write-Host "        (405 expected for GET, endpoint exists)" -ForegroundColor Gray
} else {
    $script:failed++
}

# Test 4: CORS Configuration
Write-Host "`n[4] CORS Configuration Tests" -ForegroundColor Yellow
Write-Host "=" * 40

if (Test-CorsHeaders "$backendUrl/api/v1/auth/login/") {
    $script:passed++
} else {
    $script:failed++
    Write-Host "`n  ERROR: CORS not configured correctly!" -ForegroundColor Red
    Write-Host "  Check backend/config/settings/development.py" -ForegroundColor Yellow
    Write-Host "  Ensure CORS_ALLOWED_ORIGINS includes 'http://localhost:3000'`n" -ForegroundColor Yellow
}

# Test 5: Public API Endpoints
Write-Host "`n[5] Public API Tests" -ForegroundColor Yellow
Write-Host "=" * 40

if (Test-Endpoint "Scholarships list" "$backendUrl/api/v1/scholarships/") {
    $script:passed++
} else {
    $script:failed++
}

if (Test-Endpoint "Opportunities list" "$backendUrl/api/v1/opportunities/") {
    $script:passed++
} else {
    $script:failed++
}

if (Test-Endpoint "Countries list" "$backendUrl/api/v1/countries/") {
    $script:passed++
} else {
    $script:failed++
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host "Total:  $($passed + $failed)" -ForegroundColor White

if ($failed -eq 0) {
    Write-Host "`n[SUCCESS] All integration tests passed!" -ForegroundColor Green
    Write-Host "`nNext Steps:" -ForegroundColor Yellow
    Write-Host "1. Open browser to http://localhost:3000" -ForegroundColor Gray
    Write-Host "2. Test registration: http://localhost:3000/auth/register" -ForegroundColor Gray
    Write-Host "3. Test login: http://localhost:3000/auth/login" -ForegroundColor Gray
    Write-Host "4. Follow FRONTEND_TESTING_GUIDE.md for manual testing" -ForegroundColor Gray
} else {
    Write-Host "`n[FAILURE] Some tests failed. Fix the issues above before proceeding." -ForegroundColor Red
}

Write-Host ""

exit $(if ($failed -eq 0) { 0 } else { 1 })

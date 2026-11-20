# Comprehensive Authentication Integration Test
# Tests all authentication flows with proper CSRF handling

$ErrorActionPreference = "Stop"
$results = @()

function Test-Endpoint {
    param($name, $method, $url, $body, $session, $csrfToken, $expectStatus)
    
    Write-Host "`n=== Testing: $name ===" -ForegroundColor Cyan
    
    try {
        $headers = @{
            "Content-Type" = "application/json"
            "Origin" = "http://localhost:3000"
            "Referer" = "http://localhost:3000/"
        }
        
        if ($csrfToken) {
            $headers["X-CSRFToken"] = $csrfToken
        }
        
        $params = @{
            Uri = $url
            Method = $method
            Headers = $headers
        }
        
        if ($session) {
            $params["WebSession"] = $session
        }
        
        if ($body) {
            $params["Body"] = ($body | ConvertTo-Json -Compress)
        }
        
        $response = Invoke-WebRequest @params -ErrorAction Stop
        
        Write-Host "[OK] Status: $($response.StatusCode)" -ForegroundColor Green
        
        $result = @{
            Name = $name
            Status = "PASS"
            StatusCode = $response.StatusCode
            Expected = $expectStatus
            Response = ($response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue)
        }
        
        return $result
        
    } catch {
        Write-Host "[FAIL] Failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Response: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        
        $statusCode = 0
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
        
        return @{
            Name = $name
            Status = "FAIL"
            StatusCode = $statusCode
            Expected = $expectStatus
            Error = $_.Exception.Message
            Response = $_.ErrorDetails.Message
        }
    }
}

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "GOFER EXAM - AUTHENTICATION INTEGRATION TEST" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta

# Test 1: CSRF Token Retrieval
Write-Host "`n### TEST 1: CSRF Token Retrieval ###" -ForegroundColor Yellow
$csrfResult = Test-Endpoint -name "Get CSRF Token" -method GET -url "http://localhost:8000/api/v1/auth/csrf/" -expectStatus 200

if ($csrfResult.Status -eq "PASS") {
    $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
    $csrfResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/csrf/" -Method GET -SessionVariable session
    $csrfData = $csrfResponse.Content | ConvertFrom-Json
    $csrfToken = $csrfData.csrfToken
    
    Write-Host "CSRF Token: $($csrfToken.Substring(0,20))..." -ForegroundColor Green
    Write-Host "Cookie Count: $($session.Cookies.Count)" -ForegroundColor Green
    
    $csrfResult.CsrfToken = $csrfToken.Substring(0,20) + "..."
    $csrfResult.CookiePresent = $session.Cookies.Count -gt 0
}
$results += $csrfResult

# Test 2: Registration
Write-Host "`n### TEST 2: User Registration ###" -ForegroundColor Yellow
$timestamp = Get-Date -Format 'yyyyMMddHHmmss'
$regBody = @{
    email = "verify_test_${timestamp}@test.local"
    password = "TestPass123!@#"
    password2 = "TestPass123!@#"
    first_name = "Verify"
    last_name = "Test"
    phone_number = "+1234567890"
}
$regResult = Test-Endpoint -name "Registration" -method POST -url "http://localhost:8000/api/v1/auth/register/" -body $regBody -session $session -csrfToken $csrfToken -expectStatus 201

if ($regResult.Status -eq "PASS" -and $regResult.Response) {
    Write-Host "User ID: $($regResult.Response.user.id)" -ForegroundColor Green
    Write-Host "Email: $($regResult.Response.user.email)" -ForegroundColor Green
    Write-Host "Is Verified: $($regResult.Response.user.is_verified)" -ForegroundColor Green
    $regResult.UserEmail = $regResult.Response.user.email
    $regResult.IsVerified = $regResult.Response.user.is_verified
}
$results += $regResult

# Test 3: Login with existing user
Write-Host "`n### TEST 3: User Login ###" -ForegroundColor Yellow
$loginBody = @{
    email = "student_test_functional@test.local"
    password = "TestPass123!@#"
}
$loginResult = Test-Endpoint -name "Login" -method POST -url "http://localhost:8000/api/v1/auth/login/" -body $loginBody -session $session -csrfToken $csrfToken -expectStatus 200

if ($loginResult.Status -eq "PASS" -and $loginResult.Response) {
    Write-Host "Access Token Present: $($null -ne $loginResult.Response.access)" -ForegroundColor Green
    Write-Host "Refresh Token Present: $($null -ne $loginResult.Response.refresh)" -ForegroundColor Green
    Write-Host "User Email: $($loginResult.Response.user.email)" -ForegroundColor Green
    $loginResult.HasAccessToken = $null -ne $loginResult.Response.access
    $loginResult.HasRefreshToken = $null -ne $loginResult.Response.refresh
    $accessToken = $loginResult.Response.access
}
$results += $loginResult

# Test 4: Get Current User (authenticated)
if ($accessToken) {
    Write-Host "`n### TEST 4: Get Current User (Authenticated) ###" -ForegroundColor Yellow
    try {
        $meResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/me/" -Method GET -Headers @{
            "Authorization" = "Bearer $accessToken"
            "Origin" = "http://localhost:3000"
        }
        $meData = $meResponse.Content | ConvertFrom-Json
        Write-Host "[OK] Status: $($meResponse.StatusCode)" -ForegroundColor Green
        Write-Host "User: $($meData.email) (Role: $($meData.role))" -ForegroundColor Green
        
        $meResult = @{
            Name = "Get Current User"
            Status = "PASS"
            StatusCode = $meResponse.StatusCode
            Expected = 200
            UserEmail = $meData.email
            UserRole = $meData.role
        }
    } catch {
        Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
        $meResult = @{
            Name = "Get Current User"
            Status = "FAIL"
            StatusCode = [int]$_.Exception.Response.StatusCode
            Expected = 200
            Error = $_.Exception.Message
        }
    }
    $results += $meResult
}

# Test 5: Logout
if ($accessToken) {
    Write-Host "`n### TEST 5: Logout ###" -ForegroundColor Yellow
    try {
        $logoutBody = @{
            refresh = $loginResult.Response.refresh
        } | ConvertTo-Json
        
        $logoutResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/logout/" -Method POST -Headers @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $accessToken"
            "Origin" = "http://localhost:3000"
            "X-CSRFToken" = $csrfToken
        } -Body $logoutBody -WebSession $session
        
        Write-Host "[OK] Status: $($logoutResponse.StatusCode)" -ForegroundColor Green
        
        $logoutResult = @{
            Name = "Logout"
            Status = "PASS"
            StatusCode = $logoutResponse.StatusCode
            Expected = 200
        }
    } catch {
        Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
        $logoutResult = @{
            Name = "Logout"
            Status = "FAIL"
            StatusCode = [int]$_.Exception.Response.StatusCode
            Expected = 200
            Error = $_.Exception.Message
        }
    }
    $results += $logoutResult
}

# Test 6: Password Reset Request
Write-Host "`n### TEST 6: Password Reset Request ###" -ForegroundColor Yellow
$resetBody = @{
    email = "student_test_functional@test.local"
}
$resetResult = Test-Endpoint -name "Password Reset Request" -method POST -url "http://localhost:8000/api/v1/auth/password/reset/" -body $resetBody -session $session -csrfToken $csrfToken -expectStatus 200
$results += $resetResult

# Test 7: Resend Verification Email
Write-Host "`n### TEST 7: Resend Verification Email ###" -ForegroundColor Yellow
$resendBody = @{
    email = "verify_test_${timestamp}@test.local"
}
$resendResult = Test-Endpoint -name "Resend Verification" -method POST -url "http://localhost:8000/api/v1/auth/resend-verification/" -body $resendBody -session $session -csrfToken $csrfToken -expectStatus 200
$results += $resendResult

# Summary
Write-Host "`n========================================" -ForegroundColor Magenta
Write-Host "TEST SUMMARY" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta

$passed = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$failed = ($results | Where-Object { $_.Status -eq "FAIL" }).Count
$total = $results.Count

Write-Host "`nTotal Tests: $total" -ForegroundColor White
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red

Write-Host "`nDetailed Results:" -ForegroundColor White
foreach ($result in $results) {
    $color = if ($result.Status -eq "PASS") { "Green" } else { "Red" }
    $symbol = if ($result.Status -eq "PASS") { "[PASS]" } else { "[FAIL]" }
    Write-Host "$symbol $($result.Name): $($result.Status) (HTTP $($result.StatusCode))" -ForegroundColor $color
}

# Save results to JSON
$results | ConvertTo-Json -Depth 5 | Out-File "auth_integration_results.json"
Write-Host "`nResults saved to: auth_integration_results.json" -ForegroundColor Cyan

if ($failed -eq 0) {
    Write-Host "`n[SUCCESS] ALL TESTS PASSED" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n[FAILURE] SOME TESTS FAILED" -ForegroundColor Red
    exit 1
}

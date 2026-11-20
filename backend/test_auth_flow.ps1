# Test authentication flow with proper CSRF handling

# Step 1: Get CSRF token
Write-Host "=== Step 1: Getting CSRF Token ===" -ForegroundColor Cyan
$csrfResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/csrf/" `
    -Method GET `
    -SessionVariable session `
    -Headers @{
        "Origin" = "http://localhost:3000"
    }

$csrfData = $csrfResponse.Content | ConvertFrom-Json
$csrfToken = $csrfData.csrfToken
Write-Host "CSRF Token obtained: $($csrfToken.Substring(0,20))..." -ForegroundColor Green

# Step 2: Test Registration
Write-Host "`n=== Step 2: Testing Registration ===" -ForegroundColor Cyan
$timestamp = Get-Date -Format 'yyyyMMddHHmmss'
$registrationBody = @{
    email = "flow_test_${timestamp}@test.local"
    password = "TestPass123!@#"
    password2 = "TestPass123!@#"
    first_name = "Flow"
    last_name = "Test"
    phone_number = "+1234567890"
} | ConvertTo-Json

try {
    $regResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/register/" `
        -Method POST `
        -WebSession $session `
        -Headers @{
            "Content-Type" = "application/json"
            "Origin" = "http://localhost:3000"
            "Referer" = "http://localhost:3000/"
            "X-CSRFToken" = $csrfToken
        } `
        -Body $registrationBody

    Write-Host "Registration Status: $($regResponse.StatusCode)" -ForegroundColor Green
    $regData = $regResponse.Content | ConvertFrom-Json
    Write-Host "User created: $($regData.user.email)" -ForegroundColor Green
} catch {
    Write-Host "Registration failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Response: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
}

# Step 3: Test Login with existing user
Write-Host "`n=== Step 3: Testing Login ===" -ForegroundColor Cyan
$loginBody = @{
    email = "student_test_functional@test.local"
    password = "TestPass123!@#"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login/" `
        -Method POST `
        -WebSession $session `
        -Headers @{
            "Content-Type" = "application/json"
            "Origin" = "http://localhost:3000"
            "Referer" = "http://localhost:3000/"
            "X-CSRFToken" = $csrfToken
        } `
        -Body $loginBody

    Write-Host "Login Status: $($loginResponse.StatusCode)" -ForegroundColor Green
    $loginData = $loginResponse.Content | ConvertFrom-Json
    Write-Host "Login successful for: $($loginData.user.email)" -ForegroundColor Green
} catch {
    Write-Host "Login failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Response: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan

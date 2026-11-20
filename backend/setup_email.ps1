# Email Setup Helper for GOFER EXAM (PowerShell)
# This script helps you configure email backends for development/staging

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "GOFER EXAM - Email Configuration Setup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (Test-Path ".env") {
    Write-Host "ℹ️  Found existing .env file" -ForegroundColor Yellow
    $update = Read-Host "Do you want to update it? (y/n)"
    if ($update -ne "y") {
        Write-Host "Exiting without changes." -ForegroundColor Gray
        exit 0
    }
    Write-Host ""
}

Write-Host "Choose your email backend:" -ForegroundColor White
Write-Host ""
Write-Host "1. Console (Development) - Prints emails to terminal" -ForegroundColor Gray
Write-Host "2. File (Development) - Saves emails as .eml files" -ForegroundColor Gray
Write-Host "3. Gmail SMTP (Development/Staging) - Real emails via Gmail" -ForegroundColor Gray
Write-Host "4. Brevo (Staging/Production) - Transactional email service" -ForegroundColor Gray
Write-Host "5. Custom SMTP (Staging/Production) - Other SMTP provider" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Enter your choice (1-5)"
Write-Host ""

switch ($choice) {
    "1" {
        Write-Host "Selected: Console Backend" -ForegroundColor Green
        Add-Content -Path ".env" -Value "EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend"
        Write-Host "✅ Configuration added to .env" -ForegroundColor Green
        Write-Host "Emails will be printed to your terminal." -ForegroundColor Gray
    }
    
    "2" {
        Write-Host "Selected: File Backend" -ForegroundColor Green
        $emailDir = Read-Host "Enter directory path (default: ./email_output)"
        if ([string]::IsNullOrWhiteSpace($emailDir)) {
            $emailDir = "./email_output"
        }
        
        Add-Content -Path ".env" -Value "EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend"
        Add-Content -Path ".env" -Value "EMAIL_FILE_PATH=$emailDir"
        
        New-Item -ItemType Directory -Path $emailDir -Force | Out-Null
        Write-Host "✅ Configuration added to .env" -ForegroundColor Green
        Write-Host "✅ Created directory: $emailDir" -ForegroundColor Green
        Write-Host "Emails will be saved as .eml files in $emailDir" -ForegroundColor Gray
    }
    
    "3" {
        Write-Host "Selected: Gmail SMTP" -ForegroundColor Green
        Write-Host ""
        Write-Host "📝 You'll need:" -ForegroundColor Yellow
        Write-Host "   1. Your Gmail address" -ForegroundColor Gray
        Write-Host "   2. An App Password (NOT your regular password)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "To get an App Password:" -ForegroundColor Yellow
        Write-Host "   1. Go to https://myaccount.google.com/security" -ForegroundColor Gray
        Write-Host "   2. Enable 2-Step Verification (if not already)" -ForegroundColor Gray
        Write-Host "   3. Go to 'App passwords'" -ForegroundColor Gray
        Write-Host "   4. Generate a password for 'Mail'" -ForegroundColor Gray
        Write-Host "   5. Use that 16-character password below" -ForegroundColor Gray
        Write-Host ""
        
        $gmailUser = Read-Host "Gmail address"
        $gmailPass = Read-Host "App Password (16 chars, no spaces)" -AsSecureString
        $gmailPassPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($gmailPass)
        )
        
        @"
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=$gmailUser
EMAIL_HOST_PASSWORD=$gmailPassPlain
GOFER_EMAIL_FROM=$gmailUser
"@ | Add-Content -Path ".env"
        
        Write-Host "✅ Gmail SMTP configuration added to .env" -ForegroundColor Green
    }
    
    "4" {
        Write-Host "Selected: Brevo Backend" -ForegroundColor Green
        Write-Host ""
        Write-Host "📝 You'll need:" -ForegroundColor Yellow
        Write-Host "   1. Brevo API key (starts with 'xkeysib-')" -ForegroundColor Gray
        Write-Host "   2. Verified sender email" -ForegroundColor Gray
        Write-Host ""
        Write-Host "To get started:" -ForegroundColor Yellow
        Write-Host "   1. Sign up at https://www.brevo.com/" -ForegroundColor Gray
        Write-Host "   2. Verify your sender email" -ForegroundColor Gray
        Write-Host "   3. Get API key from Settings → SMTP & API" -ForegroundColor Gray
        Write-Host ""
        
        $brevoKey = Read-Host "Brevo API Key"
        $senderEmail = Read-Host "Sender email (verified in Brevo)"
        
        @"
EMAIL_BACKEND=config.email_backends.brevo.BrevoEmailBackend
BREVO_API_KEY=$brevoKey
GOFER_EMAIL_FROM=$senderEmail
"@ | Add-Content -Path ".env"
        
        Write-Host "✅ Brevo configuration added to .env" -ForegroundColor Green
    }
    
    "5" {
        Write-Host "Selected: Custom SMTP" -ForegroundColor Green
        Write-Host ""
        
        $smtpHost = Read-Host "SMTP Host (e.g., smtp.sendgrid.net)"
        $smtpPortInput = Read-Host "SMTP Port (default: 587)"
        $smtpPort = if ([string]::IsNullOrWhiteSpace($smtpPortInput)) { "587" } else { $smtpPortInput }
        
        $useTlsInput = Read-Host "Use TLS? (y/n, default: y)"
        $useTls = if ([string]::IsNullOrWhiteSpace($useTlsInput) -or $useTlsInput -eq "y") { "True" } else { "False" }
        
        $smtpUser = Read-Host "SMTP Username"
        $smtpPass = Read-Host "SMTP Password" -AsSecureString
        $smtpPassPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($smtpPass)
        )
        $fromEmail = Read-Host "From email address"
        
        @"
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=$smtpHost
EMAIL_PORT=$smtpPort
EMAIL_USE_TLS=$useTls
EMAIL_USE_SSL=False
EMAIL_HOST_USER=$smtpUser
EMAIL_HOST_PASSWORD=$smtpPassPlain
GOFER_EMAIL_FROM=$fromEmail
"@ | Add-Content -Path ".env"
        
        Write-Host "✅ Custom SMTP configuration added to .env" -ForegroundColor Green
    }
    
    default {
        Write-Host "❌ Invalid choice" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Configuration Complete!" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart your Django development server" -ForegroundColor Gray
Write-Host "2. Test the configuration:" -ForegroundColor Gray
Write-Host "   python test_email_config.py --to your-email@example.com" -ForegroundColor White
Write-Host ""
Write-Host "For detailed testing guide, see:" -ForegroundColor Yellow
Write-Host "   EMAIL_TESTING_GUIDE.md" -ForegroundColor White
Write-Host ""

#!/bin/bash
# Email Setup Helper for GOFER EXAM
# This script helps you configure email backends for development/staging

set -e

echo "=================================================="
echo "GOFER EXAM - Email Configuration Setup"
echo "=================================================="
echo ""

# Check if .env exists
if [ -f ".env" ]; then
    echo "ℹ️  Found existing .env file"
    read -p "Do you want to update it? (y/n): " update_env
    if [ "$update_env" != "y" ]; then
        echo "Exiting without changes."
        exit 0
    fi
    echo ""
fi

echo "Choose your email backend:"
echo ""
echo "1. Console (Development) - Prints emails to terminal"
echo "2. File (Development) - Saves emails as .eml files"
echo "3. Gmail SMTP (Development/Staging) - Real emails via Gmail"
echo "4. Brevo (Staging/Production) - Transactional email service"
echo "5. Custom SMTP (Staging/Production) - Other SMTP provider"
echo ""

read -p "Enter your choice (1-5): " choice
echo ""

case $choice in
    1)
        echo "Selected: Console Backend"
        echo "EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend" >> .env
        echo "✅ Configuration added to .env"
        echo "Emails will be printed to your terminal."
        ;;
    
    2)
        echo "Selected: File Backend"
        read -p "Enter directory path (default: ./email_output): " email_dir
        email_dir=${email_dir:-./email_output}
        
        echo "EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend" >> .env
        echo "EMAIL_FILE_PATH=$email_dir" >> .env
        
        mkdir -p "$email_dir"
        echo "✅ Configuration added to .env"
        echo "✅ Created directory: $email_dir"
        echo "Emails will be saved as .eml files in $email_dir"
        ;;
    
    3)
        echo "Selected: Gmail SMTP"
        echo ""
        echo "📝 You'll need:"
        echo "   1. Your Gmail address"
        echo "   2. An App Password (NOT your regular password)"
        echo ""
        echo "To get an App Password:"
        echo "   1. Go to https://myaccount.google.com/security"
        echo "   2. Enable 2-Step Verification (if not already)"
        echo "   3. Go to 'App passwords'"
        echo "   4. Generate a password for 'Mail'"
        echo "   5. Use that 16-character password below"
        echo ""
        
        read -p "Gmail address: " gmail_user
        read -sp "App Password (16 chars, no spaces): " gmail_pass
        echo ""
        
        {
            echo "EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend"
            echo "EMAIL_HOST=smtp.gmail.com"
            echo "EMAIL_PORT=587"
            echo "EMAIL_USE_TLS=True"
            echo "EMAIL_USE_SSL=False"
            echo "EMAIL_HOST_USER=$gmail_user"
            echo "EMAIL_HOST_PASSWORD=$gmail_pass"
            echo "GOFER_EMAIL_FROM=$gmail_user"
        } >> .env
        
        echo "✅ Gmail SMTP configuration added to .env"
        ;;
    
    4)
        echo "Selected: Brevo Backend"
        echo ""
        echo "📝 You'll need:"
        echo "   1. Brevo API key (starts with 'xkeysib-')"
        echo "   2. Verified sender email"
        echo ""
        echo "To get started:"
        echo "   1. Sign up at https://www.brevo.com/"
        echo "   2. Verify your sender email"
        echo "   3. Get API key from Settings → SMTP & API"
        echo ""
        
        read -p "Brevo API Key: " brevo_key
        read -p "Sender email (verified in Brevo): " sender_email
        
        {
            echo "EMAIL_BACKEND=config.email_backends.brevo.BrevoEmailBackend"
            echo "BREVO_API_KEY=$brevo_key"
            echo "GOFER_EMAIL_FROM=$sender_email"
        } >> .env
        
        echo "✅ Brevo configuration added to .env"
        ;;
    
    5)
        echo "Selected: Custom SMTP"
        echo ""
        
        read -p "SMTP Host (e.g., smtp.sendgrid.net): " smtp_host
        read -p "SMTP Port (default: 587): " smtp_port
        smtp_port=${smtp_port:-587}
        
        read -p "Use TLS? (y/n, default: y): " use_tls
        use_tls=${use_tls:-y}
        
        read -p "SMTP Username: " smtp_user
        read -sp "SMTP Password: " smtp_pass
        echo ""
        read -p "From email address: " from_email
        
        {
            echo "EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend"
            echo "EMAIL_HOST=$smtp_host"
            echo "EMAIL_PORT=$smtp_port"
            echo "EMAIL_USE_TLS=$([ "$use_tls" = "y" ] && echo True || echo False)"
            echo "EMAIL_USE_SSL=False"
            echo "EMAIL_HOST_USER=$smtp_user"
            echo "EMAIL_HOST_PASSWORD=$smtp_pass"
            echo "GOFER_EMAIL_FROM=$from_email"
        } >> .env
        
        echo "✅ Custom SMTP configuration added to .env"
        ;;
    
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=================================================="
echo "Configuration Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Restart your Django development server"
echo "2. Test the configuration:"
echo "   python test_email_config.py --to your-email@example.com"
echo ""
echo "For detailed testing guide, see:"
echo "   EMAIL_TESTING_GUIDE.md"
echo ""

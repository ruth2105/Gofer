# Frontend Testing Guide - GOFER EXAM

This guide provides step-by-step instructions for testing the frontend application, particularly the authentication flows.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Starting the Application](#starting-the-application)
3. [Testing Registration Flow](#testing-registration-flow)
4. [Testing Login Flow](#testing-login-flow)
5. [Testing Password Reset Flow](#testing-password-reset-flow)
6. [Testing CSRF Protection](#testing-csrf-protection)
7. [Browser Testing Checklist](#browser-testing-checklist)
8. [Automated Testing](#automated-testing)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Backend Requirements
- PostgreSQL database running
- Django backend server running on `http://localhost:8000`
- All migrations applied
- Environment variables configured (`.env` file)

### Frontend Requirements
- Node.js and npm installed
- Dependencies installed (`npm install`)
- Frontend configuration (`.env.local` or `.env`)

### Verification Commands

**Check Backend:**
```bash
# From gofer-exam/backend/
python manage.py check
curl http://localhost:8000/api/v1/health/
```

**Check Frontend:**
```bash
# From gofer-exam/
npm run build  # Should complete without errors
```

---

## Starting the Application

### 1. Start Backend Server

```bash
cd gofer-exam/backend

# Activate virtual environment (if using venv)
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Start Django development server
python manage.py runserver 8000
```

**Expected Output:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### 2. Start Frontend Server

```bash
cd gofer-exam

# Start Next.js development server
npm run dev
```

**Expected Output:**
```
▲ Next.js 16.x.x (Turbopack)
- Local:        http://localhost:3000
- Network:      http://192.168.x.x:3000

✓ Ready in X.Xs
```

### 3. Verify Both Servers Running

```bash
# Check backend health
curl http://localhost:8000/api/v1/health/

# Check frontend homepage
curl http://localhost:3000/
```

---

## Testing Registration Flow

### Manual Browser Testing

**1. Navigate to Registration Page**
- Open browser: `http://localhost:3000/auth/register`
- Or click "Sign Up" / "Register" link from homepage

**2. Inspect Page Elements**
- ✅ Registration form visible
- ✅ Fields present: Email, Password, Confirm Password, First Name, Last Name
- ✅ "Register" or "Sign Up" button visible
- ✅ Link to login page ("Already have an account?")
- ✅ No console errors (open browser DevTools with F12)

**3. Test Form Validation (Client-Side)**

Test empty fields:
- Leave all fields empty
- Click "Register"
- ✅ Validation errors appear
- ✅ Error messages are clear

Test invalid email:
- Email: `notanemail`
- Other fields: valid
- Click "Register"
- ✅ Email validation error appears

Test password mismatch:
- Password: `SecurePass123!`
- Confirm Password: `DifferentPass456!`
- Click "Register"
- ✅ Password mismatch error appears

Test weak password:
- Password: `123`
- Confirm Password: `123`
- Click "Register"
- ✅ Weak password error appears (should require length, complexity)

**4. Test Successful Registration**

Fill in valid data:
- **Email:** `testuser@example.com`
- **Password:** `SecurePass123!`
- **Confirm Password:** `SecurePass123!`
- **First Name:** `Test`
- **Last Name:** `User`

Click "Register"

**Expected Behavior:**
- ✅ Form submits without frontend errors
- ✅ Loading indicator appears during submission
- ✅ Success message appears ("Check your email for verification link")
- ✅ Redirected to verification pending page or login page
- ✅ No CORS errors in console (F12 → Console tab)
- ✅ Network request to backend succeeds (F12 → Network tab)
  - Request URL: `http://localhost:8000/api/v1/auth/register/`
  - Status: 201 Created
  - Response includes user data

**Verify Backend:**
- Check Django console for verification email output
- Email should be printed to console (if using console backend)
- Email should contain verification link

**5. Test Duplicate Email**
- Try registering with same email again
- ✅ Error message: "A user with this email already exists"
- ✅ Status code: 400 Bad Request

**6. Test Email Verification Link**
- Copy verification link from console/email
- Format: `http://localhost:3000/verify-email?token=<TOKEN>`
- Click or paste link into browser
- ✅ Redirects to verification success page
- ✅ Success message: "Email verified successfully"
- ✅ Link to login page

---

## Testing Login Flow

### Manual Browser Testing

**1. Navigate to Login Page**
- Open browser: `http://localhost:3000/auth/login`
- Or click "Login" / "Sign In" link

**2. Inspect Page Elements**
- ✅ Login form visible
- ✅ Fields present: Email, Password
- ✅ "Login" or "Sign In" button visible
- ✅ "Forgot Password?" link visible
- ✅ Link to registration ("Don't have an account?")
- ✅ No console errors

**3. Test Login with Invalid Credentials**

Test non-existent user:
- Email: `nonexistent@example.com`
- Password: `AnyPassword123!`
- Click "Login"
- ✅ Error message: "Invalid credentials"
- ✅ Status: 400 Bad Request

Test wrong password:
- Email: `testuser@example.com` (existing user)
- Password: `WrongPassword456!`
- Click "Login"
- ✅ Error message: "Invalid credentials"
- ✅ User is NOT logged in

**4. Test Successful Login**

Use verified account:
- Email: `testuser@example.com`
- Password: `SecurePass123!`
- Click "Login"

**Expected Behavior:**
- ✅ Form submits without errors
- ✅ Loading indicator during submission
- ✅ Redirects to homepage or dashboard
- ✅ User menu/profile visible in header
- ✅ No CORS errors in console
- ✅ Network request succeeds (F12 → Network tab)
  - Request URL: `http://localhost:8000/api/v1/auth/login/`
  - Status: 200 OK
  - Response includes access/refresh tokens
  - Cookies set: `gofer_access`, `gofer_refresh`

**Verify Authentication State:**
- Check Application tab in DevTools (F12 → Application → Cookies)
- ✅ Cookies present: `gofer_access`, `gofer_refresh`, `csrftoken`
- ✅ Cookies have `HttpOnly`, `Secure` (if HTTPS), `SameSite` flags

**Test Authenticated Endpoints:**
- Navigate to protected page (e.g., profile, applications)
- ✅ Page loads successfully
- ✅ User data displayed
- ✅ No 401 Unauthorized errors

**5. Test Logout**
- Click "Logout" button in user menu
- ✅ Redirects to homepage or login
- ✅ User menu disappears
- ✅ Auth cookies removed
- ✅ Visiting protected pages redirects to login

**6. Test "Remember Me" (if implemented)**
- Login with "Remember Me" checked
- Close browser completely
- Reopen browser
- Visit `http://localhost:3000`
- ✅ Still logged in (if feature implemented)

---

## Testing Password Reset Flow

### Manual Browser Testing

**1. Navigate to Forgot Password Page**
- Click "Forgot Password?" link on login page
- Or visit: `http://localhost:3000/auth/forgot-password`

**2. Request Password Reset**

Enter email:
- Email: `testuser@example.com`
- Click "Send Reset Link"

**Expected Behavior:**
- ✅ Success message: "Check your email for password reset link"
- ✅ Network request succeeds (202 Accepted)
- ✅ Backend console shows reset email (if using console backend)

**3. Test with Non-Existent Email**
- Email: `doesnotexist@example.com`
- Click "Send Reset Link"
- ✅ Same success message (security: don't reveal if email exists)
- ✅ Status: 202 Accepted (always)

**4. Test Password Reset Link**
- Copy reset link from console/email
- Format: `http://localhost:3000/auth/reset-password?token=<TOKEN>`
- Click or paste link
- ✅ Redirects to password reset form
- ✅ Form has: New Password, Confirm Password fields

**5. Reset Password**

Enter new password:
- New Password: `NewSecurePass789!`
- Confirm Password: `NewSecurePass789!`
- Click "Reset Password"

**Expected Behavior:**
- ✅ Success message: "Password reset successfully"
- ✅ Redirects to login page
- ✅ Can log in with new password
- ✅ Cannot use old password

**6. Test Invalid/Expired Token**
- Use same reset link again
- ✅ Error: "Invalid or expired reset link"
- ✅ Link to request new reset

---

## Testing CSRF Protection

### Verify CSRF Tokens

**1. Check CSRF Cookie**
- Open DevTools (F12) → Application → Cookies
- Visit any page
- ✅ `csrftoken` cookie present
- ✅ Has value (64-char hex string)

**2. Check CSRF Header in Requests**
- Open DevTools (F12) → Network tab
- Perform registration or login
- Click on the request
- Go to "Headers" tab
- ✅ `X-CSRFToken` header present
- ✅ Value matches `csrftoken` cookie

**3. Test CSRF Protection**

Try request without CSRF token (using curl):
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

**Expected:**
- ✅ Status: 403 Forbidden
- ✅ Error: "CSRF token missing or incorrect"

---

## Browser Testing Checklist

### Desktop Browsers

Test in multiple browsers:
- [ ] **Chrome/Edge** (Chromium)
- [ ] **Firefox**
- [ ] **Safari** (if on Mac)

For each browser, verify:
- [ ] Registration works
- [ ] Login works
- [ ] Logout works
- [ ] Password reset works
- [ ] Cookies are set correctly
- [ ] No console errors
- [ ] Forms validate properly
- [ ] UI looks correct (no layout issues)

### Mobile/Responsive Testing

Test responsive design:
- [ ] Open DevTools → Toggle device toolbar (Ctrl+Shift+M)
- [ ] Test at various screen sizes:
  - [ ] Mobile (375px)
  - [ ] Tablet (768px)
  - [ ] Desktop (1920px)

Verify:
- [ ] Forms are usable on mobile
- [ ] Buttons are clickable (not too small)
- [ ] Text is readable (proper font sizes)
- [ ] No horizontal scrolling
- [ ] Navigation menu works on mobile

### Accessibility Testing

Basic accessibility checks:
- [ ] Tab through forms (keyboard navigation)
- [ ] All inputs have labels
- [ ] Error messages are announced (screen readers)
- [ ] Color contrast is sufficient
- [ ] Forms work without JavaScript (progressive enhancement)

Run automated accessibility audit:
- [ ] Open DevTools → Lighthouse tab
- [ ] Run audit on login/register pages
- [ ] Fix critical issues (ARIA labels, alt text, etc.)

---

## Automated Testing

### Frontend Integration Tests

Create a test script: `test_frontend_integration.js`

```javascript
// Test registration endpoint integration
const testRegistration = async () => {
  const response = await fetch('http://localhost:8000/api/v1/auth/register/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    credentials: 'include',
    body: JSON.stringify({
      email: `test${Date.now()}@example.com`,
      password: 'SecurePass123!',
      first_name: 'Test',
      last_name: 'User',
    }),
  });
  
  console.log('Registration:', response.status);
  return response.status === 201;
};

// Test login endpoint integration
const testLogin = async () => {
  const response = await fetch('http://localhost:8000/api/v1/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    credentials: 'include',
    body: JSON.stringify({
      email: 'existinguser@example.com',
      password: 'SecurePass123!',
    }),
  });
  
  console.log('Login:', response.status);
  return response.status === 200;
};

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

// Run tests
(async () => {
  await testRegistration();
  await testLogin();
})();
```

### Playwright/Puppeteer E2E Tests

For comprehensive testing, consider setting up E2E tests:

```bash
npm install -D @playwright/test
npx playwright install
```

Create `tests/auth.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test('registration flow', async ({ page }) => {
  await page.goto('http://localhost:3000/auth/register');
  
  await page.fill('input[name="email"]', 'testuser@example.com');
  await page.fill('input[name="password"]', 'SecurePass123!');
  await page.fill('input[name="confirmPassword"]', 'SecurePass123!');
  await page.fill('input[name="firstName"]', 'Test');
  await page.fill('input[name="lastName"]', 'User');
  
  await page.click('button[type="submit"]');
  
  await expect(page).toHaveURL(/verify-email|dashboard/);
});

test('login flow', async ({ page }) => {
  await page.goto('http://localhost:3000/auth/login');
  
  await page.fill('input[name="email"]', 'testuser@example.com');
  await page.fill('input[name="password"]', 'SecurePass123!');
  
  await page.click('button[type="submit"]');
  
  await expect(page).toHaveURL('http://localhost:3000/');
  await expect(page.locator('text=Logout')).toBeVisible();
});
```

Run tests:
```bash
npx playwright test
```

---

## Troubleshooting

### Issue: CORS Errors in Console

**Symptoms:**
```
Access to fetch at 'http://localhost:8000/api/v1/auth/login/' from origin 
'http://localhost:3000' has been blocked by CORS policy
```

**Fix:**
1. Check `backend/config/settings/development.py`:
   ```python
   CORS_ALLOWED_ORIGINS = [
       'http://localhost:3000',
       'http://127.0.0.1:3000',
   ]
   ```

2. Restart Django server

### Issue: CSRF Token Errors

**Symptoms:**
```
403 Forbidden: CSRF token missing or incorrect
```

**Fix:**
1. Verify `CSRF_TRUSTED_ORIGINS` includes frontend URL
2. Check frontend sends `X-CSRFToken` header
3. Ensure cookies are sent with `credentials: 'include'`
4. Clear browser cookies and try again

### Issue: "Network Error" or Request Fails

**Checklist:**
- [ ] Backend server running on port 8000?
  ```bash
  curl http://localhost:8000/api/v1/health/
  ```
- [ ] Frontend server running on port 3000?
  ```bash
  curl http://localhost:3000/
  ```
- [ ] Firewall blocking ports?
- [ ] Check browser console for error details

### Issue: Authentication Cookies Not Set

**Check:**
1. DevTools → Application → Cookies
2. Look for `gofer_access` and `gofer_refresh`
3. If missing, check:
   - Login request succeeded (200 OK)?
   - Response headers include `Set-Cookie`?
   - Browser allows third-party cookies?

**Fix:**
- Ensure `credentials: 'include'` in fetch requests
- Check `CORS_ALLOW_CREDENTIALS = True` in Django settings
- Verify cookie domain/path matches

### Issue: Cannot Access Protected Routes

**Symptoms:**
- Logged in but protected pages redirect to login
- Or show "Unauthorized" error

**Check:**
1. Cookies present in Application tab?
2. Network requests include cookies?
3. Backend validates tokens correctly?

**Test Backend:**
```bash
# Get access token from cookie (in browser console)
document.cookie

# Test with curl
curl http://localhost:8000/api/v1/auth/me/ \
  -H "Cookie: gofer_access=<TOKEN>" \
  -H "X-CSRFToken: <CSRF_TOKEN>"
```

### Issue: Verification Email Not Received

**For Development (Console Backend):**
- Check Django console output
- Email should be printed there
- Copy verification link manually

**For Staging (Real Email):**
- Check spam folder
- Verify sender email in provider dashboard
- Check provider logs for delivery status
- Test email backend:
  ```bash
  python backend/test_email_config.py --to your-email@example.com
  ```

---

## Summary Checklist

Before marking frontend testing complete:

### Core Functionality
- [ ] Registration form works
- [ ] Registration validation works (client + server)
- [ ] Email verification works
- [ ] Login form works
- [ ] Authentication persists across page refreshes
- [ ] Logout works
- [ ] Password reset request works
- [ ] Password reset completion works
- [ ] Protected routes are actually protected

### Security
- [ ] CSRF protection active
- [ ] Cookies have security flags
- [ ] No sensitive data in localStorage
- [ ] No credentials in URL parameters
- [ ] HTTPS redirects working (in staging/prod)

### User Experience
- [ ] Loading states visible during requests
- [ ] Error messages clear and helpful
- [ ] Success messages clear
- [ ] Forms validate before submission
- [ ] Responsive on mobile devices
- [ ] Accessible (keyboard navigation, screen readers)

### Technical
- [ ] No console errors
- [ ] No CORS errors
- [ ] Network requests succeed
- [ ] Proper status codes returned
- [ ] Cookies set correctly
- [ ] API integration working

---

## Next Steps

After completing frontend testing:

1. **Document any issues found** in GitHub Issues or bug tracker
2. **Fix critical blockers** before deployment
3. **Run full backend test suite** to ensure no regressions
4. **Perform security review** of authentication implementation
5. **Test on staging environment** with real email delivery
6. **Get stakeholder approval** before production deployment

---

**Need Help?**
- Review backend logs for errors
- Check Django admin for user records
- Test API endpoints directly with curl/Postman
- See `backend/EMAIL_TESTING_GUIDE.md` for email issues
- See `DEPLOYMENT_GUIDE.md` for deployment help

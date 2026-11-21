# Gofer Exam Platform - End-to-End Test Plan

**Date:** November 2, 2026  
**Version:** 1.0  
**Purpose:** Comprehensive testing strategy for complete platform verification  
**Scope:** All 13 modules from user and admin perspectives  

---

## Test Plan Overview

**Test Types:**
1. **Functional Tests:** Feature works as designed
2. **Integration Tests:** Components work together
3. **User Acceptance Tests:** Real user workflows
4. **Security Tests:** Authentication, authorization, data protection
5. **Performance Tests:** Speed, load handling, scalability
6. **Accessibility Tests:** WCAG compliance, screen readers
7. **Cross-browser Tests:** Browser compatibility

**Test Environments:**
- **Local:** Developer testing (http://localhost:3000)
- **Staging:** Pre-production testing (staging.goferexam.com)
- **Production:** Final verification (goferexam.com)

---

## Test Execution Guidelines

### Before Testing

**Prerequisites:**
```bash
# Backend
✅ Database populated with test data
✅ Email backend configured (console or SMTP)
✅ File storage configured (LOCAL or S3)
✅ All environment variables set
✅ Migrations applied

# Frontend
✅ API_PROXY_TARGET set correctly
✅ Next.js build successful
✅ No console errors on page load

# Test Data
✅ 50+ scholarships
✅ 20+ opportunities (jobs/internships)
✅ 10+ destinations
✅ 5+ services
✅ 3 test users (student, consultant, admin)
```

### Test Data Setup Script

```python
# backend/scripts/create_test_data.py
from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.scholarships.models import Scholarship
from apps.opportunities.models import Opportunity
# ... etc

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Create test users
        student = User.objects.create_user(
            email='student@test.com',
            password='Test123!@#',
            role='STUDENT',
            is_verified=True
        )
        
        consultant = User.objects.create_user(
            email='consultant@test.com',
            password='Test123!@#',
            role='CONSULTANT',
            is_verified=True
        )
        
        admin = User.objects.create_user(
            email='admin@test.com',
            password='Test123!@#',
            role='ADMIN',
            is_staff=True,
            is_superuser=True,
            is_verified=True
        )
        
        # Create 50 scholarships
        for i in range(50):
            Scholarship.objects.create(
                title=f'Test Scholarship {i+1}',
                description='Test description...',
                # ... etc
            )
        
        self.stdout.write(self.success('Test data created'))
```

### Test Credentials

```
STUDENT ACCOUNT:
Email: student@test.com
Password: Test123!@#

CONSULTANT ACCOUNT:
Email: consultant@test.com
Password: Test123!@#

ADMIN ACCOUNT:
Email: admin@test.com
Password: Test123!@#
```

**⚠️ SECURITY:** Never use these credentials in production!

---

## Module 1: Public Website Tests

### TEST-PW-001: Homepage Load
**Priority:** 🔴 CRITICAL  
**Type:** Functional

**Steps:**
1. Navigate to homepage (/)
2. Wait for page to fully load

**Expected Results:**
- ✅ Page loads in <3 seconds
- ✅ No JavaScript console errors
- ✅ All images load successfully
- ✅ Hero section visible
- ✅ Featured scholarships display (at least 3)
- ✅ Navigation menu present and functional
- ✅ Footer present with links

**Actual Results:** _[To be filled during testing]_

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Pass | ❌ Fail

---

### TEST-PW-002: Navigation Links
**Priority:** 🔴 CRITICAL  
**Type:** Functional

**Steps:**
1. From homepage, click each navigation link:
   - About
   - Scholarships
   - Study Abroad
   - Exam Prep
   - Services
   - Contact

**Expected Results:**
- ✅ Each link navigates to correct page
- ✅ No 404 errors
- ✅ Page content loads
- ✅ Back button works

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-PW-003: Responsive Design
**Priority:** 🟠 HIGH  
**Type:** UI/UX

**Test Devices:**
- Desktop (1920x1080)
- Tablet (768x1024)
- Mobile (375x667 - iPhone SE)
- Mobile landscape (667x375)

**Steps:**
1. Open homepage on each device/viewport
2. Check layout, images, text readability
3. Test navigation menu (hamburger on mobile)
4. Scroll through page

**Expected Results:**
- ✅ Content readable on all devices
- ✅ Images scale properly
- ✅ No horizontal scroll
- ✅ Buttons/links easily tappable (48x48px minimum)
- ✅ Mobile menu works

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-PW-004: Featured Scholarships
**Priority:** 🟠 HIGH  
**Type:** Integration

**Prerequisites:**
- At least 3 scholarships marked as `featured=True`

**Steps:**
1. Navigate to homepage
2. Locate "Featured Scholarships" section
3. Verify scholarships displayed
4. Click "View Details" on one scholarship

**Expected Results:**
- ✅ Featured scholarships display (3-6 cards)
- ✅ Each card shows: title, provider, deadline, amount
- ✅ "View Details" navigates to scholarship detail page
- ✅ Data matches database

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-PW-005: External Links
**Priority:** 🟡 MEDIUM  
**Type:** Functional

**Steps:**
1. Identify all external links on homepage
2. Click each link
3. Verify opens in new tab

**Expected Results:**
- ✅ External links open in new tab
- ✅ rel="noopener noreferrer" attribute present (security)
- ✅ Links are valid (not 404)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

## Module 2: Registration & Authentication Tests

### TEST-AUTH-001: Student Registration (Happy Path)
**Priority:** 🔴 CRITICAL  
**Type:** End-to-End

**Steps:**
1. Navigate to /student/register
2. Fill in registration form:
   - Email: `newstudent@test.com`
   - Password: `SecurePass123!`
   - Confirm Password: `SecurePass123!`
   - First Name: `John`
   - Last Name: `Doe`
3. Submit form
4. Check console/email for verification link
5. Click verification link
6. Confirm account verified

**Expected Results:**
- ✅ Form validates input
- ✅ "Registration successful" message displayed
- ✅ Verification email sent (check console or inbox)
- ✅ Email contains verification link
- ✅ Clicking link marks account as verified
- ✅ Redirect to login page after verification
- ✅ Can log in with verified account

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-AUTH-002: Registration Validation
**Priority:** 🔴 CRITICAL  
**Type:** Functional

**Test Cases:**

**2a. Invalid Email:**
- Input: `notanemail`
- Expected: "Please enter a valid email address"

**2b. Weak Password:**
- Input: `123`
- Expected: "Password must be at least 8 characters"

**2c. Password Mismatch:**
- Password: `SecurePass123!`
- Confirm: `DifferentPass123!`
- Expected: "Passwords do not match"

**2d. Duplicate Email:**
- Email: `student@test.com` (already exists)
- Expected: "Email already registered"

**2e. Empty Fields:**
- Submit with empty fields
- Expected: "This field is required" for each empty field

**Actual Results:** _[To be filled for each case]_

**Status:** ⬜

---

### TEST-AUTH-003: Login (Happy Path)
**Priority:** 🔴 CRITICAL  
**Type:** End-to-End

**Prerequisites:**
- Verified account exists: `student@test.com` / `Test123!@#`

**Steps:**
1. Navigate to /student/login
2. Enter email: `student@test.com`
3. Enter password: `Test123!@#`
4. Click "Login"

**Expected Results:**
- ✅ Login successful
- ✅ JWT tokens stored in cookies
- ✅ Redirect to student dashboard
- ✅ User name displayed in navigation
- ✅ "Logout" button visible

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-AUTH-004: Login Validation
**Priority:** 🟠 HIGH  
**Type:** Functional

**Test Cases:**

**4a. Invalid Credentials:**
- Email: `student@test.com`
- Password: `WrongPassword`
- Expected: "Invalid email or password"
- Status: HTTP 401

**4b. Unverified Account:**
- Email: `unverified@test.com` (registered but not verified)
- Password: `Test123!@#`
- Expected: "Please verify your email address"
- Status: HTTP 403

**4c. Empty Fields:**
- Submit with empty email or password
- Expected: "This field is required"

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-AUTH-005: Rate Limiting
**Priority:** 🟠 HIGH  
**Type:** Security

**Steps:**
1. Attempt to login with wrong password 11 times in a row
2. Observe response

**Expected Results:**
- ✅ First 10 attempts: "Invalid credentials" (HTTP 401)
- ✅ 11th attempt: "Too many login attempts. Try again in 1 hour" (HTTP 429)
- ✅ Account not locked (correct password works after 1 hour)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-AUTH-006: Password Reset
**Priority:** 🟠 HIGH  
**Type:** End-to-End

**Steps:**
1. Navigate to /student/forgot-password
2. Enter email: `student@test.com`
3. Submit
4. Check console/email for reset link
5. Click reset link
6. Enter new password: `NewSecurePass123!`
7. Confirm password: `NewSecurePass123!`
8. Submit
9. Navigate to login
10. Login with new password

**Expected Results:**
- ✅ "Password reset email sent" message
- ✅ Email received with reset link
- ✅ Reset link valid (not expired)
- ✅ New password accepted
- ✅ "Password reset successful" message
- ✅ Can login with new password
- ✅ Cannot login with old password

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-AUTH-007: Password Reset Security
**Priority:** 🔴 CRITICAL  
**Type:** Security

**Test Cases:**

**7a. Expired Token:**
- Use reset token created >60 minutes ago
- Expected: "Reset link has expired"

**7b. Used Token:**
- Use same reset token twice
- Expected: "Reset link already used"

**7c. Invalid Token:**
- Modify token in URL
- Expected: "Invalid reset link"

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-AUTH-008: Logout
**Priority:** 🟠 HIGH  
**Type:** Functional

**Prerequisites:**
- User logged in

**Steps:**
1. Click "Logout" button in navigation
2. Observe redirect
3. Try to access protected page (e.g., /student/dashboard)

**Expected Results:**
- ✅ Logout successful
- ✅ Redirect to homepage
- ✅ User name no longer in navigation
- ✅ Tokens cleared from cookies
- ✅ Cannot access protected pages (redirect to login)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-AUTH-009: Session Persistence
**Priority:** 🟡 MEDIUM  
**Type:** Functional

**Prerequisites:**
- User logged in

**Steps:**
1. Login as student
2. Close browser tab (not entire browser)
3. Open new tab
4. Navigate to /student/dashboard

**Expected Results:**
- ✅ Still logged in (session persisted)
- ✅ Dashboard accessible without re-login

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-AUTH-010: Token Refresh
**Priority:** 🟡 MEDIUM  
**Type:** Integration

**Steps:**
1. Login as student
2. Wait 16 minutes (access token expires after 15 min)
3. Make an API request (e.g., load profile)

**Expected Results:**
- ✅ Access token automatically refreshed
- ✅ API request succeeds
- ✅ No re-login required

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

## Module 3: Student Dashboard Tests

### TEST-DASH-001: Profile Creation
**Priority:** 🔴 CRITICAL  
**Type:** End-to-End

**Prerequisites:**
- Logged in as student with incomplete profile

**Steps:**
1. Navigate to /student/profile
2. Fill in all fields:
   - Date of Birth: 1995-05-15
   - Gender: Male
   - Phone: +1234567890
   - Address: 123 Main St
   - City: New York
   - Country: United States
   - Postal Code: 10001
3. Click "Save Profile"

**Expected Results:**
- ✅ All fields save successfully
- ✅ "Profile updated successfully" message
- ✅ profile_completed flag set to True
- ✅ Data persists on page reload

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-DASH-002: Profile Editing
**Priority:** 🟠 HIGH  
**Type:** Functional

**Prerequisites:**
- Complete profile exists

**Steps:**
1. Navigate to /student/profile
2. Change phone number to +9876543210
3. Click "Save Profile"
4. Reload page

**Expected Results:**
- ✅ Phone number updated
- ✅ Other fields unchanged
- ✅ Updated data displays on reload

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-DASH-003: Education History (Add)
**Priority:** 🟠 HIGH  
**Type:** CRUD

**Steps:**
1. Navigate to /student/profile
2. Scroll to "Education History" section
3. Click "Add Education"
4. Fill in:
   - Institution: Harvard University
   - Degree: Bachelor of Science
   - Field of Study: Computer Science
   - Start Date: 2015-09
   - End Date: 2019-05
   - Grade: 3.8 GPA
5. Click "Save"

**Expected Results:**
- ✅ Education entry added
- ✅ Displays in education list
- ✅ Can edit entry
- ✅ Can delete entry

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-DASH-004: Work Experience (Add)
**Priority:** 🟠 HIGH  
**Type:** CRUD

**Steps:**
1. Navigate to /student/profile
2. Scroll to "Work Experience" section
3. Click "Add Experience"
4. Fill in:
   - Company: Google
   - Position: Software Engineer
   - Start Date: 2019-06
   - End Date: Leave blank
   - Currently Working: ✅ Check
   - Description: Working on...
5. Click "Save"

**Expected Results:**
- ✅ Work experience added
- ✅ "Present" shown for end date
- ✅ Displays in experience list

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-DASH-005: Skills (Add/Remove)
**Priority:** 🟡 MEDIUM  
**Type:** CRUD

**Steps:**
1. Navigate to /student/profile
2. Scroll to "Skills" section
3. Click "Add Skill"
4. Enter skill: Python
5. Select proficiency: Advanced
6. Click "Save"
7. Add 2 more skills
8. Delete one skill

**Expected Results:**
- ✅ Skills add successfully
- ✅ Proficiency levels display
- ✅ Can delete skills
- ✅ Changes persist

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-DASH-006: Profile Completion Indicator
**Priority:** 🟡 MEDIUM  
**Type:** UI/UX

**Steps:**
1. Create new student account
2. Navigate to dashboard
3. Observe profile completion percentage
4. Add profile info step by step
5. Observe percentage increase

**Expected Results:**
- ✅ Initial: 20% (email only)
- ✅ After basic info: 50%
- ✅ After contact info: 70%
- ✅ After education: 85%
- ✅ After skills: 100%
- ✅ Visual progress bar updates

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

## Module 4: Scholarships Tests

### TEST-SCHOL-001: Browse Scholarships
**Priority:** 🔴 CRITICAL  
**Type:** Functional

**Prerequisites:**
- At least 50 scholarships in database

**Steps:**
1. Navigate to /scholarships
2. Observe scholarship list

**Expected Results:**
- ✅ Scholarships display as cards
- ✅ Each card shows: title, provider, amount, deadline, country
- ✅ Pagination controls present
- ✅ 10-20 scholarships per page
- ✅ Images load (or placeholder)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-SCHOL-002: Scholarship Detail Page
**Priority:** 🔴 CRITICAL  
**Type:** Functional

**Steps:**
1. From scholarship list, click first scholarship
2. View detail page

**Expected Results:**
- ✅ Full description visible
- ✅ Eligibility criteria listed
- ✅ Application deadline prominent
- ✅ "Apply Now" or "Visit Official Site" button
- ✅ Amount and currency displayed
- ✅ Scholarship level (Undergrad/Master/PhD)
- ✅ Field of study shown

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-SCHOL-003: Search Scholarships
**Priority:** 🟠 HIGH  
**Type:** Functional

**Steps:**
1. Navigate to /scholarships
2. Enter search term: "Engineering"
3. Submit search

**Expected Results:**
- ✅ Results filter to scholarships containing "Engineering"
- ✅ Search in title, description, field_of_study
- ✅ Case-insensitive search
- ✅ Search term persists in search box
- ✅ Can clear search

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-SCHOL-004: Filter by Country
**Priority:** 🟠 HIGH  
**Type:** Functional

**Steps:**
1. Navigate to /scholarships
2. Select country filter: "United States"
3. Apply filter

**Expected Results:**
- ✅ Only US scholarships displayed
- ✅ Filter chip/badge shown
- ✅ Can remove filter
- ✅ URL updates with filter param (?country=USA)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-SCHOL-005: Filter by Level
**Priority:** 🟠 HIGH  
**Type:** Functional

**Steps:**
1. Navigate to /scholarships
2. Select level filter: "Master"
3. Apply filter

**Expected Results:**
- ✅ Only Master's scholarships displayed
- ✅ Can combine with other filters
- ✅ Filter persists on pagination

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-SCHOL-006: Combined Filters
**Priority:** 🟠 HIGH  
**Type:** Integration

**Steps:**
1. Navigate to /scholarships
2. Apply multiple filters:
   - Country: Canada
   - Level: PhD
   - Type: Full Scholarship
   - Field: Computer Science
3. Observe results

**Expected Results:**
- ✅ Results match ALL filters (AND logic)
- ✅ No results if no match (show empty state)
- ✅ All filter chips visible
- ✅ Can remove individual filters

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-SCHOL-007: Sort Scholarships
**Priority:** 🟡 MEDIUM  
**Type:** Functional

**Steps:**
1. Navigate to /scholarships
2. Test each sort option:
   - Deadline (soonest first)
   - Amount (highest first)
   - Recently added

**Expected Results:**
- ✅ Results reorder correctly
- ✅ Sort persists on pagination
- ✅ Sort + filters work together

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-SCHOL-008: Pagination
**Priority:** 🟠 HIGH  
**Type:** Functional

**Steps:**
1. Navigate to /scholarships
2. Click "Next" page
3. Click "Previous" page
4. Click specific page number

**Expected Results:**
- ✅ Pagination controls work
- ✅ Scroll to top on page change
- ✅ URL updates with page param (?page=2)
- ✅ Browser back/forward buttons work
- ✅ Current page highlighted

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-SCHOL-009: External Application Link
**Priority:** 🟠 HIGH  
**Type:** Functional

**Steps:**
1. Open scholarship detail page
2. Click "Apply on Official Site" button

**Expected Results:**
- ✅ Opens external link in new tab
- ✅ rel="noopener noreferrer" for security
- ✅ URL valid (not 404)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

## Module 5: Applications Tests

### TEST-APP-001: Create Application (Draft)
**Priority:** 🔴 CRITICAL  
**Type:** End-to-End

**Prerequisites:**
- Logged in as student
- Profile completed

**Steps:**
1. Navigate to scholarship detail page
2. Click "Apply" button
3. Fill application form:
   - Motivation letter (200+ words)
   - Additional info (optional)
4. Click "Save Draft"

**Expected Results:**
- ✅ Draft saved with status=DRAFT
- ✅ "Application saved as draft" message
- ✅ Can navigate away and return to edit
- ✅ Draft appears in "My Applications" with DRAFT badge

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-APP-002: Submit Application
**Priority:** 🔴 CRITICAL  
**Type:** End-to-End

**Prerequisites:**
- Draft application exists

**Steps:**
1. Navigate to draft application
2. Review details
3. Click "Submit Application"
4. Confirm submission

**Expected Results:**
- ✅ Status changes to SUBMITTED
- ✅ submitted_at timestamp recorded
- ✅ "Application submitted successfully" message
- ✅ Cannot edit after submission
- ✅ Email notification sent (check console)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-APP-003: Application Validation
**Priority:** 🟠 HIGH  
**Type:** Functional

**Test Cases:**

**3a. Empty Motivation Letter:**
- Submit with empty letter
- Expected: "Motivation letter is required"

**3b. Short Motivation Letter:**
- Submit with <50 words
- Expected: "Motivation letter must be at least 50 words"

**3c. Incomplete Profile:**
- Student with incomplete profile tries to apply
- Expected: "Please complete your profile before applying"

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-APP-004: View Application List
**Priority:** 🟠 HIGH  
**Type:** Functional

**Prerequisites:**
- Student has 5+ applications

**Steps:**
1. Navigate to /student/applications
2. View list of applications

**Expected Results:**
- ✅ All applications displayed
- ✅ Each shows: scholarship name, status, date
- ✅ Status badges color-coded (DRAFT=gray, SUBMITTED=blue, APPROVED=green, REJECTED=red)
- ✅ Can filter by status
- ✅ Can sort by date

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-APP-005: View Application Details
**Priority:** 🟠 HIGH  
**Type:** Functional

**Steps:**
1. From application list, click one application
2. View details

**Expected Results:**
- ✅ Scholarship details shown
- ✅ Motivation letter displayed
- ✅ Status and timeline shown
- ✅ If reviewed: Reviewer notes visible
- ✅ Attached documents listed

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-APP-006: Cannot Edit Submitted Application
**Priority:** 🔴 CRITICAL  
**Type:** Security

**Steps:**
1. Open submitted application
2. Try to edit motivation letter

**Expected Results:**
- ✅ Edit button disabled or not visible
- ✅ Fields read-only
- ✅ API rejects edit attempts (HTTP 403)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-APP-007: Admin Assigns Consultant
**Priority:** 🟠 HIGH  
**Type:** Admin Workflow

**Prerequisites:**
- Logged in as admin
- Submitted application exists
- Consultant account exists

**Steps:**
1. Navigate to /admin/applications
2. Select submitted application
3. Click "Assign Consultant"
4. Select consultant from dropdown
5. Confirm assignment

**Expected Results:**
- ✅ Consultant assigned to application
- ✅ Application status changes to UNDER_REVIEW
- ✅ Consultant receives notification (if implemented)
- ✅ Appears in consultant's assigned applications

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-APP-008: Consultant Reviews Application
**Priority:** 🟠 HIGH  
**Type:** Consultant Workflow

**Prerequisites:**
- Logged in as consultant
- Application assigned to consultant

**Steps:**
1. Navigate to /consultant/applications
2. Click assigned application
3. Review details
4. Add reviewer notes: "Strong candidate. Recommend approval."
5. Click "Start Review"

**Expected Results:**
- ✅ Consultant can view application details
- ✅ Consultant can view student profile
- ✅ Consultant can view attached documents
- ✅ Reviewer notes save successfully
- ✅ Cannot view unassigned applications (security)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-APP-009: Admin Approves Application
**Priority:** 🟠 HIGH  
**Type:** Admin Workflow

**Prerequisites:**
- Application in UNDER_REVIEW status

**Steps:**
1. Login as admin
2. Navigate to application
3. Review consultant notes
4. Change status to APPROVED
5. Add admin notes (optional)
6. Save

**Expected Results:**
- ✅ Status changes to APPROVED
- ✅ reviewed_at timestamp recorded
- ✅ Student notified via email (check console)
- ✅ Status history recorded

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-APP-010: Application Permissions
**Priority:** 🔴 CRITICAL  
**Type:** Security

**Test Cases:**

**10a. Student Cannot View Others' Applications:**
- Login as student1
- Try to access student2's application
- Expected: HTTP 403 or redirect

**10b. Consultant Cannot View Unassigned:**
- Login as consultant
- Try to access application not assigned to them
- Expected: HTTP 403

**10c. Anonymous Cannot View:**
- Logout
- Try to access application URL
- Expected: Redirect to login

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

## Module 6: Documents Tests

### TEST-DOC-001: Upload Document
**Priority:** 🔴 CRITICAL  
**Type:** End-to-End

**Prerequisites:**
- Logged in as student

**Steps:**
1. Navigate to /student/documents
2. Click "Upload Document"
3. Select document type: Transcript
4. Choose file: transcript.pdf (2MB)
5. Add title: "University Transcript"
6. Add description (optional)
7. Click "Upload"

**Expected Results:**
- ✅ File uploads successfully
- ✅ Progress bar displays during upload
- ✅ "Document uploaded successfully" message
- ✅ Document appears in list
- ✅ File size shown correctly
- ✅ Upload date recorded

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-DOC-002: Document Type Validation
**Priority:** 🟠 HIGH  
**Type:** Functional

**Test Cases:**

**2a. Valid File Types:**
- Upload: .pdf, .doc, .docx, .jpg, .png
- Expected: All accept successfully

**2b. Invalid File Type:**
- Upload: .exe, .zip, .mp4
- Expected: "File type not allowed"

**2c. Oversized File:**
- Upload: 25MB file (limit: 20MB)
- Expected: "File size exceeds 20MB limit"

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-DOC-003: Download Document
**Priority:** 🟠 HIGH  
**Type:** Functional

**Prerequisites:**
- Document uploaded

**Steps:**
1. Navigate to /student/documents
2. Click download icon on document
3. Observe file download

**Expected Results:**
- ✅ File downloads to browser
- ✅ Filename matches original
- ✅ File not corrupted (can open)
- ✅ Download tracked in logs (security)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-DOC-004: Delete Document
**Priority:** 🟡 MEDIUM  
**Type:** CRUD

**Steps:**
1. Navigate to /student/documents
2. Click delete icon on document
3. Confirm deletion

**Expected Results:**
- ✅ Confirmation dialog appears
- ✅ Document removed from list
- ✅ File deleted from storage
- ✅ Cannot download after deletion

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-DOC-005: Document Privacy
**Priority:** 🔴 CRITICAL  
**Type:** Security

**Test Cases:**

**5a. Student Cannot View Others' Documents:**
- Login as student1
- Try to access student2's document URL
- Expected: HTTP 403 Forbidden

**5b. Consultant Can View Assigned Application Documents:**
- Login as consultant
- Access document from assigned application
- Expected: Can download

**5c. Anonymous Cannot Access:**
- Logout
- Try to access document URL
- Expected: HTTP 401 or redirect to login

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-DOC-006: Document List Pagination
**Priority:** 🟡 MEDIUM  
**Type:** Functional

**Prerequisites:**
- 30+ documents uploaded

**Steps:**
1. Navigate to /student/documents
2. Observe pagination
3. Navigate through pages

**Expected Results:**
- ✅ Documents paginated (10-20 per page)
- ✅ Can filter by document type
- ✅ Can sort by date
- ✅ Search by filename works

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-DOC-007: File Storage Persistence
**Priority:** 🔴 CRITICAL  
**Type:** Infrastructure

**⚠️ WARNING:** This test depends on storage configuration!

**Steps:**
1. Upload document
2. Restart backend server
3. Try to download document

**Expected Results (S3/GCS):**
- ✅ Document still accessible after restart
- ✅ Download succeeds

**Expected Results (LOCAL storage):**
- ❌ Document lost after restart (known issue)
- ⚠️ This is a production blocker!

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

## Module 7: Consulting Services Tests

### TEST-CONSULT-001: Browse Services
**Priority:** 🟠 HIGH  
**Type:** Functional

**Prerequisites:**
- 5+ services published

**Steps:**
1. Navigate to /services
2. View service catalogue

**Expected Results:**
- ✅ Services display as cards
- ✅ Each shows: title, price, duration, description
- ✅ Only published services visible
- ✅ Can filter by category (if implemented)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-CONSULT-002: Request Consultation
**Priority:** 🟠 HIGH  
**Type:** End-to-End

**Prerequisites:**
- Logged in as student

**Steps:**
1. Navigate to service detail page
2. Click "Book Consultation"
3. Fill form:
   - Preferred date: [future date]
   - Preferred time: 2:00 PM
   - Message: "I need help with scholarship applications"
4. Submit request

**Expected Results:**
- ✅ Consultation request created with status=PENDING
- ✅ "Request submitted successfully" message
- ✅ Request appears in student's consultation list
- ✅ Admin notified (if implemented)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-CONSULT-003: Admin Assigns Consultant
**Priority:** 🟠 HIGH  
**Type:** Admin Workflow

**Steps:**
1. Login as admin
2. Navigate to pending consultations
3. Select consultation request
4. Assign consultant
5. Confirm assignment

**Expected Results:**
- ✅ Consultant assigned
- ✅ Status changes to CONFIRMED
- ✅ Student notified
- ✅ Consultant notified
- ✅ Appears in consultant's schedule

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-CONSULT-004: View Consultation Details
**Priority:** 🟡 MEDIUM  
**Type:** Functional

**Prerequisites:**
- Student has consultations

**Steps:**
1. Navigate to /student/consultations
2. Click consultation
3. View details

**Expected Results:**
- ✅ Service details shown
- ✅ Consultant info displayed (if assigned)
- ✅ Date/time shown
- ✅ Status visible
- ✅ Can cancel if status=PENDING or CONFIRMED

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-CONSULT-005: Consultant Adds Notes
**Priority:** 🟡 MEDIUM  
**Type:** Consultant Workflow

**Prerequisites:**
- Logged in as consultant
- Consultation assigned

**Steps:**
1. Navigate to /consultant/consultations
2. Select consultation
3. Add notes: "Discussed scholarship options. Recommended 3 scholarships."
4. Save notes

**Expected Results:**
- ✅ Notes save successfully
- ✅ Notes visible to admin
- ✅ Notes NOT visible to student (private)
- ✅ Can edit notes later

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-CONSULT-006: Mark Consultation Complete
**Priority:** 🟡 MEDIUM  
**Type:** Workflow

**Steps:**
1. Login as consultant
2. Navigate to scheduled consultation
3. Click "Mark as Complete"
4. Confirm

**Expected Results:**
- ✅ Status changes to COMPLETED
- ✅ completion_date recorded
- ✅ Student can now leave feedback

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-CONSULT-007: Student Leaves Feedback
**Priority:** 🟡 MEDIUM  
**Type:** End-to-End

**Prerequisites:**
- Consultation status=COMPLETED

**Steps:**
1. Login as student
2. Navigate to completed consultation
3. Click "Leave Feedback"
4. Rate: 5 stars
5. Comment: "Very helpful! Highly recommend."
6. Submit

**Expected Results:**
- ✅ Feedback saved
- ✅ Rating and comment visible to admin
- ✅ Consultant can view feedback
- ✅ Cannot edit feedback after submission

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

## Module 8: Notifications Tests

### TEST-NOTIF-001: Email Notifications (Console)
**Priority:** 🟠 HIGH  
**Type:** Integration

**⚠️ NOTE:** Tests email TRIGGERING, not delivery (console backend)

**Steps:**
1. Register new user
2. Check console/logs for email

**Expected Results:**
- ✅ Email logged to console
- ✅ Contains verification link
- ✅ Template renders correctly (no {{ variables }} visible)
- ✅ Includes proper headers (From, To, Subject)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-NOTIF-002: In-App Notification Created
**Priority:** 🟡 MEDIUM  
**Type:** Integration

**Steps:**
1. Perform action that triggers notification (e.g., application status change)
2. Check database for notification record

**Expected Results:**
- ✅ Notification record created
- ✅ is_read=False initially
- ✅ Contains title and message
- ✅ Links to relevant resource

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-NOTIF-003: View Notifications
**Priority:** 🟡 MEDIUM  
**Type:** Functional

**Prerequisites:**
- User has 5+ notifications

**Steps:**
1. Navigate to /notifications
2. View notification list

**Expected Results:**
- ✅ All notifications displayed
- ✅ Unread notifications highlighted
- ✅ Sorted by date (newest first)
- ✅ Unread count shown

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-NOTIF-004: Mark Notification as Read
**Priority:** 🟡 MEDIUM  
**Type:** Functional

**Steps:**
1. View notification list
2. Click unread notification

**Expected Results:**
- ✅ Notification marked as read
- ✅ Unread count decreases
- ✅ Visual indicator changes (no longer bold/highlighted)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-NOTIF-005: Mark All as Read
**Priority:** 🟢 LOW  
**Type:** Functional

**Steps:**
1. Navigate to notifications page
2. Click "Mark all as read"

**Expected Results:**
- ✅ All notifications marked as read
- ✅ Unread count = 0
- ✅ Visual indicators updated

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

## Module 9: Admin Panel Tests

### TEST-ADMIN-001: Admin Login
**Priority:** 🔴 CRITICAL  
**Type:** Functional

**Steps:**
1. Navigate to /admin
2. Enter admin credentials
3. Login

**Expected Results:**
- ✅ Admin panel loads
- ✅ All registered models visible
- ✅ Can access each model

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-ADMIN-002: User Management
**Priority:** 🟠 HIGH  
**Type:** Admin Function

**Steps:**
1. Navigate to /admin/accounts/user/
2. View user list
3. Click user
4. Edit role to CONSULTANT
5. Save

**Expected Results:**
- ✅ Can view all users
- ✅ Can search by email
- ✅ Can filter by role
- ✅ Can edit user details
- ✅ Can deactivate user

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-ADMIN-003: Create Scholarship
**Priority:** 🟠 HIGH  
**Type:** Content Management

**Steps:**
1. Navigate to /admin/scholarships/scholarship/
2. Click "Add Scholarship"
3. Fill all required fields
4. Set featured=True
5. Set is_published=True
6. Save

**Expected Results:**
- ✅ Scholarship created
- ✅ Appears in frontend scholarship list immediately
- ✅ Featured on homepage

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-ADMIN-004: Bulk Actions
**Priority:** 🟡 MEDIUM  
**Type:** Admin Function

**Steps:**
1. Navigate to scholarship admin
2. Select multiple scholarships (checkbox)
3. Choose bulk action: "Mark as featured"
4. Execute

**Expected Results:**
- ✅ All selected scholarships marked as featured
- ✅ Changes reflected immediately

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-ADMIN-005: Application Overview
**Priority:** 🟠 HIGH  
**Type:** Admin Function

**Steps:**
1. Navigate to /admin/applications/application/
2. View application list
3. Filter by status: SUBMITTED

**Expected Results:**
- ✅ Can view all applications
- ✅ Can filter by status, date, scholarship
- ✅ Can search by student name/email
- ✅ Can export to CSV (if implemented)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-ADMIN-006: Non-Admin Cannot Access
**Priority:** 🔴 CRITICAL  
**Type:** Security

**Test Cases:**

**6a. Student Attempts Admin Access:**
- Login as student
- Navigate to /admin
- Expected: HTTP 403 or redirect

**6b. Consultant Attempts Admin Access:**
- Login as consultant
- Navigate to /admin
- Expected: HTTP 403 or redirect

**6c. Anonymous Attempts Access:**
- Logout
- Navigate to /admin
- Expected: Redirect to admin login

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

## Module 10: Security Tests

### TEST-SEC-001: SQL Injection Prevention
**Priority:** 🔴 CRITICAL  
**Type:** Security

**Steps:**
1. Navigate to scholarship search
2. Enter malicious query: `'; DROP TABLE scholarships; --`
3. Submit

**Expected Results:**
- ✅ Query treated as literal string
- ✅ No database error
- ✅ No tables dropped (Django ORM prevents SQL injection)
- ✅ Returns no results or safe error

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-SEC-002: XSS Prevention
**Priority:** 🔴 CRITICAL  
**Type:** Security

**Steps:**
1. Login as admin
2. Create scholarship with title: `<script>alert('XSS')</script>`
3. Save
4. View scholarship on frontend

**Expected Results:**
- ✅ Script tag rendered as text (escaped)
- ✅ Alert does NOT execute
- ✅ Displays: `<script>alert('XSS')</script>`

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-SEC-003: CSRF Protection
**Priority:** 🔴 CRITICAL  
**Type:** Security

**Steps:**
1. Inspect profile update form
2. Check for CSRF token
3. Try to submit form without token (use curl/Postman)

**Expected Results:**
- ✅ CSRF token present in form
- ✅ Submission without token: HTTP 403 CSRF verification failed
- ✅ Submission with invalid token: HTTP 403

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-SEC-004: Password Security
**Priority:** 🔴 CRITICAL  
**Type:** Security

**Steps:**
1. Register user with password: `Test123!@#`
2. Check database for password storage

**Expected Results:**
- ✅ Password NOT stored in plain text
- ✅ Stored as hash (pbkdf2_sha256$...)
- ✅ Different users with same password have different hashes (salt)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-SEC-005: JWT Token Security
**Priority:** 🔴 CRITICAL  
**Type:** Security

**Steps:**
1. Login and capture JWT token (from cookie or response)
2. Decode token (jwt.io)
3. Verify contents

**Expected Results:**
- ✅ Token contains: user_id, exp (expiry), iat (issued at)
- ✅ Token does NOT contain: password, sensitive data
- ✅ Token expires after 15 minutes (access token)
- ✅ HttpOnly cookie flag set (cannot access via JavaScript)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-SEC-006: Authorization Checks
**Priority:** 🔴 CRITICAL  
**Type:** Security

**Test Matrix:**

| Action | Student | Consultant | Admin | Anonymous |
|--------|---------|-----------|-------|-----------|
| View own profile | ✅ | ✅ | ✅ | ❌ |
| View others' profile | ❌ | ❌ | ✅ | ❌ |
| Create scholarship | ❌ | ❌ | ✅ | ❌ |
| Apply to scholarship | ✅ | ❌ | ❌ | ❌ |
| Review application | ❌ | ✅ (assigned) | ✅ | ❌ |
| Assign consultant | ❌ | ❌ | ✅ | ❌ |

**Test each cell in matrix**

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-SEC-007: Sensitive Data in Logs
**Priority:** 🟠 HIGH  
**Type:** Security

**Steps:**
1. Trigger events that log data (login, password reset)
2. Check application logs

**Expected Results:**
- ✅ Passwords NOT logged
- ✅ API keys NOT logged
- ✅ Tokens NOT logged (or redacted)
- ✅ Database credentials NOT logged

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

## Module 11: Performance Tests

### TEST-PERF-001: Homepage Load Time
**Priority:** 🟠 HIGH  
**Type:** Performance

**Steps:**
1. Open browser DevTools (Network tab)
2. Clear cache
3. Navigate to homepage
4. Measure load time

**Expected Results:**
- ✅ First Contentful Paint (FCP): <1.5s
- ✅ Largest Contentful Paint (LCP): <2.5s
- ✅ Time to Interactive (TTI): <3.5s
- ✅ Total page size: <2MB

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-PERF-002: API Response Time
**Priority:** 🟠 HIGH  
**Type:** Performance

**Steps:**
1. Use browser DevTools or Postman
2. Make API requests to key endpoints
3. Measure response time

**Test Endpoints:**

| Endpoint | Expected Response Time |
|----------|----------------------|
| GET /scholarships/ | <500ms |
| GET /scholarships/{id}/ | <200ms |
| POST /auth/login/ | <300ms |
| GET /students/me/ | <200ms |
| POST /applications/ | <500ms |

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-PERF-003: Database Query Performance
**Priority:** 🟡 MEDIUM  
**Type:** Performance

**Steps:**
1. Enable Django Debug Toolbar
2. Load scholarship list page
3. Check number of queries

**Expected Results:**
- ✅ <10 queries for list page
- ✅ No N+1 queries
- ✅ Queries use indexes (check EXPLAIN)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-PERF-004: Concurrent Users
**Priority:** 🟡 MEDIUM  
**Type:** Load Testing

**Tools:** Apache JMeter, Locust, or Artillery

**Steps:**
1. Set up load test
2. Simulate 50 concurrent users
3. Each user: Browse homepage → Search scholarships → View detail
4. Run for 5 minutes

**Expected Results:**
- ✅ No errors (0% error rate)
- ✅ Average response time <1s
- ✅ 95th percentile response time <2s
- ✅ Server CPU <80%
- ✅ Database connections <80% of pool

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

## Module 12: Accessibility Tests

### TEST-A11Y-001: Keyboard Navigation
**Priority:** 🟠 HIGH  
**Type:** Accessibility

**Steps:**
1. Navigate to homepage
2. Use only keyboard (Tab, Enter, Arrow keys)
3. Navigate through entire page

**Expected Results:**
- ✅ All interactive elements focusable
- ✅ Focus indicator visible
- ✅ Tab order logical
- ✅ Can access navigation menu
- ✅ Can submit forms
- ✅ Skip to content link present

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-A11Y-002: Screen Reader (NVDA/JAWS)
**Priority:** 🟡 MEDIUM  
**Type:** Accessibility

**Tools:** NVDA (free) or JAWS

**Steps:**
1. Enable screen reader
2. Navigate homepage
3. Listen to announcements

**Expected Results:**
- ✅ Page title announced
- ✅ Headings announced with levels (H1, H2)
- ✅ Links announced with text
- ✅ Images have alt text
- ✅ Form labels associated with inputs
- ✅ Error messages announced

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-A11Y-003: Color Contrast
**Priority:** 🟡 MEDIUM  
**Type:** Accessibility

**Tools:** WebAIM Contrast Checker or axe DevTools

**Steps:**
1. Inspect text on homepage
2. Check color contrast ratios

**Expected Results (WCAG AA):**
- ✅ Normal text: 4.5:1 contrast ratio
- ✅ Large text (18pt+): 3:1 contrast ratio
- ✅ UI components: 3:1 contrast ratio
- ✅ No contrast issues detected

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-A11Y-004: ARIA Attributes
**Priority:** 🟡 MEDIUM  
**Type:** Accessibility

**Steps:**
1. Inspect page HTML
2. Check for ARIA attributes on interactive components

**Expected Results:**
- ✅ aria-label on icon-only buttons
- ✅ aria-expanded on accordions/dropdowns
- ✅ aria-live on dynamic content
- ✅ aria-describedby on form errors
- ✅ role attributes where appropriate

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

## Module 13: Cross-Browser Tests

### TEST-BROWSER-001: Chrome
**Priority:** 🔴 CRITICAL  
**Type:** Compatibility

**Version:** Chrome 120+

**Steps:**
1. Test all critical user flows in Chrome
2. Check console for errors

**Expected Results:**
- ✅ All features work
- ✅ No console errors
- ✅ Layout correct

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-BROWSER-002: Firefox
**Priority:** 🟠 HIGH  
**Type:** Compatibility

**Version:** Firefox 120+

**Expected Results:**
- ✅ All features work
- ✅ CSS rendering correct
- ✅ Form validation works

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-BROWSER-003: Safari
**Priority:** 🟠 HIGH  
**Type:** Compatibility

**Version:** Safari 17+ (macOS/iOS)

**Expected Results:**
- ✅ All features work
- ✅ File uploads work
- ✅ Date pickers work

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-BROWSER-004: Edge
**Priority:** 🟡 MEDIUM  
**Type:** Compatibility

**Version:** Edge 120+ (Chromium-based)

**Expected Results:**
- ✅ All features work (should match Chrome)

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-BROWSER-005: Mobile Safari (iOS)
**Priority:** 🟠 HIGH  
**Type:** Mobile Compatibility

**Version:** iOS 16+

**Steps:**
1. Open on iPhone
2. Test critical flows

**Expected Results:**
- ✅ Touch interactions work
- ✅ Forms usable
- ✅ No layout issues
- ✅ Viewport correct

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### TEST-BROWSER-006: Chrome Mobile (Android)
**Priority:** 🟠 HIGH  
**Type:** Mobile Compatibility

**Version:** Android 12+

**Expected Results:**
- ✅ All features work on Android
- ✅ File uploads work from camera/gallery
- ✅ Forms usable

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

## Critical User Journeys (End-to-End)

### JOURNEY-001: Student Registration to Application Submission
**Priority:** 🔴 CRITICAL  
**Duration:** ~15 minutes

**Complete Flow:**
1. Visit homepage
2. Click "Register"
3. Fill registration form and submit
4. Check email for verification link
5. Click verification link
6. Login with credentials
7. Complete profile (personal info, education, skills)
8. Upload documents (transcript, resume)
9. Browse scholarships
10. Search for "Engineering" scholarships
11. Filter by country: USA
12. Click scholarship
13. Read details
14. Click "Apply"
15. Fill motivation letter
16. Save as draft
17. Review draft
18. Submit application
19. Verify application in "My Applications"

**Expected Result:** Complete journey without errors, application submitted successfully

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### JOURNEY-002: Admin Manages Application
**Priority:** 🔴 CRITICAL  
**Duration:** ~10 minutes

**Complete Flow:**
1. Login as admin
2. Navigate to applications list
3. Filter by status: SUBMITTED
4. Select an application
5. Review student profile
6. Review attached documents
7. Assign consultant
8. Logout admin
9. Login as consultant
10. View assigned application
11. Add reviewer notes
12. Mark as reviewed
13. Logout consultant
14. Login as admin
15. Approve application
16. Verify student receives notification

**Expected Result:** Application processed through full workflow

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

### JOURNEY-003: Student Books and Completes Consultation
**Priority:** 🟠 HIGH  
**Duration:** ~10 minutes

**Complete Flow:**
1. Login as student
2. Browse services
3. Select consultation service
4. Request consultation with preferred date/time
5. Verify request in "My Consultations"
6. Logout
7. Login as admin
8. Assign consultant to consultation
9. Logout
10. Login as student
11. Verify consultation confirmed
12. (After consultation) View completed consultation
13. Leave feedback (5 stars + comment)
14. Verify feedback submitted

**Expected Result:** Complete consultation workflow

**Actual Results:** _[To be filled]_

**Status:** ⬜

---

## Test Execution Summary

**Test Categories:**

| Category | Total Tests | Critical | High | Medium | Low |
|----------|-------------|----------|------|--------|-----|
| Public Website | 5 | 2 | 2 | 1 | 0 |
| Authentication | 10 | 4 | 5 | 1 | 0 |
| Student Dashboard | 6 | 1 | 3 | 2 | 0 |
| Scholarships | 9 | 2 | 5 | 2 | 0 |
| Applications | 10 | 3 | 5 | 2 | 0 |
| Documents | 7 | 3 | 2 | 1 | 1 |
| Consulting | 7 | 0 | 4 | 3 | 0 |
| Notifications | 5 | 0 | 1 | 4 | 0 |
| Admin | 6 | 2 | 3 | 1 | 0 |
| Security | 7 | 6 | 1 | 0 | 0 |
| Performance | 4 | 0 | 2 | 2 | 0 |
| Accessibility | 4 | 0 | 1 | 3 | 0 |
| Cross-Browser | 6 | 1 | 3 | 1 | 1 |
| User Journeys | 3 | 2 | 1 | 0 | 0 |
| **TOTAL** | **89** | **26** | **38** | **23** | **2** |

---

## Test Execution Checklist

### Pre-Testing
- [ ] Test data script run successfully
- [ ] Test users created (student, consultant, admin)
- [ ] Database populated with scholarships, opportunities, services
- [ ] Environment variables configured
- [ ] Backend server running without errors
- [ ] Frontend build successful
- [ ] All migrations applied

### During Testing
- [ ] Record all test results (Pass/Fail/Blocked)
- [ ] Screenshot failures
- [ ] Note error messages
- [ ] Record browser/device used
- [ ] Time duration of user journeys
- [ ] Note any workarounds used

### Post-Testing
- [ ] Calculate pass rate (passed / total * 100)
- [ ] Categorize failures by severity
- [ ] Create bug reports for failures
- [ ] Prioritize fixes
- [ ] Re-test after fixes
- [ ] Update documentation

---

## Bug Report Template

```markdown
**Bug ID:** BUG-001
**Test Case:** TEST-AUTH-003
**Severity:** 🔴 Critical / 🟠 High / 🟡 Medium / 🟢 Low
**Status:** Open / In Progress / Fixed / Won't Fix

**Summary:** [One-line description]

**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Result:**
[What should happen]

**Actual Result:**
[What actually happened]

**Environment:**
- Browser: Chrome 120.0.6099.129
- OS: Windows 11
- Screen Size: 1920x1080
- Backend: Local (http://localhost:8000)

**Screenshots/Logs:**
[Attach screenshots, error logs, console output]

**Notes:**
[Additional context, workarounds, related bugs]
```

---

## Success Criteria

**Minimum Acceptable Pass Rate by Priority:**

| Priority | Minimum Pass Rate |
|----------|------------------|
| 🔴 Critical | 100% (0 failures allowed) |
| 🟠 High | 95% (max 2 failures) |
| 🟡 Medium | 85% |
| 🟢 Low | 70% |

**Overall Minimum:** 90% pass rate across all tests

**Release Decision:**
- ✅ **GO:** Critical 100%, High 95%+, Overall 90%+
- ⚠️ **GO WITH KNOWN ISSUES:** Critical 100%, High 90%+, Overall 85%+
- ❌ **NO GO:** Any critical failures, or High <90%

---

## Next Steps After Testing

1. **Generate Test Report:**
   - Summary of results
   - Pass/fail rates by category
   - List of all failures with severity
   - Regression risk assessment

2. **Triage Bugs:**
   - Assign to developers
   - Set fix priorities
   - Estimate fix time
   - Schedule re-testing

3. **Re-test After Fixes:**
   - Re-run failed tests
   - Run regression tests
   - Verify fixes didn't break other features

4. **Final Sign-off:**
   - Product Owner review
   - Technical Lead approval
   - Deployment authorization

---

**Document Version:** 1.0  
**Last Updated:** November 2, 2026  
**Related Documents:**
- GOFER_COMPLETE_FUNCTIONAL_AUDIT.md
- GOFER_MISSING_FEATURES.md

---

**END OF END-TO-END TEST PLAN**

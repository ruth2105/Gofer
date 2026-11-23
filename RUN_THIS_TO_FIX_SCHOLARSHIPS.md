# 🚀 FIX SCHOLARSHIPS NOW - Quick Guide

## The Problem
Scholarships exist in your database but aren't showing on the website.

## The Solution (3 Minutes)

### Method 1: Run on Render (Recommended)

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com/
   - Click on service: `gofere-api-ruth2105`

2. **Open Shell**
   - Click the "Shell" tab in the navigation

3. **Run the fix script**
   ```bash
   python fix_production_scholarships.py
   ```

4. **Wait for completion**
   - Script will show what it's doing
   - Should complete in 10-30 seconds
   - You'll see "🎉 SUCCESS!" when done

5. **Test it worked**
   ```bash
   curl https://gofere-api-ruth2105.onrender.com/api/v1/scholarships/
   ```
   You should see scholarship data!

### Method 2: Alternative Using Management Command

If the script above doesn't work, use the management commands:

```bash
# 1. Diagnose the issue
python manage.py diagnose_scholarships

# 2. Get your admin email (look for ADMIN or SUPERADMIN role)
python manage.py shell -c "from apps.accounts.models import User; print('\n'.join([f'{u.email} ({u.role})' for u in User.objects.filter(role__in=['ADMIN','SUPERADMIN'])]))"

# 3. Fix with your admin email
python manage.py fix_scholarship_visibility \
  --publish-all \
  --extend-deadlines \
  --verify-sources \
  --admin-email "YOUR_EMAIL_HERE"
```

Replace `YOUR_EMAIL_HERE` with the email from step 2.

### Method 3: Local Fix (If You Have Database Access)

If you have the production `DATABASE_URL`:

```bash
# From gofer-exam/backend directory
export DATABASE_URL="your_production_database_url"
python fix_production_scholarships.py
```

## What This Does

The fix script will:
1. ✅ Publish all unpublished scholarships (`is_published = True`)
2. ✅ Extend expired deadlines by 90 days
3. ✅ Verify all source records (mark as VERIFIED, AVAILABLE)
4. ✅ Assign an admin as the verifier

## Expected Output

```
======================================================================
  SCHOLARSHIP VISIBILITY DIAGNOSTIC
======================================================================

📊 Total scholarships in database: 25
📝 Published scholarships: 25/25
📅 With valid deadlines (>= 2026-11-02): 25/25
🔗 With source records: 25/25
✅ Fully visible scholarships: 25/25

✅ 25 scholarships should be visible

======================================================================
  SAMPLE VISIBLE SCHOLARSHIPS
======================================================================

📚 Merit-Based Academic Excellence Award
   Deadline: 2027-02-02
   Amount: $5,000
   Source: VERIFIED

🎉 SUCCESS! Scholarships are now visible.
```

## Verification

After running the fix:

**Test the API:**
```bash
curl https://gofere-api-ruth2105.onrender.com/api/v1/scholarships/
```

**Check the website:**
- Go to: https://gofere.vercel.app/scholarships
- You should see scholarships listed

## Troubleshooting

### "No admin user found"

Create one:
```bash
python manage.py createsuperuser
```

Or promote an existing user:
```bash
python manage.py shell
```
```python
from apps.accounts.models import User
user = User.objects.get(email='your-email@example.com')
user.role = 'ADMIN'
user.save()
```

### Script not found

Make sure you're in the backend directory:
```bash
cd backend
python fix_production_scholarships.py
```

### Still not visible after fix

1. Check if backend has latest code:
   ```bash
   curl https://gofere-api-ruth2105.onrender.com/api/v1/health/
   ```
   Should return 200 OK (not 404)

2. If 404, deploy latest code:
   - Render Dashboard → `gofere-api-ruth2105` → "Manual Deploy"

3. Check frontend is deployed:
   - Vercel Dashboard → Check deployment status

## Need Help?

Run the diagnostic and share output:
```bash
python manage.py diagnose_scholarships
```

This shows exactly what's wrong.

# Next Steps: Fix Scholarship Visibility in Production

## Current Situation

✅ **Code pushed to GitHub** (commit 928488a)
- Added diagnostic tools to identify why scholarships aren't visible
- Added automated fix tools to make scholarships visible
- Comprehensive guide for troubleshooting

❌ **Scholarships not visible in production**
- Backend is deployed but may still be on old commit (health endpoint returns 404)
- Database has scholarships but they may not meet visibility criteria

## What You Need to Do Now

### Step 1: Verify Latest Code is Deployed

The latest commit (928488a) includes the diagnostic tools. First, check if Render has deployed it:

1. Go to https://dashboard.render.com/
2. Find service: `gofere-api-ruth2105`
3. Check the "Events" tab to see if commit 928488a was deployed
4. If not deployed, click "Manual Deploy" → "Deploy latest commit"

**Wait for deployment to complete** (usually 5-10 minutes)

### Step 2: Run the Diagnostic

Once deployed, open a shell on Render:

**Option A: Via Render Dashboard**
1. Go to https://dashboard.render.com/
2. Click on `gofere-api-ruth2105`
3. Click "Shell" tab
4. Run: `python manage.py diagnose_scholarships`

**Option B: Via Render CLI**
```bash
# Install Render CLI
npm install -g @render/cli

# Open shell
render shell gofere-api-ruth2105

# Run diagnostic
python manage.py diagnose_scholarships
```

The diagnostic will tell you exactly what's wrong:
- ❌ No scholarships in database
- ❌ Scholarships not published
- ❌ Deadlines expired
- ❌ Source records not verified

### Step 3: Fix the Issues

Based on the diagnostic output, run the fix command.

**First, do a dry run to see what will change:**

```bash
python manage.py fix_scholarship_visibility \
  --publish-all \
  --extend-deadlines \
  --verify-sources \
  --admin-email "YOUR_ADMIN_EMAIL_HERE" \
  --dry-run
```

**Replace `YOUR_ADMIN_EMAIL_HERE`** with your actual admin email (the one you use to log into the Gofer admin panel).

**If the dry run looks good, apply the fix:**

```bash
python manage.py fix_scholarship_visibility \
  --publish-all \
  --extend-deadlines \
  --verify-sources \
  --admin-email "YOUR_ADMIN_EMAIL_HERE"
```

### Step 4: Verify Scholarships Are Visible

Test the API endpoint:

```bash
curl https://gofere-api-ruth2105.onrender.com/api/v1/scholarships/
```

You should see scholarship data in the JSON response.

Also run the diagnostic again to confirm:

```bash
python manage.py diagnose_scholarships
```

Should show: "✓ X scholarships should be visible"

### Step 5: Deploy the Frontend

If scholarships are visible in the API but not on the website, the frontend may not be deployed:

1. Go to https://vercel.com/dashboard
2. Find project: `gofere`
3. Check if latest code is deployed
4. If not, trigger a deployment
5. Verify domain: https://gofere.vercel.app

## Troubleshooting

### "No admin user found"

You need an admin user to verify scholarship sources. Check if you have one:

```bash
python manage.py shell
```

Then:

```python
from apps.accounts.models import User

# List all admins
admins = User.objects.filter(role__in=['ADMIN', 'SUPERADMIN'])
for admin in admins:
    print(f"{admin.email} - {admin.role}")
```

If no admin exists, create one:

```bash
python manage.py createsuperuser
```

Or promote an existing user:

```python
from apps.accounts.models import User
user = User.objects.get(email='your-email@example.com')
user.role = 'ADMIN'
user.save()
```

### Health endpoint still returns 404

This means commit 26a75f9 (which fixed the health endpoint) is not deployed yet. Go to Render dashboard and trigger a manual deploy.

### Frontend returns 404

Check:
1. Is the Vercel project deployed?
2. Is the domain configured correctly?
3. Are the environment variables pointing to the correct backend URL?

## Complete Guide

For detailed instructions, see: **SCHOLARSHIP_VISIBILITY_GUIDE.md**

## Summary

1. ✅ Diagnostic tools pushed to GitHub (commit 928488a)
2. ⏳ Deploy to Render (manual deploy if needed)
3. ⏳ Run `diagnose_scholarships` to identify issues
4. ⏳ Run `fix_scholarship_visibility` to make scholarships visible
5. ⏳ Verify via API: `/api/v1/scholarships/`
6. ⏳ Deploy frontend to Vercel
7. ⏳ Test on live website: https://gofere.vercel.app

## Need Help?

If you run into issues, share the output of:

```bash
python manage.py diagnose_scholarships
```

This will help identify the exact problem.

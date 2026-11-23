# Scholarship Visibility Diagnostic Guide

## Problem
Scholarships are not visible on the production website even though they exist in the database.

## Why Scholarships Might Be Hidden

Scholarships are only visible when ALL of these conditions are met:

1. **Published**: `is_published = True`
2. **Valid deadline**: `application_deadline >= today`
3. **Verified source**: The linked `OpportunitySourceRecord` must have:
   - `verification_status = 'VERIFIED'`
   - `source_status = 'AVAILABLE'`
   - `verified_at` is not null
   - `verified_by` is an ADMIN or SUPERADMIN user
   - The parent `source.is_active = True`

## Diagnostic Steps

### Step 1: Run the diagnostic command

Connect to your production server (Render shell) and run:

```bash
python manage.py diagnose_scholarships
```

This will show you:
- Total scholarships in the database
- How many are published
- How many have valid deadlines
- How many have verified source records
- Specific issues preventing visibility

### Step 2: Identify the problem

The diagnostic will tell you which condition(s) are failing:
- ❌ No scholarships in database → Need to create scholarships
- ❌ Scholarships not published → Need to publish them
- ❌ Deadlines expired → Need to extend deadlines
- ❌ Source records not verified → Need to verify sources

## Fixing Scholarship Visibility

### Option A: Fix Existing Scholarships (Recommended)

If you have scholarships in the database but they're not visible:

```bash
# DRY RUN first to see what will change
python manage.py fix_scholarship_visibility \
  --publish-all \
  --extend-deadlines \
  --verify-sources \
  --admin-email "your-admin@example.com" \
  --dry-run

# If the dry run looks good, apply the changes
python manage.py fix_scholarship_visibility \
  --publish-all \
  --extend-deadlines \
  --verify-sources \
  --admin-email "your-admin@example.com"
```

**Replace `your-admin@example.com`** with the email of an actual admin user in your database.

### Option B: Check Your Admin User

First, verify you have an admin user:

```bash
python manage.py shell
```

Then in the Python shell:

```python
from apps.accounts.models import User

# List all admin users
admins = User.objects.filter(role__in=['ADMIN', 'SUPERADMIN'])
for admin in admins:
    print(f"{admin.email} - {admin.role}")

# If no admin exists, create one or promote an existing user
user = User.objects.get(email='your-email@example.com')
user.role = 'ADMIN'
user.save()
```

### Option C: Manual Database Fix

If you prefer to use the Django admin or database directly:

1. **Publish scholarships**: Set `is_published = True`
2. **Extend deadlines**: Set `application_deadline` to a future date
3. **Verify sources**: For each `OpportunitySourceRecord`:
   - Set `verification_status = 'VERIFIED'`
   - Set `source_status = 'AVAILABLE'`
   - Set `verified_at = current timestamp`
   - Set `verified_by = admin user ID`

## Running Commands on Render

### Via Render Dashboard:

1. Go to https://dashboard.render.com/
2. Find your service: `gofere-api-ruth2105`
3. Click "Shell" tab
4. Run the commands above

### Via Render CLI:

```bash
# Install Render CLI if not already installed
npm install -g @render/cli

# Open shell
render shell gofere-api-ruth2105

# Run diagnostic
python manage.py diagnose_scholarships

# Fix visibility
python manage.py fix_scholarship_visibility \
  --publish-all \
  --extend-deadlines \
  --verify-sources \
  --admin-email "your-admin@example.com"
```

## Verification

After fixing, verify the scholarships are visible:

```bash
# Run diagnostic again
python manage.py diagnose_scholarships

# Should show: "X scholarships should be visible"
```

Then test the API endpoint:

```bash
curl https://gofere-api-ruth2105.onrender.com/api/v1/scholarships/
```

You should see scholarship data in the response.

## Common Issues

### "No admin user found"
You need an admin user to verify source records. Create one:
```bash
python manage.py createsuperuser
```

### "All scholarships already fixed but still not visible"
Check if the backend is actually deployed:
```bash
curl https://gofere-api-ruth2105.onrender.com/api/v1/health/
```

If this returns 404, the latest code (commit 26a75f9) is not deployed yet.

### "Frontend shows 404"
The backend might be working but the frontend isn't deployed or configured correctly. Check:
- Vercel deployment status at https://vercel.com/dashboard
- Domain configuration for `gofere.vercel.app`
- Environment variables in Vercel pointing to the correct backend URL

## Next Steps After Scholarships Are Visible

1. ✅ Verify backend health endpoint: `/api/v1/health/` should return 200
2. ✅ Verify scholarships endpoint: `/api/v1/scholarships/` should return data
3. ✅ Deploy frontend to Vercel
4. ✅ Test full flow: search scholarships, view details, apply

## Need Help?

If scholarships are still not visible after running these commands, run the diagnostic and share the output:

```bash
python manage.py diagnose_scholarships > diagnostic_output.txt
```

This will help identify any remaining issues.

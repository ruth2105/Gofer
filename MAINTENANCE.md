# Gofer Exam Maintenance Guide

Updated: 2026-11-11

This guide describes the checked-in application and its operational requirements.
It is not evidence that production hosting, data recovery, or third-party
integrations have been configured or tested.

## Architecture

- **Frontend:** Next.js App Router, React, TypeScript, and Tailwind CSS. Public
  pages use the backend catalogue APIs; student and consultant pages use the
  same-origin `/api/v1` proxy and browser cookies.
- **Backend:** Django 5 and Django REST Framework, split settings, role-aware
  permissions, and `drf-spectacular` API schema. Accounts use JWTs in HttpOnly
  cookies, with CSRF protection for unsafe browser requests.
- **Data:** PostgreSQL is the production database. Django apps own accounts,
  students, opportunities, scholarships, universities, destinations,
  applications, consultations, documents, notifications, and services.
- **Deployments:** [render.yaml](./render.yaml) describes a Render preview
  frontend, API, and free PostgreSQL database. The frontend build also relies on
  the server-only `API_PROXY_TARGET`. The supplied Vercel domain was not serving
  the app during this audit; the Render preview did.
- **Email:** Django's email backend sends account-verification messages.
  Development and tests use console and in-memory backends respectively.
  Production requires a real provider, sender address, and verified sender
  domain. No real delivery was validated.

## Environment variable names

Configure values only in the relevant hosting environment or local ignored
environment files. Do not commit credentials or paste them into this guide.

### Frontend

- `API_PROXY_TARGET`
- `NEXT_PUBLIC_API_URL` (legacy fallback; prefer `API_PROXY_TARGET`)
- `NEXT_PUBLIC_APP_NAME`
- `NEXT_PUBLIC_APP_URL`

### Backend

- `DJANGO_SETTINGS_MODULE`
- `PYTHON_VERSION` (Render runtime selection)
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `DATABASE_URL` (production), or `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
  `DB_HOST`, and `DB_PORT` (development)
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `GOFER_FRONTEND_URL`
- `EMAIL_BACKEND`, `GOFER_EMAIL_FROM`, `EMAIL_HOST`, `EMAIL_PORT`,
  `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`,
  and `EMAIL_TIMEOUT`
- `EMAIL_VERIFICATION_TOKEN_TTL_MINUTES`
- `EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS`
- `DJANGO_LOG_LEVEL`

Optional object-storage variable names (`AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`) appear
in examples, but durable media storage is not configured in the checked-in
production settings. Do not treat those names as a working integration.

## Data backup and recovery

**Current state:** A verified production backup schedule, retention policy, and
restore drill were not evidenced. The Render blueprint uses a free database
that expires after 30 days, and local media storage is not durable across service
restarts or deployments. Do not rely on this preview for student records or
uploads.

Before accepting real student data:

1. Select a durable managed database and private, persistent object storage.
2. Assign an owner to encrypted automated backups, off-site retention, and
   monitoring. Define recovery-point and recovery-time objectives.
3. Back up uploaded documents separately from the database, with access controls
   and retention rules appropriate for personal data.
4. Perform a restore drill into an isolated environment before calling the
   recovery path usable. Record the date, owner, duration, and validation result.
5. Before any database or storage change, confirm the latest backup and rollback
   plan. Do not run destructive migrations or overwrite existing data as a
   recovery shortcut.

Recovery runbook (to be completed and rehearsed by the hosting owner):

1. Declare the incident, restrict writes if necessary, and preserve relevant
   logs without recording credentials or verification tokens.
2. Identify the last known-good database and file backups and confirm their
   integrity.
3. Restore to isolated infrastructure; verify schema/migrations, account and
   ownership relationships, and private-file access controls.
4. Run Django checks and the application smoke tests against the isolated
   restore. Confirm the restored data meets the recovery objectives.
5. Obtain approval before directing production traffic to the restored system.
   Preserve the original environment until the recovery is confirmed.

## Verified catalogue content

Do not import demo fixtures from the frontend `data/` directory as real
opportunities or scholarship records. No scholarship importer command or
approved verified catalogue dataset is currently configured. Until one is
reviewed, an authorized administrator can curate entries through Django Admin:

1. Use the official scholarship/opportunity provider page as the source of
   truth. Record the canonical source and application URLs, provider name,
   access date, application deadline, eligibility/nationality rules, required
   documents, and any restrictions.
2. Cross-check the opportunity is current, the application link works, and the
   deadline and eligibility are stated by the provider. Keep uncertain details
   unset and clearly unconfirmed; never infer or fabricate them.
3. Create or update the record as unpublished. For source-backed records, use
   the source-record review workflow; only an active source record verified by
   an administrator and marked available can support publication.
4. Populate the structured nationality and required-document fields from the
   verified provider information. Save, inspect the public API detail response,
   and confirm the student page shows the exact values. Publish only after
   review.
5. Revisit open listings on a schedule. Close or unpublish expired, withdrawn,
   broken-link, or no-longer-verifiable listings; retain an audit trail.

For a future bulk importer, first agree a CSV schema and a human-review queue.
Validate each row and source URL, import as drafts only, report rejected rows,
and require an administrator to verify and publish. Never apply a bulk update
that deletes existing data or makes unreviewed content public.

## Testing and routine checks

Run commands from the relevant project directory. The backend command uses its
own virtual environment and test settings:

```powershell
Set-Location C:\Users\user\Desktop\abc\gofer-exam\backend
$env:DJANGO_SETTINGS_MODULE = 'config.settings.test'
.\venv\Scripts\python manage.py test --verbosity 1
.\venv\Scripts\python manage.py check
.\venv\Scripts\python manage.py makemigrations --check --dry-run
```

Frontend checks:

```powershell
Set-Location C:\Users\user\Desktop\abc\gofer-exam
npx tsc --noEmit
npm run lint
npm run build
```

The current frontend package has no automated test script. A successful build
does not validate browser/API journeys. Before a release, exercise signup through
verification and login, cookie/CSRF behavior, student-owned application access,
consultation actions, and public catalogue loading against a staging API with
non-production accounts. Do not send automated test messages to real users.

## Release checklist

- [ ] Confirm intended Git revision, reviewed changes, and clean release scope.
- [ ] Run backend tests, Django checks, migration-drift check, TypeScript,
      ESLint, and optimized frontend build.
- [ ] Review migrations and deployment startup behavior; [render.yaml](./render.yaml)
      applies migrations when the API service starts.
- [ ] Confirm database and private-file backups and a current restore-drill
      result before production data changes.
- [ ] Confirm frontend/API domains, HTTPS, allowed hosts, CORS, CSRF origins,
      proxy target, and cookie behavior.
- [ ] Configure production email-provider variables and a sender on a verified
      domain. Send a controlled test message and confirm provider acceptance;
      separately check inbox delivery and domain authentication.
- [ ] Verify the production API schema and key endpoints match the frontend
      contract. Run staging browser journeys at mobile, tablet, and desktop
      widths, plus keyboard/accessibility checks.
- [ ] Confirm monitoring, error reporting, alert ownership, privacy notices,
      access controls, and incident contacts.
- [ ] Obtain human approval for deployment. Deploy manually; verify health and
      smoke tests, monitor errors, and follow the approved rollback plan if
      checks fail.

The currently connected Render Blueprint has automatic sync enabled. Confirm
that setting before pushing changes: a push to its tracked branch may trigger a
deployment and the API start command runs migrations.

## Security maintenance

- Keep secrets in a managed secret store or ignored environment configuration;
  rotate credentials after suspected exposure and never log secrets, passwords,
  JWTs, verification tokens, or provider responses containing them.
- Enforce HTTPS and secure cookies in production. Keep production settings
  validation enabled; do not use test or development settings to serve users.
- Review authentication throttles, role/ownership permissions, dependency
  advisories, administrator access, and audit logs regularly.
- Use private storage for personal documents, least-privilege access, content
  validation, retention/deletion rules, and tested backup controls before
  implementing uploads.
- Review opportunity and scholarship sources, eligibility, deadlines, and
  official links before publishing. Remove or expire outdated records promptly.
- Re-test restore procedures, email delivery, rate-limit behavior, and auth
  flows after infrastructure or dependency changes.

## Known issues

- At audit time, `https://gofere.vercel.app` returned HTTP 404. The Render
  frontend preview returned HTTP 200.
- The live API schema returned HTTP 200 but did not expose the email-verification
  and resend routes present in the repository. The live backend therefore was
  not confirmed to match the checked-in frontend/backend.
- Production email settings were not configured and deployment had previously
  failed on required configuration. Email delivery and sender-domain
  verification remain unproven.
- Render's preview database is free and temporary; file uploads do not have a
  configured durable private-storage backend. Backup and restore operations are
  unverified.
- Scholarship records were absent in the deployed catalogue. Opportunity and
  other public catalogue content still require live verification against
  authoritative sources; no invented records should be published.
- Password reset is not implemented. Login has no dedicated endpoint throttle
  in the inspected configuration. Document upload APIs and secure user-owned
  storage are not implemented. Notification email delivery and scheduled
  reminders are absent.
- Application target/type consistency is validated by the API serializer but
  not enforced by a database constraint.
- The custom web admin is a metrics overview, not a full management console.
  No full end-to-end browser or assistive-technology suite is configured.
- Development settings retain a fallback database password and the shared base
  settings define an insecure default secret; production rejects weak secrets,
  but local environments should set unique values and the fallbacks should be
  removed or made explicit.
- The scholarship API mapper can fail on an unrecognized enum value, and a
  profile completion refresh failure can be reported as though the profile save
  itself failed. These frontend/API-contract behaviors need regression coverage.
- Review and rotate any deployment-hook credential that may have been exposed
  in prior operational views. No credential value is recorded here.

## Future upgrades

1. Restore deployment parity, complete provider/domain configuration, and prove
   persistent database and file recovery.
2. Implement password recovery and apply consistent login throttling; strengthen
   database-level invariants for application records.
3. Add private document workflows with authorization, scanning/validation,
   retention, and durable storage.
4. Add notifications and reminders through a monitored background worker with
   user preferences and delivery retry/error handling.
5. Establish editorial ownership and expiry monitoring for verified
   scholarships, opportunities, universities, and destinations before automating
   collection.
6. Add complete browser, API contract, accessibility, and responsive regression
   tests; correct enum mapping and truthful profile-save feedback.
7. Expand exam-preparation content only against verified current provider
   formats; add payments, rewards, or calendar integrations only after policy,
   legal, and provider requirements are approved.

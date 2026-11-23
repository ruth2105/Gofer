# Phase 2.1 Completion Report

**Date:** 2026-11-12  
**Scope:** Role-aware frontend navigation and route handling, plus email
configuration readiness. No production service was contacted, no original
database migration was applied, and nothing was deployed or pushed.

## Outcome

Role-aware navigation and client-side route guards are implemented for Guest,
Student, Consultant, Admin, and Superadmin. Each authenticated role has an
appropriate dashboard destination; Superadmin has a distinct security-audit
landing page. Public links remain available to every actor, while private
navigation links are role-filtered.

Email delivery is **not ready for live use** in the inspected local
environment. The resolved email backend is Django's console backend, the
sender remains `webmaster@localhost`, and no provider configuration or
authorized test recipient was available. No email was sent, and delivery is
not claimed as verified.

## Route and navigation implementation

- Added a shared route policy for protected paths, authorized roles,
  role-specific dashboard URLs, safe post-login destinations, and role
  navigation links.
- Added a root auth provider that checks `/api/v1/auth/me/`, rechecks on
  client-side route changes, handles login/logout and session-expiry events,
  and withholds protected children during identity checks or account-check
  failures.
- Added one role route guard for student, consultant, admin, superadmin, and
  authenticated notification routes. Wrong-role routes redirect to that
  actor's dashboard; unauthenticated requests preserve the protected
  destination on a login redirect.
- Admin and Superadmin share `/admin` for permitted overview functions.
  Superadmin's role home is `/admin/security`, an audit landing page backed by
  the independently Superadmin-protected audit API.
- Shared navigation conditionally shows dashboards and workflows for the
  current role. Only Superadmin sees the Security Audit link. The mobile
  menu scrolls within the viewport when expanded.
- The login page uses the shared safe-destination policy.
- The old session-only client guard was removed. Next.js `proxy.ts` still
  provides the initial session-marker navigation redirect; the new client
  guard resolves the actor role.

**Security boundary:** These frontend checks are usability and navigation
controls. They do not authenticate a browser or authorize data access.
Django API permissions and scoped querysets remain authoritative for direct
requests.

## Email configuration inspection

The backend `.env` file exists, but inspection did not print its contents.
Resolved email settings were:

- Backend: `django.core.mail.backends.console.EmailBackend`
- Sender: not configured; resolves to the local `webmaster@localhost`
  default
- SMTP host and provider credentials: absent
- Frontend URL: HTTP localhost, not a production HTTPS origin
- `.env.example`: contains placeholder-only SMTP settings

Production settings now reject console, dummy, in-memory, and file-based
backends; require a valid non-placeholder sender; and, for SMTP, require a
host, valid port, TLS or SSL, mutually compatible transport flags, and a
complete credential pair (or no credentials for an explicitly authorized
relay). A fake placeholder SMTP configuration was accepted by the
production-settings import check; this only verifies configuration shape and
does not test any provider.

### Required provider setup and delivery test

1. Select the transactional email provider and its SMTP endpoint or supported
   provider backend.
2. Verify the sender domain with the provider. Publish its required SPF and
   DKIM records and configure a DMARC policy.
3. Configure the production environment, using the hosting platform's secret
   manager for credentials:

   ```text
   DJANGO_SETTINGS_MODULE=config.settings.production
   GOFER_FRONTEND_URL=https://<public-frontend-host>
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   GOFER_EMAIL_FROM=no-reply@<verified-domain>
   EMAIL_HOST=<provider-smtp-host>
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_USE_SSL=False
   EMAIL_HOST_USER=<provider-username>
   EMAIL_HOST_PASSWORD=<provider-password>
   EMAIL_TIMEOUT=10
   ```

   For an SSL-only provider, set `EMAIL_USE_SSL=True` and `EMAIL_USE_TLS=False`
   and use the provider's SSL port. Use a custom backend only when its package
   is installed and its credentials are configured securely.
4. Obtain an explicitly authorized test mailbox. Send and receive one
   verification message and one password-reset message; verify sender,
   HTTPS link host, successful receipt, single-use/expiry behavior, and
   provider acceptance logs. Do not test against unconsenting student
   addresses.

No recipient was supplied, so steps 4 and live provider acceptance remain
blocked.

## Files changed in Phase 2.1

- `lib/auth/access.ts` (new)
- `lib/auth/access.test.mjs` (new)
- `components/auth/AuthProvider.tsx` (new)
- `components/auth/RoleRouteGuard.tsx` (new)
- `components/auth/AuthSessionGuard.tsx` (removed as superseded)
- `components/layout/Navigation.tsx`
- `app/layout.tsx`
- `app/student/login/page.tsx`
- `app/admin/security/page.tsx` (new)
- `lib/api/client.ts`
- `backend/config/settings/production.py`
- `package.json`
- `ACTOR_FUNCTIONALITY_AUDIT.md`
- `ROLE_PERMISSION_MATRIX.md`

No catalogue migration was changed. No database operation was performed.

## Validation evidence

### Backend

- Full suite using `config.settings.test`: **197 tests passed, 1 skipped**.
- Focused accounts, consultation, and application API suites: **89 tests
  passed, 1 skipped**. This includes role-management, audit access,
  authentication lifecycle, ownership, and assignment API coverage.
- Django system checks: passed.
- Migration drift check: **No changes detected**.
- Production email settings accepted a structurally valid, entirely fake
  SMTP configuration. This did not contact a provider or send a message.

### Frontend

- Route policy test script: **5 tests passed**. Coverage includes role
  dashboard destinations, protected-route matrix, public paths, same-origin
  and role-authorized login destinations, and role-specific navigation links.
- ESLint: passed.
- TypeScript: passed.
- Production build: passed; Next.js generated `/admin/security` and the
  remaining app routes. The build reported a pre-existing parent
  `package-lock.json` workspace-root warning.

### Browser route and mobile checks

Local browser checks used stubbed `/auth/me/` responses; they did not use real
accounts or contact a backend/provider.

- Guest request for `/student/applications` redirected to
  `/student/login?next=%2Fstudent%2Fapplications&reason=auth_required`.
- Student request for `/consultant` redirected to `/student`.
- Consultant request for `/student/applications` redirected to `/consultant`.
- Admin request for `/admin/security` redirected to `/admin`.
- Superadmin request for `/student/profile` redirected to `/admin/security`.
- At 375px viewport, Superadmin navigation included Admin Overview and
  Security Audit; Admin navigation included Admin Overview but not Security
  Audit. Document width was 360px, with no horizontal overflow.

The local API was not running during the browser checks, so API-backed
dashboard data loading in the browser was not validated. The corresponding
backend role and permission API tests passed separately.

## Remaining blockers and next steps

- Configure a real email provider and verified sender domain, then run the
  authorized mailbox tests above. Until then, email delivery is unverified.
- Apply no migrations without separate explicit approval. The original local
  database still has five pending migrations; the Superadmin audit-event
  table is not present there until the approved `accounts.0002` and `.0003`
  chain is applied.
- Continue to treat frontend guards as supplementary; preserve API-level role,
  ownership, and assignment checks.
- Documents, saved opportunities, and job/internship application workflows
  remain outside this phase.

See [ACTOR_FUNCTIONALITY_AUDIT.md](./ACTOR_FUNCTIONALITY_AUDIT.md) and
[ROLE_PERMISSION_MATRIX.md](./ROLE_PERMISSION_MATRIX.md) for updated actor
status.

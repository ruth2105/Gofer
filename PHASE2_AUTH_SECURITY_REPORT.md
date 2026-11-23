# Phase 2 Authentication and Security Report

**Date:** 2026-11-12  
**Scope:** Local Phase 2 authentication, role separation, authorization, and
frontend session handling. No production service was contacted, no production
or original-local migrations were applied, and nothing was deployed, pushed,
staged, or committed.

## Summary

Phase 2 extends the existing custom Django user model, cookie-based JWT
authentication, CSRF protections, email-verification workflow, scoped
querysets, and Next.js client API rather than introducing a second auth
system. It adds password recovery/change, protected account management,
distinct Admin and Superadmin permission classes, security audit events, a
consultant self-profile endpoint, and an HttpOnly session marker for
navigation gating.

The backend tests, Django checks, migration-drift check, frontend lint,
TypeScript, production build, and local mobile-width login/registration checks
passed. The account migrations passed a forward and reverse rehearsal on a
disposable PostgreSQL database restored from the verified local backup. The
original local database remains unchanged.

This is not a production security certification. Full role-aware frontend
route gating, document access, and real provider delivery remain unverified
or incomplete.

## Existing functionality reused

- `accounts.User` remains the custom email-identified user with
  `STUDENT`, `CONSULTANT`, `ADMIN`, and `SUPERADMIN` roles.
- Existing cookie-based SimpleJWT, CSRF enforcement, registration, login,
  logout, refresh, email verification, resend cooldown, active-account checks,
  and profile APIs remain in place.
- Existing student-owned and consultant-assigned querysets remain the
  primary object-level data boundary.
- Existing Axios API client and Next.js app structure are used for session
  expiry and password recovery.
- Existing Django email backend configuration is used. SMTP/backend
  environment variables are configurable in settings; provider acceptance
  was not tested with a real provider.

## Implemented behavior and API surface

### Authentication lifecycle

| Method and route | Behavior |
|---|---|
| `POST /api/v1/auth/register/` | Creates an unverified student; rejects privileged role submissions; duplicate-email and case-normalization checks apply. |
| `POST /api/v1/auth/verify-email/` | Validates and consumes an expiring verification token. |
| `POST /api/v1/auth/resend-verification/` | Resends with cooldown and scoped throttling. |
| `POST /api/v1/auth/login/` | Sets HttpOnly JWT cookies; rejects inactive accounts and unverified students. |
| `POST /api/v1/auth/logout/` | Blacklists refresh token and clears auth cookies. |
| `POST /api/v1/auth/token/refresh/` | Refreshes the cookie session after checking account eligibility. |
| `POST /api/v1/auth/password/reset/` | Returns a generic, non-enumerating response; sends reset email only for active accounts. |
| `POST /api/v1/auth/password/reset/confirm/` | Validates a single-use Django reset token, changes password, and revokes refresh sessions. |
| `POST /api/v1/auth/password/change/` | Validates the current password, changes password, revokes refresh sessions, and clears cookies. |
| `GET /api/v1/auth/me/`, `PATCH /api/v1/auth/me/` | Reads or updates the authenticated user's allowed profile fields; role and verification fields cannot be changed here. |

Reset-token expiry is one hour. Reset email failures are logged without
including tokens or secrets; the public response does not imply delivery.
Actual SMTP/provider acceptance and sender-domain verification are still
required.

### Role and object authorization

- `IsAdmin` authorizes only `ADMIN`; `IsSuperAdmin` authorizes only
  `SUPERADMIN`. Shared admin capabilities can continue to admit both roles.
- `GET /api/v1/auth/users/` and `GET/PATCH
  /api/v1/auth/users/{user_id}/` provide protected account management.
  Admin can manage ordinary student/consultant account fields and activation
  but cannot change roles or manage administrative accounts. Superadmin can
  manage roles and administrative accounts. Self-lockout is denied.
- Role and activation changes are audited; deactivation revokes outstanding
  refresh tokens.
- `GET /api/v1/auth/security/audit/` is read-only and Superadmin-only.
- Consultant self-profile is at `GET/PATCH
  /api/v1/consultations/me/`; verification and system-owned fields are
  protected.
- Existing owner- and assignment-scoped endpoints for students, applications,
  consultations, and notifications continue to deny cross-owner or
  unassigned access. Opportunity publication safeguards were not weakened.
- Public registration cannot request `ADMIN` or `SUPERADMIN`.

### Frontend

- Added a Next.js 16 `proxy.ts` session-marker check for protected navigation.
  It preserves the intended same-origin destination when redirecting to
  login.
- Login destination handling rejects unsafe external destinations.
- Failed refresh emits a session-expired event; the app-level guard redirects
  to login.
- Added forgot-password and reset-password forms and API-client methods.
- The proxy is a navigation/usability control, not an authorization layer. It
  checks session presence, not the full actor role; backend API permissions
  remain authoritative.

## Files changed for Phase 2

### Backend

- `backend/apps/accounts/models.py`
- `backend/apps/accounts/audit.py` (new)
- `backend/apps/accounts/password_reset.py` (new)
- `backend/apps/accounts/serializers.py`
- `backend/apps/accounts/views.py`
- `backend/apps/accounts/urls.py`
- `backend/apps/accounts/admin.py`
- `backend/apps/accounts/migrations/0003_securityauditevent.py` (new)
- `backend/apps/accounts/tests.py`
- `backend/apps/common/permissions.py`
- `backend/apps/applications/views.py`
- `backend/apps/applications/tests.py`
- `backend/apps/consultations/views.py`
- `backend/apps/consultations/serializers.py`
- `backend/apps/consultations/urls.py`
- `backend/apps/consultations/tests.py`
- `backend/apps/notifications/views.py`
- `backend/apps/students/views.py`
- `backend/apps/scholarships/views.py`
- `backend/config/settings/base.py`
- `backend/templates/accounts/password_reset.html` (new)
- `backend/templates/accounts/password_reset.txt` (new)

### Frontend

- `proxy.ts` (new)
- `components/auth/AuthSessionGuard.tsx` (new)
- `app/layout.tsx`
- `app/student/login/page.tsx`
- `app/student/applications/page.tsx`
- `app/student/forgot-password/page.tsx` (new)
- `app/student/reset-password/page.tsx` (new)
- `app/student/reset-password/ResetPasswordForm.tsx` (new)
- `lib/api/client.ts`

The unrelated catalogue migrations (`opportunities.0005`, `opportunities.0006`,
and `scholarships.0004`) were left intact.

## Migration and database safety

`accounts.0003_securityauditevent` depends on
`accounts.0002_emailverificationtoken`. Both were applied and reversed only on
a disposable PostgreSQL database restored from:

- Backup: `C:\Users\user\.copilot\session-state\9ff64949-aeb0-4f2d-8872-6d381f382a57\files\gofer_exam_local_20261112_094522_+0300.dump`
- Size: 135,061 bytes
- SHA-256: `B585A8E792D653B50384570B7A112FB08AC9449D93A80BA11EA0F20DF4B47EFD`

The disposable restore began with 27 public tables, one user, and
`accounts.0001_initial` applied. Forward migration created both account
tables; `accounts_securityauditevent` had 8 columns, 5 indexes, and 2 foreign
keys. User count and pre-existing application-table counts remained
unchanged. Reverse migration to `accounts.0001_initial` removed both added
tables and preserved existing counts. The exact disposable database was
dropped.

The original local database still reports these five unapplied migrations:

1. `accounts.0002_emailverificationtoken`
2. `accounts.0003_securityauditevent` (depends on accounts.0002)
3. `opportunities.0005_opportunity_documents_required_and_more`
4. `opportunities.0006_opportunity_management_mvp` (depends on opportunities.0005)
5. `scholarships.0004_opportunity_management_mvp`

No migration was applied to the original local database. Because the new
security audit table is not present there yet, account API code paths that
write audit events require the approved account migrations before use against
that database.

## Validation evidence

- Full backend test suite using `config.settings.test`: **197 tests passed,
  1 skipped**.
- `manage.py check`: passed with no issues.
- `manage.py makemigrations --check --dry-run`: **No changes detected**.
- Frontend `npm run lint`: passed.
- Frontend `npx tsc --noEmit`: passed.
- Frontend production `npm run build` with
  `API_PROXY_TARGET=http://127.0.0.1:8000/api/v1`: passed. Next.js emitted a
  workspace-root warning because a parent-directory package lock exists;
  build completed successfully.
- Local browser check at 375px viewport: login and registration pages rendered
  their expected headings/forms; document width was 360px for both pages, so
  no horizontal overflow was observed.
- PostgreSQL account-migration rehearsal: forward, schema inspection, reverse,
  and pre-existing table/user-count checks passed on the disposable restore.
- No live provider delivery, production API, production database, deployment,
  or role-specific browser journey was tested.

## Remaining risks and recommended next steps

1. Obtain explicit approval before applying any migration to the original
   local database. Do not mix catalogue migration decisions with the account
   migration approval.
2. Configure a real email provider and verified sender domain, then run an
   explicitly approved end-to-end delivery test.
3. Add complete role-aware frontend navigation and direct API/route tests for
   every protected page; do not rely on the session marker for roles.
4. Define and implement private document access, including ownership,
   storage, scanning, and retention.
5. Add a dedicated superadmin API/UI for privileged system settings and
   arbitrary permission management if required by product policy.
6. Keep opportunity saving and external application submission listed as
   missing until implemented and tested.

See [AUTHENTICATION_TEST_REPORT.md](./AUTHENTICATION_TEST_REPORT.md),
[ROLE_PERMISSION_MATRIX.md](./ROLE_PERMISSION_MATRIX.md), and
[ACTOR_FUNCTIONALITY_AUDIT.md](./ACTOR_FUNCTIONALITY_AUDIT.md) for validation
and actor-specific details.

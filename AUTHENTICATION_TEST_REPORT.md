# Authentication Test Report

**Date:** 2026-11-12  
**Scope:** Phase 2 local backend, frontend, and disposable PostgreSQL
validation.

## Results

| Check | Result | Evidence |
|---|---|---|
| Full Django backend suite | **Passed: 197 tests, 1 skipped** | `config.settings.test`; test runner output ended with `OK (skipped=1)`. |
| Django system checks | **Passed** | `manage.py check` reported no issues. |
| Migration drift | **Passed** | `manage.py makemigrations --check --dry-run` reported `No changes detected`. |
| Frontend lint | **Passed** | `npm run lint` completed successfully. |
| Frontend TypeScript | **Passed** | `npx tsc --noEmit` completed successfully. |
| Production build | **Passed** | `API_PROXY_TARGET=http://127.0.0.1:8000/api/v1 npm run build`; Next.js generated all routes. |
| Mobile login/registration layout | **Passed for basic overflow/render check** | Local browser at 375px viewport rendered page headings and forms; document width was 360px on each page. |
| PostgreSQL migration rehearsal | **Passed on disposable restore** | Applied `accounts.0002` and `.0003`, verified schema/counts, reversed to `.0001`, then dropped the exact disposable database. |
| Live email delivery | **Not tested** | Automated tests use Django's test email backend and simulated delivery failures. |
| Production database/API | **Not tested** | No production service was contacted. |

## Backend test coverage observed

The full backend run includes the account/authentication tests in
`backend/apps/accounts/tests.py`, role and object-permission tests in the
application/consultation workflow suites, and the rest of the repository's
backend tests.

Account test groups cover:

- Registration as an unverified student, email generation, duplicate
  addresses, case normalization, and privileged-role rejection.
- Login verification, inactive accounts, JWT cookies, CSRF, logout,
  refresh, and invalid/expired sessions.
- Email verification valid/invalid/expired/reused tokens, resend cooldown,
  rate limiting, and safe email-provider failure behavior.
- Admin/Superadmin account-management differences, denied role escalation,
  superadmin role assignment, self-lockout rejection, and superadmin-only
  read-only audit access.
- Generic password-reset responses, invalid/expired/reused reset tokens,
  provider-failure handling, password change, and refresh-session revocation.
- Consultant/student ownership and assignment boundaries in existing
  applications and consultations tests.

One test was skipped because it is explicitly PostgreSQL-only; the test
settings use their configured test database and are not PostgreSQL proof.
PostgreSQL evidence below is from the separate migration rehearsal, not a
claim that the complete suite ran against PostgreSQL.

## PostgreSQL rehearsal details

- Verified archive size: 135,061 bytes.
- SHA-256: `B585A8E792D653B50384570B7A112FB08AC9449D93A80BA11EA0F20DF4B47EFD`.
- Restored backup baseline: 27 public tables, 1 user, account migration
  `0001_initial`.
- Forward migration target: `accounts.0003`; both pending account migrations
  applied successfully.
- Audit table: 8 columns, 5 indexes, 2 foreign keys.
- User count and pre-existing application-table counts remained unchanged.
- Reverse migration target: `accounts.0001`; both newly-created account tables
  were removed and existing application-table/user counts remained unchanged.
- Disposable rehearsal database was dropped. The original local database was
  only queried for migration status and remains unmigrated.

An initial attempt to create the disposable database used a transactional
connection and PostgreSQL rejected `CREATE DATABASE` inside a transaction.
No database was created or migration run by that attempt. The rehearsal was
then rerun with autocommit enabled and completed successfully.

## Frontend browser check

The local Next.js production build was opened at `/student/login` and
`/student/register` at a 375x812 viewport. The expected heading and form
controls were present, and neither page had horizontal overflow. This was a
basic layout check, not a full visual, keyboard-accessibility, screen-reader,
or role-redirection test.

## Original local migration state

Read-only `showmigrations` reports these five unapplied migrations:

- `accounts.0002_emailverificationtoken`
- `accounts.0003_securityauditevent`
- `opportunities.0005_opportunity_documents_required_and_more`
- `opportunities.0006_opportunity_management_mvp`
- `scholarships.0004_opportunity_management_mvp`

No migrations were applied to the original local database, no production
database was accessed, and no deployment or Git push occurred.

## Known validation limits

- Real SMTP/provider delivery and domain verification remain unverified.
- The full test suite did not run against PostgreSQL; only the account
  migration chain was rehearsed on the disposable PostgreSQL restore.
- Browser checks did not submit registration/reset forms or test all protected
  routes for each actor role.
- Security review was not an independent penetration test.

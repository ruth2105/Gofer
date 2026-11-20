# Gofer Exam Project Audit

**Updated:** 2026-11-11
**Scope:** Repository implementation, automated local checks, and read-only
checks of the supplied public deployment URLs. No production credentials,
database, or private operations console were accessed.

## Status definitions

- **Working and tested:** Relevant automated tests or direct checks passed for
  the stated scope; this does not imply production readiness.
- **Implemented but not verified:** Code exists, but an end-to-end or deployed
  behavior was not verified.
- **Partially implemented:** Some pieces exist, but the stated product workflow
  is incomplete.
- **Broken:** A directly checked workflow or deployed endpoint did not work.
- **Not implemented:** No functioning workflow was found.
- **Blocked by external requirements:** Completion depends on provider,
  configuration, durable infrastructure, verified content, or operational
  approval.

## Executive summary

The repository contains substantial Django API and Next.js functionality. The
backend suite (now 167 tests, 1 skipped), Django checks, migration-drift check,
frontend type check, lint, and production build passed locally. This is not
equivalent to a verified production release.

**The current deployment is not production-ready.** The Vercel URL returned
HTTP 404; the Render preview loaded; and the live API schema returned HTTP 200
but did not include the repository's email-verification or resend endpoints.
The scholarship preview displayed a genuine empty state with zero records.
Production email configuration, real delivery, persistent file storage, and a
tested database recovery path remain unverified.

## Feature audit

| Feature | Status | Evidence, affected areas, risk, and recommended next step |
|---|---|---|
| Registration and email verification | **Broken in current deployment; implemented locally** | Local tests cover unverified registration, token verification, expiry/reuse, resend, and delivery failure. Frontend and backend flows exist in [registration](./app/student/register/page.tsx), [verification](./app/student/verify-email/page.tsx), and [accounts](./backend/apps/accounts/). The live schema did not expose the verification/resend routes. Production email settings are required and were not validated. Align deployments and verify the full flow in staging with a test provider before inviting users. |
| Login, logout, session and CSRF | **Working and tested locally; live parity not verified** | Backend tests cover login/session behavior, HttpOnly JWT cookies, refresh/logout, and CSRF. The frontend client handles cookie sessions and eligible refreshes in [client.ts](./lib/api/client.ts). Login has no dedicated endpoint throttle in the inspected configuration; add one and run live access-control tests. [Development settings](./backend/config/settings/development.py) and shared base settings also retain fallback credentials intended for local use; use unique local values and avoid carrying these defaults into shared environments. |
| Password reset | **Not implemented** | The frontend password-help route explicitly says reset is unavailable: [forgot-password](./app/student/forgot-password/page.tsx). Add a secure, expiring, single-use reset workflow before representing password recovery as a service. |
| Student profiles and country registry | **Implemented but not fully verified** | Profile APIs, country references, and a profile editor/completion display exist in [students](./backend/apps/students/) and [profile page](./app/student/profile/page.tsx). Automated backend coverage exists; no production browser journey was verified. Region/subregion data is not populated from a verified source. |
| Scholarships and eligibility matching | **Implemented but not fully verified** | Public published-record APIs, admin publishing, filters, and structured matching (country, degree, GPA, field) are implemented in [scholarships](./backend/apps/scholarships/). The live preview displayed **0 of 0 scholarships** and an explicit empty state. Publish only verified current records; check the client mapper's handling of unknown enum values in [scholarship client mapping](./lib/api/scholarships.ts). Language and other unstructured eligibility criteria are not evaluated. |
| Opportunities, jobs, internships | **Partially implemented** | Admin-authored, reviewed opportunities have publication/source checks and public listing/detail APIs in [opportunities](./backend/apps/opportunities/). Automated collection, scheduling, retries, and deadline extraction are absent. Jobs/internships share general opportunity categories; dedicated employment-type, salary, remote, and experience filters were not found. Maintain official-source review and expiry procedures. |
| Universities and study destinations | **Implemented but not verified** | API-backed list/detail pages and backend tests exist in [universities](./backend/apps/universities/) and [destinations](./backend/apps/destinations/). Current live record coverage was not confirmed. Programs, comparison, verified admissions requirements, and student assistance workflows remain incomplete. |
| Student application tracking | **Working and tested locally; provider submission not implemented** | Authenticated students can create drafts, mark them submitted in their tracker, and withdraw; ownership/status tests exist in [applications](./backend/apps/applications/). “Submitted” updates the platform tracker; it does not transmit an application to an institution. The API serializer checks target/type consistency, but the database has no matching constraint. Add a database invariant after a reviewed migration plan. |
| Consultant and consultation workflows | **Implemented but not fully verified** | Assigned-case review and request/confirm/cancel/complete/feedback flows exist in [consultations](./backend/apps/consultations/) and [consultant pages](./app/consultant/). Tests exist, but there was no deployed browser journey, calendar sync, reminder delivery, or payment verification. |
| Documents | **Partially implemented** | A document model/admin exists in [document models](./backend/apps/documents/models.py), but no student-owned upload/download API or frontend workflow was found. Private durable storage, scanning/content validation, ownership checks, and retention controls are prerequisites; do not collect personal documents before these exist. |
| Notifications | **Partially implemented** | Authenticated in-app list/read/unread APIs and a frontend page exist in [notification views](./backend/apps/notifications/views.py) and [notifications page](./app/notifications/page.tsx). Email/Telegram delivery, preferences, retrying workers, and scheduled reminders are absent. |
| Exam preparation | **Partially implemented** | IELTS, TOEFL, and DET guidance and a short generic quiz exist in [exam preparation](./app/exam-prep/). This is not an exam-format simulation or scored learning product; current-format validation, lessons, study plans, and progress tracking remain. |
| Admin | **Partially implemented** | Django Admin supports operational record management; the custom frontend admin page is a metrics overview, not a full management console ([admin page](./app/admin/page.tsx)). Verify staff authorization and operational usability before relying on it. |
| Payments and rewards | **Not implemented** | No functioning payment, referral, or rewards workflow was found. Select providers and approve legal, refund, and support policies before implementation. |
| Public frontend and accessibility | **Implemented but not fully verified** | Routes render in the production build and loading/error/empty states are present across several pages. A limited preview smoke check at mobile/tablet/desktop widths found no horizontal overflow on registration, login, and scholarships. No comprehensive visual, keyboard, screen-reader, or end-to-end suite exists. Nested link/button controls and a profile-save error-state issue were identified; see [navigation](./components/layout/Navigation.tsx), [button](./components/ui/Button.tsx), and [profile page](./app/student/profile/page.tsx). |
| Production hosting and data operations | **Broken / blocked by external requirements** | The supplied Vercel URL returned HTTP 404. The Render preview returned HTTP 200. The live API schema was reachable but lacked verification routes present in the repository. The Render blueprint uses a free database with 30-day expiry and does not configure durable private media storage. No production backup/restore drill was evidenced. Resolve deployment parity, durable persistence, and provider configuration before production use. |

## Public deployment checks

Read-only checks of the supplied URLs found:

- `https://gofere.vercel.app/`: HTTP 404.
- `https://gofere-web-preview.onrender.com/`: HTTP 200; the student
  registration, login, and scholarship pages loaded.
- Render preview scholarship catalogue: loaded its explicit empty state,
  reporting zero published records.
- Live public API list endpoints returned HTTP 200 and zero records for
  scholarships, universities, destinations, and services.
- Live API `opportunities/`, `countries/`, `consultations/consultants/`,
  `auth/verify-email/`, and `auth/resend-verification/` returned HTTP 404. The
  reachable API schema listed scholarships, services, universities, and
  destinations, but did not list those missing routes. This is evidence that
  the deployed API is behind the checked-in backend; it is not evidence that
  the database contains no unpublished rows.
- The live applications endpoint returned HTTP 401 without a session, which is
  consistent with its authenticated permission. No real student or consultant
  account was used to test protected journeys.
- API reads through the Render preview proxy reproduced the backend route and
  data state. The proxy works for the available catalogue endpoints; an
  unavailable backend route remains unavailable through the proxy.
- The Render preview returned HTTP 200 for the public catalogue, exam-prep,
  student, application, and consultant page routes. This only verifies page
  rendering, not successful protected workflows. API CORS checks returned the
  expected `Access-Control-Allow-Origin` and credential headers for both the
  Vercel and Render preview origins. The frontend normally uses a same-origin
  rewrite, so CORS is not the cause of the missing API routes or empty data.
- At viewport presets of 390, 768, and 1440 CSS pixels, registration, login,
  and scholarships had no measured horizontal overflow. This smoke check does
  not certify all routes, devices, browser engines, or accessibility.
- The Vercel dashboard redirected to its login page, so project root directory,
  environment variables, build settings, alias assignment, and latest
  deployment status could not be inspected. The repository has a root
  `package.json`, `next.config.ts`, and `app/` directory, which are consistent
  with a Next.js project rooted at `.`.

No live account was created, no production email was sent, and no production
database was queried directly; the public list API cannot distinguish an
empty table from unpublished or source-filtered records. No production data was
changed.

## Validation results

| Check | Result |
|---|---|
| Django full test suite (`config.settings.test`) | **Passed:** 167 tests, 1 skipped. Tests use an in-memory SQLite database and Django's in-memory email backend; this does not test production infrastructure or real email delivery. |
| `python manage.py check` | **Passed:** no issues. |
| `python manage.py makemigrations --check --dry-run` | **Passed:** no model/migration drift detected after adding the opportunity detail fields. |
| `npx tsc --noEmit` | **Passed.** |
| `npm run lint` | **Passed.** |
| `npm run build` | **Passed:** optimized Next.js production build and static route generation completed. A non-blocking warning noted an ancestor `package-lock.json` outside the repository. |
| `manage.py check --deploy` | **Not a production sign-off:** invoked with test settings. It reported 42 warnings, including schema-generation warnings for the custom cookie authenticator/path typing and security warnings expected from test settings. Run and resolve a production-settings check only after safe production configuration is available. |
| Browser/API end-to-end suite | **Not available:** no frontend automated test script or complete end-to-end suite is configured. Limited public-page smoke checks only. |
| Production database migration state, backup/restore | **Not verified.** |
| Real email provider acceptance/domain delivery | **Not verified; configuration remains required.** |
| Vercel project settings/deployment | **Not verified:** dashboard access requires sign-in; the custom domain returned HTTP 404 with Vercel server headers. |

The production settings in [production.py](./backend/config/settings/production.py)
fail fast without valid production email configuration and enforce key HTTPS,
host, secret, and database requirements. The names and setup guidance are in
[backend/.env.example](./backend/.env.example) and [render.yaml](./render.yaml);
no values or credentials are recorded in this report.

## Priority plan for review

### P0 — Deployment and user-data safety

1. Reconcile Vercel/Render frontend and API revisions. Resolve the Vercel 404
   and confirm the live API exposes the same auth contract as the checked-in
   code. Deploy only after explicit approval; no deployment was performed here.
2. Configure a real email provider and sender domain, run a controlled staging
   verification flow, and confirm provider acceptance and inbox behavior.
3. Replace temporary preview persistence with durable database and private file
   storage; define retention and complete a restore drill before storing real
   student data.
4. Review and rotate any deployment-hook credential that may have been exposed
   in prior operational views. No credential value is reproduced here.

### P1 — Authentication and data integrity

5. Implement password reset and login throttling; validate throttling across
   production workers with shared cache.
6. Add database-level application target/type consistency through a reviewed,
   non-destructive migration; retain existing records and test legacy data.
7. Implement private document workflows with ownership, scanning/validation,
   durable storage, and retention controls before accepting uploads.
8. Correct the frontend/API enum-mapping failure mode and ensure profile-save
   success is not reported as failure when only the completion refresh fails.
9. Resolve nested interactive controls and run keyboard/assistive-technology
   checks.

### P2 — Content and product completion

10. Assign editorial owners for verified opportunities, scholarships,
    universities, and destinations; publish only current records backed by
    authoritative sources and promptly expire stale listings.
11. Add a monitored notification/reminder worker, calendar support, and
    dedicated job filters only after requirements and operational ownership are
    approved.
12. Expand exam practice, payments, rewards, and student-support workflows
    after validating provider, policy, and legal requirements.
13. Add frontend contract and browser end-to-end tests across key student and
    consultant journeys, devices, and accessibility requirements.

## Changes made for this audit

- Updated this evidence-based audit and its priority plan.
- Added [MAINTENANCE.md](./MAINTENANCE.md) with architecture, environment-variable
  names, recovery guidance, testing, release, and security checklists.
- Added opportunity nationality eligibility and required-document fields to the
  local model/admin/API/detail-page contract, with an additive migration.
- Improved API error reporting, added guards for malformed pagination, displayed
  scholarship nationality and document requirements, and made production
  frontend builds require an explicit API proxy target.
- Updated the scholarship admin to expose nationality eligibility controls and
  documented a verified-content review/import process.
- No production data was changed. No push or deployment was performed.

# Gofer Exam Actor Functionality Audit

**Assessment date:** 2026-11-12
**Phase:** Phase 1 inspection baseline; see the Phase 2 implementation update below
**Repository:** `C:\Users\user\Desktop\abc\gofer-exam`
**Branch / HEAD:** `master` / `d2626774530a8f377cae348a07d6585c9484aa0a`

## Executive summary

> **Current-state note:** The findings below record the Phase 1 snapshot and
> are superseded where they differ from the
> [Phase 2 update](#phase-2-authentication-and-authorization-update). Phase 2
> introduced password recovery, role-management APIs, separate Admin and
> Superadmin permissions, and a Next.js session-marker proxy. It did not apply
> migrations to the original local database or verify live email delivery.

The project has four stored account roles - `STUDENT`, `CONSULTANT`, `ADMIN`,
and `SUPERADMIN` - plus unauthenticated guests. Several important actor
workflows exist locally: student registration and email verification, student
profiles, scholarship matching, an internal application tracker, consultation
booking and assigned-consultant actions, in-app notifications, and an
administered opportunity catalogue.

The system is not yet a complete actor platform. The most material gaps are:

- The application API treats `ADMIN` and `SUPERADMIN` as the same role; no
  separate superadmin-only application capabilities or frontend exist.
- The frontend admin route is an overview, not an administrative management
  console. Django admin is the principal management surface.
- No student document API/upload workflow, saved-opportunity workflow,
  opportunity application workflow, password-reset workflow, or payment
  integration was found.
- Application submission is an internal tracking action, not submission to a
  university, scholarship provider, employer, or external application system.
- Consultant access is scoped to assigned applications and consultations, but
  consultant profile management, assignment management, and private application
  notes are not implemented as dedicated workflows.
- No Next.js `middleware.ts` or `proxy.ts` exists. Browser-side route checks
  cannot replace backend authorization.
- Four migrations remain unapplied on the original local database, including
  the email-verification-token migration. The audit does not authorize applying
  them.

**Audit conclusion:** core actor foundations are present and some access-control
boundaries are covered by backend tests, but users cannot complete several
expected end-to-end journeys. Production behavior remains unverified.

## Scope and evidence

This is a source and existing-test audit, not a penetration test or a fresh
production check. No code, migrations, database records, production settings,
or deployment were changed. No production service was contacted.

Evidence includes the current backend views, serializers, permissions, models,
URL mounts, admin registrations, frontend route files and API client; existing
backend tests; and the prior
[Opportunity PostgreSQL fix report](./OPPORTUNITY_POSTGRESQL_FIX_REPORT.md).
That report records a backend run of **178 tests passed, 1 skipped**, Django
system checks passing, and no migration drift. These are historical local
validation results, not production verification. Frontend lint/build results
were not re-run for this audit.

The worktree was already dirty before this audit, including Opportunity MVP
changes, reports, and untracked migration files. Those changes were preserved.
The only files created for this phase are this report and
[ROLE_PERMISSION_MATRIX.md](./ROLE_PERMISSION_MATRIX.md).

## Actor model and authentication

`User.ROLE_CHOICES` defines the four stored roles. `User.is_admin` returns true
for both `ADMIN` and `SUPERADMIN`, and `IsAdminUser` delegates to that property.
The registration serializer accepts no role field and creates users as
`STUDENT`. The user self-update serializer only accepts first name, last name,
and phone number; the serialized role is read-only. This prevents a registrant
or ordinary profile update from selecting a privileged role.

The auth API provides CSRF, register, verify-email, resend-verification, login,
logout, refresh, and current-user routes. Student login is rejected until
email-verified. Registration, verification, and resend have DRF scoped
throttles. No DRF login throttle was found. A password-assistance page exists,
but it explicitly says password reset is unavailable and there is no reset API
route.

Authentication uses JWT cookies and CSRF-protected session-changing auth
views. API permissions and owner-scoped querysets provide the real data
boundary. The frontend has no server-side route middleware file, so a hidden
dashboard link or client-side redirect must not be treated as authorization.

## Actor-by-actor findings

### Guest

- Can browse public catalogue pages and public read-only APIs for published
  scholarships and opportunities, universities, destinations, services, and
  countries.
- Cannot use the authenticated personalized scholarship-eligibility endpoint,
  student/consultant workflows, notifications, or application tracker.
- Can register only as a student through the public registration API.
- Cannot reset a forgotten password.
- Exact public data depends on deployment and catalogue contents; those are not
  verified here.

### Student

- Can register, verify email, log in, maintain their own student profile, and
  read profile-completion feedback.
- Can request personalized scholarship-eligibility results; unknown
  nationality/eligibility remains a verification state rather than a positive
  match.
- Can create and manage only their own application records. The supported
  application targets are a university or scholarship, not a job, internship,
  or general opportunity.
- Can mark an internal application record submitted or withdraw it. This does
  not transmit an application to the external provider.
- Can list verified/available consultants, request/cancel consultations, and
  provide feedback after completion. Student consultation querysets are
  restricted to the requesting student.
- Can read and update their own in-app notification state.
- Cannot upload/manage documents through an API, save/bookmark opportunities,
  apply to an opportunity through Gofer, purchase services, or make payments.
- Profile schema includes sensitive values such as passport number and
  emergency-contact information. The API is authenticated and self-scoped;
  encryption-at-rest and production media/storage controls are not established
  by this audit.

### Consultant

- Can list and search applications assigned to the authenticated consultant;
  unassigned and other-consultant records are filtered out.
- Can move an assigned submitted application into review. A status update is
  added to the student-visible status timeline and a student notification is
  created.
- Can list only assigned consultations and confirm, cancel, or complete those
  consultations. Completion notes/action items are stored on the consultation.
- The consultant directory exposes only active, verified, available consultant
  profiles to authenticated students.
- No dedicated consultant profile-editing, availability/calendar management,
  application-assignment, workload/task, or private-application-note API was
  found. Consultant directory fields are managed outside a consultant
  self-service API.
- The application review note is part of `status_updates`, which is serialized
  to the student. It is not a private consultant note; sensitive internal
  commentary must not be placed there.

### Admin

- The admin overview API returns aggregate user, catalogue, application, and
  consultation counts and is guarded by authenticated admin permission.
- Django admin is the primary management UI for users, consultations,
  documents, scholarships, opportunities, sources, and related catalogue data.
- Opportunity API writes are admin-only. Opportunity publication safeguards
  require valid verified source records; the previous fix report records
  invalid publication returning HTTP 400 and a valid publication succeeding
  against a disposable PostgreSQL database.
- The Next.js `/admin` page is an overview, not a complete user, consultant,
  application, document, payment, or catalogue management console.
- Django `UserAdmin` exposes the role and Django permission fields to users who
  have the relevant Django admin permissions. This is a privileged operation
  and lacks a separately verified ADMIN-versus-SUPERADMIN policy in the
  application layer.

### Superadmin

- `SUPERADMIN` satisfies the same `is_admin` check as `ADMIN` for application
  API permissions. There are no separate superadmin-only API routes or
  superadmin frontend pages in the inspected route/API surface.
- Django's `is_superuser`/`is_staff` flags add built-in Django admin authority,
  but that is not equivalent to a defined, tested product-level superadmin
  workflow or separation of duties.
- No application-level immutable audit log or controlled superadmin-only role
  assignment workflow was found.

## Cross-cutting feature status

| Area | Status | Evidence and limitation |
|---|---|---|
| Authentication / registration | **Implemented and verified locally** | Cookie JWT auth, CSRF, registration and login routes exist; student role is fixed at registration; backend tests cover auth. Production is unverified. |
| Email verification | **Implemented and verified in test database** | Token expiry/use, resend cooldown, throttles, and delivery-failure behavior have implementation/tests. Its migration is unapplied on the original local database; real provider acceptance is unverified. |
| Student profile | **Implemented, with gaps** | Authenticated self profile/completion APIs exist. Profile lacks some job-readiness and application-workflow data; production privacy/storage controls are unknown. |
| Scholarship discovery | **Implemented and verified locally** | Public published-only list/detail and authenticated personalized eligibility API exist. Original local aggregate count is zero; production data is unknown. |
| Job/internship discovery | **Partially implemented** | Opportunity categories and related frontend routes/schema exist in current source, but migrations are unapplied locally, no opportunity application/saving flow exists, and no genuine data availability is established. |
| Opportunity source review | **Implemented locally, not production-verified** | Source and source-record models/admin and publication checks exist. The original local database has no source/opportunity records; migrations remain pending. |
| Applications | **Partially implemented** | Student tracker and assigned consultant review work locally; only scholarship/university targets; external submission is not performed; history is JSON rather than a dedicated immutable event model. |
| Consultations | **Implemented locally with gaps** | Student booking, verified-consultant directory, scoped consultant actions, and in-app notices exist. No external calendar/video/payment/reminder integration or production journey is established. |
| Documents | **Partially implemented / student workflow missing** | Document model and Django admin exist. No mounted document API or student upload/download workflow exists. Production private storage, scanning, retention, and parent-object authorization are unknown. |
| Services | **Partially implemented** | Public service catalogue exists; purchase, payment, and service fulfillment workflows do not. |
| Payments | **Missing** | No provider, payment ledger, webhook, reconciliation, or refund workflow found. Consultation payment booleans/amounts are not evidence of payment processing. |
| Notifications | **Partially implemented** | Authenticated in-app list/read APIs and workflow-created notices exist. External delivery, durable outbox/retry, and preferences are not established. |
| Admin dashboard | **Partially implemented** | API-backed metrics page plus Django admin. No broad Next.js management console or separate superadmin workspace. |
| Password reset | **Missing** | Frontend page explicitly states reset is not available; no backend route. |
| Frontend route protection | **Partially implemented** | Client-side role checks exist in dashboards; no `middleware.ts`/`proxy.ts`; server/API authorization must remain authoritative. |
| End-to-end actor verification | **Unverified** | Existing backend tests cover selected role/ownership boundaries. No configured frontend test suite was found; a live production actor journey was not run. |

## API surface relevant to actors

The root URL configuration mounts:

- `auth`: CSRF, register, verify/resend, login/logout/refresh, current user.
- `applications`: student-owned tracker, consultant-assigned applications/review,
  and admin overview metrics.
- `consultations`: student booking/feedback/cancellation, student-only
  consultant directory, and consultant-assigned consultation actions.
- `notifications`: authenticated in-app notifications.
- `students`: authenticated student profile and completion.
- `scholarships`: public catalogue and authenticated eligibility matching.
- `opportunities`: public catalogue/detail and admin write actions.
- `countries`, `universities`, `destinations`, and `services`: catalogue APIs.
- API schema and Swagger/Redoc documentation.

No mounted document or payment API, saved-opportunity API, password-reset API,
consultant-profile self-service API, or student opportunity-application API was
found. Some administration exists only in Django admin and should not be
mistaken for a supported public/product API.

## Database, tests, and deployment boundary

- Prior database reports identify **four unapplied migrations** on the
  original local database: `accounts.0002_emailverificationtoken`,
  `opportunities.0005`, `opportunities.0006`, and `scholarships.0004`.
  Opportunity `.0006` depends on `.0005`. Do not infer the original local
  database has the current model schema.
- The latest recorded local aggregate snapshot was 1 user, 249 countries, and
  zero scholarships, opportunities/source records, applications, universities,
  destinations, and services. These are historical local counts only; no
  student personal data is included. They are not current production counts.
- Latest recorded backend evidence is 178 tests passed and 1 skipped, Django
  system checks passing, and no migration drift. The source/report indicates
  selected ownership, assigned-consultant, publication, and authentication
  tests. Tests run on the configured test database and do not prove the
  original database was migrated.
- `package.json` provides lint and build scripts but no frontend test script;
  no frontend unit/e2e test files were found in the repository route/test
  search.
- Production deployment health, database schema/counts, role assignments,
  provider configuration, and end-to-end journeys are **UNKNOWN** for this
  Phase 1 audit. Prior status documents contain historical HTTP observations;
  they were not rechecked by contacting production.

## Recommended implementation order

1. **Close schema readiness first.** Review migration files and the existing
   backup/rehearsal evidence, then follow the separate explicit-approval process
   before applying anything to the original local database.
2. **Define the privileged-role policy.** Specify ADMIN versus SUPERADMIN
   powers, guard user/role administration, and add backend tests for role
   assignment and every privileged endpoint.
3. **Complete student account recovery and secure documents.** Implement and
   test password reset; only then design a student-owned upload/download path
   with private storage and authorization tests.
4. **Clarify application semantics.** Separate internal tracking from external
   submission, introduce explicit workflow/audit history, and design student
   application support for opportunities only after product requirements are
   agreed.
5. **Add consultant operations.** Define profile/availability, assignment,
   private note, and task workflows without leaking internal notes to students.
6. **Build the admin/superadmin console and supporting APIs** around the
   approved permission model; preserve publication and source-review safeguards.
7. **Add real notifications/payments only with provider requirements,** then
   verify retries, idempotency, privacy, and failure behavior.
8. **Run role-by-role end-to-end tests** on a disposable/local test environment
   across guest, student, consultant, admin, and superadmin; separately verify
   deployment only when authorized.

See [ROLE_PERMISSION_MATRIX.md](./ROLE_PERMISSION_MATRIX.md) for the observed
role-to-action mapping and unimplemented capabilities.

## Phase 2 authentication and authorization update

**Assessment date:** 2026-11-12  
**Evidence:** Current source, Django API tests, Django checks, migration
rehearsal on a disposable PostgreSQL restore, frontend checks, and a local
375px browser layout check. No production service was contacted.

### Implemented and tested locally

- Registration explicitly rejects submitted privileged roles and creates
  student accounts. Existing cookie-based JWT, CSRF, email-verification, and
  inactive-account protections were retained.
- Login, refresh, logout, email verification, and resend remain under the
  existing auth routes. Login and recovery endpoints now have scoped
  throttling.
- Password reset uses Django's single-use token generator with a one-hour
  expiry, a generic non-enumerating request response, HTML and plain-text
  templates, password validation, and refresh-token revocation. Authenticated
  password change also revokes refresh sessions.
- `IsAdmin` and `IsSuperAdmin` distinguish ordinary administrators from
  superadmins. Admin user-management access is limited to student and
  consultant accounts. Role changes and administrative activation changes are
  superadmin-only through the user-management API; sensitive account changes
  are written to `SecurityAuditEvent`.
- A read-only audit-events API is superadmin-only. Consultant self-profile
  access is available through the existing consultation API and excludes
  verification/system-owned fields.
- Existing owner- and assignment-scoped querysets and permissions were
  preserved and strengthened for applications, consultations, notifications,
  student profiles, scholarships, and opportunities.
- Next.js `proxy.ts` checks an HttpOnly session-marker cookie for protected
  navigation and preserves the requested destination on login redirects. The
  marker is a usability gate only; backend authentication and authorization
  remain authoritative.

### Current boundaries and blockers

- Frontend proxy checks session presence, not actor role. Role-specific page
  redirects are not a substitute for complete route-by-route role gating;
  direct API authorization is the security boundary and was exercised by
  backend tests.
- Legacy endpoints using the shared admin permission still allow both Admin
  and Superadmin where the action is shared. A dedicated product API for
  arbitrary Django permission/system-setting administration is not present.
- Student documents still have no private student upload/download API;
  opportunity saving and job/internship application workflows are also
  missing. Internal application tracking is not external submission.
- The configured email backend was exercised through Django's test backend,
  including simulated provider failures. Acceptance by a real email provider
  and sender-domain verification remain unverified.
- The original local database remains unmigrated. It has five pending
  migrations: `accounts.0002_emailverificationtoken`,
  `accounts.0003_securityauditevent`, `opportunities.0005`,
  `opportunities.0006`, and `scholarships.0004`. The new `accounts.0003`
  depends on `accounts.0002`. The account migration chain passed forward and
  reverse rehearsal only on a disposable database restored from the verified
  local backup.
- Production configuration, provider acceptance, deployment, and real-user
  journeys were not tested.

### Current validation

- Backend: 197 tests passed, 1 skipped; Django system checks passed; migration
  drift check reported no changes.
- Frontend: ESLint, TypeScript, and production build passed. Local browser
  checks at 375px rendered login and registration headings/forms without
  horizontal overflow.
- PostgreSQL: restored backup baseline had 27 public tables and 1 user.
  Forward migration created the verification-token and audit tables; the
  audit table had 8 columns, 5 indexes, and 2 foreign keys. Existing
  application-table counts and user count remained unchanged. Reverse
  migration on the disposable database removed both tables and preserved
  existing counts. The disposable database was dropped afterward.

## Phase 2.1 route and email-readiness update

**Assessment date:** 2026-11-12  
**Evidence:** Current frontend source, route-policy unit tests, local browser
route checks with stubbed `/auth/me/` responses, backend auth/permission tests,
and production-settings configuration checks. No email was sent and no
production service was contacted.

### Role-aware navigation and route handling

- The root auth provider checks the current account and rechecks on client
  route transitions. Protected route content waits for this check.
- Students are routed to `/student`, consultants to `/consultant`, Admins to
  `/admin`, and Superadmins to the distinct `/admin/security` audit landing.
- Student routes are Student-only; consultant routes are Consultant-only;
  `/admin` is for Admin/Superadmin; `/admin/security` is Superadmin-only; and
  notifications are available to all authenticated roles.
- Guests remain on public routes. A guest navigation to protected routes is
  redirected to login with a same-origin `next` destination. A role mismatch
  redirects to that role's dashboard. Unsafe or cross-role login destinations
  are rejected.
- Navigation keeps public links available and conditionally renders the
  current role's dashboard/management links. Admin navigation does not show
  Security Audit; Superadmin navigation does.
- Failed session refresh is handled by the shared guard and preserves a safe
  return destination. A temporary account-check error does not render
  protected children and offers retry.
- The new route checks are UI usability controls only. Direct API access is
  still controlled by Django permissions/querysets. The API tests cover
  account management, audit visibility, ownership, assignment, and role
  separation.

### Email readiness

The local backend `.env` exists, but inspection found no email configuration
variables there or in the process environment. Resolved local settings use
Django's console email backend, `webmaster@localhost`, and the localhost
frontend URL. Production-safe provider configuration is therefore **not
available** in this environment. No recipient/test account was supplied, so
no message was sent.

Production settings now reject console, dummy, in-memory, and file-based
email backends; validate a non-placeholder sender; and, for SMTP, require a
host, valid port, encrypted TLS/SSL, and either both credentials or neither
for an explicitly authorized relay.

Required setup before delivery verification:

1. Select the transactional provider and its SMTP endpoint or supported
   provider backend.
2. Verify the sender domain with that provider and publish its required
   SPF/DKIM records; configure a DMARC policy.
3. Configure `DJANGO_SETTINGS_MODULE=config.settings.production`,
   `GOFER_FRONTEND_URL` as the public HTTPS frontend origin,
   `EMAIL_BACKEND`, `GOFER_EMAIL_FROM`, `EMAIL_HOST`, `EMAIL_PORT`,
   `EMAIL_USE_TLS` or `EMAIL_USE_SSL`, and `EMAIL_TIMEOUT`. Set
   `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` together when the provider
   requires authentication. Store credentials in the hosting platform's
   secret manager, never in source control.
4. With an explicitly authorized mailbox, send one verification message and
   one password-reset message. Confirm actual receipt, correct sender and
   HTTPS link host, token expiry/reuse behavior, and provider acceptance
   logs. Do not use student addresses without authorization.

### Phase 2.1 validation

- Route-policy unit tests: **5 passed**.
- Browser route checks with stubbed identity: Guest redirect; Student denied
  from Consultant workspace; Consultant denied from Student applications;
  Admin denied from Superadmin security; Superadmin denied from Student
  profile. A full live API-backed actor journey was not possible because the
  local API provider was not running.
- Mobile navigation checks at 375px: Superadmin displayed Security Audit and
  Admin Overview; Admin displayed Admin Overview but not Security Audit.
  Observed document width was 360px, with no horizontal overflow.
- Full backend, lint, type, and build results are recorded in
  [PHASE2_1_COMPLETION_REPORT.md](./PHASE2_1_COMPLETION_REPORT.md).

### Remaining gaps

- The original local database still has five pending migrations. In
  particular, the `accounts_securityauditevent` table is absent until
  `accounts.0002` and `.0003` are explicitly approved and applied; the audit
  screen cannot provide live events against that schema yet.
- Real email delivery, provider acceptance, sender-domain verification, and
  production role behavior remain unverified.
- Navigation and client route guards do not replace backend authorization.
- Document access and opportunity saving/application workflows remain outside
  this Phase 2.1 scope.

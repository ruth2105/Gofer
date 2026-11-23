# Gofer Exam — Current Project Status

**Audit date:** 2026-11-12

**Repository:** `C:\Users\user\Desktop\abc\gofer-exam`

**Audit type:** Read-only project audit, except for creating this report. No
application code, database records, migrations, deployment settings, or secrets
were changed.

## 1. Executive summary

Gofer Exam is an **early MVP / integration and deployment-recovery project**.
It has meaningful Django APIs, a broad Next.js App Router frontend, 17 domain
models, local backend tests, and operational content-review scaffolding. It is
not production-ready: production availability is currently impaired, the
public catalogue has no locally available records, key user workflows are
missing or incomplete, and durable data recovery and private document storage
are not established.

### Overall completion estimate: **about 40%**

This is a reasoned product-scope estimate, not a measured code or test
percentage. It counts the existence and local verification of core
authentication, profiles, catalogues, applications, consultations, and
administrative APIs, but weighs down the score for:

- The failed latest backend deployment and the Vercel 404.
- Current 503/429 API observations and no current proof of frontend/backend
  compatibility.
- Zero scholarship, opportunity, university, destination, service, and student
  workflow records in the reachable local development database.
- Missing password reset, public job schema, secure document workflow,
  payments, and notification delivery.
- No confirmed production database counts/migration state, backup restore,
  email acceptance, or end-to-end user journey.

The status labels below mean:

- **IMPLEMENTED AND VERIFIED:** the relevant local automated test or build
  passed. It does **not** mean verified in production.
- **IMPLEMENTED BUT UNVERIFIED:** the repository contains the functionality,
  but adequate end-to-end evidence is absent.
- **PARTIALLY IMPLEMENTED:** part of the user-facing workflow exists, with
  material capability or safety gaps.
- **MISSING:** no functioning implementation was found.
- **BROKEN:** an observed required journey or endpoint failed in the stated
  environment.

**Production verification is separate and remains incomplete unless expressly
stated.**

## 2. Feature status matrix

| Module | Status | Evidence and limits |
|---|---|---|
| Authentication and registration | **IMPLEMENTED AND VERIFIED (local only)** | Registration/login/logout/current-user/refresh/CSRF routes exist in `backend/apps/accounts/`; cookie JWT and CSRF flows are covered by the backend suite. Production sign-in was not tested. Login has no dedicated throttle in current settings. |
| Student profiles | **IMPLEMENTED AND VERIFIED (local only)** | `StudentProfile` and authenticated profile/completion APIs exist; local backend tests pass. Local database contains 0 profiles. No production account journey was run. |
| Email verification | **IMPLEMENTED AND VERIFIED (local only)** | Secure token, expiration, resend/cooldown and delivery-failure handling exist with local tests. The local database is missing the token table and has its migration pending. Production email acceptance is unverified; the latest Render build failed on missing production email configuration. |
| Scholarships | **IMPLEMENTED AND VERIFIED (local API only)** | Public published-only list/detail, filters, source-record safeguards, and eligibility matching exist; scholarship API tests pass locally. Local DB contains 0 total/published/unpublished records. Latest live API calls returned 503 or 429; a prior preview GET on Nov. 11 returned HTTP 200 with zero results. |
| Jobs and internships | **PARTIALLY IMPLEMENTED** | Internship is an opportunity category, but there is no dedicated Job category or employment schema for employment type, compensation, experience, remote/location policy, or work authorization. |
| Opportunity search and filters | **IMPLEMENTED AND VERIFIED (local API only)** | Opportunity list/detail/search/filter/ordering APIs and page integration exist; backend tests pass. No current live API verification; opportunity-specific application and saved-item workflows are absent. |
| Universities and study destinations | **IMPLEMENTED AND VERIFIED (local API only)** | List/detail APIs, serializers, and frontend routes exist. Local counts are 0 universities and 0 destinations; live status/data are not currently verifiable. Programs remain embedded JSON/free text. |
| Applications and tracking | **IMPLEMENTED AND VERIFIED (local tests only)** | Authenticated student drafts and status actions plus assigned consultant review exist. “Submitted” is an internal tracker state, not submission to the institution. Target/type correctness is serializer-enforced, not database-enforced. |
| Document management | **PARTIALLY IMPLEMENTED** | `Document` model and Django admin exist. No mounted document API or student upload/download workflow was found. Private durable storage, scanning/content checks, ownership-to-parent enforcement, and retention are unestablished. |
| Consultancy services | **PARTIALLY IMPLEMENTED** | Service catalogue list/detail and administration exist. Purchase/payment and service transaction workflows are absent. Local service count is 0. |
| Consultation booking | **PARTIALLY IMPLEMENTED** | Student booking, consultant directory/assigned actions, and local API tests exist. No real provider/calendar/reminder integration or production journey was tested. The student dashboard also says booking is unavailable despite a dedicated consultations page; copy and actual availability are inconsistent. |
| Payments | **MISSING** | No payment provider integration, payment ledger, webhook processing, refund handling, or reconciliation workflow found. Boolean/amount fields are not payment evidence. |
| Notifications | **PARTIALLY IMPLEMENTED** | Authenticated in-app list/read/unread APIs exist. No durable email outbox, provider delivery/retries, notification preferences, or reminder worker found. |
| Admin dashboard | **PARTIALLY IMPLEMENTED** | Django admin provides data entry/review. The frontend admin route is a metrics overview, not a complete management console. Production admin access was not tested. |
| Data import and verification | **PARTIALLY IMPLEMENTED** | ISO country import exists; opportunity source/run/source-record review scaffolding exists. No scholarship/opportunity import pipeline or automated collector/scheduler was found. Publishing real catalogue data remains an editorial task. |
| User interface and mobile responsiveness | **IMPLEMENTED BUT UNVERIFIED** | 33 route page files are present and a production build generated 44 static/dynamic route variants. Tailwind responsive UI patterns exist, but no current comprehensive mobile/tablet/browser/accessibility or end-to-end suite is configured. A build does not verify functionality. |
| Password reset | **MISSING** | `app/student/forgot-password/page.tsx` explicitly says reset is unavailable; no backend reset route was found. |

### Frontend route inventory

The current Next.js build generated routes for:

`/`, `/about`, `/admin`, `/consultant`, `/consultant/consultations`,
`/contact`, `/disclaimer`, `/exam-prep`, `/exam-prep/[exam]`,
`/exam-prep/ielts`, `/exam-prep/toefl`, `/exam-prep/duolingo`,
`/exam-prep/practice-test`, `/faq`, `/notifications`, `/opportunities`,
`/opportunities/[slug]`, `/privacy`, `/scholarships`,
`/scholarships/[id]`, `/services`, `/services/[slug]`, `/student`,
`/student/applications`, `/student/consultations`,
`/student/forgot-password`, `/student/login`, `/student/profile`,
`/student/register`, `/student/scholarships`, `/student/verify-email`,
`/study-abroad`, `/study-abroad/[id]`, `/terms`, `/universities`,
`/universities/[id]`, plus not-found and route-validation entries.

Build output confirms route generation only; it does not prove each page's
API-backed user journey works.

## 3. Database status

### Schema inventory

- **17 application-owned models** across 13 Django apps:
  `User`, `EmailVerificationToken`, `StudentProfile`, `ConsultantProfile`,
  `Scholarship`, `University`, `Destination`, `Service`, `Application`,
  `Consultation`, `Document`, `Notification`, `OpportunitySource`,
  `CollectionRun`, `Opportunity`, `OpportunitySourceRecord`, and `Country`.
- **21 domain migration files** are present in the repository.
- Important relationships: user-to-student/consultant profiles; student-to-
  application; application-to-university or scholarship; consultation-to-
  student/consultant/service; document-to-user and optionally application/
  consultation; notification-to-user and optionally application/consultation;
  source-to-collection-runs and source records; source records optionally
  relate to scholarship/opportunity.
- Country, fields/programs, and application status are represented
  inconsistently across strings, JSON, and related rows. Application
  target/type and document parent ownership are not fully database-enforced.
- The [database architecture audit](./DATABASE_AUDIT.md) contains the detailed
  model-by-model inventory and Mermaid ER diagram.

### Local development database

Read-only aggregate inspection used Django development settings and confirmed
that the configured PostgreSQL host was loopback before querying. No production
connection or personal fields were printed.

| Module/data | Local count/state |
|---|---:|
| User rows | 1 |
| Student profiles | 0 |
| Consultant profiles | 0 |
| Email verification token table | **Missing** |
| Scholarships: total / published / unpublished | **0 / 0 / 0** |
| Opportunities | 0 |
| Opportunity sources / collection runs / source records | 0 / 0 / 0 |
| Universities | 0 |
| Destinations | 0 |
| Services | 0 |
| Applications | 0 |
| Consultations | 0 |
| Documents | 0 |
| Notifications | 0 |
| Countries | 249 |

The 1 user count is aggregate only; no student identity or account data is
included. The local database is not a production proxy.

### Migration state and readiness

- Local `showmigrations --plan` reported **two unapplied domain migrations**:
  `accounts.0002_emailverificationtoken` and
  `opportunities.0005_opportunity_documents_required_and_more`.
- The local database lacks the email verification token table, consistent with
  the first migration being unapplied.
- `makemigrations --check --dry-run` reported no model/migration drift. This
  checks migration files against current models; it does not mean migrations
  are applied to a database.
- **Production migration state: UNKNOWN.** No production DB query, credentials,
  or management operation was used.
- **Production aggregate counts: UNKNOWN.** Public list endpoints cannot
  reveal unpublished rows, and current API requests are failing.
- **Backup/restore status: UNKNOWN and not established.** No restore drill or
  durable recovery proof was available in this audit.

The local development database is **not schema-current** and the platform is
**not established as ready for real student data**. Production readiness also
requires verified persistent database/file storage, ownership/security review,
backups and tested restore.

## 4. Backend and API status

### Checked-in API surface

`backend/config/urls.py` mounts schema/docs, Django admin, and these API
families:

- `/api/v1/auth/`: CSRF, register, verify-email, resend-verification, login,
  logout, token refresh, current user.
- `/api/v1/students/`: current student profile and completion.
- `/api/v1/scholarships/`: public list/detail and authenticated
  `eligible-for-me`.
- `/api/v1/opportunities/`: public opportunity list/detail.
- `/api/v1/universities/`, `/destinations/`, `/services/`: public catalogue
  list/detail families.
- `/api/v1/countries/`: country registry.
- `/api/v1/applications/`: student workflows, consultant assigned review,
  admin overview.
- `/api/v1/consultations/`: consultant directory and student/consultant
  booking actions.
- `/api/v1/notifications/`: authenticated list/read/unread actions.
- `/api/v1/schema/`, `/docs/`, `/redoc/`.

There is **no mounted documents API**, no password reset endpoint, and no
payment endpoint. Exact route registration is in each app's `urls.py`.

### Contracts, permissions, and quality

- DRF defaults to cookie JWT authentication, `IsAuthenticated`, page-number
  pagination at 20 rows, and Search/Ordering backends; public viewsets override
  permissions explicitly.
- Read-only catalogue list/detail endpoints are public in source. Student,
  consultant, and admin actions have role/ownership guards exercised by local
  tests.
- Catalogue filters are configured per view; search/order availability is not
  identical across all endpoints. A shared normalized catalogue contract is
  not present.
- Scholarship list responses use the standard `{count,next,previous,results}`
  response. The Next.js client expects that shape. List serializers omit some
  optional detail fields; mapping defaults those fields. Production response
  schemas are currently inaccessible for comparison.
- `drf-spectacular` schema and Swagger/ReDoc routes are configured. The latest
  live schema probe on Nov. 12 returned HTTP 503; deployed endpoint parity is
  therefore **UNKNOWN**.
- A custom API exception handler is configured. Frontend errors distinguish
  several HTTP categories but generic service errors can hide operational
  detail from users. No centralized frontend telemetry/reporting was found.
- Production settings enforce HTTPS/security headers and fail fast when key,
  host, database, or email configuration is invalid. The shared base settings
  still define a development fallback secret; production validates against
  weak defaults.
- Registration, email verification, and resend have scoped throttles. A
  dedicated login throttle is absent. Shared distributed throttle/cache
  behavior was not verified.
- The test suite validates substantial local API behavior. It does not test
  production PostgreSQL, email provider acceptance, real file storage, or
  deployed browser workflows.

## 5. Frontend status

- Next.js 16 App Router and TypeScript pages cover public content, student
  authentication/profile/application/consultation routes, consultant actions,
  and a limited admin overview.
- The API client uses the same-origin `/api/v1` prefix with a Next.js rewrite.
  `render.yaml` declares `API_PROXY_TARGET` to the Render API. The actual
  Vercel project settings and frontend environment are not accessible here.
- Scholarship and other catalogue pages have loading, empty, error, and retry
  UI. Some pages have similar API-backed states. The scholarship page correctly
  rendered a zero-results state following an observed HTTP 200 empty response
  on Nov. 11; newer API probes on Nov. 12 failed with 429/503.
- Login/register/verification/profile/application forms exist. Password reset
  is explicitly not implemented. No browser-level form regression suite is
  configured.
- The student dashboard copy says consultation booking is unavailable while
  a separate booking page and backend actions exist. Reconcile this messaging
  and verify actual role/auth/API behavior.
- `app/student/page.tsx` states document upload is unavailable, consistent
  with the absence of a document API.
- Responsive classes are used, but current audit validation covered build
  output, not every viewport. Keyboard, assistive-technology, and broken
  navigation checks remain incomplete.

## 6. Production and deployment status

### Git and Render deployment evidence

- Local branch: **`master`**.
- Local `HEAD`: **`d2626774530a8f377cae348a07d6585c9484aa0a`**,
  commit date Nov. 11, 2026. Message: `feat: complete student platform workflows`.
- The worktree is **dirty**. It contains 25 modified tracked paths and
  pre-existing untracked audit/maintenance documents, an opportunity
  migration, and a model backup. This report is also newly created. Do not
  treat the worktree as the committed or deployed state.
- Render dashboard identifies **`30ab294a88315af3a80061b8d37946e0a00d0b97`**
  as the last successfully deployed API commit.
- The latest API deployment attempts for **`d262677...`** are marked failed.
  The checked deployment log's first fatal configuration message was:
  `Configure a production email backend and GOFER_EMAIL_FROM.`
  Dependency installation had succeeded before production settings rejected
  the missing required email configuration.
- Thus the checked-in current `HEAD` is not the last successful API deployment.
  Frontend preview commit and Vercel production deployment commit are
  **UNKNOWN**; frontend/backend compatibility cannot currently be established.

### Live URL checks performed on Nov. 12, 2026

| Target | Observed result | Interpretation |
|---|---|---|
| `https://gofere.vercel.app/` | **HTTP 404** | Production frontend domain is not serving the app at this check. Vercel project/team settings could not be confirmed. |
| `https://gofere-web-preview.onrender.com/` | **HTTP 200** | Preview home page rendered. This does not prove API functionality. |
| `https://gofere-api-ruth2105.onrender.com/api/v1/schema/` | **HTTP 503** | API/schema unavailable during this probe. |
| `https://gofere-web-preview.onrender.com/api/v1/schema/` | **HTTP 503** | Same-origin proxy could not provide schema during this probe. |
| Direct scholarship list on Render API | **HTTP 503** in the Nov. 11 diagnostic probe | Earlier probe only; not repeated directly on Nov. 12. |
| Preview scholarship proxy | **HTTP 429** in the Nov. 12 probe | Rate-limit response; not proof of empty data. |
| Preview scholarship proxy, Nov. 11 browser capture | **HTTP 200**, `{"count":0,"next":null,"previous":null,"results":[]}` | At that time the route and pagination worked but returned no public scholarships. See [scholarship diagnosis](./SCHOLARSHIP_DISPLAY_DIAGNOSIS.md). |

The Render API service and blueprint declare a PostgreSQL resource and
`DATABASE_URL` binding in [`render.yaml`](./render.yaml). This declaration does
not prove which database the live service is effectively using. Production
database identity, applied migrations, row counts, backup configuration, and
restore status remain **UNKNOWN**.

The blueprint start command runs `manage.py migrate --noinput` before Gunicorn.
Because Auto Sync was previously shown enabled in the Render dashboard, a
push to the tracked branch may trigger a deployment; no push or deploy was
performed during this audit.

### Required environment-variable names

Names only; no values are recorded. Frontend: `API_PROXY_TARGET`,
`NEXT_PUBLIC_API_URL` (legacy fallback), `NEXT_PUBLIC_APP_NAME`,
`NEXT_PUBLIC_APP_URL`. Backend: `DJANGO_SETTINGS_MODULE`, `PYTHON_VERSION`,
`SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`,
`CSRF_TRUSTED_ORIGINS`, `GOFER_FRONTEND_URL`, `EMAIL_BACKEND`,
`GOFER_EMAIL_FROM`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`,
`EMAIL_USE_SSL`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_TIMEOUT`,
`EMAIL_VERIFICATION_TOKEN_TTL_MINUTES`, `EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS`,
and `DJANGO_LOG_LEVEL`. Production values and secret state were not inspected.

## 7. Tests and code quality

All commands below were run locally on Nov. 12, 2026. Backend commands used
the repository virtual environment and `config.settings.test`, except the
read-only migration-state/count inspection, which used loopback-guarded
development settings.

| Check | Actual result |
|---|---|
| Full Django suite: `manage.py test --verbosity 1` | **Passed: 167 tests, 1 skipped.** Test database was ephemeral SQLite; logs included expected negative-path 4xx/5xx cases. This does not certify PostgreSQL or production. |
| `manage.py check` | **Passed:** no issues. |
| `manage.py makemigrations --check --dry-run` | **Passed:** no model/migration drift. Separate `showmigrations --plan` found two unapplied local migrations. |
| `npx tsc --noEmit` | **Passed:** exit code 0. |
| `npm run lint` | **Passed:** exit code 0. |
| `npm run build` | **Passed:** optimized production build; Next.js generated route output. Non-blocking warning: it ignored an ancestor `package-lock.json` outside this Git repository. |
| `git diff --check` | **Passed** for tracked changes. Git printed line-ending conversion warnings for some existing files. Untracked files are not included in that Git check. |
| Production API and frontend | **Not passed/verified:** Vercel 404; Render API probes 503/429. |
| Production DB, email provider, backups/restore, authenticated E2E | **Not verified.** |
| Frontend automated tests | **Not configured:** `package.json` has no frontend test script. |

## 8. Known blockers and risks

1. **Production frontend is broken at the provided domain:** Vercel returns
   404. Correct project/team/domain ownership and deployment settings remain
   unconfirmed.
2. **Latest API deployment failed:** current repo `HEAD` does not match the
   last successful API commit. Production email configuration caused the
   latest build failure.
3. **Live API is not reliably reachable now:** 503 and 429 responses prevent
   current endpoint/schema verification. The preview page alone is not proof
   of a healthy full stack.
4. **No production content counts:** local catalogues are empty, and live list
   endpoints cannot establish production totals or unpublished counts.
5. **Local DB is behind source migrations:** email-token and opportunity
   migration are pending locally. Production migration state is unknown.
6. **Persistence/recovery risk:** the blueprint declares a free database plan;
   durable production retention, backup/restore, and private media storage have
   not been proven.
7. **Sensitive documents are not safe to collect yet:** no user-facing API,
   verified private object storage, malware scan, parent ownership check, or
   retention controls exist.
8. **Security/product gaps:** password reset, dedicated login throttling,
   application target database constraint, payment ledger, and outbound
   notification delivery are missing.
9. **Content governance is manual:** sources and review models exist, but
   automated collection/expiry and scholarship/opportunity imports do not.
10. **UI journey inconsistency:** booking is presented as both available and
    unavailable on different student pages. Full responsive/accessibility and
    end-to-end regression evidence is absent.
11. **Dirty worktree and untracked migration:** changes are not represented by
    `HEAD`; current tests/build include local working-tree code and do not mean
    that code has been deployed.

## 9. Prioritized implementation roadmap

Effort estimates are engineering effort, not calendar commitments. **No
roadmap task below was implemented by this audit.**

### P0 — Critical blockers

| Task | Files/modules | Dependencies | Acceptance criteria | Estimate |
|---|---|---|---|---:|
| Restore coherent frontend/API deployment | `render.yaml`, `next.config.ts`, Vercel project settings, backend production environment | Owner/admin access to Render and correct Vercel team; approved deployment window; resolve required email configuration before retry | Both intended domains serve expected revisions; schema and frontend route contracts match; scholarship/auth smoke requests return expected status; commit IDs recorded; rollback path documented | 1–3 days |
| Establish production data safety | Render database/service settings; `backend/config/settings/production.py`; storage configuration/runbooks | Hosting-owner access; choose durable DB and private object storage; backup/restore approval | API-to-database identity confirmed without exposing URL; applied migrations and aggregate counts reported; backup restored in isolation; RPO/RTO recorded; no destructive migration | 2–5 days plus restore window |
| Verify email configuration and real staging journey | `backend/apps/accounts/`, `app/student/register/`, `app/student/verify-email/`, environment config | P0 service alignment; provider and verified sender domain; staging account | Provider accepts controlled staging email; token verify/expiry/resend/login flow succeeds; no real user/test messages; errors and logs contain no token/secret | 1–2 days plus provider setup |
| Restore genuine public catalogue content | Scholarship/opportunity/university admin and source-review workflows; optional importer in `backend/apps/*` | Production counts and DB identity established; verified official sources/editorial owner | Aggregate counts reconciled; only authentic, current, source-checked records are published; public list/detail and official link confirmed | 2–5 days initial curation; importer estimate after schema |

### P1 — Essential functionality and data integrity

| Task | Files/modules | Dependencies | Acceptance criteria | Estimate |
|---|---|---|---|---:|
| Secure document lifecycle | `backend/apps/documents/`, `backend/config/urls.py`, `app/student/`, storage settings | P0 durable private storage; privacy/retention policy | Owner-scoped upload/download/delete; parent owner consistency; size/MIME/content checks and malware scan; audit access; private storage and restore verified | 1–3 weeks |
| Add password reset and login abuse controls | `backend/apps/accounts/`, `backend/config/settings/base.py`, student auth pages | Email staging service; shared production rate-limit cache design | Single-use expiring reset token, generic responses, abuse/rate-limit tests; login throttles work across workers | 3–6 days |
| Enforce application target/status invariants | `backend/apps/applications/models.py`, serializers/views/tests, new reviewed migration | Production migration state, duplicate/orphan audit, backup and staging PostgreSQL | Exactly one target consistent with type; no existing rows lost; status history records actor/time append-only; migration tested on representative data | 4–8 days |
| Complete opportunity application/saved workflows and job data | `backend/apps/opportunities/`, `backend/apps/applications/`, `lib/api/`, relevant frontend pages | P0 content model and P1 application constraints | Job/internship eligibility attributes and filters; save/unsave; application target support; no fabricated opportunity details; full owner/permission tests | 1–2 weeks |
| Clarify and verify consultation journey | `app/student/page.tsx`, `app/student/consultations/`, `backend/apps/consultations/` | Deployed API and consultant availability policy | Dashboard copy matches actual route; authenticated request/confirm/cancel journey works in staging; timezone/overlap behavior tested; reminder limitations explicit | 3–6 days |
| Complete notification delivery | `backend/apps/notifications/`, `backend/config/`, deployment worker config | Provider, queue/worker and retry/monitoring decisions | Persisted outbox, delivery attempts, user preferences, idempotency/retry, failures surfaced; no false “sent” state | 1–2 weeks |

### P2 — Important improvements

| Task | Files/modules | Dependencies | Acceptance criteria | Estimate |
|---|---|---|---|---:|
| Reviewed catalogue import and lifecycle | `backend/apps/scholarships/`, `backend/apps/opportunities/`, management commands/admin | Verified schema and editorial review workflow | Draft-only idempotent imports; row validation/rejection report; duplicate review; source provenance; publish/expiry audit | 1–2 weeks |
| Normalize country/program/field concepts | `common`, `students`, `scholarships`, `universities`, `destinations`, opportunities | Data audit and API compatibility plan | Expand/backfill with ambiguity report and dual-read; no inferred mappings; unique/check constraints added only after reconciliation | 2–4 weeks |
| Add browser, API contract, accessibility and responsive tests | Frontend test tooling and key auth/catalogue/application pages | Stable staging deployment and test accounts/data | CI exercises registration, verification, login, catalogue/detail, application and booking journeys; device breakpoints and keyboard checks; no production email | 1–2 weeks |
| Improve error observability and deployment health | `lib/api/errors.ts`, API exception/logging settings, Render health/monitoring | Stable deploy and privacy-safe logging policy | Distinct throttled/unavailable/empty states; request correlation and alerts; no secrets/PII in logs; health check reflects critical dependencies | 3–6 days |

### P3 — Future enhancements

| Task | Files/modules | Dependencies | Acceptance criteria | Estimate |
|---|---|---|---|---:|
| Payments and refunds | New payment/service booking modules, provider callbacks, frontend purchase flow | Business/legal policy, provider account, pricing/currency/refunds decisions | Idempotent webhook ledger and reconciliation; test-mode end-to-end; auditable refunds; no payment represented by booleans alone | 2–4 weeks |
| Advanced exam preparation | `app/exam-prep/`, learning/progress API if required | Current official exam specifications and licensed content review | Accurate practice content, scoring and explanations; user progress saved; accessibility and curriculum review | 2–6 weeks |
| Source collection automation | `backend/apps/opportunities/`, scheduler/worker/monitoring | Source terms/robots policy, human review rules, content provenance | Scheduled fetch/recheck, error/retry observability, duplicate handling, expiry and admin review; never auto-publish unverified content | 2–4 weeks |

## 10. Recommended next task

**Do not begin feature expansion yet.** The safest next action is a deployment
recovery checkpoint led by the project owner:

1. Confirm the Vercel project/team and domain assignment that should serve
   `gofere.vercel.app`.
2. Resolve the production email configuration missing from the failed Render
   build; record required environment-variable names only in the release plan.
3. Confirm which API revision is meant to run and inspect the deployed database
   binding and migration state using authorized, aggregate-only checks.
4. Establish a production-safe backup/restore plan before any migration or
   data repair.
5. Re-test the API schema and public catalogues after an explicitly approved
   deployment; then curate verified real content.

Until these are complete, treat production record counts, migration state,
frontend/backend compatibility, email delivery, and data recovery as
**UNKNOWN**.

# GOFER EXAM Complete Five-Actor Functional Audit

**Audit date:** 2026-11-16
**Mode:** Audit only. No application, backend, or production data was modified.
**Production frontend:** https://gofere-web-preview.onrender.com/
**Production backend:** https://gofere-api-ruth2105.onrender.com/

## Executive summary

**The five-actor product is not fully functional in production.** The deployed API schema contains authentication basics, applications collection/detail, and read-only scholarship, university, destination, and service catalogues. It does not expose several locally implemented API groups that the frontend depends on.

Production, read-only evidence:

- The API schema returns HTTP 200, but does not list student profile/completion, education/experience/skills, consultations, documents, notifications, opportunities, countries, user management, admin overview, password reset/change, verification, or security-audit routes.
- Direct and same-origin GET requests to `/api/v1/students/me/completion/` return **404**. The deployed student dashboard requests this endpoint before it sets the dashboard user state. An authenticated student therefore cannot reach the dashboard content while this API remains missing.
- `/api/v1/consultations/`, `/api/v1/documents/`, `/api/v1/notifications/`, and `/api/v1/opportunities/` return **404**.
- The production frontend returns **404** for `/admin/security`, `/jobs`, `/internships`, and `/student/reset-password`.
- The public catalogue API routes `/scholarships/`, `/universities/`, `/destinations/`, and `/services/` return **200**. Anonymous `/api/v1/auth/me/` and `/api/v1/applications/` return **401**, as expected for protected resources.
- Representative frontend pages return HTTP 200, but that only establishes that an HTML route/shell is served; it does not establish that its authenticated workflow works.

Local-code evidence is materially broader than production. The working directory contains many pre-existing modified and untracked files. The audit build and full test suite ran against that current local tree, not against a production checkout. In particular, several local routes are untracked and are not present in the deployed revision. These workspace changes were not altered.

No production registration, login, upload, update, delete, approval, role change, or other write was attempted. No production credentials, test accounts, or authenticated sessions were provided, so production actor-specific workflows and persistence could not be exercised.

## Audit method and evidence limits

- Read-only production GET requests were made to the public frontend, API schema, public catalogues, and selected protected endpoints. The API schema path list and response codes are recorded below.
- Render returned a free-instance wake-up interstitial/503 on an initial browser request; subsequent HTTP requests served the site. Cold-start availability is therefore a real observed operational delay, not evidence that the underlying route works.
- Local checks run against the current workspace:
  - `npm run lint` — passed.
  - `npx tsc --noEmit` — passed.
  - `npm run build` — passed. Next.js emitted a warning that a parent `package-lock.json` is outside the Git repository; the build completed.
  - `npm run test:auth-routes` — 5 passed.
  - `backend\venv\Scripts\python.exe manage.py test --settings=config.settings.test --verbosity=1` — 197 passed, 1 skipped.
- The Django suite uses isolated test settings with an in-memory SQLite database. Its API and role tests are local test evidence, not production workflow evidence.
- The workspace includes modified/untracked implementation files. Therefore the successful local build/tests do **not** certify that the deployed Git revision contains those changes.
- “Expected” describes the requested/product workflow; “actual” distinguishes production observations from local source/test behavior. Any production flow requiring a login or write remains untested.

## Phase 1 — Route inventory

The local `app/` tree currently resolves to 37 page routes. No duplicate App Router page paths were found. There are no `app/api/**/route.ts` handlers; API calls use the Next.js rewrite in `next.config.ts`. A separate local `proxy.ts` implements session-route gating but is untracked and absent from the deployed Git revision.

### Local public routes

`/`, `/about`, `/contact`, `/disclaimer`, `/faq`, `/privacy`, `/terms`, `/exam-prep`, `/exam-prep/[exam]`, `/exam-prep/practice-test`, `/internships`, `/jobs`, `/opportunities`, `/opportunities/[slug]`, `/scholarships`, `/scholarships/[id]`, `/services`, `/services/[slug]`, `/study-abroad`, `/study-abroad/[id]`, `/universities`, `/universities/[id]`.

### Local student routes

`/student`, `/student/profile`, `/student/scholarships`, `/student/applications`, `/student/consultations`, `/notifications`.

### Local authentication routes

`/student/login`, `/student/register`, `/student/verify-email`, `/student/forgot-password`, `/student/reset-password`.

### Local consultant routes

`/consultant`, `/consultant/consultations`.

### Local admin and superadmin routes

`/admin`, `/admin/security`. There is no separate `/superadmin` page; both roles use `/admin`. The security-audit page is intended for superadmins.

### Production route observations

| Route | Production GET | What this proves |
|---|---:|---|
| `/`, `/student/login`, `/student/register`, `/student`, `/student/profile`, `/student/applications`, `/student/consultations`, `/student/scholarships`, `/consultant`, `/consultant/consultations`, `/admin`, `/notifications`, `/scholarships`, `/opportunities`, `/universities`, `/study-abroad`, `/services`, `/exam-prep` | 200 | The route or HTML shell is served; authenticated UI behavior is not verified. |
| `/student/verify-email`, `/student/forgot-password` | 200 | The unauthenticated page route is served; its backend workflow is not verified. |
| `/admin/security`, `/jobs`, `/internships`, `/student/reset-password` | 404 | These locally present routes are unavailable on the deployed frontend. |
| Backend `/admin/` | 302 | Django admin redirects to a login page; authenticated access was not tested. |
| Backend `/api/v1/docs/`, `/api/v1/redoc/`, `/api/v1/schema/` | 200 | API documentation/schema is public and reachable. |

The deployed home navigation exposes Opportunities, Scholarships, Universities, Study Abroad, Exam Prep, Services, About, Contact, Sign In, and Get Started. No duplicate links were identified from the inspected navigation. Direct production requests confirm that the locally present jobs, internships, security, and reset-password routes are not deployed.

## Production API probe summary

All requests below were read-only unauthenticated GETs. Statuses were also checked through the frontend’s same-origin `/api/v1/` rewrite for representative routes.

| Production backend path | Result | Interpretation |
|---|---:|---|
| `/api/v1/schema/` | 200 | Schema reachable. Its deployed path list is limited to auth basics, application collection/detail, and read-only catalogues. |
| `/api/v1/auth/me/` | 401 | Protected user endpoint rejects an unauthenticated request. |
| `/api/v1/applications/` | 401 | Protected application endpoint rejects an unauthenticated request. |
| `/api/v1/scholarships/` | 200 | Public catalogue route exists. |
| `/api/v1/universities/` | 200 | Public catalogue route exists. |
| `/api/v1/destinations/` | 200 | Public catalogue route exists. |
| `/api/v1/services/` | 200 | Public catalogue route exists. |
| `/api/v1/students/me/`, `/api/v1/students/me/completion/`, `/api/v1/students/education/`, `/api/v1/students/experience/`, `/api/v1/students/skills/` | 404 | Student endpoints absent from the deployed API. |
| `/api/v1/consultations/`, `/api/v1/consultations/me/`, `/api/v1/consultations/consultants/` | 404 | Consultation endpoints absent from the deployed API. |
| `/api/v1/documents/`, `/api/v1/notifications/` | 404 | Document and notification endpoints absent from the deployed API. |
| `/api/v1/opportunities/`, `/api/v1/countries/` | 404 | Opportunity and country endpoints absent from the deployed API. |
| `/api/v1/scholarships/eligible-for-me/` | 404 | Personalized student matching route absent from the deployed API. |
| `/api/v1/applications/admin/overview/`, `/api/v1/applications/consultant/assigned/` | 404 | Admin overview and consultant assignment routes absent from the deployed API. |

The production schema also omits email verification, password reset/change, managed-user, security-audit, and application submit/withdraw action paths. No POST/PATCH/DELETE request was made to production.

## Phase 2 — Student audit

### Registration and email verification

**Actor/feature:** Student — registration and verification. **Frontend route:** `/student/register`, `/student/verify-email`. **Backend endpoint:** Local code has `POST /api/v1/auth/register/`, `POST /api/v1/auth/verify-email/`, and `POST /api/v1/auth/resend-verification/`. **Expected:** Register a student with a verification email, then activate the account using a one-time token. **Actual:** Frontend routes return 200 in production. Production schema lists registration but not verify-email or resend-verification, so the complete production workflow cannot be completed as deployed. No registration was submitted. **Test evidence:** Local full backend suite passed, including registration CSRF/privileged-role tests; email delivery was not tested against production. **Status:** **FAIL (production end-to-end); NOT TESTED (live registration).** **Root cause:** Deployed API is behind the local implementation. **Recommended correction:** Deploy and verify the matching verification endpoints and production email provider configuration before advertising registration as complete.

### Login and logout

**Actor/feature:** All actors — sign in/out. **Frontend route:** `/student/login`; successful destination is selected by role. **Backend endpoint:** `POST /api/v1/auth/login/`, `POST /api/v1/auth/logout/`, `GET /api/v1/auth/me/`, refresh via `POST /api/v1/auth/token/refresh/`. **Expected:** Authenticate, issue secure session cookies, route to the role workspace, revoke session on logout. **Actual:** Production schema includes login/logout/me/refresh; an unauthenticated live `GET /auth/me/` returned 401. No test-account login or logout was attempted. **Test evidence:** Local account tests cover cookie flags, verification gating, refresh, logout, and invalid tokens; all 197 backend tests passed overall. Five frontend auth-route tests passed. **Status:** **NOT TESTED (production credential flow); PASS (local code/tests).** **Root cause:** No isolated production test accounts were supplied. **Recommended correction:** Validate login/logout for each role in a staging environment with dedicated accounts.

### Password reset and change

**Actor/feature:** Student and staff — reset/change password. **Frontend route:** `/student/forgot-password` is served; `/student/reset-password` is production 404. No password-change page or use of the change-password API wrapper was found. **Backend endpoint:** Local code supports reset request/confirmation and authenticated password change. The deployed schema omits these endpoints. **Expected:** Request reset, receive a one-time link, set a new password; signed-in users can change their password. **Actual:** Reset request UI route is served, but the reset form route/API is absent in production; no change-password UI exists locally. No reset email or write was attempted. **Test evidence:** Local backend suite includes reset validation/token tests; frontend auth route tests do not test reset API delivery. **Status:** **FAIL (production reset); NOT IMPLEMENTED (change-password UI); NOT TESTED (live email).** **Root cause:** Route/API deployment gap and missing account-settings UI. **Recommended correction:** Deploy the reset endpoints/page, verify email delivery in staging, and expose an authenticated password-change workflow.

### Dashboard, profile, and completion percentage

**Actor/feature:** Student — dashboard/profile progress. **Frontend route:** `/student`, `/student/profile`. **Backend endpoint:** `GET /api/v1/students/me/`, `GET /api/v1/students/me/detail/`, `GET /api/v1/students/me/completion/`, `PATCH /api/v1/students/me/`. **Expected:** Load the student portal, profile and persisted completion percentage; refresh completion after profile edits. **Actual:** Production completion and profile GETs return 404. The deployed dashboard requests completion before setting its user state, and renders its error branch on the failed request. The dashboard therefore cannot finish loading for an authenticated student. **Test evidence:** Live API GETs; local completion tests assert the exact 12.5% initial and 100% post-update response and a fresh GET; local profile page refetches completion after save. **Status:** **FAIL (production); PASS (local response/update tests).** **Root cause:** Student API is absent from the deployed API version. **Recommended correction:** Deploy the student API matching the frontend, then run authenticated staging tests for load, edit, refresh, and missing-field display.

### Education, work experience, and skills CRUD

**Actor/feature:** Student — profile records. **Frontend route:** `/student/profile`. **Backend endpoint:** Local `GET/POST/PATCH/DELETE /api/v1/students/education/`, `/experience/`, and `/skills/`. **Expected:** Create, list, edit, and delete records, scoped to the current student. **Actual:** Each corresponding production API route returns 404. **Test evidence:** Local backend test suite passed, including education and skill delete coverage; tests use an isolated database. **Status:** **FAIL (production); PASS (local API tests).** **Root cause:** Student CRUD endpoints are not deployed. **Recommended correction:** Deploy the matching API and verify CRUD plus cross-account denial in staging.

### Document upload, download, delete, and review

**Actor/feature:** Student, consultant, admin — document handling. **Frontend route:** Upload/download/delete controls are embedded in `/student/profile`; no consultant document-review page was found. **Backend endpoint:** Local `POST/GET /api/v1/documents/`, `DELETE/PATCH /api/v1/documents/{id}/`, `GET .../{id}/download/`, `POST .../{id}/verify/`. **Expected:** Securely store owner documents, allow permitted review, and preserve uploaded files. **Actual:** Production `/api/v1/documents/` returns 404. Local code checks a 10 MB limit and filename extension, but not file content/signature. Production storage is not configured in `render.yaml`; local base settings point media to filesystem `MEDIA_ROOT`. The `is_confidential` field is not used to filter consultant document query/download access. **Test evidence:** Local tests cover upload, extension/size, ownership, download, and deletion. No production upload or cross-role test was run. **Status:** **FAIL (production); FAIL (local confidentiality enforcement); NOT TESTED (durable production storage).** **Root cause:** Missing production endpoint, no durable storage configuration, and no confidentiality-based visibility filter. **Recommended correction:** Deploy the API, use durable private object storage, validate MIME/signature as appropriate, and define/enforce confidentiality policy in both list and download permissions.

### Scholarship search and eligibility

**Actor/feature:** Public/student — search and personalized matches. **Frontend route:** `/scholarships`, `/scholarships/[id]`, `/student/scholarships`. **Backend endpoint:** Public `GET /api/v1/scholarships/`; local student `GET /api/v1/scholarships/eligible-for-me/`. **Expected:** Browse/filter published scholarships and see matches based on profile. **Actual:** Public list route returns 200 in production; eligibility route returns 404. No scholarship result set or student match was inspected using an authenticated account. **Test evidence:** Local scholarship tests cover published filtering/search and matching; local backend suite passed. **Status:** **PASS (public endpoint availability only); FAIL (production personalized matches); NOT TESTED (authenticated search UX/data).** **Root cause:** Matching endpoint absent from production; public response content not verified. **Recommended correction:** Deploy matching endpoint and verify filtering/matches against safe staging data.

### Opportunity search, filters, and saved opportunities

**Actor/feature:** Public/student — find and save opportunities. **Frontend route:** `/opportunities`, `/opportunities/[slug]`; category pages `/jobs` and `/internships` are local only. **Backend endpoint:** Local `GET /api/v1/opportunities/` and detail; local admin writes. No saved/bookmark endpoint or UI was found. **Expected:** Search/filter published opportunities and save selected items. **Actual:** The deployed opportunity endpoint returns 404. `/jobs` and `/internships` are 404 in production. Save/bookmark behavior is not implemented locally. **Test evidence:** Local opportunity tests cover published/source verification; full local backend suite passed. Production only received read-only GETs. **Status:** **FAIL (production search/routes); NOT IMPLEMENTED (saved opportunities).** **Root cause:** API/page changes are not in the deployed revision and the saved feature has no implementation. **Recommended correction:** Deploy the listing API/routes and decide whether saved opportunities are in scope before exposing the UI.

### Application submission and tracking

**Actor/feature:** Student — application tracker. **Frontend route:** `/student/applications`. **Backend endpoint:** Local `GET/POST /api/v1/applications/`, `GET/PATCH/PUT /{id}/`, `POST /{id}/submit/`, `POST /{id}/withdraw/`. **Expected:** Track application records and update tracker state. **Actual:** Production collection GET returns 401 when unauthenticated; production schema includes collection/detail but does not list submit/withdraw actions. The local UI explicitly tells the student that “submit” only changes tracker state and does not send an application to an institution. **Test evidence:** Local application tests cover ownership, draft validation, and status actions; production authenticated tests were not run. **Status:** **NOT TESTED (production tracker); FAIL (production submit/withdraw API absent); PASS (local tracker intent is disclosed).** **Root cause:** Production API is behind the local version; external institution submission is not a feature. **Recommended correction:** Deploy tracker actions; do not describe the tracker action as an actual external application submission.

### Notifications

**Actor/feature:** Student, consultant, admin — view/manage notifications. **Frontend route:** `/notifications`. **Backend endpoint:** Local `GET /api/v1/notifications/`, unread count, `POST /{id}/read/`, `POST /read-all/`. **Expected:** Show actor-owned notifications and allow marking read. **Actual:** Production `/api/v1/notifications/` returns 404. The frontend route itself returns 200 but the page cannot load its data. No admin notification-send API was found; Django admin model registration is not equivalent to a tested in-product notification workflow. **Test evidence:** Local backend notification tests ran in the full suite; no production account test. **Status:** **FAIL (production); NOT IMPLEMENTED (admin send/manage workflow).** **Root cause:** Notification API deployment gap and no actor-facing admin workflow. **Recommended correction:** Deploy the API and specify how authorized staff create notifications.

### Consultation requests

**Actor/feature:** Student — consultant enquiries/bookings. **Frontend route:** `/student/consultations`. **Backend endpoint:** Local `GET/POST /api/v1/consultations/`, `POST /{id}/cancel/`, `POST /{id}/feedback/`, student-only consultant directory. **Expected:** Request a consultation, track/cancel it, and submit feedback after completion. **Actual:** Production consultation endpoints return 404. **Test evidence:** Local consultation tests cover ownership and lifecycle; full suite passed. No live booking was submitted. **Status:** **FAIL (production); PASS (local API test coverage only).** **Root cause:** Consultation API absent from deployed backend. **Recommended correction:** Deploy matching endpoints and verify with staging student/consultant accounts.

## Phase 3 — Consultant audit

### Consultant login and permissions

**Actor/feature:** Consultant — authenticate and access own workspace. **Frontend route:** Shared `/student/login`, `/consultant`. **Backend endpoint:** Shared auth endpoints; local assigned applications and consultations require `IsConsultant`. **Expected:** Consultant role signs in and can access only consultant functions. **Actual:** Production login endpoint is documented, but no consultant credentials were supplied. `/consultant` returns an HTML shell; role behavior was not verified live. **Test evidence:** Local auth and role tests passed as part of the 197-test suite. **Status:** **NOT TESTED (production); PASS (local role code/tests).** **Root cause:** No safe test account. **Recommended correction:** Run a staging role matrix with dedicated consultant credentials.

### Assigned student/application list and status updates

**Actor/feature:** Consultant — review assigned applications. **Frontend route:** `/consultant`. **Backend endpoint:** Local `GET /api/v1/applications/consultant/assigned/`, `POST /consultant/assigned/{id}/start-review/`. **Expected:** See only assigned students and advance eligible submitted applications to review. **Actual:** Production assigned route returns 404. Local behavior supports search/status filtering and only the “start review” transition; no consultant decision/accept/reject action exists. **Test evidence:** Local tests specifically cover assigned-only results, retrieving unassigned application denial, and review assignment; full suite passed. **Status:** **FAIL (production); PASS (local assigned boundary tests); NOT IMPLEMENTED (further status decisions).** **Root cause:** Backend deployment gap and limited action set. **Recommended correction:** Deploy these endpoints and define any additional consultant status transitions explicitly.

### Student profile/progress access

**Actor/feature:** Consultant — inspect assigned student's profile and progress. **Frontend route:** No dedicated student profile/progress view in the consultant workspace. **Backend endpoint:** Local `/students/me/detail/` and `/me/completion/` are student-only; assigned application responses include limited application/student details. **Expected:** Access explicitly authorized profile information and progress for assigned students only. **Actual:** No consultant profile/progress endpoint or UI exists; production student endpoints are 404. **Test evidence:** Local role checks and assignment tests ran; no consultant profile endpoint exists to exercise. **Status:** **NOT IMPLEMENTED.** **Root cause:** Student detail endpoints are scoped to the student, with no assigned-consultant read surface. **Recommended correction:** Define a least-privilege assigned-student read model and add ownership/assignment tests before exposing it.

### Document review

**Actor/feature:** Consultant — review student documents. **Frontend route:** No consultant document-review route/UI found. **Backend endpoint:** Local `GET /api/v1/documents/` and `POST /{id}/verify/` permit assigned-consultant document access. **Expected:** Review assigned students' documents and record verification decisions. **Actual:** Production document API is 404; local UI does not expose review controls. **Test evidence:** Local document tests include ownership and verification behavior, but consultant UI/production review was not tested. **Status:** **FAIL (production); NOT IMPLEMENTED (consultant UI).** **Root cause:** Missing deployed API and frontend review interface. **Recommended correction:** Deploy the API, implement only the agreed review controls, and test that unassigned and confidential documents are inaccessible.

### Consultation management, notes, and communication

**Actor/feature:** Consultant — manage assigned consultations and communicate outcomes. **Frontend route:** `/consultant/consultations`. **Backend endpoint:** Local `GET /api/v1/consultations/consultant/assigned/`, `POST /consultant/assigned/{id}/{confirm|cancel|complete}/`. **Expected:** Confirm/cancel/complete assigned bookings and record meeting URL, notes, and action items. **Actual:** Production consultation API returns 404. Local UI supports consultation status actions and notes/action items; no general messaging/chat endpoint or page was found. **Test evidence:** Local consultation assignment/action tests passed in the full suite; no live consultant account. **Status:** **FAIL (production API); PASS (local implementation/test evidence); NOT IMPLEMENTED (general messaging).** **Root cause:** API deployment gap; messaging is not part of the implementation. **Recommended correction:** Deploy and staging-test assigned consultation lifecycle; document that free-form messaging is not available.

## Phase 4 — Admin audit

### Dashboard and reports

**Actor/feature:** Admin — platform overview/reporting. **Frontend route:** `/admin`. **Backend endpoint:** Local `GET /api/v1/applications/admin/overview/`. **Expected:** Show account, catalogue, application, and consultation counts. **Actual:** Production admin route returns an HTML shell; overview endpoint returns 404. No live admin login was attempted. The page is an overview, not a full reporting/export facility. **Test evidence:** Local tests cover admin overview empty counts and role denial; full suite passed. **Status:** **FAIL (production); PASS (local limited overview tests); NOT IMPLEMENTED (broader reporting/export).** **Root cause:** Endpoint absent from production and limited report scope. **Recommended correction:** Deploy overview API and test with staging ADMIN and SUPERADMIN accounts.

### User, student, and consultant management

**Actor/feature:** Admin — manage students and consultants; superadmin — manage administrator accounts. **Frontend route:** No dedicated Next.js user-management page found. **Backend endpoint:** Local `GET /api/v1/auth/users/`, `GET/PATCH /auth/users/{id}/`; regular admin can manage student/consultant accounts, while superadmin has the broader account scope. **Expected:** Search/view/activate/deactivate permitted accounts and prevent ordinary admin role escalation. **Actual:** Production schema does not include managed-user endpoints. Local backend permissions are implemented, but no Next.js workflow is present. `/admin/` redirects to Django admin login; role account usability there was not tested. **Test evidence:** Local tests for admin escalation denial and superadmin role/account management passed in full suite. **Status:** **FAIL (production endpoint); NOT IMPLEMENTED (Next.js management UI); PASS (local role boundary tests).** **Root cause:** Missing deployed endpoints and user-management interface. **Recommended correction:** Deploy APIs, add role-gated UI if required, and test the distinction between application `role` and Django `is_staff`.

### Opportunities CRUD/publication

**Actor/feature:** Admin — create/edit/publish opportunities. **Frontend route:** No dedicated admin opportunity-management page. **Backend endpoint:** Local admin-authenticated `ModelViewSet` on `/api/v1/opportunities/`; public GET filters published, in-date, source-verified records. **Expected:** Manage drafts and publication without allowing students/consultants to publish. **Actual:** Production opportunity route returns 404. Local publication controls and checks exist; this audit did not mutate production. **Test evidence:** Local tests cover publication requirements and student denial; full suite passed. **Status:** **FAIL (production); NOT IMPLEMENTED (Next.js admin management UI); PASS (local API test evidence).** **Root cause:** API absent from deployed backend; admin UI missing. **Recommended correction:** Deploy backend and add a role-gated management surface if management is intended for the web product.

### Scholarship, university, destination, and service catalogue management

**Actor/feature:** Admin — catalogue CRUD and publication. **Frontend route:** No dedicated management pages. **Backend endpoint:** Local public catalogue APIs are read-only; models are registered in Django admin. **Expected:** Admin can maintain catalogue records and public pages reflect publication state. **Actual:** Production public list endpoints respond 200, but catalogue write workflows were not tested. There are no catalogue CRUD REST endpoints or Next.js management screens in local code. Django admin login is available by redirect but role access and CRUD were not tested. **Test evidence:** Local catalogue tests cover public filtering; no production write. **Status:** **NOT IMPLEMENTED (REST/Next UI); NOT TESTED (Django admin CRUD in production).** **Root cause:** Catalogue administration is outside the API/UI surface and depends on Django staff access. **Recommended correction:** Confirm intended workflow and ensure authorized staff accounts can administer each model through the supported interface.

### Application management

**Actor/feature:** Admin — manage applications. **Frontend route:** `/admin` only shows counts; no application-management page. **Backend endpoint:** Local admin overview is read-only; application collection is student-owned. Django admin registers the model. **Expected:** Admin review/manage application records as required by policy. **Actual:** No admin application API/UI beyond aggregate counts; production overview endpoint is missing. **Test evidence:** Local tests cover ownership and aggregate overview; no production admin test. **Status:** **NOT IMPLEMENTED (dedicated management API/UI); FAIL (production overview).** **Root cause:** Application API is student-scoped and admin view is only a summary. **Recommended correction:** Define permitted admin operations before adding a management workflow.

### Notification management

**Actor/feature:** Admin — create/manage notifications. **Frontend route:** None; `/notifications` is actor-facing inbox. **Backend endpoint:** Local user-owned list/read APIs; Django admin model registered. **Expected:** Authorized staff can create/send notifications to users. **Actual:** No dedicated REST or Next.js notification management workflow; production user inbox endpoint returns 404. **Test evidence:** Local notification API tests ran; no live user or admin action. **Status:** **NOT IMPLEMENTED (staff notification workflow); FAIL (production inbox API).** **Root cause:** Current backend exposes only owner inbox operations through the API. **Recommended correction:** Define and implement a restricted notification creation workflow if required.

### Admin audit logs

**Actor/feature:** Admin — view security audit logs. **Frontend route:** `/admin/security` is locally present but returns 404 in production. **Backend endpoint:** Local `GET /api/v1/auth/security/audit/` is `IsSuperAdmin`, not ordinary ADMIN. **Expected:** Preserve superadmin-only visibility. **Actual:** The endpoint is absent from production schema; normal admins should not be granted access per local policy. **Test evidence:** Local tests include denial of audit access to non-superadmin; full suite passed. **Status:** **FAIL (production route/API); PASS (local role boundary tests).** **Root cause:** Security route and audit API are not deployed. **Recommended correction:** Deploy the page/API and verify ADMIN receives 403 while SUPERADMIN receives only permitted audit records.

## Phase 5 — Superadmin audit

### Login and workspace

**Actor/feature:** Superadmin — sign in and reach administrative workspace. **Frontend route:** Shared `/student/login` and `/admin`; no dedicated superadmin route. **Backend endpoint:** Shared auth; local user profile returns `role: SUPERADMIN`. **Expected:** Superadmin signs in and receives all intended administrator functions. **Actual:** No superadmin test account was supplied; the production admin HTML shell alone does not demonstrate access. **Test evidence:** Local role destination and superadmin assignment tests passed. **Status:** **NOT TESTED (production).** **Root cause:** No isolated superadmin account. **Recommended correction:** Validate the full role landing and authorized functions in staging.

### Admin account, role, and permission management

**Actor/feature:** Superadmin — manage admin accounts/roles. **Frontend route:** No dedicated user/role-management page. **Backend endpoint:** Local `/api/v1/auth/users/` and `/auth/users/{id}/` restrict admin-account operations to superadmin. **Expected:** Superadmin can manage admin roles; ordinary ADMIN cannot elevate privileges. **Actual:** Production schema omits these endpoints, and no front-end management UI exists. **Test evidence:** Local tests cover ordinary admin denial and superadmin role assignment; full suite passed. **Status:** **FAIL (production); NOT IMPLEMENTED (Next.js UI); PASS (local permission tests).** **Root cause:** Deployed API and UI gaps. **Recommended correction:** Deploy and staging-test both roles, including denial of SUPERADMIN-only changes by ADMIN.

### System settings and system-level operations

**Actor/feature:** Superadmin — system configuration/operations. **Frontend route:** None. **Backend endpoint:** No system-settings API or application page identified. **Expected:** Access explicitly defined system settings and controlled operational functions. **Actual:** No such workflow is present in the audited app/API surface. **Test evidence:** Route/API inventory. **Status:** **NOT IMPLEMENTED.** **Root cause:** No feature/API definition found. **Recommended correction:** Specify required settings and operational controls before implementation.

### Audit logs

**Actor/feature:** Superadmin — review security audit events. **Frontend route:** Local `/admin/security`; production 404. **Backend endpoint:** Local `GET /api/v1/auth/security/audit/`, superadmin-only. **Expected:** Read paginated security events without exposing them to ordinary admins. **Actual:** Endpoint absent from production schema; no authenticated production read. **Test evidence:** Local authorization test passed; full suite passed. **Status:** **FAIL (production); PASS (local access-control evidence).** **Root cause:** Deployment mismatch. **Recommended correction:** Deploy and test with separate ADMIN and SUPERADMIN accounts.

## Phase 6 — Backend, database, and persistence

- **Local endpoint surface:** `backend/config/urls.py` includes account, application, consultation, document, notification, scholarship, country, opportunity, service, university, destination, and student apps. This local route inventory does not match the production schema.
- **Production endpoint availability:** The public schema contains only auth basics, applications collection/detail, and scholarship/university/destination/service catalogues. Live endpoint 404s are recorded above. The schema and API docs being available does not establish that omitted workflows work.
- **Authentication and role policy:** Local DRF defaults to cookie JWT and authenticated access unless an endpoint opts out. Local custom permissions distinguish STUDENT, CONSULTANT, ADMIN/SUPERADMIN, and SUPERADMIN. Tests passed locally; no role-specific production accounts were used.
- **Persistence:** Local Django tests use an in-memory SQLite test database and exercise persistence between API requests for selected workflows. Production persistence for profile/application/document mutations was not tested because no production writes were allowed.
- **Migrations:** Render's local `render.yaml` start command runs `python manage.py migrate --noinput`. The actual production applied migration set was not inspected; no production database query/admin operation was attempted.
- **Database backups:** No backup automation/configuration is present in the deployment manifest. The backend README warns that the included free database is temporary and not suitable for durable production data.
- **File storage:** Base settings use local `MEDIA_ROOT`; production cloud object storage settings are commented out. Durability of uploaded files across Render restarts/deployments is not established and is a production readiness risk.
- **Email:** Production settings require a valid sender and SMTP/provider configuration. The Render manifest does not declare SMTP settings; dashboard-level environment values were not accessible/inspected. Verification/reset email delivery is **NOT TESTED**.
- **Configuration:** `render.yaml` sets database, API service, frontend API proxy target, host/CORS/CSRF origins and uses free plans. Secret values were not inspected.

## Phase 7 — Security findings

### Controls with local evidence

- Public registration serializer forces STUDENT role and rejects privileged role fields.
- Local JWT authentication reads an access token from an HttpOnly cookie; access/refresh tokens are not returned in JSON in the tested cookie flow. Production settings require Secure cookies and HTTPS.
- Browser-cookie authenticated mutations enforce CSRF. Local tests for CSRF, refresh, logout, inactive/unverified accounts, and token rejection passed.
- Local role tests deny ordinary ADMIN role escalation and protect superadmin operations.
- Local application tests enforce student ownership and consultant assignment boundaries, including denial for unassigned applications.
- Live unauthenticated GETs to `/api/v1/auth/me/` and `/api/v1/applications/` return 401. This verifies only those anonymous requests, not cross-role or IDOR behavior in production.

### Findings and unverified controls

1. **Confidential document visibility is not enforced in local API query/download paths.** `is_confidential` is included in document data, but consultant query/download authorization uses assigned-student association without filtering this flag. **Impact:** If the field is intended to restrict consultant visibility, its value currently has no effect. **Evidence:** `backend/apps/documents/views.py`; production documents API is absent, so live exploitability was not tested. **Recommendation:** Define the confidentiality policy and enforce it consistently for list, detail, and download.
2. **File type validation is extension-based.** Local serializer checks filename extension and a 10 MB size limit but does not validate content signatures/MIME. **Impact:** A file with an allowed suffix is not proven to contain the expected file type. **Evidence:** `backend/apps/documents/serializers.py`; no production upload was attempted. **Recommendation:** Add content-level validation and scanning appropriate to the file risk and storage pipeline.
3. **Production route and API access-control behavior is not fully verified.** No production test accounts were provided. Local client-side page guards are not a substitute for API permission checks. API endpoints that are missing return 404, not authorization responses.
4. **Production authentication cookie/CSRF configuration is not independently verified.** Local settings/tests provide evidence, but no authenticated production response was inspected. **Recommendation:** Validate cookie attributes and CSRF rejection in a staging environment.
5. **Production document confidentiality and IDOR behavior are NOT TESTED.** Local ownership/assignment tests passed; the live document API is unavailable.
6. **Durable private document storage and backup/recovery are not demonstrated.** The manifest has no durable media storage or backup automation.

No passwords, access tokens, personal documents, or production user data were requested or included in this report.

## Phase 8 — Test results

| Check | Result | Scope/limitation |
|---|---|---|
| Backend full suite | **197 passed, 1 skipped** | Local code; `config.settings.test`, in-memory SQLite. |
| Auth route frontend tests | **5 passed** | Local `lib/auth/access.test.mjs`; does not test production login. |
| ESLint | **Passed** | Current local working tree. |
| TypeScript | **Passed** | `npx tsc --noEmit`, current local working tree. |
| Production build | **Passed** | Current local working tree, including modified/untracked files; package-lock root warning. Not a production artifact verification. |
| Backend API integration and role tests | **Passed as part of 197 tests** | Local in-process Django API tests only. |
| Production API GET probes | **Partial** | Public GETs and anonymous protected GETs only; many required APIs return 404. |
| Authenticated production workflow / data persistence | **Not run** | No dedicated test accounts; no production mutations permitted. |
| E2E browser workflow suite | **Not available/run** | No E2E runner/script identified in `package.json`; production browser session is unauthenticated. |

## Prioritized failures and blockers

1. **Critical — student dashboard is blocked by the missing production student API.** `GET /api/v1/students/me/completion/` returns 404, and the dashboard waits for it before rendering. Profile, completion, education, experience, and skills APIs are also absent.
2. **Critical — large sections of the shipped product have no matching production API.** Consultation, document, notification, and opportunity endpoints return 404; consultant/admin workflows depending on them cannot operate.
3. **High — deployed API/schema is behind the local implementation.** Verification, password reset/change, managed-user, admin overview, audit, student profile, and application action endpoints are absent from production schema.
4. **High — local frontend routes are not deployed.** `/admin/security`, `/student/reset-password`, `/jobs`, and `/internships` return 404. These route files are untracked in the audited workspace.
5. **High — document confidentiality has no effective consultant visibility filter in local API code.** Confirm intended policy and enforce it before enabling document access.
6. **High — production document durability and backups are not established.** Render manifest has no durable object storage or backup/recovery automation; local media is filesystem-backed.
7. **Medium — consultant lacks student profile/progress access and document-review UI.** Backend does not provide an assigned-consultant student detail/progress endpoint; consultant UI has no document review controls.
8. **Medium — administration is incomplete in the Next.js product.** No dedicated user/student/consultant, catalogue CRUD, application-management, or notification-management pages; Django admin access was not authenticated/tested.
9. **Medium — opportunity bookmarking/saved items and authenticated password-change UI are not implemented.**
10. **Medium — application “submit” only updates a tracker record.** The UI discloses this accurately; it does not submit to an institution.
11. **Unverified — production registration email delivery, authenticated role redirects, cross-role denial, upload/download, mutations, and database persistence.** These require isolated staging accounts and a safe test database.

## Relevant local implementation references

- Frontend routes and auth gating: [app/](./app/), [proxy.ts](./proxy.ts), [next.config.ts](./next.config.ts).
- Student API/permission implementation: [backend/apps/students/](./backend/apps/students/).
- Auth and role permissions: [backend/apps/accounts/](./backend/apps/accounts/), [backend/apps/common/permissions.py](./backend/apps/common/permissions.py).
- Application and consultant assignment: [backend/apps/applications/](./backend/apps/applications/).
- Consultations, documents, notifications, and opportunities: [backend/apps/consultations/](./backend/apps/consultations/), [backend/apps/documents/](./backend/apps/documents/), [backend/apps/notifications/](./backend/apps/notifications/), [backend/apps/opportunities/](./backend/apps/opportunities/).
- Production configuration and deployment manifest: [backend/config/settings/production.py](./backend/config/settings/production.py), [render.yaml](./render.yaml).

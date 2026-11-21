# GOFER EXAM — Production Deployment Consistency Audit

**Audit date:** 2026-11-16
**Mode:** Read-only deployment audit. No source/configuration files other than this requested report were changed. No commits, pushes, deploys, migrations, production writes, or database queries were performed.
**Baseline:** [GOFER_COMPLETE_ACTOR_AUDIT.md](./GOFER_COMPLETE_ACTOR_AUDIT.md)

## Executive summary

The frontend and backend are **not deployed from the same commit**:

| Item | Finding |
|---|---|
| Current local branch and HEAD | `master`, `b380fe1d3a2b1c6193ed341908c08f374af6db99` |
| GitHub `origin/master` | Same SHA as local HEAD; no ahead/behind commit difference at inspection |
| Frontend Render service | `gofere-web-preview`, service `srv-dbko547b9u1s73801h7g`, repository `ruth2105/Gofere`, branch `master` |
| Frontend live SHA | `b380fe1d3a2b1c6193ed341908c08f374af6db99` — same as local HEAD |
| Backend Render service | `gofere-api-ruth2105`, service `srv-dbko0a6gekts73en6cr0`, repository `ruth2105/Gofere`, branch `master`, root directory `backend` |
| Backend live SHA | `30ab294a88315af3a80061b8d37946e0a00d0b97` |
| Backend most recent deployment | **Failed** for `d2626774530a8f377cae348a07d6585c9484aa0a`; Render build log reports missing production email configuration (`GOFER_EMAIL_FROM` / production email backend). Earlier attempt for the same commit also failed. |
| Frontend most recent deployment | **Succeeded** and is live at `b380fe1`; deployment took 1m 50s in the dashboard. |
| API schema | Prior audit captured HTTP 200 and a limited schema. A follow-up request during this audit returned 503 while the free backend was idle/waking; the Render dashboard warns about spin-down. Treat the prior schema/path observations as the last successful response, not as evidence of a new schema. |

The production schema is stale because the backend service never advanced past `30ab294`. The deployment attempt for `d262677` did not build; the Render log explicitly fails while importing production settings because the required email backend/sender configuration is missing. That is a verified deploy blocker. The local checkout also contains substantial uncommitted work, including endpoint registrations and migrations, which neither production service can receive from Git until separately reviewed, committed, and pushed. This audit did not stage, commit, or push any of that work.

## 1. Git state and file classification

At the time of the status inventory, local `master` and `origin/master` both pointed to `b380fe1d3a2b1c6193ed341908c08f374af6db99`. The working tree contained **61 modified tracked files** and **49 untracked files**. This report is an additional untracked deliverable, so after its creation the untracked count is one greater. Existing modifications and untracked files were left untouched.

### Committed versus deployed feature code

- The frontend progress card at [app/student/page.tsx](./app/student/page.tsx) is part of commit `b380fe1`, and that exact commit is live on the frontend.
- The backend live commit is `30ab294`, which is an ancestor of local HEAD. There are ten later commits on `master`; backend changes among them are not live. The latest backend attempt reached `d262677`, but the build failed before the new application could become live.
- The student-profile URL registrations, document URL module, several account/consultation URL changes, much of the backend endpoint implementation, and five migrations are currently uncommitted or untracked. They are **not deployable from the GitHub branch** as currently recorded.
- The local Render manifest and Next.js proxy configuration are tracked in `b380fe1`; `next.config.ts` itself has an additional uncommitted modification.

### Modified tracked source/configuration files

These are tracked files with local edits that are not in the currently deployed frontend/backend release as a complete working-tree state:

```text
app/about/page.tsx
app/consultant/page.tsx
app/layout.tsx
app/opportunities/[slug]/OpportunityDetail.tsx
app/opportunities/page.tsx
app/scholarships/[id]/ScholarshipDetail.tsx
app/scholarships/page.tsx
app/services/[slug]/ServiceDetail.tsx
app/services/page.tsx
app/student/applications/page.tsx
app/student/forgot-password/page.tsx
app/student/login/page.tsx
app/student/profile/page.tsx
app/study-abroad/[id]/DestinationDetail.tsx
app/study-abroad/page.tsx
app/universities/[id]/UniversityDetail.tsx
app/universities/page.tsx
backend/apps/accounts/admin.py
backend/apps/accounts/models.py
backend/apps/accounts/serializers.py
backend/apps/accounts/tests.py
backend/apps/accounts/urls.py
backend/apps/accounts/views.py
backend/apps/applications/tests.py
backend/apps/applications/views.py
backend/apps/common/permissions.py
backend/apps/consultations/serializers.py
backend/apps/consultations/tests.py
backend/apps/consultations/urls.py
backend/apps/consultations/views.py
backend/apps/documents/views.py
backend/apps/notifications/views.py
backend/apps/opportunities/admin.py
backend/apps/opportunities/models.py
backend/apps/opportunities/serializers.py
backend/apps/opportunities/tests.py
backend/apps/opportunities/views.py
backend/apps/scholarships/admin.py
backend/apps/scholarships/models.py
backend/apps/scholarships/serializers.py
backend/apps/scholarships/services/matching.py
backend/apps/scholarships/tests.py
backend/apps/scholarships/views.py
backend/apps/students/admin.py
backend/apps/students/models.py
backend/apps/students/serializers.py
backend/apps/students/urls.py
backend/apps/students/views.py
backend/config/settings/base.py
backend/config/settings/production.py
backend/config/urls.py
components/layout/Navigation.tsx
lib/api/catalogues.ts
lib/api/client.ts
lib/api/errors.ts
lib/api/scholarships.ts
next.config.ts
package.json
types/index.ts
```

`README.md` and `PROJECT_AUDIT.md` are also modified tracked files; they are documentation rather than deployment routing or runtime code.

### Untracked implementation files

These are not in GitHub `master`; in particular they cannot be deployed by selecting the current branch:

```text
app/admin/security/page.tsx
app/internships/page.tsx
app/jobs/page.tsx
app/student/reset-password/ResetPasswordForm.tsx
app/student/reset-password/page.tsx
backend/apps/accounts/audit.py
backend/apps/accounts/migrations/0003_securityauditevent.py
backend/apps/accounts/password_reset.py
backend/apps/documents/serializers.py
backend/apps/documents/urls.py
backend/apps/opportunities/migrations/0005_opportunity_documents_required_and_more.py
backend/apps/opportunities/migrations/0006_opportunity_management_mvp.py
backend/apps/opportunities/models.py.backup
backend/apps/scholarships/migrations/0004_opportunity_management_mvp.py
backend/apps/students/migrations/0003_education_skill_workexperience.py
backend/templates/accounts/password_reset.html
backend/templates/accounts/password_reset.txt
backend/tests/test_documents_api.py
backend/tests/test_student_profile_api.py
components/auth/AuthProvider.tsx
components/auth/RoleRouteGuard.tsx
lib/auth/access.test.mjs
lib/auth/access.ts
proxy.ts
```

The remaining untracked files at the inventory point were reports/docs:

```text
ACTOR_FUNCTIONALITY_AUDIT.md
API_PROXY_INTEGRATION_REPORT.md
AUTHENTICATION_TEST_REPORT.md
DATABASE_AUDIT.md
DATABASE_READINESS_REPORT.md
DJANGO_BLOCKER_INVESTIGATION_REPORT.md
DJANGO_CHECKCONSTRAINT_COMPATIBILITY_REPORT.md
GOFER_COMPLETE_ACTOR_AUDIT.md
GOFER_CURRENT_PROGRESS_AUDIT.md
GOFER_MASTER_IMPLEMENTATION_REPORT.md
GOFER_OVERALL_PROGRESS_REPORT.md
GOFER_PHASE3_4_VERIFICATION_REPORT.md
GOFER_PHASE4B_FINAL_VERIFICATION_REPORT.md
GOFER_PHASE4B_FRONTEND_INTEGRATION_REPORT.md
MAINTENANCE.md
OPPORTUNITY_MVP_IMPLEMENTATION_REPORT.md
OPPORTUNITY_POSTGRESQL_FIX_REPORT.md
OPPORTUNITY_POSTGRESQL_READINESS.md
PHASE2_1_COMPLETION_REPORT.md
PHASE2_AUTH_SECURITY_REPORT.md
PHASE_4B_COMPLETION_REPORT.md
PHASE_4B_FINAL_COMPLETION_REPORT.md
PROJECT_CURRENT_STATUS.md
ROLE_PERMISSION_MATRIX.md
SCHOLARSHIP_DISPLAY_DIAGNOSIS.md
```

## 2. Render service/repository alignment and deployed commits

The Render dashboard shows both web services as Blueprint-managed and linked to `ruth2105/Gofere` on `master`. The Blueprint inventory contains the frontend and backend services plus the database. They therefore share a **repository and branch**, but their live deploys are independently versioned.

### Frontend

- Live: `b380fe1d3a2b1c6193ed341908c08f374af6db99` (dashboard short SHA `b380fe1`).
- This matches local `HEAD`/`origin/master`.
- The current deployment record is marked **Live** and **Deployed**.

### Backend

- Last successful/live: `30ab294a88315af3a80061b8d37946e0a00d0b97`.
- Newer deployment attempts target `d2626774530a8f377cae348a07d6585c9484aa0a`; Render marks the latest attempt **Failed** and shows the previous `30ab294` deployment still **Live**.
- The build log for the failed attempt ends with:

  ```text
  django.core.exceptions.ImproperlyConfigured:
  Configure a production email backend and GOFER_EMAIL_FROM.
  ==> Build failed
  ```

- This pins the immediate reason the backend did not move to the newer code: the new release fails while loading production settings due to required email configuration. The actual configured environment values were not opened, copied, or disclosed.
- `d262677` is not HEAD: `ba0915a` and then `b380fe1` are newer on `master`. No later backend attempt for `b380fe1` was visible in the dashboard history inspected.

The consequence is not merely “frontend and backend use different variables.” The frontend successfully deployed code that calls endpoints, while the backend deploy that would provide newer backend routes failed before startup. The front-end proxy can reach the configured backend, but cannot make an endpoint present in the backend code currently running.

## 3. Local backend routes versus deployed API schema

### Current local route wiring

Current working-tree [backend/config/urls.py](./backend/config/urls.py) mounts:

```text
/api/v1/auth/
/api/v1/applications/
/api/v1/consultations/
/api/v1/documents/        (working tree only; URL module is untracked)
/api/v1/notifications/
/api/v1/scholarships/
/api/v1/countries/
/api/v1/opportunities/
/api/v1/services/
/api/v1/universities/
/api/v1/destinations/
/api/v1/students/
```

The current working-tree URL modules include additional local routes for verification, password reset/change, managed users, security audit, consultant-assigned consultations, student profile completion, education, experience, and skills. Those local source changes are not equivalent to deployed endpoints: several route files/config edits are uncommitted, and the backend is running the older `30ab294` image.

### Production schema and direct probes from the baseline audit

The last successful production schema response (HTTP 200, as recorded in [GOFER_COMPLETE_ACTOR_AUDIT.md](./GOFER_COMPLETE_ACTOR_AUDIT.md)) listed auth basics, application collection/detail, and public read-only scholarship, university, destination, and service catalogues. Direct requests showed:

| Endpoint group | Production observation | Current local intention |
|---|---|---|
| `/auth/csrf/`, `/register/`, `/login/`, `/logout/`, `/token/refresh/`, `/me/` | Listed in schema; anonymous `/me/` returns 401 | Existing auth plus newer email/password/account-management operations |
| `/auth/verify-email/`, `/resend-verification/` | Not listed | Current modified `accounts/urls.py` adds both |
| `/auth/password/reset/`, `/password/reset/confirm/`, `/password/change/` | Not listed | Current modified account URLs/views add these |
| `/auth/users/`, `/auth/users/{id}/`, `/auth/security/audit/` | Not listed | Current modified account URLs/views add management/audit |
| `/applications/`, `/applications/{id}/` | Listed; anonymous collection request returns 401 | Present; local code adds admin/consultant and submit/withdraw actions |
| `/applications/admin/overview/`, `/applications/consultant/assigned/`, application action routes | Not listed | Current local application view changes expose these |
| `/students/me/`, `/students/me/detail/`, `/students/me/completion/` | Direct GETs return 404 | Current local student routes expose profile and completion |
| `/students/education/`, `/students/experience/`, `/students/skills/` | Direct GETs return 404 | Current local router exposes profile CRUD |
| `/consultations/`, `/consultations/me/`, `/consultations/consultants/`, consultant-assigned actions | Direct GETs return 404 | Current modified consultation URLs/views expose assigned workflows |
| `/documents/` and document detail/download/verify routes | Direct GET returns 404 | Entire URL module is untracked; config include is an uncommitted edit |
| `/notifications/` | Direct GET returns 404 | Local view changes add actor inbox actions |
| `/opportunities/` | Direct GET returns 404 | Local code contains opportunity listing/management endpoints |
| `/scholarships/`, `/universities/`, `/destinations/`, `/services/` | Public list endpoints return 200 | Present; local scholarship matching is an additional route |
| `/scholarships/eligible-for-me/`, `/countries/` | Direct GETs return 404 | Local endpoint implementation/availability differs; validate schema after backend is successfully deployed |

The expected local source is also ahead of `HEAD`: the route list above describes the working tree, not necessarily even the committed `b380fe1` tree. Production’s 404s therefore have two layers: backend service is pinned to older commit `30ab294`, and some of the current local backend route/module/migration changes have not been committed at all.

## 4. Frontend API calls and proxy/environment behavior

- Current frontend API client uses the same-origin base path `/api/v1`; pages do not directly call the backend host. The Next.js rewrite forwards `/api/v1/:path*` to the configured target and appends the trailing slash.
- Current [next.config.ts](./next.config.ts) target precedence is:

  1. `API_PROXY_TARGET`
  2. `NEXT_PUBLIC_API_URL`
  3. `http://localhost:8000/api/v1` fallback

- [render.yaml](./render.yaml) sets `API_PROXY_TARGET` for `gofere-web-preview` to `https://gofere-api-ruth2105.onrender.com/api/v1`; backend service is rooted at `backend`. Thus the checked-in manifest points the frontend at the intended backend.
- A dashboard-level Render variable can override a Blueprint value. The effective production environment was not inspected; therefore no live override/misconfiguration is asserted. Before release, confirm the frontend’s effective target is the backend URL above, without disclosing any other environment values.
- `API_PROXY_TARGET` is read by `next.config.ts` to define a Next.js rewrite. Treat the destination as a build/deployment setting: after changing it, rebuild/redeploy the frontend and confirm the emitted rewrite points to the intended API.
- The localhost fallback is appropriate for local development but would misroute production requests if the required Render variable were missing. Fail closed or add deployment validation rather than silently accepting the fallback for production.
- Baseline API probes through the frontend proxy returned the same representative 404s as direct backend probes. That is consistent with the backend being stale/missing endpoints; it does not prove that the configured proxy target is wrong.
- There is no `app/api/**/route.ts` proxy implementation. The API path is handled by the Next config rewrite. Local `proxy.ts` handles page/session gating, is untracked, and is not the API reverse proxy.

## 5. Migration status and risk

### What is known

The working tree has five **untracked** Django migrations absent from GitHub `master`:

| Migration | Observed operation | Risk/consideration |
|---|---|---|
| `backend/apps/accounts/migrations/0003_securityauditevent.py` | Creates `SecurityAuditEvent` table and indexes/FKs | Adds production schema and references user accounts. |
| `backend/apps/opportunities/migrations/0005_opportunity_documents_required_and_more.py` | Adds eligibility/document fields to Opportunity | Schema change with JSON/text/choice fields; validate compatibility and expected defaults. |
| `backend/apps/opportunities/migrations/0006_opportunity_management_mvp.py` | Adds compensation, employment, experience, location, skills, and work-mode fields; alters choices | Multiple schema alterations; validate backfill/default and rollback behavior on a production-sized copy. |
| `backend/apps/scholarships/migrations/0004_opportunity_management_mvp.py` | Alters Scholarship status choices | Verify no persisted values conflict and understand reversal behavior. |
| `backend/apps/students/migrations/0003_education_skill_workexperience.py` | Creates education, skills, and work-experience tables, keys, and indexes | New student data tables; confirm migration dependencies and clean reverse/restore plan. |

The files are visible locally but are untracked, so they cannot be part of a Git-based Render deploy yet. Other existing migrations are tracked in the repository.

### What is not known

- The database’s actual applied migration records and current schema were **not queried**. Production migration status is therefore **unknown**, not “pending” or “applied.”
- No production migration command, database connection, or write was run.
- A successful app build/start and healthy schema endpoint do not prove that every local migration is applied.

### Automatic migration risk

The checked-in [render.yaml](./render.yaml) backend `startCommand` runs `python manage.py migrate --noinput` before Gunicorn starts. Consequently, a successful backend deployment using this manifest can apply every migration packaged in that deployment automatically. Do not treat a deploy as a code-only operation. The untracked migrations must first be reviewed, committed intentionally, checked against a staging database and a migration plan, and included in the backup/rollback decision.

## 6. Database configuration (secret-safe)

- The Blueprint provisions a Render PostgreSQL database named `gofere-db` and injects its `connectionString` into the backend’s `DATABASE_URL` environment variable.
- Production settings parse `DATABASE_URL` into Django database configuration and require SSL. No literal URL, password, host credential, or secret value was read or included.
- The Blueprint declares a **free** database plan. The baseline project documentation identifies the free database as temporary; a durable production retention/backup arrangement is not demonstrated in the manifest.
- Render dashboard environment values, database records, and migration tables were not inspected. This avoids disclosure and avoids production data access.
- The release must be gated on a verified database snapshot/backup and a tested restore path. File storage needs a separate backup: database backup alone does not back up document/media contents. The current production storage configuration does not demonstrate durable object storage.

## 7. Root-cause conclusion

1. **Confirmed release blocker:** Backend deploy of `d262677` failed during build because required production email backend and `GOFER_EMAIL_FROM` configuration were absent/invalid for that build. The Render log contains the error, not the underlying secret values.
2. **Confirmed deploy skew:** Frontend is live at `b380fe1`; backend remains live at `30ab294`. The front-end release therefore calls newer API behavior than the API process exposes.
3. **Additional source-control gap:** Current local API/URL/config/migration changes include 61 modified tracked files and 49 pre-report untracked files. Uncommitted/untracked changes are not on remote `master`, so no Render deploy from that branch can include them.
4. **Proxy misconfiguration is not the primary proven cause:** `render.yaml` points the frontend at the backend, and representative same-origin proxy requests reproduced backend 404s. The actual Render environment override remains unverified.
5. **Migration application state is unknown:** there is no evidence that production has the locally present migrations; they are not committed, and no DB migration query was made.

## 8. Exact safe deployment sequence — for approval before execution

This sequence is a recommendation only; **nothing below was performed**.

### Pre-deployment gates

1. Review all dirty tracked files and untracked files; decide explicitly which are intended release content. Do not blindly add all 61 modified files or the untracked reports/backups.
2. Resolve and test the missing production email configuration in a non-production Render environment. Configure required values through the Render secret/environment UI; never write credentials into source, logs, or this report. Re-run the exact backend build and verify it succeeds before promoting.
3. Review each migration and its dependency chain. On an isolated staging copy, run `showmigrations` and `migrate --plan`; apply only to staging first, test forward migration, application startup, relevant workflows, and rollback/restore procedures. Do not infer production migration status from local tests.
4. Create a timestamped PostgreSQL backup/snapshot immediately before release, verify it is restorable, and separately back up media/documents and any other persistent object storage. Record backup identifiers and retention window without publishing secret URLs.
5. Agree on a maintenance window, user-impact communication, release owner, stop/rollback criteria, and whether writes will be paused during backup/deploy/verification.
6. Produce one reviewed, committed release candidate on `master` containing the intended backend, frontend, and migration files. Run backend tests, lint, TypeScript, production build, and the staging migration/workflow checks against that exact SHA. Keep unrelated workspace changes out.

### Production rollout

1. Verify the frontend and backend Render services still reference `ruth2105/Gofere` / `master`, confirm intended deployment SHA and root directories, and inspect effective `API_PROXY_TARGET` without displaying secrets. Confirm it resolves to `https://gofere-api-ruth2105.onrender.com/api/v1`.
2. Ensure the backup gates above are green. Since backend startup automatically runs migrations, obtain explicit approval for both the backend deploy and the exact migration set before starting it.
3. Deploy the reviewed backend SHA first. Monitor build and start logs; confirm the migration command completed and health check `/api/v1/schema/` succeeds. Compare schema paths against the expected API contract, then run safe authenticated smoke tests using dedicated non-production or approved test accounts. Do not proceed if build, migration, or health checks fail.
4. Deploy the frontend at the same reviewed release SHA (or a separately reviewed frontend SHA explicitly compatible with the backend). Rebuild so the rewrite destination is current. Confirm the production frontend proxy reaches the expected backend.
5. Run read-only public checks, then controlled end-to-end checks with isolated test accounts; verify student completion/profile update/refresh, consultant assignment boundaries, and admin-vs-superadmin denials. Use only approved test data and clean it up under an approved process.
6. Monitor error rates, logs, API health, and data integrity. Retain the pre-deployment database/media backups and the previous deploy IDs through the agreed observation window.

## 9. Rollback plan

1. **Application rollback:** If health, schema, auth, or smoke checks fail, stop promotion and roll the affected Render service(s) back to the last known-good deployment IDs/SHAs: frontend `b380fe1`, backend `30ab294`. Roll back frontend/backend together when their API contracts are incompatible.
2. **Database rollback is separate:** Rolling back code does not reverse database migrations. Do not run reverse migrations blindly. Use the reviewed reversible migration plan where proven safe; otherwise restore the verified pre-deploy PostgreSQL snapshot and separately restore the matching media/document backup.
3. **Data-loss guard:** Restoring a snapshot may discard legitimate writes made after its timestamp. Pause writes/maintenance mode, identify and communicate the recovery point, obtain approval, and preserve post-snapshot data for reconciliation before restoring.
4. **Verify after rollback:** Confirm backend health/schema and expected paths, frontend proxy behavior, login/session behavior, and read-only records. Resume traffic only after checks pass. Preserve deploy logs and backup identifiers for the incident record.
5. Keep the prior app deploys and backups available until the observation period ends; do not delete, overwrite, or rotate the only known-good backup as part of rollback.

## Evidence and limitations

- Repository state: `git status --short --branch`, `git rev-parse HEAD`, `git log`, and comparison against `origin/master`.
- Remote branch: GitHub `master` points at `b380fe1d3a2b1c6193ed341908c08f374af6db99`.
- Render service/deploy metadata: dashboard showed both service links to `ruth2105/Gofere master`; frontend live SHA `b380fe1`; backend live SHA `30ab294`; latest backend attempt for `d262677` failed.
- Render build-log failure: missing required production email backend / `GOFER_EMAIL_FROM`; secret values not accessed.
- Routes/config/migrations: local tracked/untracked source, `render.yaml`, `next.config.ts`, settings and migration files.
- Production API route list/statuses are taken from the baseline audit’s last successful schema/probe. A new schema fetch during this follow-up returned 503; no credentials or production data were used.
- No migration status was queried from the production database, no deployment was triggered, and no production environment value was inspected or revealed.

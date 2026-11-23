# Opportunity MVP Implementation Report

## Summary

Implemented the local opportunity-management MVP using the existing Django/DRF and Next.js architecture. The dedicated `Scholarship` model remains the scholarship catalogue; the existing `Opportunity` model now also supports jobs and internships. Public listings require publication and current, verified source evidence. No catalogue records were created.

| Feature | Implemented | Deployed | Verified |
|---|---|---|---|
| Opportunity/job/internship API and management | Yes | No deployment performed | Backend tests pass locally |
| Scholarship publication safeguards and catalogue filters | Yes | No deployment performed | Backend tests pass locally |
| `/jobs`, `/internships`, and opportunity details | Yes | No deployment performed | TypeScript, lint, and production build pass locally |
| Production catalogue/data and live user experience | Not established by this task | Unknown | Not tested against a live environment |

## Existing functionality reused

- The existing `Opportunity` model, API, pagination, and detail route.
- `Scholarship` as a separate model and API; no duplicate scholarship records were introduced in `Opportunity`.
- Existing `OpportunitySource`, `CollectionRun`, and `OpportunitySourceRecord` models and admin source-review workflow.
- Existing Next.js design system, API client, scholarship and opportunity pages, and shared opportunity detail page.

## Implemented

### Backend

- Added job category support and structured location, employment type, work mode, compensation, duration, skills, and experience fields to `Opportunity`.
- Added `EXPIRED` status handling for opportunities and scholarships.
- Restricted opportunity create/update endpoints to administrators. Publication requires an official application/provider URL and current verified source evidence; invalidating source availability unpublishes linked listings.
- Kept public opportunity results limited to published, open/upcoming, in-date opportunities with a valid matching verified source. Added category, country, education/level, nationality, compensation, employment type, work mode, keyword, ordering, and pagination support.
- Nationality matching requires explicitly listed eligibility and excludes unknown eligibility.
- Tightened scholarship publication/public-query safeguards to require current verified source evidence, an official link, and an unexpired open/upcoming status. Added nationality and funding/type filtering.
- Normalized listing URLs when saving so URL comparisons with normalized source records work consistently.
- Updated a scholarship application test fixture to satisfy the verified-publication requirement.

### Admin

- Extended opportunity administration for job/internship fields, search/filter, verification evidence, publish/unpublish, close/expire actions, and duplicate visibility.
- Kept source-record verification restricted to administrators and tied verification evidence to the current listing facts.
- Added scholarship expiration management and administrator-role restrictions to scholarship administration.

### Frontend

- Connected scholarship search, country/type/level filters, deadline ordering, result counts, and pagination to the API instead of filtering only the current client-loaded catalogue.
- Added job and internship listing routes that reuse the opportunity listing and detail experience.
- Added opportunity category, country, education, nationality, compensation, employment, work-mode, and deadline-order filters.
- Updated opportunity details with location, employment/compensation, internship duration, experience, skills, verified sources, and official application links.
- Added verified-source details to scholarship detail pages.
- Preserved explicit loading, error, empty, and retry states; no fake fallback data is used.

## Files changed for this milestone

- Backend: `backend/apps/opportunities/models.py`, `serializers.py`, `views.py`, `admin.py`, `tests.py`.
- Backend: `backend/apps/scholarships/models.py`, `serializers.py`, `views.py`, `admin.py`, `services/matching.py`, `tests.py`.
- Backend integration test: `backend/apps/applications/tests.py`.
- Frontend: `app/opportunities/page.tsx`, `app/opportunities/[slug]/OpportunityDetail.tsx`, `app/scholarships/page.tsx`, `app/scholarships/[id]/ScholarshipDetail.tsx`.
- Frontend new routes: `app/jobs/page.tsx`, `app/internships/page.tsx`.
- Frontend API/types: `lib/api/client.ts`, `lib/api/scholarships.ts`, `types/index.ts`.
- New migration files: `backend/apps/opportunities/migrations/0006_opportunity_management_mvp.py` and `backend/apps/scholarships/migrations/0004_opportunity_management_mvp.py`.

The worktree already contained other unrelated changes and reports; they were not reverted or included in this feature list.

## Migrations and database safety

- `opportunities.0006_opportunity_management_mvp` depends on `opportunities.0005_opportunity_documents_required_and_more`. The `0005` file remains untracked in the worktree; the user previously confirmed its five field additions are intended. Both files must be kept together in source control before preparing a migration sequence.
- `scholarships.0004_opportunity_management_mvp` adds the `EXPIRED` status choice.
- `manage.py makemigrations --check --dry-run` reported `No changes detected`.
- No migration was applied to the original local PostgreSQL database or production. Django tests used a temporary SQLite test database, which was destroyed after testing.
- PostgreSQL execution and migration behavior have not been independently rehearsed as part of this milestone. Do not treat SQLite tests as PostgreSQL validation.

## Validation results

- Backend: `manage.py test --verbosity 1` with `DJANGO_SETTINGS_MODULE=config.settings.test` — **176 tests passed, 1 skipped**.
- Migration drift: `manage.py makemigrations --check --dry-run` — **No changes detected**.
- Frontend lint: `npm run lint` — **passed**.
- TypeScript: `tsc --noEmit` — **passed**.
- Production build: `API_PROXY_TARGET=http://127.0.0.1:8000 npm run build` — **passed**. This local-only target was used to satisfy the build-time configuration; no API was contacted and no live email or catalogue behavior was verified.
- The Next.js build emitted a workspace-root warning because a parent-directory `package-lock.json` is outside the project repository; the build completed successfully.
- Mobile layout was implemented with responsive utility classes but was not manually/browser-tested.

## Not completed / remaining risks

- Deployment, production API compatibility, and live database/catalogue behavior were not checked or changed.
- No real scholarship/job/internship source records were added or reviewed. Existing listings without a matching, current verified source will intentionally remain hidden from public endpoints until an administrator reviews and verifies them.
- PostgreSQL-specific behavior, including the JSON nationality filters and the unapplied migrations, still needs a disposable PostgreSQL rehearsal before approval to apply migrations.
- No frontend browser automation or manual responsive-device verification was run.
- A production deployment still requires the correct `API_PROXY_TARGET` and the project's approved deployment process. Build success does not establish deployment.

## Recommended next task

Review the two opportunity migrations and scholarship migration together, then rehearse them against a disposable PostgreSQL database restored from the existing backup. Do not apply them to the original local or production database without separate approval. After schema approval, have an administrator verify a small set of genuine provider records and exercise the public listing/detail flow in a non-production environment.

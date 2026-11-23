# Opportunity PostgreSQL Readiness

**Assessment date:** 2026-11-12  
**Scope:** Local PostgreSQL migration rehearsal and local-only Opportunity MVP functional/frontend checks.

## Executive result

The Opportunity MVP migrations applied and reversed successfully on a disposable PostgreSQL restore, and the catalogue list/detail flow worked through the locally built Next.js proxy against PostgreSQL. This is **not approval to migrate the original local database** and is not evidence about production.

The work is **not release-ready**:

1. `opportunities.0005`, `opportunities.0006`, and `scholarships.0004` are all untracked and absent from Git history. `0006` depends on `0005`; the migration set must be resolved and preserved together before release.
2. An API request attempting to publish an opportunity without a valid verified source returned **HTTP 500** instead of a client validation response. The failure should be fixed and regression-tested before release.
3. The original local database still has four unapplied migrations, including `accounts.0002_emailverificationtoken`; that migration was outside this rehearsal.

No application code or migration was edited in this readiness task. No production API or database was contacted. The original local database was inspected read-only and left unchanged.

## Environment and backup

- Django settings: `config.settings.development`.
- Database engine: PostgreSQL; server version recorded during rehearsal as PostgreSQL 18.6.
- Original local database: `gofer_exam`; configured host `localhost` (loopback).
- Production identity: not queried or contacted.
- Backup archive: `C:\Users\user\.copilot\session-state\9ff64949-aeb0-4f2d-8872-6d381f382a57\files\gofer_exam_local_20261112_094522_+0300.dump`
- Backup size: 135,061 bytes. `pg_restore --list` completed with exit code 0 and 299 archive-list lines.
- The archive was restored to the disposable database `gofer_exam_opportunity_rehearsal_20261112`.

The exact disposable database was dropped after testing. A final PostgreSQL metadata check confirmed `gofer_exam` still exists and the rehearsal database no longer exists. No credentials were recorded in this report.

## Migration and Git assessment

### Git tracking

The current worktree contains pre-existing modifications and untracked files; they were preserved. In particular:

| Migration | Git state | History/ignore assessment |
|---|---|---|
| `opportunities.0005_opportunity_documents_required_and_more` | Untracked; absent from index and `HEAD` | Not ignored; no commit history found |
| `opportunities.0006_opportunity_management_mvp` | Untracked; absent from index and `HEAD` | Not ignored; no commit history found |
| `scholarships.0004_opportunity_management_mvp` | Untracked; absent from index and `HEAD` | Not ignored; no commit history found |

Git cannot establish whether these files were intentionally left untracked or accidentally omitted. `0005` must accompany `0006`, which depends on it. Do not stage or commit the entire dirty worktree as a shortcut; review the migration files and unrelated changes separately.

### Operations and rehearsal results

| Migration | Operations | PostgreSQL result and downgrade risk | Assessment |
|---|---|---|---|
| `opportunities.0005` | Adds `documents_required` (JSON), `eligibility_notes` (text), `eligibility_scope`, and eligible/excluded nationality JSON fields. Depends on opportunities `0004`. | Forward migration succeeded. Existing rows received defaults. Reverse migration drops the new columns and would lose values written to them. | Forward-tested on disposable PostgreSQL; do not reverse after populating the fields. Not approved for the original database. |
| `opportunities.0006` | Adds compensation amount/currency/period/status, duration, employment type, experience requirement, location, minimum years of experience, required skills, and work mode; expands category/status choices. Depends on `0005`. | Forward migration succeeded. PostgreSQL created the numeric, varchar/text, JSONB, and smallint columns. Choice changes generated no database SQL. Reverse drops the added columns; values in new categories/statuses may also be incompatible with older application code. | Forward-tested on disposable PostgreSQL; not approved for the original database. |
| `scholarships.0004` | Expands scholarship status choices to include `EXPIRED`; depends on scholarships `0003`. | Forward migration succeeded and generated no PostgreSQL schema SQL because this is an application-level choice change. Older code may not recognize persisted `EXPIRED` values after reversal. | Forward/reverse-tested on disposable PostgreSQL; not approved for the original database. |
| `accounts.0002_emailverificationtoken` | Not part of this Opportunity rehearsal. | Still unapplied on the original local database; no result is claimed here. | Requires its own approved rehearsal. |

The disposable restore had opportunities through `0004` and scholarships through `0003`. The Opportunity migrations were applied in dependency order (`0005` then `0006`); scholarship `0004` was then applied. Reverse migration succeeded in the reverse dependency order: scholarship `0004`, opportunity `0006`, then opportunity `0005`.

PostgreSQL schema inspection confirmed:

- The Opportunity table has its primary key and unique slug constraint.
- `minimum_experience_years` has a nonnegative database check. Its maximum-80 validator is application-level; it is not an equivalent database constraint.
- The compensation nonnegative validator is application-level, not a database check.
- JSON nationality and skills validators are not PostgreSQL constraints.
- Existing opportunity indexes include category, country, and publication-related indexes. No new indexes were added for compensation, employment type, work mode, or nationality JSON filters.
- Source records retain their foreign keys, unique `(source_id, source_record_key)` constraint, and check constraint preventing a record from targeting both an opportunity and a scholarship.

The downgrade test was safe because the restored backup had no catalogue/source/application rows and the test records were disposable. Downgrading a database after new field values have been entered would lose those values.

### Original local migration state

`manage.py showmigrations accounts opportunities scholarships --plan` was run read-only against `gofer_exam`. These are still unapplied:

- `accounts.0002_emailverificationtoken`
- `opportunities.0005_opportunity_documents_required_and_more`
- `opportunities.0006_opportunity_management_mvp`
- `scholarships.0004_opportunity_management_mvp`

`manage.py makemigrations --check --dry-run` reported **“No changes detected.”** This confirms the checked model state matches the migration files on disk; it does not resolve their Git tracking status or authorize applying them.

## PostgreSQL functional checks

Functional checks ran only on the restored disposable database. Test-only records were created for one scholarship, one job, and one internship, with verified source records. Those records and the temporary reviewer account were removed when the disposable database was dropped.

**17 checks passed**, covering:

- Scholarship, job, and internship creation.
- Verified source records and authorized publication.
- Public list/detail responses.
- Category, funding, education, and nationality filtering.
- Sorting and pagination.
- Hiding unpublished and expired records.
- Admin/student permission behavior.

**One negative publication case did not return a controlled response:** attempting to publish an opportunity without a verified matching source caused an uncaught Django model `ValidationError` and returned **HTTP 500**. This is a confirmed API error-handling defect; the request should return a controlled validation response and have a regression test. The fix was not made because this task was a readiness review.

After reversing the migrations, the restored aggregate counts matched the backup baseline: 1 user, 249 countries, and zero opportunity, scholarship, source-record, and application rows. No student personal data was inspected or reported.

## Frontend and API integration

The local frontend was rebuilt with `API_PROXY_TARGET=http://127.0.0.1:8000/api/v1`; the rebuilt Next.js rewrite manifest pointed to the correct API prefix. The build completed successfully, including TypeScript checking and generation of 46 routes. No frontend code was changed.

The local browser used only `127.0.0.1` and the disposable PostgreSQL-backed API:

| Page/API request | Result |
|---|---|
| Jobs listing and opportunity detail by slug | API responses 200; listing and detail rendered |
| Internships listing and opportunity detail by slug | API responses 200; listing and detail rendered |
| Scholarship listing and detail by slug | API responses 200; listing and detail rendered |
| Official application links on detail pages | Correct test URLs rendered for job, internship, and scholarship |
| Mobile layout at 375px viewport | Document width 360px on checked pages; no horizontal overflow |

The UI detail routes use slugs. A direct scholarship API request using the UUID returned 404, while the slug route used by the frontend returned 200; this is consistent with the implemented frontend contract.

An earlier local build manifest had pointed at the API root rather than `/api/v1` and produced failed proxy requests. Rebuilding locally with the correct API proxy target resolved that harness/configuration issue; it was not a source-code change. The local frontend and Django servers were stopped after testing.

## Validation summary

- Full backend test suite, test settings: **176 tests passed, 1 skipped**.
- PostgreSQL model/migration drift check: **No changes detected**.
- Disposable PostgreSQL forward migration: **Passed**.
- Disposable PostgreSQL reverse migration: **Passed**.
- PostgreSQL catalogue functional checks: **17 passed; invalid-publication case returned HTTP 500**.
- Frontend production build and TypeScript check: **Passed**.
- Local browser/API integration and mobile-width checks: **Passed for the pages listed above**.
- Original local database: migration status inspected read-only; no migration applied.
- Production, deployment, and live email/API behavior: **Not tested**.

## Required follow-up before approval

1. Resolve and review the three untracked migration files as one coherent migration set. Preserve dependency order and verify the intended files are included in version control before any environment is migrated.
2. Fix the uncaught publication validation exception so invalid publication attempts return an appropriate DRF 4xx response; add a PostgreSQL-backed regression test for the negative case.
3. Rehearse `accounts.0002_emailverificationtoken` separately; it remains pending and was not part of this opportunity rehearsal.
4. Before applying the Opportunity migrations to the original local database, obtain explicit approval and take/verify a fresh backup. Do not run these migrations against production under this report.
5. Add query-plan/performance checks for the new catalogue filters against representative data before relying on them at scale; the current rehearsal used a small dataset.

**Conclusion:** PostgreSQL compatibility and reversibility were demonstrated on the disposable restore. Migration tracking, the API 500, and the pending unreviewed account migration remain blockers. No deployment or production readiness is established.

# Opportunity PostgreSQL Fix Report

**Assessment date:** 2026-11-12  
**Scope:** Invalid publication API error, migration tracking review, and PostgreSQL regression rehearsal. No production systems were contacted.

## Executive summary

The HTTP 500 is fixed at the serializer boundary. When model `full_clean()` rejects a create or update, the serializer now translates Django's `ValidationError` to DRF's `ValidationError`. The existing publication requirements are unchanged: publication still requires a currently verified, available official source that matches the opportunity. Invalid requests return HTTP 400 with a field-level `is_published` error, and valid publication still succeeds.

The three Opportunity/scholarship migration files are present locally, untracked, not ignored, and absent from Git history. Their operations match the current models and form a non-conflicting continuation of the existing migration chains. They should be retained and tracked together with the corresponding code after review. They were not changed or applied to the original local database.

The full backend suite, Django checks, migration drift check, and targeted disposable-PostgreSQL API checks passed. The original local database still has four unapplied migrations and unchanged aggregate counts.

## Invalid publication investigation

### Exact request and traceback

The new regression test, `test_admin_cannot_publish_opportunity_without_verified_source`, reproduces the failure with an authenticated admin request:

```http
PATCH /api/v1/opportunities/private-training-opportunity/
Content-Type: application/json

{"is_published": true}
```

The target is an existing draft with an application URL but no valid verified source record. This matches the earlier PostgreSQL reproduction recorded in [OPPORTUNITY_POSTGRESQL_READINESS.md](./OPPORTUNITY_POSTGRESQL_READINESS.md).

Before the fix, the test client exposed this exception:

```text
django.core.exceptions.ValidationError: {
  'is_published': [
    'An opportunity needs at least one currently verified, available official source before publication.'
  ]
}
```

The captured stack ran through DRF `partial_update` → `update` → `perform_update` → `serializer.save()` → `ModelSerializer.update()` → `instance.save()`, then [Opportunity.save()](./backend/apps/opportunities/models.py) called `full_clean()`. [Opportunity.clean()](./backend/apps/opportunities/models.py) correctly rejected publication because no matching verified source existed. That Django model exception was not a DRF `APIException`, so DRF re-raised it rather than returning a normal validation response; the live API therefore produced HTTP 500.

Serializer field validation alone did not catch this cross-model safeguard because it runs in model `clean()` when the instance is saved.

### Fix and regression tests

[OpportunitySerializer](./backend/apps/opportunities/serializers.py) now catches only Django `ValidationError` in `create()` and `update()`, converts its field/message details to DRF `ValidationError`, and preserves exception chaining. The configured API error handler formats it as the project's normal 400 error response. Other exceptions are not swallowed.

Publication rules in the model and permissions in the view were not changed or weakened.

[OpportunityApiTests](./backend/apps/opportunities/tests.py) now covers invalid publication through both PATCH and POST. The tests assert:

- The API returns HTTP 400.
- The error identifies `is_published` and explains that a verified source is required.
- The draft remains unpublished after the rejected PATCH.
- An invalid POST does not create a published opportunity.

The existing `test_admin_can_create_draft_and_publish_opportunity` remains the valid-publication regression: it creates a draft, adds a matching verified source, publishes it through the API, and confirms publication succeeds.

## Migration tracking audit

All three files are currently untracked, absent from the Git index/`HEAD`, not ignored, and have no Git history entry. Git evidence cannot determine whether that state was intentional or accidental.

| Migration | Operations / affected model | Dependency and ordering | Model correspondence and necessity | Conflict / retain-and-track assessment |
|---|---|---|---|---|
| [`opportunities.0005`](./backend/apps/opportunities/migrations/0005_opportunity_documents_required_and_more.py) | Adds `Opportunity.documents_required` (JSON), `eligibility_notes` (text), `eligibility_scope` (choice string), `eligible_nationalities` (JSON), and `excluded_nationalities` (JSON). Nationality fields use the existing ISO-code validator. | Depends on `opportunities.0004`; it must precede `.0006`. | All five fields are present on the current `Opportunity` model. Required for its document and eligibility schema. | No operation conflicts with `.0001`–`.0004`; it continues that chain. Safe to retain and track alongside `.0006` and the model/API code. Forward addition was PostgreSQL-tested. Reversing drops the added columns and loses their values. |
| [`opportunities.0006`](./backend/apps/opportunities/migrations/0006_opportunity_management_mvp.py) | Adds compensation amount/currency/period/status, duration, employment type, experience requirement, location, minimum experience years, required skills, and work mode to `Opportunity`. Alters category and status choice definitions. | Depends on `opportunities.0005`; required order is `.0005` then `.0006`. | Each field and choice definition exists on the current `Opportunity` model. Required for the current jobs/internships management schema. | No conflicting branch or duplicate field operation was found. Safe to retain and track with `.0005` and its code. PostgreSQL forward addition was tested. Reversal drops the new columns; new status/category values could also be unknown to older application code. |
| [`scholarships.0004`](./backend/apps/scholarships/migrations/0004_opportunity_management_mvp.py) | Alters `Scholarship.status` choices to include `EXPIRED`; no field is added or removed. | Depends on `scholarships.0003`; it is a separate chain from the Opportunity `.0005`/`.0006` dependency. | `EXPIRED` is present in the current `Scholarship.STATUS_CHOICES`. Required to keep Django migration state aligned with the current model. | No conflict with scholarships `.0001`–`.0003`. Safe to retain and track with the model changes. PostgreSQL emitted no schema SQL for this choice-only alteration; older code may not recognize persisted `EXPIRED` values if rolled back. |

`manage.py makemigrations --check --dry-run` reported **“No changes detected”**, confirming the migration state represented by the local files matches current models. It does not imply the migration files are tracked or that applying them is authorized.

### All four unapplied migrations on the original local database

The original `gofer_exam` migration recorder lists these as unapplied:

| Unapplied migration | Dependency | Meaning |
|---|---|---|
| `accounts.0002_emailverificationtoken` | `accounts.0001_initial` | Creates the one-to-one email verification token table, including a unique token hash, expiry/use timestamps, and an expiry index. Independent of the three catalogue migrations. |
| `opportunities.0005_opportunity_documents_required_and_more` | `opportunities.0004_opportunity_opportunitysourcerecord_opportunity_and_more` | Adds eligibility and required-document fields described above. |
| `opportunities.0006_opportunity_management_mvp` | `opportunities.0005_opportunity_documents_required_and_more` | Adds job/internship management fields and expands category/status choices. |
| `scholarships.0004_opportunity_management_mvp` | `scholarships.0003_scholarship_country_reference_and_more` | Adds `EXPIRED` to the scholarship status choices. |

There are no cross-app dependencies among these four pending migrations. Within the Opportunity chain, `.0005` must precede `.0006`. Existing `opportunities.0001` depends on `scholarships.0002`, which is already applied on the original database. The separate pending account migration was not included in the Opportunity PostgreSQL rehearsal.

**Migration decision:** retain all three catalogue migration files; do not delete, rename, or squash them. Resolve their untracked Git state deliberately before approving any migration. No migration was applied to the original local database.

## PostgreSQL regression rehearsal

The verified backup archive was restored to the disposable PostgreSQL database `gofer_exam_opportunity_fix_rehearsal_20261112`. Only that database received the Opportunity `.0005`/`.0006` and scholarship `.0004` migrations. All completed with `OK`; Django system check reported no issues.

Schema inspection found all 16 expected new Opportunity columns with PostgreSQL types (`jsonb`, `numeric`, `character varying`, `text`, and `smallint`). Migration recorder rows showed the Opportunity migrations through `.0006` and scholarship migrations through `.0004`.

The authenticated API checks on this database returned:

- Invalid POST and invalid PATCH publication without a qualifying source: both **HTTP 400**, with the `is_published` verification error; neither persisted a published record.
- Valid publication after creating a matching active, verified source record: **HTTP 200**; database state became published.

The direct API test initially encountered a local harness-only `DisallowedHost` because the test client uses `testserver`, which is not in development `ALLOWED_HOSTS`. The isolated harness added `testserver` in memory and reran; no settings file or environment configuration was changed.

The disposable database was dropped after verification. No test data was written to the original database.

## Validation evidence

- Targeted test command for invalid and valid publication:
  `manage.py test apps.opportunities.tests.OpportunityApiTests.test_admin_cannot_publish_opportunity_without_verified_source apps.opportunities.tests.OpportunityApiTests.test_admin_cannot_create_published_opportunity_without_verified_source apps.opportunities.tests.OpportunityApiTests.test_admin_can_create_draft_and_publish_opportunity --verbosity 1`
  - **3 tests passed**.
- Full backend test suite under `config.settings.test`:
  - **178 tests run; OK; 1 skipped**.
- `manage.py check` under test settings:
  - **System check identified no issues**.
- `manage.py makemigrations --check --dry-run`:
  - **No changes detected**.
- `git diff --check`:
  - **Clean** (Git emitted only existing line-ending warnings for unrelated files).
- PostgreSQL disposable forward migrations, schema check, invalid/valid API requests:
  - **Passed** as detailed above.
- Original local database verification before and after the rehearsal:
  - Database: `gofer_exam`, PostgreSQL on loopback.
  - Counts remained: users 1, countries 249, scholarships 0, opportunities 0, opportunity sources 0, source records 0, applications 0.
  - Applied migration rows for accounts/opportunities/scholarships remained unchanged; all four migrations listed above remain pending.
  - The disposable database no longer exists.

No production endpoint, database, or deployment was accessed. No production migration or data change occurred.

## Files changed

- Updated [backend/apps/opportunities/serializers.py](./backend/apps/opportunities/serializers.py) to convert model validation exceptions into DRF 400 errors.
- Updated [backend/apps/opportunities/tests.py](./backend/apps/opportunities/tests.py) with the invalid-publication regression; retained the valid-publication test.
- Added this report.

No migration file was edited, staged, committed, or applied to the original local database.

## Remaining risks and recommended next step

1. **Migration tracking blocker:** review the current dirty worktree, then deliberately track all three migration files with the corresponding model/API code. Do not stage unrelated changes.
2. **Approval blocker:** after reviewing the tracked migration set and obtaining explicit approval, take and verify a fresh local backup before applying migrations to `gofer_exam`. This report does not authorize that application.
3. **Account migration:** rehearse `accounts.0002_emailverificationtoken` separately before applying it anywhere.
4. **Rollback risk:** once the new opportunity columns contain data, reversing `.0005`/`.0006` loses those values. Choice-only scholarship reversal can leave `EXPIRED` values that older code does not understand.
5. **Product data:** this task did not add or verify genuine opportunities. Building a verified catalogue still requires approved, authoritative sources and a governed import/review workflow.

**Recommended next step:** resolve and track the migration files after review, then request approval for a separate, backed-up local migration application. Do not migrate production or represent catalogue features as deployed or verified from these local checks.

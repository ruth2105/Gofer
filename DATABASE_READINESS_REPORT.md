# Gofer Exam — Database Readiness and Migration Review

**Review date:** 2026-11-12
**Scope:** Working-tree Django models and migrations; loopback-only local
development database metadata and aggregate counts; isolated automated tests;
and a PostgreSQL backup/restore rehearsal of `accounts.0002` on a disposable
database. The migration was not applied to the original local database or
production. No model/code files or application records in the original
database were changed, and no production database was accessed.

## Executive summary

The working tree contains **17 application-owned models** across 13 Django apps
and **21 domain migration files** (20 tracked by Git; the pending opportunity
0005 migration is currently untracked). `accounts.0002` is tracked in `HEAD`
but is unapplied in the local database. The local development PostgreSQL
database was confirmed to use a loopback host before inspection. Its recorded
migration state has two pending migrations:

1. `accounts.0002_emailverificationtoken`
2. `opportunities.0005_opportunity_documents_required_and_more`

The first creates the token table needed by the checked-in verification
workflow. That table is currently absent in the local development database.
The second adds five non-nullable model fields with defaults to Opportunity;
existing rows receive defaults when the migration is applied. There are no
destructive operations in either pending migration.

`accounts.0002_emailverificationtoken` was rehearsed successfully on a
disposable PostgreSQL database restored from a verified local `pg_dump`
archive. Forward and reverse migrations both completed, and application-table
row counts were preserved. The original `gofer_exam` database still has the
migration pending and the token table absent. `opportunities.0005` was not
applied in either database.

`makemigrations --check --dry-run` reports no model/migration drift. The full
backend suite passes (167 tests, 1 skipped) using the isolated test settings;
the test runner creates and migrates a disposable SQLite database. This does
not apply migrations to the local development PostgreSQL database and does not
verify PostgreSQL locking or production state.

The schema is a workable early MVP foundation, but **not ready to support
reliable catalogue growth or real-user data without planned integrity and
operations work**. Main gaps include country and academic-field duplication,
missing relational program/employment/funding structures, weak database-level
invariants for application targets and source provenance, manual expiration,
and no verified production schema/backup/restore evidence.

## Current database and migration state

### Local development database

Read-only inspection used `config.settings.development`. The database backend
was PostgreSQL and the configured host was loopback (`localhost`); the
inspection refused non-loopback connections. No database URL, password, or
personal data was printed.

| Model/table | Local state |
|---|---:|
| `accounts.User` | 1 row |
| `accounts.EmailVerificationToken` | Table missing |
| `students.StudentProfile` | 0 |
| `consultants.ConsultantProfile` | 0 |
| `scholarships.Scholarship` | 0 |
| `universities.University` | 0 |
| `destinations.Destination` | 0 |
| `services.Service` | 0 |
| `applications.Application` | 0 |
| `consultations.Consultation` | 0 |
| `documents.Document` | 0 |
| `notifications.Notification` | 0 |
| `opportunities.OpportunitySource` | 0 |
| `opportunities.CollectionRun` | 0 |
| `opportunities.Opportunity` | 0 |
| `opportunities.OpportunitySourceRecord` | 0 |
| `common.Country` | 249 |

Scholarship publication/status aggregate: **no rows**. The local user count is
aggregate only; no identifying details were inspected or included. These
counts describe only the loopback development database, not staging or
production.

### Migration state

`showmigrations --plan` showed all listed domain migrations applied except the
two below. Production migration state is **UNKNOWN**.

#### Pending migration 1: `accounts.0002_emailverificationtoken`

- **Dependency:** `accounts.0001_initial`.
- **Operation:** create `EmailVerificationToken`.
- **Schema added:** BigAutoField primary key; `user` OneToOne FK to the custom
  User with `CASCADE`; unique 64-character `token_hash`; `created_at`,
  `expires_at`, `last_sent_at`; nullable `used_at`; index on `expires_at`.
- **Data behavior:** creates a new empty table; no existing User records are
  rewritten.
- **Risk:** no destructive operation. The one-to-one uniqueness allows one
  token row per user. Service code must continue to enforce expiry, one-time
  use, and resend behavior; those rules are not database constraints.
- **Readiness effect:** local code expects this table. It is missing in the
  development database, so token operations against that database will fail
  until the migration is applied.

#### Pending migration 2 — untracked working-tree file:
`opportunities.0005_opportunity_documents_required_and_more`

- **Dependency:** `opportunities.0004_opportunity_opportunitysourcerecord_opportunity_and_more`.
- **Operations:** add five fields to Opportunity:
  - `documents_required`: JSONField, `default=list`, blank allowed.
  - `eligibility_notes`: TextField, blank allowed.
  - `eligibility_scope`: CharField, default `UNSPECIFIED`, choices include
    unspecified and Ethiopia-specific variants.
  - `eligible_nationalities`: JSONField, `default=list`, blank allowed, with a
    Python validator for uppercase alpha-2 strings.
  - `excluded_nationalities`: same JSON type/default/validator.
- **Data behavior:** no rows are deleted. For pre-existing Opportunity rows,
  the non-null additions use migration defaults (`[]`, `""`, or
  `UNSPECIFIED`) to populate the new columns. These are schema/backfill
  defaults, not verified eligibility facts.
- **Risk:** no destructive operation. The validator and choices are
  application-level validation, not PostgreSQL constraints on JSON contents.
  The migration imports the validator from `apps.opportunities.models`, so
  deployment must include a compatible import path/version.
- **Readiness effect:** the current serializer references these fields. The
  local table does not yet have them.
- **Version-control risk:** this migration file is untracked in the current
  worktree and is not part of `HEAD`. Django discovers it locally, but it will
  not be present in a checkout built from the current commit unless it is
  reviewed and included in a later approved change.

### Git tracking and migration safety review

The inspected `HEAD` is `d2626774530a8f377cae348a07d6585c9484aa0a`.
`git status --short --untracked-files=all` reported **25 modified tracked
files and 7 untracked files**:

**Modified tracked files**

- `PROJECT_AUDIT.md`, `README.md`
- `app/consultant/page.tsx`
- `app/opportunities/[slug]/OpportunityDetail.tsx`
- `app/scholarships/[id]/ScholarshipDetail.tsx`
- `app/scholarships/page.tsx`
- `app/services/[slug]/ServiceDetail.tsx`, `app/services/page.tsx`
- `app/student/applications/page.tsx`, `app/student/page.tsx`
- `app/study-abroad/[id]/DestinationDetail.tsx`, `app/study-abroad/page.tsx`
- `app/universities/[id]/UniversityDetail.tsx`, `app/universities/page.tsx`
- `backend/apps/opportunities/admin.py`
- `backend/apps/opportunities/models.py`
- `backend/apps/opportunities/serializers.py`
- `backend/apps/opportunities/tests.py`
- `backend/apps/scholarships/admin.py`
- `lib/api/catalogues.ts`, `lib/api/client.ts`, `lib/api/errors.ts`,
  `lib/api/scholarships.ts`
- `next.config.ts`
- `types/index.ts`

**Untracked files**

- `DATABASE_AUDIT.md`
- `DATABASE_READINESS_REPORT.md`
- `MAINTENANCE.md`
- `PROJECT_CURRENT_STATUS.md`
- `SCHOLARSHIP_DISPLAY_DIAGNOSIS.md`
- `backend/apps/opportunities/migrations/0005_opportunity_documents_required_and_more.py`
- `backend/apps/opportunities/models.py.backup`

`accounts.0002_emailverificationtoken.py` is tracked and has no worktree
modification. All other domain migration files found in the worktree are
tracked; `opportunities.0005` is the only migration file missing from `HEAD`.
It is untracked because Git reports the path as `??`: it has not been added to
the index or committed. It is not ignored, and it has no path history in Git.
Its five `AddField` operations match the five new fields in the modified
working-tree Opportunity model. This supports that it was created alongside
those local model changes, but does **not** establish whether it was
intentionally left untracked or accidentally omitted from a commit. There is
no evidence to resolve that intent. The current working-tree model also
includes model-level Python validation beyond the schema changes represented
by the operations; those checks are not PostgreSQL constraints.

The following PostgreSQL SQL was generated using Django's `sqlmigrate` with
development settings and the configured loopback PostgreSQL backend. These
commands only rendered SQL; they did not execute DDL or change the database.
The disposable PostgreSQL rehearsal below subsequently applied and reversed
accounts 0002 only; opportunities 0005 was not rehearsed.

| Migration | Forward PostgreSQL effect | Reverse effect / data-loss risk |
|---|---|---|
| `accounts.0002_emailverificationtoken` | One `CreateModel`: creates `accounts_emailverificationtoken` with a generated `bigint` primary key; `varchar(64)` unique `token_hash`; timezone-aware `created_at`, `expires_at`, and `last_sent_at`; nullable `used_at`; unique UUID `user_id`; a deferred FK to `users(id)`; a token-hash pattern index and expiry index. Existing User rows are untouched. | `DROP TABLE ... CASCADE`. Any token rows created after applying the migration are lost, and outstanding verification links cease to have corresponding token records. |
| `opportunities.0005_opportunity_documents_required_and_more` | Five `AddField` operations on the existing Opportunity table: `documents_required` (`jsonb`, non-null, initial `[]`); `eligibility_notes` (`text`, non-null, initial empty string); `eligibility_scope` (`varchar(30)`, non-null, initial `UNSPECIFIED`); `eligible_nationalities` and `excluded_nationalities` (`jsonb`, non-null, initial `[]`). SQL adds each column with a temporary default to initialize existing rows, then removes the database default. No existing columns are altered or removed. | Drops all five columns with `CASCADE`. Any values later stored in these fields are lost. Any dependent database objects removed by `CASCADE` would also need review. |

Both forward operations are additive and the generated SQL is valid for the
configured Django PostgreSQL backend. `sqlmigrate` is evidence of SQL
generation—not proof that either migration was applied successfully on
PostgreSQL, that it will be fast on a populated table, or that production has
the same schema/backend version. `0005`'s nationality validator is imported
from `apps.opportunities.models`; keep that historical import path available
unless a deliberate migration-safe refactor is made.

**Disposition**

| Migration | Assessment | Decision in this review |
|---|---|---|
| `accounts.0002_emailverificationtoken` | Forward migration is additive; no migration-file correction is indicated by the inspection. Rollback is destructive to token rows. | **Safe for local application only after an explicit approval, recoverable backup, and PostgreSQL rehearsal. Not approved for production.** |
| `opportunities.0005_opportunity_documents_required_and_more` | The operations match the working-tree model additions and are additive, but the migration is absent from `HEAD` while the model change is tracked. That version-control mismatch must be resolved. | **Do not apply yet.** Confirm the intended source change and ensure the reviewed migration and corresponding model/API changes are included together in an approved versioned change. No specific DDL rewrite is established as necessary by this review. Not approved for production. |

The pending migrations have no dependency on each other directly. Django's
graph places each after its app's existing history; `0005` specifically cannot
run before Opportunity is created by `0004`.

## Local PostgreSQL backup and `accounts.0002` rehearsal

### Environment and original database

| Item | Confirmed value |
|---|---|
| Active Django settings | `config.settings.development` |
| Database engine | `django.db.backends.postgresql` |
| Database name | `gofer_exam` |
| Configured host / port | `localhost:5432` |
| Connected server address | `::1` (IPv6 loopback) |
| PostgreSQL version | `18.6` |
| Environment classification | Local development; settings and live connection both point to loopback, not production |
| User/credential | Not included in this report |

Original migration status before and after the rehearsal:

- `accounts.0001_initial`: applied; `accounts.0002_emailverificationtoken`:
  pending.
- `opportunities.0001` through `0004`: applied;
  `opportunities.0005_opportunity_documents_required_and_more`: pending.
- Original DB verification after rehearsal: token table still absent, 27
  public tables and one User row, and no rehearsal database left behind.

These are local development facts only. No production database identity or
migration state was accessed.

### Backup verification

- Created with PostgreSQL 18 `pg_dump.exe` in custom archive format, without
  owner or ACL restoration metadata.
- Private local archive:
  `C:\Users\user\.copilot\session-state\9ff64949-aeb0-4f2d-8872-6d381f382a57\files\gofer_exam_local_20261112_094522_+0300.dump`
- File modification time: `2026-11-12 09:45:31 +03:00`.
- Size: **135,061 bytes** (nonzero).
- `pg_restore --list` archive validation: **passed**.
- Full restore to the disposable PostgreSQL database: **passed**.
- SHA-256:
  `B585A8E792D653B50384570B7A112FB08AC9449D93A80BA11EA0F20DF4B47EFD`.

The archive remains in the current user's session storage and contains a
database backup; keep it private and retain or remove it according to the
project's local backup policy. Credentials were supplied to the tools through
process environment, not printed or placed in command arguments.

### Disposable PostgreSQL rehearsal

The backup was restored to
`gofer_exam_rehearsal_20261112_094923` on the same loopback PostgreSQL 18.6
server. It was created from `template0`, restored with `pg_restore
--exit-on-error --no-owner --no-acl`, used only for the rehearsal, then
dropped. No rehearsal database remains.

Before forward migration, the restored database had **27 public tables**, one
User row, and no `accounts_emailverificationtoken` table. The forward
`accounts.0002_emailverificationtoken` migration completed with `OK`.
Post-migration inspection confirmed:

- Columns: `id` (`bigint`, primary key), `token_hash` (`varchar(64)`),
  `created_at`, `expires_at`, `last_sent_at` (`timestamp with time zone`),
  `used_at` (nullable timestamp), and `user_id` (`uuid`).
- Indexes: primary key on `id`; unique indexes on `token_hash` and `user_id`;
  the token-hash pattern index; and the `expires_at` index.
- Constraints: unique token hash, unique user relation, primary key, and a
  `user_id` foreign key to `users(id)` that is `DEFERRABLE INITIALLY DEFERRED`.
- The new token table had zero rows. No pre-existing application table row
  counts changed. Django's migration recorder gained the expected one
  migration row. Django `post_migrate` also added the new model's content type
  and four permissions.
- `opportunities.0005` was not applied.

The reverse migration to `accounts.0001_initial` completed with `OK` on that
disposable database. It removed the token table; all pre-existing application
table counts remained unchanged and the migration recorder returned to its
baseline. Django's content-type and permission metadata remained after
reversal (+1 content type and +4 permissions), as expected for `post_migrate`
metadata; the disposable database was then dropped. **Reverse is not a
complete cleanup of Django metadata and would lose any token rows if present.**

### Rehearsal result and residual risk

**Result:** forward/reverse PostgreSQL rehearsal **passed** for the restored
local database snapshot on PostgreSQL 18.6. The rehearsal is evidence for this
local version and data snapshot only. It is not production verification, and
does not test deployment timing/locking against a large production database.
No live email-verification flow was exercised.

The original local database remains unchanged: `accounts.0002` is pending,
the token table is absent, `accounts` migration history remains at `0001`,
the original User row count remains one, and `opportunities.0005` remains
pending. The local archive and rehearsal do not establish production backup,
schema, or PostgreSQL version compatibility.

### Exact command to apply to local development (not executed)

**Do not run without a separate explicit approval.** From PowerShell, the
command that targets only the reviewed accounts migration in the configured
local development database is:

```powershell
Set-Location 'C:\Users\user\Desktop\abc\gofer-exam\backend'
$env:DJANGO_SETTINGS_MODULE = 'config.settings.development'
.\venv\Scripts\python.exe manage.py migrate accounts 0002 --noinput
```

This command was not run against the original `gofer_exam` database.
`opportunities.0005` is not part of this target and must remain unapplied.

### All domain migrations, by migration

`Applied`/`Pending` below is the loopback local development migration recorder
state, not production state. `opportunities.0005` is an untracked local file;
all other listed domain migrations are tracked. Each entry describes the
working-tree migration operations.

| Migration | Local | Dependency / operations |
|---|---|---|
| `accounts.0001_initial` | Applied | Depends on Django auth; creates custom User and permission M2Ms. |
| `accounts.0002_emailverificationtoken` | **Pending** | Depends on accounts 0001; creates hashed, one-row-per-user verification-token table and expiry index. |
| `applications.0001_initial` | Applied | Depends on scholarship, university, and custom user initial models; creates Application and its target/owner FKs and indexes. |
| `common.0001_initial` | Applied | Creates Country registry. |
| `consultants.0001_initial` | Applied | Depends on custom User; creates one-to-one ConsultantProfile. |
| `consultations.0001_initial` | Applied | Depends on Service and User; creates Consultation and participant/service relations. |
| `destinations.0001_initial` | Applied | Creates Destination. |
| `documents.0001_initial` | Applied | Depends on Application, Consultation, and User; creates Document and ownership/parent/verifier FKs. |
| `notifications.0001_initial` | Applied | Depends on Application, Consultation, and User; creates Notification. |
| `opportunities.0001_initial` | Applied | Depends on scholarship publication and custom User; creates source, collection-run, and source-record models plus indexes and unique `(source, source_record_key)`. |
| `opportunities.0002_alter_collectionrun_error_summary_and_more` | Applied | Alters collection error/request metadata and source payload JSON fields/validation. |
| `opportunities.0003_opportunitysourcerecord_eligibility_notes_and_more` | Applied | Adds source-record eligibility scope, notes, eligible nationalities, and excluded nationalities. |
| `opportunities.0004_opportunity_opportunitysourcerecord_opportunity_and_more` | Applied | Creates Opportunity, adds its nullable FK to source records, adds an index and an at-most-one-public-target check. |
| `opportunities.0005_opportunity_documents_required_and_more` | **Pending** | Depends on 0004; adds the five opportunity document/eligibility fields described above. |
| `scholarships.0001_initial` | Applied | Creates Scholarship. |
| `scholarships.0002_scholarship_is_published` | Applied | Adds `is_published`. |
| `scholarships.0003_scholarship_country_reference_and_more` | Applied | Depends on Country and scholarship 0002; adds nullable host Country FK, nationality mode and excluded countries, adjusts funding/nationality fields, and adds indexes. No country-string backfill is present. |
| `services.0001_initial` | Applied | Depends on User; creates Service. |
| `students.0001_initial` | Applied | Depends on User; creates StudentProfile. |
| `students.0002_studentprofile_nationality_country_and_more` | Applied | Depends on Country; adds nullable nationality and residence Country FKs. No text-field backfill is present. |
| `universities.0001_initial` | Applied | Creates University. |

There are no `DeleteModel`, `RemoveField`, `RunPython`, or `RunSQL` operations in
the inspected domain migration history. This source review and local recorder
do not establish the production schema, whether any production migration was
faked, or whether backups can restore it.

## Model and relationship review

The 17 model field definitions were inspected through Django model metadata
under test settings (no database writes). Fields use UUID primary keys for
most domain records; `Country.code` is a string primary key and
`EmailVerificationToken` uses a BigAutoField. Django adds indexes to foreign
keys by default unless disabled. The detailed field inventory remains in
[`DATABASE_AUDIT.md`](./DATABASE_AUDIT.md).

| Model | Important relations and deletion behavior | Uniqueness, indexes, structural observations |
|---|---|---|
| `accounts.User` | Django permission/group M2Ms; reverse ownership/role relations. | Unique email; explicit email, role, active indexes. Email unique plus explicit index may duplicate work. |
| `accounts.EmailVerificationToken` | OneToOne User, `CASCADE`. | Unique token hash and user; expiry index. Table is absent locally until pending migration. |
| `students.StudentProfile` | OneToOne User `CASCADE`; nationality/residence Country FKs `SET_NULL`. | User, legacy country string, education-level indexes; also stores text country/nationality beside FKs. |
| `consultants.ConsultantProfile` | OneToOne User `CASCADE`. | User, verification, availability, featured, rating indexes; expertise countries/fields and verification documents are JSON. |
| `scholarships.Scholarship` | Optional host `Country` FK `SET_NULL`; application/source-record reverse links. | Unique slug; country string/FK, category/level/status/featured/deadline/slug/nationality indexes. Eligibility and nationality lists are JSON. |
| `universities.University` | No FK relationships. | Unique slug; indexes country, city, type, featured, ranking, slug. Country and programs are text/JSON. |
| `destinations.Destination` | No FK to Country or University. | Unique name/slug; popularity, feature, rank, slug indexes. Country is represented by name; counts are denormalized. |
| `services.Service` | Optional consultant User FK `CASCADE`; consultation reverse relation. | Unique slug; category/consultant/active/featured/slug indexes. `purchase_count` lacks transaction records. |
| `applications.Application` | Student User `CASCADE`; university and scholarship `SET_NULL`; consultant User `SET_NULL`. | No unique target/student rule or DB target/type constraint; separate indexes on student/status/type/targets/consultant/deadline; mutable JSON status history. |
| `consultations.Consultation` | Student and consultant User FKs `CASCADE`; optional Service `SET_NULL`. | Indexes participants/status/date/paid; no DB exclusion constraint for booking overlap or payment ledger. |
| `documents.Document` | Owner User `CASCADE`; optional Application/Consultation `CASCADE`; verifier User `SET_NULL`. | Indexes owner/type/status/parents; no constraint that linked parent belongs to the same owner. |
| `notifications.Notification` | User/Application/Consultation FKs `CASCADE`. | Composite user/read and user/created indexes plus type/priority; no delivery-attempt or consistency constraints. |
| `opportunities.OpportunitySource` | Reverse runs and source records. | Unique normalized base URL; active/reliability, type, last-success indexes. |
| `opportunities.CollectionRun` | Source FK `PROTECT`; reverse source records. | Source/start and status/start indexes; model validation, not DB constraints, governs completion/timestamps and bounded metadata. |
| `opportunities.Opportunity` | No direct FK to Country or category detail tables; source records link back optionally. | Unique slug; category/status, published/deadline, country indexes. Job-specific attributes and source/publication audit columns are absent. |
| `opportunities.OpportunitySourceRecord` | Source and run `PROTECT`; Scholarship/Opportunity and verifier `SET_NULL`. | Unique `(source, source_record_key)`; check permits **at most one** public target but allows both targets null; indexes on verification, target, URL, identity fingerprint. |
| `common.Country` | Referenced by optional profile/scholarship FKs. | Code primary key; unique name; alpha-3 optional and not unique; name/region/active indexes. |

### Database constraints versus application validation

- Most declared choices, range validators, model `clean()` checks, and
  serializer checks do not automatically become database CHECK constraints.
  Bulk updates and direct SQL can bypass them.
- `OpportunitySourceRecord` is the only reviewed domain model with explicit
  table-level `UniqueConstraint`/`CheckConstraint`, beyond field-level primary
  keys and `unique=True` values. Its target check is:
  `scholarship IS NULL OR opportunity IS NULL`. It rejects both set, but
  **does not require either target to be set**.
- Application `application_type` is not constrained against its two nullable
  target FKs. It can be inconsistent in direct writes; the serializer is the
  primary guard.
- Several model `save()`/`clean()` rules are bypassable by `QuerySet.update`,
  bulk operations, or direct SQL. Existing admin actions do use queryset
  updates in some workflows.
- Explicit indexes may overlap with unique indexes or Django's automatic FK
  indexes. Do not remove any before checking PostgreSQL index definitions and
  representative query plans.

## Catalogue and relationship design

### Opportunity: shared base or separate entities?

The current Opportunity model is explicitly a **non-scholarship** public
catalogue model. Its categories include `INTERNSHIP`, `FELLOWSHIP`, `GRANT`,
research, exchange, training, competition, and other. It can hold generic
fellowships and internships, but:

- It has no `JOB` category.
- There are no employment-specific fields such as employment type, duration,
  compensation, remote/location mode, experience, or work authorization.
- Scholarship is a separate, more detailed model with dedicated eligibility,
  funding and matching behavior.
- `OpportunitySourceRecord` has separate nullable FKs to Scholarship and
  Opportunity rather than one normalized public-target relation.

**Recommendation:** do not duplicate a table for every opportunity subtype.
Keep Opportunity as the shared record for jobs, internships, fellowships,
grants, and similar open calls; add an explicit job category and a small,
typed employment-detail relation or carefully bounded typed fields when
requirements are confirmed. Keep Scholarship separate for now because its
funding and student-matching semantics differ materially. If one unified
catalogue/search index becomes necessary, introduce a common base/target
abstraction through an expand/backfill/dual-read migration, not a destructive
rewrite.

### Eligibility, location, study, and funding

- **Host country:** Scholarship duplicates country as a string and nullable
  Country FK. University and Opportunity use country strings; Destination is a
  named country-like row but does not link to the Country registry. These
  values can diverge from ISO codes or one another.
- **Applicant nationality:** Scholarship stores alpha-2 target/excluded codes
  in JSON and a `ALL`/`SPECIFIC`/`NOT_CONFIRMED` mode. Serializer validation
  normalizes and checks active Country rows. Opportunity and source records
  use JSON alpha-2 lists with Python regex validators and a scope enum that
  contains Ethiopia-specific cases. Neither structure uses relational
  country-through tables or DB validation of each code.
- **Study level:** Scholarship and Opportunity use different enumerations;
  StudentProfile has another current-education enumeration and a free-text
  target degree. Cross-model matching relies on aliases/normalization code.
- **Academic field/program:** scholarship eligibility and student preferred
  fields are JSON/free text; university programs/majors are JSON; no canonical
  `FieldOfStudy` or `UniversityProgram` relation exists. Program-specific
  requirements cannot be consistently joined or constrained.
- **Funding:** Scholarship has a decimal `amount` described as USD plus free
  text `amount_type`; it does not represent currency, range, periodicity,
  tuition versus stipend composition, or funding conditions structurally.
  Opportunity has generic `benefits` JSON and no numeric funding model.
  Consultation/service payment flags and counters are not a transaction
  ledger.

### Verification, publication, and expiration

- The source subsystem has approved-source configuration, collection run
  records, source-specific keys, content/identity hashes, last-seen/change
  times, verification state, verifier, source status, and admin review
  patterns.
- `(source, source_record_key)` uniqueness prevents duplicates for one source,
  not cross-source duplicates. Identity fingerprints are indexed, not unique.
- Source/run pairing and verifier role/time consistency rely partly on model
  validation. Source record can have neither public target due to its DB check
  semantics.
- Scholarship publication checks linked-source state in model/query code.
  Opportunity uses related-source checks too, but the reviewed public
  queryset/model rules do not consistently require an active source and
  administrator verifier in every path. `is_published` is a boolean, not an
  approval event with reviewer and reason.
- Scholarship and Opportunity have status/deadline fields, and source records
  include `EXPIRED` verification status; there is no scheduled expiry/recheck
  job or dedicated `expires_at` for source verification. Status can become
  stale after a deadline unless staff or an external process updates it.

## Missing relationships and duplicate representations

1. No Application FK to Opportunity, and no saved/bookmarked opportunity model.
2. No relational study field or university program; matching relies on text
   and JSON.
3. Multiple country encodings coexist: Country FKs, country names, alpha-2
   JSON arrays, and free text.
4. Student profile stores nationality/residence twice (string and optional
   Country FK); Scholarship stores destination country twice (string and
   optional FK).
5. Scholarship and Opportunity are separate public targets; source provenance
   has two optional target FKs.
6. Application target relationship is polymorphic by paired nullable FKs
   without a DB-level exactly-one/type-matches-target invariant.
7. Document can reference an application/consultation whose owner does not
   match the Document user.
8. Consultation schedules are fields on the booking but not normalized
   consultant availability; booking overlap is not enforced by a PostgreSQL
   exclusion constraint.
9. Application status history is mutable JSON; there is no append-only event
   model or actor FK.
10. Cached counters and payment-state fields are not reconciled against
    transaction/event tables.

## Required schema improvements

Prioritized design work (not implemented):

### Critical before real user data

- Verify production database identity, applied migration graph, backups,
  private file storage and an isolated restore drill.
- Add database-enforced Application target/type integrity only after auditing
  existing rows and planning a backward-compatible migration.
- Define and enforce Document owner-to-parent consistency before exposing any
  upload/download API.
- Decide retention and access audit requirements for personal records.

### High

- Normalize country use with Country references/codes using staged nullable
  fields, verified mapping reports, dual-read/write, and only later deprecate
  legacy strings. Do not infer ambiguous values.
- Add append-only Application status events while retaining legacy JSON through
  a backfill and compatibility period.
- Tighten source-record constraints to require exactly one target and require
  the collection run to belong to the same source at the database layer where
  practical; validate/admin-publish consistently.
- Establish explicit publication reviewer, timestamp, and rejection/unpublish
  reason if content governance/audit requirements demand it.

### Medium

- Add canonical FieldOfStudy and UniversityProgram structures when query and
  program-detail requirements are agreed.
- Add job/internship typed details to the shared Opportunity record; model
  funding amounts/currency/basis explicitly rather than extending free-text
  fields.
- Add automatic deadline/source freshness processing with an auditable close
  reason, scheduled re-verification, and tests.
- Add unique cross-source duplicate review workflow; do not make a fingerprint
  unique until false-positive policy is proven.
- Add payment ledger only if payments are in scope; replace purchase/paid
  counters as sources of truth with transaction records.
- Review redundant indexes using PostgreSQL query plans after representative
  data exists.

## Proposed safe local migration sequence

This sequence is a proposal only. **No migration was run against the original
local development database during this review.** The disposable rehearsal
described above is separate.

1. Confirm the target database is the intended loopback development database
   and not staging/production. Record the current migration plan, table
   presence, and aggregate row counts; retain a recoverable local backup
   according to project policy.
2. Clone the local schema/data into a disposable PostgreSQL database and test
   the migration plan there. Current automated tests use SQLite, so they do
   not substitute for this PostgreSQL step.
3. Before rehearsing `opportunities.0005`, resolve whether it is intended to
   be part of the change. Review the migration and its modified model,
   serializer, admin, and tests together; ensure the migration is present in
   the eventual approved source revision. Do not apply a migration that is
   available only as an untracked local file.
4. Review the planned operations and generated SQL against the disposable
   PostgreSQL clone:
   - apply `accounts.0002_emailverificationtoken`;
   - apply `opportunities.0005_opportunity_documents_required_and_more`,
     after 0004 as its dependency requires.
   Django's migration graph can apply them in its planned order; do not bypass
   dependencies.
5. On the disposable PostgreSQL copy, verify table/column/index/FK creation,
   expected defaults for any pre-existing Opportunity rows, preserved row
   counts, verification API tests, and serializer round-trips. Check migration
   duration/locks using representative data and a compatible PostgreSQL
   version.
6. Only after explicit approval, apply only the reviewed migrations to the
   loopback local development database. Confirm `showmigrations`, inspect the
   token table and Opportunity columns, rerun aggregate row counts, and run
   the backend suite.
7. Keep any later schema improvements separate: expand with nullable
   structures, backfill in a restartable and auditable process, compare data,
   dual-read/write, then add constraints. Contract/drop operations require a
   later explicit review and approval.

Production migrations require a separate release approval, verified backup
and restore, confirmed target identity, staging rehearsal, and production
change window; this report is not authorization.

## Checks run

| Check | Result |
|---|---|
| Django model metadata inspection | **17 application-owned models** enumerated; fields, nullability, unique/index declarations, FK targets and deletion functions inspected without database writes. |
| Domain migration graph inspection | **21 migrations**; operations/dependencies enumerated from 20 tracked migration files and the one untracked working-tree migration. |
| Local development `showmigrations --plan` | All listed domain migrations applied except accounts 0002 and opportunities 0005. |
| Local loopback database aggregate inspection | Read-only; 1 user, 249 countries, zero rows in other present domain tables; EmailVerificationToken table missing. |
| Local PostgreSQL backup | **Passed:** custom-format `pg_dump`; 135,061 bytes; `pg_restore --list` and full restore passed. Private path and timestamp are recorded above. |
| Disposable PostgreSQL rehearsal of accounts 0002 | **Passed:** restored from the backup on local PostgreSQL 18.6; forward and reverse succeeded; token schema, indexes, constraints and application-table counts verified; temporary DB dropped. |
| Original local database after rehearsal | **Unchanged:** accounts 0002 and opportunities 0005 remain pending; token table absent; 27 public tables and one User row; no rehearsal DB remains. |
| `makemigrations --check --dry-run` under test settings | **Passed: no model changes detected.** |
| Full Django test suite under `config.settings.test` | **Passed: 167 tests, 1 skipped.** Test runner created and destroyed an isolated SQLite test database and applied migrations there. |
| Production DB inspection | **Not performed.** Production schema, migration state, records, backups and restoration remain unknown. |

## Approval boundary

This deliverable is the requested review and rehearsal. **No migration has
been applied to the original loopback development database or production.
The model, migration, and application records in the original database were
not modified.** The disposable rehearsal database was removed after testing.
Wait for explicit approval before applying either pending migration to the
original local database or implementing the proposed schema changes.

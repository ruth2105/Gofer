# Gofer Exam Scholarship Display Diagnosis

**Checked:** 2026-11-11
**Scope:** Read-only trace from the deployed preview page through its API
proxy, Django scholarship endpoint, queryset, and local development database.
No data, code, migrations, secrets, or deployments were changed.

## Summary

The primary confirmed cause of the empty catalogue is **no scholarship rows
available to the public query**:

- The deployed preview page issued `GET
  https://gofere-web-preview.onrender.com/api/v1/scholarships/?page=1`.
- The request returned **HTTP 200** with the valid DRF pagination response
  `{"count":0,"next":null,"previous":null,"results":[]}`.
- The checked-in loopback development PostgreSQL database returned **0 total,
  0 published, 0 unpublished**, and **0 rows in the public queryset**.
- The scholarship list endpoint intentionally returns only published
  scholarships, and additionally excludes records with invalid linked source
  records. It does not filter by deadline or open status.

The page's current captured state was the empty-catalogue state, not its error
state. Separate checks also observed **HTTP 429** from an extra preview-proxy
request and **HTTP 503** from a direct request to the API host. These show
intermittent service/rate-limit failures during diagnosis, but do not overturn
the successful preview request or establish that a route is missing. The
production database counts and its applied schema were not inspected.

## End-to-end evidence

| Layer | Evidence | Result |
|---|---|---|
| Scholarship page | [`app/scholarships/page.tsx`](./app/scholarships/page.tsx) calls `getScholarships()` on mount. | Browser confirmed the page sends a list request. |
| API client | [`lib/api/scholarships.ts`](./lib/api/scholarships.ts) calls `api.scholarships.list({ page })`; [`lib/api/client.ts`](./lib/api/client.ts) uses Axios `GET /scholarships/`. | Actual method is **GET**; first request is page 1. |
| Next.js proxy | [`next.config.ts`](./next.config.ts) rewrites `/api/v1/:path*` to the configured API target. [`render.yaml`](./render.yaml) declares the target as the Render API's `/api/v1` base. | Observed browser URL was the same-origin preview proxy URL. |
| Live preview API response | Captured from the page's actual request. | **HTTP 200**, `application/json`, `{"count":0,"next":null,"previous":null,"results":[]}`. Valid pagination shape, zero results. |
| Extra preview request | A separate diagnostic fetch to the same proxy. | **HTTP 429**, `text/plain`, `Too Many Requests`. Not the captured page request. |
| Direct API host probe | Direct request to the configured API host during this check. | **HTTP 503** at that attempt. A later proxied page request succeeded; the direct 503 therefore appears transient or service-state dependent. |
| Django queryset | [`backend/apps/scholarships/services/matching.py`](./backend/apps/scholarships/services/matching.py), `get_public_scholarships()`. | `is_published=True`, excluding any scholarship with a linked source record failing verification/availability/admin-attribution/active-source checks. |
| Local development database | Read-only Django aggregate query, guarded to run only against loopback/local DB. | Total **0**; published **0**; unpublished **0**; public queryset **0**; no status groups. Remote/production DB was not queried. |
| Automated backend tests | `config.settings.test`, `ScholarshipPublicApiTests`. | **6 tests passed**. The tests use an ephemeral SQLite test DB and fixtures; they are not production record counts. |
| Page state | Deployed page snapshot after the successful API response. | “Showing 0 of 0 scholarships” and “No scholarships are published yet”; no active load error in that captured state. |

## Frontend/API contract findings

- The page uses **GET** and does not add authentication or CSRF requirements
  to safe requests. In [`lib/api/client.ts`](./lib/api/client.ts), the CSRF
  interceptor only runs for methods other than GET, HEAD, OPTIONS, and TRACE.
- The public Django `ScholarshipViewSet` explicitly uses
  `permissions.AllowAny`; the personalized `eligible-for-me` endpoint is
  separately authenticated.
- The client expects the standard DRF shape `{count, next, previous, results}`
  and follows `next` by requesting subsequent page numbers. The observed live
  body matches this shape exactly. The API default page size is 20.
- The page's filters are applied client-side after fetching all pages. The
  initial list request sent only `page=1`, so page filters did not remove the
  records in the observed zero-result response.
- The list serializer returns a smaller field set than the client interface:
  fields such as `eligibility`, `fields`, `application_url`, and
  `website_url` are absent in list responses. The mapper treats these as
  optional and uses empty/default values; detail requests use the detail
  serializer. This can reduce card/detail-link content, but it does not explain
  the observed `count: 0`.
- For non-2xx errors, [`lib/api/errors.ts`](./lib/api/errors.ts) gives generic
  messages for 5xx/network errors and returns a plain-text 429 body as its
  message. Thus the page's error state can obscure the distinction between an
  empty successful response and an API/proxy failure. In the successful
  captured request, however, the page correctly rendered the empty state.

## Backend and publication findings

- [`backend/config/urls.py`](./backend/config/urls.py) mounts
  `/api/v1/scholarships/`; [`backend/apps/scholarships/urls.py`](./backend/apps/scholarships/urls.py)
  registers the read-only router.
- [`backend/apps/scholarships/views.py`](./backend/apps/scholarships/views.py)
  exposes the list as public, uses the list serializer, and supports country,
  type, level, status, featured, search, and ordering filters.
- The list queryset is `get_public_scholarships()`: it filters
  `is_published=True` and excludes records with any linked, invalid source
  record. It does **not** require `status=OPEN` or an unexpired deadline for
  the general catalogue. Those filters are used by the personalized/current
  matching workflow instead.
- [`backend/apps/scholarships/serializers.py`](./backend/apps/scholarships/serializers.py)
  emits the expected list fields, including `id`, `slug`, `name`, `type`,
  `level`, `amount`, `amount_type`, `status`, and `is_featured`.
- No import or publication operation was performed. No scholarship records
  were invented or changed.

## Root-cause classification

1. **Database/content (confirmed for the local DB and live public response):**
   there are no rows in the local development database; the deployed preview
   API returned a successful public response with zero visible records. The
   production database's total and publication counts remain **unknown**.
2. **Deployment/service availability (intermittent, needs follow-up):** direct
   API access returned 503 once, and an additional preview request returned
   429. The page's captured list request returned 200. This is inconsistent
   service evidence, not proof of a missing endpoint or a stable API outage.
3. **Frontend contract (not the cause of the zero count):** the client
   pagination contract matches the live response. Optional list-field
   omissions can cause incomplete cards, but not a zero result count.
4. **Authentication/CSRF/filtering (not the cause):** list access is public,
   GET does not trigger CSRF handling, and no UI filter was sent on the
   captured request.

## Affected files reviewed

- Frontend: [`app/scholarships/page.tsx`](./app/scholarships/page.tsx),
  [`lib/api/scholarships.ts`](./lib/api/scholarships.ts),
  [`lib/api/client.ts`](./lib/api/client.ts),
  [`lib/api/errors.ts`](./lib/api/errors.ts),
  [`types/index.ts`](./types/index.ts),
  [`next.config.ts`](./next.config.ts),
  [`.env.example`](./.env.example).
- Backend: [`backend/config/urls.py`](./backend/config/urls.py),
  [`backend/config/settings/base.py`](./backend/config/settings/base.py),
  [`backend/config/settings/development.py`](./backend/config/settings/development.py),
  [`backend/config/settings/production.py`](./backend/config/settings/production.py),
  [`backend/apps/scholarships/models.py`](./backend/apps/scholarships/models.py),
  [`backend/apps/scholarships/urls.py`](./backend/apps/scholarships/urls.py),
  [`backend/apps/scholarships/views.py`](./backend/apps/scholarships/views.py),
  [`backend/apps/scholarships/serializers.py`](./backend/apps/scholarships/serializers.py),
  [`backend/apps/scholarships/services/matching.py`](./backend/apps/scholarships/services/matching.py),
  [`backend/apps/scholarships/tests.py`](./backend/apps/scholarships/tests.py).
- Deployment declaration: [`render.yaml`](./render.yaml).

## Recommended minimal recovery

1. From an authorized Render session, obtain **aggregate-only** production
   counts: total scholarships; published/unpublished; counts by status; and
   published rows excluded by invalid source records. Do not query or export
   student data. Confirm the API service's database resource and migration
   state without exposing connection strings.
2. If production counts are zero, use the existing admin/editorial workflow
   to enter or import only verified, genuine scholarships; validate official
   source links and publication requirements before publishing. Do not make
   draft or unverified records public to populate the page.
3. Investigate Render API/proxy logs and health around the observed 429/503
   responses, then repeat one controlled public GET to the direct API and the
   preview proxy and compare status/body. Do not redeploy as part of this
   diagnosis.
4. If the aggregate query finds published rows but the public queryset is
   empty, inspect the linked source-record verification and active-source
   state before changing publication data.
5. Consider a separate small frontend improvement to distinguish 429
   throttling, 5xx service outage, and successful zero-result states; do not
   add fake fallback records or replace errors with empty success.

## Tests and remaining proof needed

**Run now:** from the `backend` directory in PowerShell:

```powershell
$env:DJANGO_SETTINGS_MODULE = 'config.settings.test'
.\venv\Scripts\python.exe manage.py test apps.scholarships.tests.ScholarshipPublicApiTests --verbosity 1
```

Result: **6 passed**, with Django system checks clean.

**Still required before calling the deployed catalogue healthy:**

- Authorized read-only production aggregate counts and database/resource
  identity confirmation.
- One controlled direct-API and preview-proxy comparison after service
  recovery, including HTTP status and pagination body.
- If real records exist, verify visible counts against the published aggregate
  after source-verification exclusions.
- Browser verification of a nonempty catalogue using approved, genuine data,
  including a detail route and official application URL.
- Optional frontend typecheck/build after any code change; no frontend code
  was changed in this diagnostic task.

**Limitations:** the Render production database was not queried; its row
counts, migration state, and record-level publication causes remain unknown.
The single direct 503 and extra proxy 429 are point-in-time observations and
do not establish a persistent outage.

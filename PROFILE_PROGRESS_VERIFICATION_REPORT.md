# Profile Progress Verification Report

**Date:** 2026-11-16

**Scope:** Student dashboard profile-progress card and `/students/me/completion/`

## Result

The progress card is retained. The API response contract, completion calculation, profile-edit refresh, and backend persistence were verified. ESLint, TypeScript compilation, production build, and the focused backend tests passed.

## API contract and calculation

The endpoint is implemented by `StudentProfileCompletionView`, which serializes `StudentProfile.get_profile_completion_details()`. The response contains exactly:

```json
{
  "percentage": 12.5,
  "is_completed": false,
  "missing_fields": [
    "date_of_birth",
    "nationality",
    "school_name",
    "field_of_study",
    "target_countries",
    "target_degree_level",
    "preferred_fields"
  ]
}
```

That is the response for a newly created test profile. The model checks eight required fields; `current_education_level` has a non-empty `UNDERGRADUATE` default, so the initial percentage is 1/8 (12.5%), not 0%. Completion is calculated as `completed_fields / 8 * 100`, rounded to two decimal places. `is_completed` becomes true at 80% or higher.

The frontend type `StudentProfileCompletionApiRecord` matches the serializer:

- `percentage`: Django REST Framework `FloatField` → TypeScript `number`
- `is_completed`: `BooleanField` → `boolean`
- `missing_fields`: `ListField(CharField)` → `string[]`

The dashboard uses the returned percentage for the bar width (clamped to 0–100) and displays its nearest integer. Missing keys are rendered unchanged in backend snake_case; they are accurate field identifiers but are not converted to human-readable labels.

## States and update/persistence behavior

- **Loading:** The dashboard waits for authentication and the completion request before rendering the progress card.
- **Empty/default profile:** Shows the calculated percentage and returned missing fields. A fully complete profile has an empty missing-fields list, which is not rendered.
- **Error:** A 401 redirects to student login. Other errors show a dashboard-unavailable message and a retry action. The error heading/fallback wording was clarified because the completion request can fail even when authentication succeeds.
- **Profile edit:** After a successful profile save, the profile page refetches completion and updates its completion state.
- **Dashboard refresh:** On a fresh dashboard mount, the completion endpoint is requested again, so the displayed progress comes from persisted backend data rather than browser-local state.
- **Persistence test:** The backend API test performs a profile PATCH and then a separate GET to the completion endpoint. The exact response changes from 12.5% with seven missing fields to 100.0%, `is_completed: true`, and no missing fields.

The API request sequence verifies persistence across requests. A separate browser-driven refresh with an authenticated user was not run in this environment.

## Validation

| Check | Result |
|---|---|
| ESLint (`npm run lint`) | Passed |
| TypeScript (`npx tsc --noEmit`) | Passed |
| Production build (`npm run build`) | Passed; Next.js emitted a workspace-root/package-lock warning, but completed successfully |
| Django student profile API tests (`apps.students.tests` and `tests.test_student_profile_api`, test settings) | Passed: 33 tests |
| Exact empty-profile API payload | Passed |
| Progress update after profile PATCH | Passed |
| Fresh GET returns persisted updated progress | Passed |

# Gofer Exam Role-Permission Matrix

**Assessment date:** 2026-11-12
**Scope:** Observed local source behavior; not a production authorization
certification.

> **Current-state note:** The matrix below is the Phase 1 baseline. The
> [Phase 2 matrix update](#phase-2-current-permission-matrix) below supersedes
> rows that conflict with it.

## Legend

- **Allowed** - implemented by a public endpoint, permission, or owner-scoped
  queryset in the inspected source.
- **Restricted** - the actor cannot use the action through the product API.
- **Django admin** - available through Django admin subject to Django staff and
  model permissions, not through a dedicated product workflow.
- **Missing** - no supporting endpoint/workflow was found.
- **Same as ADMIN** - application API permission treats `ADMIN` and
  `SUPERADMIN` alike.

`Guest` is unauthenticated and is not a `User` role. Stored roles are
`STUDENT`, `CONSULTANT`, `ADMIN`, and `SUPERADMIN`.

## Action matrix

| Action | Guest | Student | Consultant | Admin | Superadmin |
|---|---|---|---|---|---|
| Read public scholarship/opportunity/university/destination/service catalogues | Allowed, published/read-only data | Allowed | Allowed | Allowed | Allowed |
| Register an account | Allowed; registration creates `STUDENT` only | N/A | N/A | N/A | N/A |
| Choose or change own role through registration/profile API | Restricted | Restricted | Restricted | Restricted | Restricted |
| Verify/resend student email | Allowed via throttled public auth endpoints | Own account flow | N/A | N/A | N/A |
| Log in / refresh / log out | Own session only | Allowed after student email verification | Allowed | Allowed | Allowed |
| Reset forgotten password | Missing | Missing | Missing | Missing | Missing |
| Read/update student profile | Restricted | Own profile only | Restricted | Django admin | Django admin |
| Read profile completion | Restricted | Own profile only | Restricted | Not a product API | Not a product API |
| Read personalized scholarship eligibility | Restricted | Allowed, authenticated | Restricted | Restricted by endpoint role | Restricted by endpoint role |
| Create/update own application tracker records | Restricted | Own draft records only | Restricted | Django admin | Django admin |
| Mark application submitted/withdrawn | Restricted | Own record, valid status transitions | Restricted | Django admin | Django admin |
| Read/review application | Restricted | Own tracker record | Assigned applications only | Admin overview API; Django admin for records | Same as ADMIN |
| Assign consultants to applications | Restricted | Restricted | Restricted | Django admin | Django admin |
| Read consultant directory | Restricted | Verified/available consultants only | Restricted | Not a product API | Not a product API |
| Request/cancel consultation or give completed-session feedback | Restricted | Own consultation only | Restricted | Django admin | Django admin |
| Confirm/cancel/complete consultation | Restricted | Restricted | Assigned consultations only | Django admin | Django admin |
| Read/update in-app notifications | Restricted | Own notifications | Own notifications | Own notifications | Own notifications |
| Create/publish/unpublish opportunities | Restricted | Restricted | Restricted | Allowed; publication safeguards apply | Same as ADMIN |
| Verify opportunity source records | Restricted | Restricted | Restricted | Django admin | Django admin |
| Manage scholarship catalogue | Restricted | Restricted | Restricted | Django admin | Django admin |
| Upload/download student documents | Missing | Missing | Missing | Django admin model management only | Django admin model management only |
| Save/bookmark an opportunity | Missing | Missing | Missing | Missing | Missing |
| Apply to job/internship/opportunity through Gofer | Missing | Missing | Missing | Missing | Missing |
| Purchase services / make or reconcile payments | Missing | Missing | Missing | No payment workflow found | No payment workflow found |
| View frontend admin metrics | Restricted | Restricted | Restricted | Allowed via authenticated admin API | Allowed via same admin check |
| Manage users/roles through product API | Missing | Missing | Missing | Missing | Missing |
| Manage users/roles through Django admin | Restricted | Restricted | Restricted | Django admin if granted Django permissions | Django admin with superuser privileges |
| Product-level superadmin-only actions | N/A | N/A | N/A | No separate boundary found | No separate boundary found |

## Backend evidence and interpretation

### Authentication and roles

- `UserRegistrationSerializer` omits `role` and creates a `STUDENT`.
- `UserProfileUpdateSerializer` only accepts first name, last name, and phone
  number. `UserSerializer` makes `role` read-only.
- `IsStudent`, `IsConsultant`, and `IsAdminUser` enforce role checks. The admin
  permission uses `User.is_admin`, which includes both admin roles.
- Registration, email verification, and resend have scoped throttles. A DRF
  login throttle was not found. Password-reset URLs are absent; the existing
  forgot-password page explicitly reports the feature unavailable.

### Ownership and assignment

- The student application viewset filters applications by
  `student=request.user` and only permits draft edits. Application tests cover
  cross-student access and attempts to set ownership/status.
- Consultant application and consultation list/action views filter by
  `consultant=request.user`; tests cover assigned versus unassigned cases.
- Student consultation and notification views are scoped to the requesting
  user.
- Student profile views operate on the authenticated student's profile.

### Public and administrative catalogues

- Scholarship and opportunity reads are public/read-only. Public listing
  safeguards exclude unpublished records; opportunity publication also
  requires verified source safeguards.
- Opportunity create/update permissions admit admin roles only. Scholarship,
  user, consultation, and document management is available principally in
  Django admin.
- The Next.js `/admin` surface is a metrics overview, not a complete
  management interface.

## Security and policy gaps to resolve

1. **Admin/superadmin separation:** no product-level distinction exists in the
   shared admin permission. Define which actions are superadmin-only and add
   explicit permission checks and tests before delegating user/role
   administration.
2. **Django admin role editing:** the custom `UserAdmin` exposes `role`,
   `is_superuser`, and related permission fields. Ensure only the intended
   authority can grant privileged roles and that role changes are auditable.
3. **Login abuse controls:** no DRF login throttle was found. Verify any
   gateway-level protection separately; do not assume it exists.
4. **Document privacy:** a document model/admin exists, but no authenticated
   upload/download endpoint was found. Do not expose private documents through
   generic media URLs without a verified private-storage and ownership policy.
5. **Consultant notes:** the review note is added to the student-visible
   application status timeline. A distinct private note store/API is absent.
6. **Frontend route protection:** no Next.js middleware/proxy exists. Backend
   authorization must be tested directly and remain authoritative.
7. **Local schema state:** email-verification and catalogue migrations remain
   unapplied on the original local database. Use the existing approval and
   rehearsal process; this matrix does not authorize migrations.

## Required permission regression tests before broader implementation

- Every protected endpoint returns unauthorized/forbidden for each wrong role.
- A student cannot read or mutate another student's profile, application,
  consultation, notification, or document.
- A consultant cannot read/update unassigned applications or consultations,
  and cannot access another consultant's assignments.
- A normal admin cannot perform actions designated superadmin-only; only the
  explicitly authorized superadmin can.
- Registration and self-profile updates cannot assign privileged roles.
- Admin role changes are restricted and recorded; test add, edit, deactivate,
  and elevation attempts.
- Public catalogue routes never expose unpublished, expired, or
  source-unverified records.
- Direct API requests bypassing frontend route checks remain correctly denied.
- Document access checks both document ownership and any linked
  application/consultation relationship.

## Phase 2 current permission matrix

This table reflects the local implementation after Phase 2. “API enforced”
means the backend is authoritative; frontend route checks do not grant API
access.

| Action | Guest | Student | Consultant | Admin | Superadmin |
|---|---|---|---|---|---|
| Read public catalogue APIs | Public published/available records only | Same | Same | Same | Same |
| Register or request email verification | Public registration creates Student only; verification/resend are throttled | Own account flow | N/A | N/A | N/A |
| Login, refresh, logout | Own session only | Available when active and verified | Available when active | Available when active | Available when active |
| Read/update own profile | Denied | Own account/profile | Own account; dedicated consultant self-profile | Own account | Own account |
| Read/update another actor's private records | Denied | Denied; owner-scoped querysets | Assigned student records only on supported APIs | Only through explicitly authorized management APIs | Through authorized management APIs |
| Applications and consultations | Denied | Own records | Assigned records/actions only | Shared admin workflows where provided | Shared admin workflows where provided |
| Read/update notifications | Denied | Own notifications | Own notifications | Own notifications | Own notifications |
| Create/publish opportunities | Denied | Denied | Denied | Allowed within verified-source publication safeguards | Allowed within verified-source publication safeguards |
| Manage student/consultant accounts | Denied | Denied | Denied | List/read/update ordinary account fields and activation; cannot change roles or administer admin accounts | May manage roles and administrative accounts through protected user API |
| Manage account roles | Denied | Denied | Denied | Denied | Allowed through protected user-management API; changes are audited |
| Read security audit events | Denied | Denied | Denied | Denied | Read-only API access |
| Django permission/system administration | Denied | Denied | Denied | Not granted by product role alone | Available only through separately authorized Django admin permissions |
| Student document upload/download | Missing | Missing | Missing | Django admin model management only | Django admin model management only |
| Save opportunities or apply to jobs/internships through Gofer | Missing | Missing | Missing | Missing | Missing |

### Phase 2 implementation notes

- Role escalation through public registration and self-profile updates is
  rejected. Inactive users are denied authentication/refresh; student login
  requires email verification.
- Object ownership and consultant assignment continue to be enforced by
  backend permissions and scoped querysets. Wrong-role and cross-owner
  requests are covered by API tests; route hiding is not relied on.
- `IsAdmin` means `ADMIN` only. `IsSuperAdmin` means `SUPERADMIN` only.
  Existing shared admin endpoints may intentionally admit both roles.
- Password reset is public but throttled and non-enumerating; confirmation
  requires a valid single-use, expiring token. Password change/reset revoke
  refresh tokens.
- The Next.js proxy checks the HttpOnly session marker for navigation only;
  it does not independently establish a user's role.
- Security audit events are exposed read-only to Superadmin and protected
  from deletion through the model/admin interfaces.
- The original local database still has five pending migrations:
  `accounts.0002_emailverificationtoken`,
  `accounts.0003_securityauditevent`, `opportunities.0005`,
  `opportunities.0006`, and `scholarships.0004`. No original-local or
  production migration was applied.

### Remaining gaps

- Frontend actor-role gates are not implemented comprehensively for every
  route; the API remains authoritative.
- There is no dedicated API for arbitrary Django permission or privileged
  system-setting management.
- No student document API/private-storage workflow, saved-opportunity API,
  or Gofer job/internship application flow exists.
- Real email-provider delivery, domain verification, deployment behavior,
  and production authorization are unverified.

## Phase 2.1 current frontend route matrix

This update supersedes the earlier Phase 2 statement that comprehensive
role-specific route checks were incomplete.

| Route | Guest | Student | Consultant | Admin | Superadmin |
|---|---|---|---|---|---|
| Public pages and public catalogue pages | Allowed | Allowed | Allowed | Allowed | Allowed |
| `/student/*` except login/register/verify/reset pages | Redirect to login | Allowed | Redirect to Consultant workspace | Redirect to Admin overview | Redirect to Superadmin security landing |
| `/consultant/*` | Redirect to login | Redirect to Student portal | Allowed | Redirect to Admin overview | Redirect to Superadmin security landing |
| `/admin` and `/admin/*` except `/admin/security` | Redirect to login | Redirect to Student portal | Redirect to Consultant workspace | Allowed | Allowed |
| `/admin/security/*` | Redirect to login | Redirect to Student portal | Redirect to Consultant workspace | Redirect to Admin overview | Allowed |
| `/notifications/*` | Redirect to login | Allowed | Allowed | Allowed | Allowed |

Dashboard destinations are `/student`, `/consultant`, `/admin`, and
`/admin/security` for Student, Consultant, Admin, and Superadmin respectively.
Login return destinations are restricted to same-origin paths authorized for
the role.

### Navigation and enforcement notes

- Shared navigation always exposes public links. It shows account links only
  for the authenticated role; the Security Audit link is Superadmin-only.
- The root `AuthProvider` resolves `/api/v1/auth/me/` and refreshes on
  client-side route changes. Protected route children are withheld while
  identity is loading or unavailable.
- A route mismatch redirects to the correct role dashboard. Failed refresh
  returns the user to login with a safe intended destination.
- These are client-side navigation controls. They are not security controls
  against a modified browser or direct API requests. Django permissions and
  scoped querysets remain authoritative.
- `/admin/security` reads the existing Superadmin-only audit endpoint. The
  endpoint itself remains protected independently of the page guard.
- No migration was applied to the original local database. Because
  `accounts.0003_securityauditevent` is still pending there, the audit UI
  requires the authorized account migration chain before its live data request
  can work against that database.

### Phase 2.1 route evidence

- Five Node route-policy tests pass, covering the role matrix, public paths,
  dashboards, safe login destinations, and role-specific navigation links.
- Local browser checks used stubbed `/auth/me/` identities, not real users or
  a live backend. They confirmed guest redirect and wrong-role redirects for
  Student, Consultant, Admin, and Superadmin.
- At a 375px viewport, Superadmin mobile navigation showed Security Audit;
  Admin mobile navigation did not. Both rendered without horizontal overflow.

### Email state

No local provider configuration is available. The resolved local email
backend remains Django console with a localhost sender; production settings
enforce sender/backend/SMTP shape but cannot verify provider receipt. No
message was sent. See
[PHASE2_1_COMPLETION_REPORT.md](./PHASE2_1_COMPLETION_REPORT.md) for the
exact provider and authorized-test-mailbox steps.

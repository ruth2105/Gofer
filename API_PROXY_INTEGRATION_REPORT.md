# API Proxy Integration Report

## Scope

This review covers the recent proxy-related changes in [next.config.ts](./next.config.ts) and [.env.example](./.env.example), plus the surrounding authentication/proxy integration path in [lib/api/client.ts](./lib/api/client.ts), [proxy.ts](./proxy.ts), [components/auth/AuthProvider.tsx](./components/auth/AuthProvider.tsx), and [lib/api/errors.ts](./lib/api/errors.ts).

No production, deploy, push, or database changes were made during this review. The work was limited to validation and documentation.

## Summary

The proxy integration is correctly configured for local development and deployment.

- Environment-variable precedence is correct and stable: `API_PROXY_TARGET` > `NEXT_PUBLIC_API_URL` > local default (`http://localhost:8000/api/v1`).
- Browser calls are same-origin through `/api/v1`, so local requests are routed to the intended Django API by Next.js rewrite rules.
- Deployment overrides remain supported via the server-side environment value used by the rewrite target.
- No secret or private credentials are introduced into the browser bundle: the frontend client uses `/api/v1`, not a direct backend URL, and the rewrite target remains server-only.
- API errors, unavailable backends, and request timeouts are handled through Axios timeouts and user-facing error mapping.
- The authentication and protected-route flows remain compatible with the proxy model, and the focused auth test suite still passes.
- The production build still passes with the proxy configuration in place.

## Detailed verification

### 1) Environment-variable precedence is correct

Reviewed logic in [next.config.ts](./next.config.ts):

```ts
const configuredApiProxyTarget = (
  process.env.API_PROXY_TARGET
  || process.env.NEXT_PUBLIC_API_URL
  || "http://localhost:8000/api/v1"
);
const apiProxyTarget = configuredApiProxyTarget.replace(/\/+$/, "");
```

This yields the intended precedence:

1. `API_PROXY_TARGET`
2. `NEXT_PUBLIC_API_URL`
3. `http://localhost:8000/api/v1`

This preserves deployment overrides while still allowing local development to function without extra manual setup. The use of `API_PROXY_TARGET` as the preferred server-side variable is consistent with the project documentation in [README.md](./README.md).

### 2) Local requests reach the intended Django API

The actual browser client uses a same-origin base URL in [lib/api/client.ts](./lib/api/client.ts):

```ts
const API_BASE_URL = '/api/v1';
```

The rewrite rule in [next.config.ts](./next.config.ts):

```ts
async rewrites() {
  return [{
    source: "/api/v1/:path*",
    destination: `${apiProxyTarget}/:path*/`,
  }];
}
```

This means browser requests such as `/api/v1/auth/login/` are rewritten to the configured backend base, e.g. `http://localhost:8000/api/v1/auth/login/` in development. That matches the intended Django API location and keeps the auth cookies on the frontend origin.

### 3) Deployment overrides are preserved

The rewrite target is intentionally server-side and deployment-controlled. The config does not hardcode a production URL; it resolves from environment variables and only falls back to localhost for local development.

This preserves the deployment override workflow used by the project, including the Render configuration referenced in [render.yaml](./render.yaml), which sets `API_PROXY_TARGET` to the deployed backend service.

### 4) No secrets or private configuration are exposed to browser bundles

The frontend client never reads the backend URL directly. Instead, [lib/api/client.ts](./lib/api/client.ts) calls the relative path `/api/v1` and the proxy layer handles the upstream target on the server.

That means:

- no JWTs or session secrets are placed in the browser bundle,
- no private backend endpoint is hardcoded into client code,
- no browser-exposed env var is required for the normal auth flow.

The project intentionally prefers the server-only `API_PROXY_TARGET` variable over `NEXT_PUBLIC_API_URL`; the latter is treated as a legacy fallback only.

### 5) API errors, unavailable backend responses and timeouts are handled correctly

The client layer in [lib/api/client.ts](./lib/api/client.ts) creates Axios with a 30-second timeout and credentials enabled:

```ts
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
  withCredentials: true,
});
```

Error handling is centralized in [lib/api/errors.ts](./lib/api/errors.ts):

- `ECONNABORTED` -> user-friendly timeout message
- no response object -> service unreachable message
- 404 -> route/record not found message
- 5xx -> temporary service unavailable message
- API payload error strings are surfaced cleanly

This provides appropriate feedback when the backend is down, slow, or returning an unexpected response.

### 6) Login, registration, password reset and protected-route flows still work with the proxy

The proxy remains compatible with the app’s auth flow because the browser continues to call same-origin `/api/v1/...` endpoints while the server rewrites them to the configured Django base URL.

Relevant flow points:

- [lib/api/client.ts](./lib/api/client.ts) sends auth actions such as `/auth/login/`, `/auth/register/`, `/auth/password/reset/`, and `/auth/token/refresh/` via the proxy path.
- [proxy.ts](./proxy.ts) protects routes under `/student`, `/consultant`, `/admin`, and `/notifications` by requiring the `gofer_session` cookie before allowing access.
- [components/auth/AuthProvider.tsx](./components/auth/AuthProvider.tsx) loads `/api/v1/auth/me/` and handles 401/403 states by treating them as anonymous sessions or expired sessions.

The focused auth route tests in [lib/auth/access.test.mjs](./lib/auth/access.test.mjs) validate protected-route logic and role-based authorization. They pass with the current proxy setup.

### 7) Existing authentication tests and production build still pass

Validation executed:

```bash
cd "C:\Users\user\Desktop\abc\gofer-exam"
npm run build
npm run test:auth-routes
```

Results:

- `npm run build` passed successfully.
- `npm run test:auth-routes` passed successfully: 5 tests passed, 0 failed.

This confirms that the proxy integration still satisfies the project’s existing auth validation and build requirements.

## Findings

No proxy-integration issues were found in the reviewed changes. The configuration is sound for local development and deployment override support, and it remains consistent with the app’s auth and protected-route behavior.

## Risk notes

The main operational caveat is not code-related: the backend must actually be reachable at the configured `API_PROXY_TARGET` value in each environment. The app can handle downtime and timeout failures gracefully, but it cannot fix a missing or unreachable upstream backend.

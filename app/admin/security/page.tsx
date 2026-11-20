'use client';

import axios from 'axios';
import { useEffect, useState } from 'react';
import { Footer } from '@/components/layout/Footer';
import { Navigation } from '@/components/layout/Navigation';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { api, PaginatedResponse, SecurityAuditEventApiRecord } from '@/lib/api/client';
import { getApiErrorMessage } from '@/lib/api/errors';

function formatRole(role: string): string {
  return role || 'System';
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

export default function SuperadminSecurityPage() {
  const [page, setPage] = useState(1);
  const [request, setRequest] = useState<{
    page: number;
    loading: boolean;
    events?: PaginatedResponse<SecurityAuditEventApiRecord>;
    error?: string;
  }>({ page: 0, loading: true });
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;

    api.admin.auditEvents({ page })
      .then((result) => {
        if (active) setRequest({ page, loading: false, events: result });
      })
      .catch((requestError: unknown) => {
        if (!active) return;
        if (axios.isAxiosError(requestError) && requestError.response?.status === 403) {
          setRequest({
            page,
            loading: false,
            error: 'Your account is not authorized to view security audit events.',
          });
        } else {
          setRequest({
            page,
            loading: false,
            error: getApiErrorMessage(requestError, 'Security audit events could not be loaded.'),
          });
        }
      })

    return () => {
      active = false;
    };
  }, [page, retry]);

  const loading = request.loading || request.page !== page;
  const error = request.page === page ? request.error : undefined;
  const events = request.page === page ? request.events : undefined;

  return (
    <div className="flex min-h-screen flex-col">
      <Navigation />
      <main id="main-content" tabIndex={-1} className="flex-1 bg-gray-50 px-4 py-10 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl">
          <header className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Security Audit</h1>
            <p className="mt-2 text-gray-600">
              Read-only records of sensitive account and access-control changes.
            </p>
          </header>

          {loading ? (
            <p className="py-12 text-center text-gray-600" role="status">Loading security events…</p>
          ) : error ? (
            <div className="py-12 text-center" role="alert">
              <p className="text-gray-700">{error}</p>
              <Button className="mt-4" onClick={() => {
                setRequest((current) => ({ ...current, loading: true }));
                setRetry((value) => value + 1);
              }}>Try Again</Button>
            </div>
          ) : events?.results.length ? (
            <>
              <div className="space-y-4">
                {events.results.map((event) => (
                  <Card as="article" key={event.id}>
                    <CardHeader>
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div>
                          <CardTitle>{event.action.replaceAll('_', ' ')}</CardTitle>
                          <CardDescription className="mt-1">{formatDate(event.created_at)}</CardDescription>
                        </div>
                        <span className="rounded-full bg-primary-50 px-3 py-1 text-sm font-medium text-primary-800">
                          {formatRole(event.actor_role)}
                        </span>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <dl className="grid gap-3 text-sm sm:grid-cols-2">
                        <div>
                          <dt className="font-medium text-gray-500">Actor</dt>
                          <dd className="break-all text-gray-900">{event.actor_id || 'System'}</dd>
                        </div>
                        <div>
                          <dt className="font-medium text-gray-500">Target</dt>
                          <dd className="break-all text-gray-900">
                            {event.target_id || 'Not applicable'}
                            {event.target_role ? ` (${event.target_role})` : ''}
                          </dd>
                        </div>
                      </dl>
                      {Object.keys(event.details).length > 0 && (
                        <details className="mt-4">
                          <summary className="cursor-pointer font-medium text-primary-700">
                            Change details
                          </summary>
                          <pre className="mt-2 overflow-x-auto rounded-lg bg-gray-100 p-3 text-xs text-gray-800">
                            {JSON.stringify(event.details, null, 2)}
                          </pre>
                        </details>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
              <nav className="mt-6 flex items-center justify-between" aria-label="Audit event pages">
                <Button
                  variant="outline"
                  disabled={!events.previous || loading}
                  onClick={() => setPage((value) => Math.max(1, value - 1))}
                >
                  Previous
                </Button>
                <span className="text-sm text-gray-600" aria-live="polite">
                  Page {page} · {events.count} event{events.count === 1 ? '' : 's'}
                </span>
                <Button
                  variant="outline"
                  disabled={!events.next || loading}
                  onClick={() => setPage((value) => value + 1)}
                >
                  Next
                </Button>
              </nav>
            </>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <h2 className="text-lg font-semibold text-gray-900">No security events yet</h2>
                <p className="mt-2 text-gray-600">New audit events will appear here when sensitive actions are recorded.</p>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}

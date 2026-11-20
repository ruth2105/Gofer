'use client';

import { ReactNode, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { getRoleHome, isAuthorizedForRoute, isProtectedRoute } from '@/lib/auth/access';
import { useAuth } from '@/components/auth/AuthProvider';
import { Button } from '@/components/ui/Button';

export function RoleRouteGuard({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, status, sessionExpired, error, retry } = useAuth();
  const protectedRoute = isProtectedRoute(pathname);
  const authorized = !!user && isAuthorizedForRoute(pathname, user.role);

  useEffect(() => {
    if (!protectedRoute || status === 'loading' || status === 'error') return;
    if (!user) {
      const next = `${pathname}${window.location.search}`;
      const reason = sessionExpired ? 'session_expired' : 'auth_required';
      router.replace(`/student/login?reason=${reason}&next=${encodeURIComponent(next)}`);
      return;
    }
    if (!authorized) router.replace(getRoleHome(user.role));
  }, [authorized, pathname, protectedRoute, router, sessionExpired, status, user]);

  if (!protectedRoute) return children;

  if (status === 'error') {
    return (
      <div className="mx-auto max-w-xl p-8 text-center" role="alert">
        <h1 className="text-xl font-semibold text-gray-900">Account check unavailable</h1>
        <p className="mt-2 text-gray-600">{error}</p>
        <Button className="mt-5" onClick={retry}>Try Again</Button>
      </div>
    );
  }

  if (status === 'loading' || !user || !authorized) {
    return <p className="p-8 text-center text-gray-600" role="status">Checking your access…</p>;
  }

  return children;
}

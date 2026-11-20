import type { UserApiRecord } from '@/lib/api/client';

export type UserRole = UserApiRecord['role'];

const publicStudentRoutes = [
  '/student/login',
  '/student/register',
  '/student/verify-email',
  '/student/forgot-password',
  '/student/reset-password',
];

function matchesPath(pathname: string, route: string): boolean {
  return pathname === route || pathname.startsWith(`${route}/`);
}

export function isPublicStudentRoute(pathname: string): boolean {
  return publicStudentRoutes.some((route) => matchesPath(pathname, route));
}

export function isProtectedRoute(pathname: string): boolean {
  if (isPublicStudentRoute(pathname)) return false;
  return (
    matchesPath(pathname, '/student')
    || matchesPath(pathname, '/consultant')
    || matchesPath(pathname, '/admin')
    || matchesPath(pathname, '/notifications')
  );
}

export function isAuthorizedForRoute(pathname: string, role: UserRole): boolean {
  if (matchesPath(pathname, '/admin/security')) return role === 'SUPERADMIN';
  if (matchesPath(pathname, '/admin')) return role === 'ADMIN' || role === 'SUPERADMIN';
  if (matchesPath(pathname, '/student') && !isPublicStudentRoute(pathname)) {
    return role === 'STUDENT';
  }
  if (matchesPath(pathname, '/consultant')) return role === 'CONSULTANT';
  if (matchesPath(pathname, '/notifications')) return true;
  return true;
}

export function getRoleHome(role: UserRole): string {
  switch (role) {
    case 'STUDENT':
      return '/student';
    case 'CONSULTANT':
      return '/consultant';
    case 'ADMIN':
      return '/admin';
    case 'SUPERADMIN':
      return '/admin/security';
  }
}

export function getSafeLoginDestination(
  candidate: string | null,
  role: UserRole,
  origin: string
): string {
  const fallback = getRoleHome(role);
  if (
    !candidate
    || !candidate.startsWith('/')
    || candidate.startsWith('//')
    || candidate.includes('\\')
  ) {
    return fallback;
  }

  try {
    const destination = new URL(candidate, origin);
    if (destination.origin !== origin || !isProtectedRoute(destination.pathname)) {
      return fallback;
    }
    if (!isAuthorizedForRoute(destination.pathname, role)) return fallback;
    return `${destination.pathname}${destination.search}${destination.hash}`;
  } catch {
    return fallback;
  }
}

export function getRoleNavigation(role: UserRole): Array<{ href: string; label: string }> {
  switch (role) {
    case 'STUDENT':
      return [
        { href: '/student', label: 'Student Portal' },
        { href: '/student/applications', label: 'My Applications' },
        { href: '/student/consultations', label: 'My Consultations' },
        { href: '/student/profile', label: 'My Profile' },
      ];
    case 'CONSULTANT':
      return [
        { href: '/consultant', label: 'Consultant Workspace' },
        { href: '/consultant/consultations', label: 'Manage Consultations' },
      ];
    case 'ADMIN':
      return [{ href: '/admin', label: 'Admin Overview' }];
    case 'SUPERADMIN':
      return [
        { href: '/admin', label: 'Admin Overview' },
        { href: '/admin/security', label: 'Security Audit' },
      ];
  }
}

import { NextRequest, NextResponse } from 'next/server';

const publicStudentRoutes = [
  '/student/login',
  '/student/register',
  '/student/verify-email',
  '/student/forgot-password',
  '/student/reset-password',
];

function isPublicStudentRoute(pathname: string): boolean {
  return publicStudentRoutes.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`)
  );
}

function requiresSession(pathname: string): boolean {
  if (isPublicStudentRoute(pathname)) return false;
  return (
    pathname === '/student'
    || pathname.startsWith('/student/')
    || pathname === '/consultant'
    || pathname.startsWith('/consultant/')
    || pathname === '/admin'
    || pathname.startsWith('/admin/')
    || pathname === '/notifications'
    || pathname.startsWith('/notifications/')
  );
}

export function proxy(request: NextRequest) {
  if (!requiresSession(request.nextUrl.pathname)) {
    return NextResponse.next();
  }

  if (request.cookies.has('gofer_session')) {
    return NextResponse.next();
  }

  const loginUrl = new URL('/student/login', request.url);
  loginUrl.searchParams.set(
    'next',
    `${request.nextUrl.pathname}${request.nextUrl.search}`
  );
  loginUrl.searchParams.set('reason', 'auth_required');
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: [
    '/student/:path*',
    '/consultant/:path*',
    '/admin/:path*',
    '/notifications/:path*',
  ],
};

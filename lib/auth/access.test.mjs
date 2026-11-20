import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';

const source = await readFile(new URL('./access.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2022,
  },
}).outputText;
const {
  getRoleHome,
  getRoleNavigation,
  getSafeLoginDestination,
  isAuthorizedForRoute,
  isProtectedRoute,
} = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);

test('role dashboards map to their respective destinations', () => {
  assert.equal(getRoleHome('STUDENT'), '/student');
  assert.equal(getRoleHome('CONSULTANT'), '/consultant');
  assert.equal(getRoleHome('ADMIN'), '/admin');
  assert.equal(getRoleHome('SUPERADMIN'), '/admin/security');
});

test('protected route matrix keeps each actor within authorized areas', () => {
  const protectedPaths = [
    '/student',
    '/student/applications',
    '/consultant',
    '/consultant/consultations',
    '/admin',
    '/admin/security',
    '/notifications',
  ];
  const expected = {
    STUDENT: [true, true, false, false, false, false, true],
    CONSULTANT: [false, false, true, true, false, false, true],
    ADMIN: [false, false, false, false, true, false, true],
    SUPERADMIN: [false, false, false, false, true, true, true],
  };

  for (const [role, outcomes] of Object.entries(expected)) {
    protectedPaths.forEach((path, index) => {
      assert.equal(isProtectedRoute(path), true);
      assert.equal(isAuthorizedForRoute(path, role), outcomes[index], `${role} ${path}`);
    });
  }
});

test('public routes remain available to guests', () => {
  for (const path of [
    '/',
    '/scholarships',
    '/student/login',
    '/student/register',
    '/student/verify-email',
    '/student/forgot-password',
    '/student/reset-password',
  ]) {
    assert.equal(isProtectedRoute(path), false, path);
  }
});

test('login destinations are same-site and role-authorized', () => {
  const origin = 'https://gofer.example';
  assert.equal(
    getSafeLoginDestination('/student/applications?page=2', 'STUDENT', origin),
    '/student/applications?page=2',
  );
  assert.equal(getSafeLoginDestination('/admin/security', 'ADMIN', origin), '/admin');
  assert.equal(
    getSafeLoginDestination('/admin/security', 'SUPERADMIN', origin),
    '/admin/security',
  );
  assert.equal(
    getSafeLoginDestination('//attacker.example/path', 'STUDENT', origin),
    '/student',
  );
  assert.equal(
    getSafeLoginDestination('/consultant', 'STUDENT', origin),
    '/student',
  );
});

test('navigation links expose only destinations for the current role', () => {
  const adminLinks = getRoleNavigation('ADMIN');
  const superadminLinks = getRoleNavigation('SUPERADMIN');
  assert.equal(adminLinks.some(({ href }) => href === '/admin/security'), false);
  assert.equal(superadminLinks.some(({ href }) => href === '/admin/security'), true);
});

import { Suspense } from 'react';
import { PublicPageShell } from '@/components/layout/PublicPageShell';
import { ResetPasswordForm } from './ResetPasswordForm';

export const metadata = {
  referrer: 'no-referrer',
};

export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ uid?: string; token?: string }>;
}) {
  return (
    <Suspense fallback={<p className="p-6 text-center text-gray-600" role="status">Loading reset form…</p>}>
      <ResetPasswordContent searchParams={searchParams} />
    </Suspense>
  );
}

async function ResetPasswordContent({
  searchParams,
}: {
  searchParams: Promise<{ uid?: string; token?: string }>;
}) {
  const { uid = '', token = '' } = await searchParams;

  return (
    <PublicPageShell
      title="Choose a new password"
      description="Reset links are single-use and expire automatically."
    >
      <ResetPasswordForm uid={uid} token={token} />
    </PublicPageShell>
  );
}

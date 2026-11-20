'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { api } from '@/lib/api/client';
import { getApiErrorMessage } from '@/lib/api/errors';

export function ResetPasswordForm({ uid, token }: { uid: string; token: string }) {
  const router = useRouter();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [linkExpired, setLinkExpired] = useState(false);
  const invalidLink = !uid || !token || linkExpired;

  useEffect(() => {
    if (uid && token) {
      window.history.replaceState(null, '', window.location.pathname);
    }
  }, [token, uid]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await api.auth.confirmPasswordReset({
        uid,
        token,
        new_password: newPassword,
        new_password2: confirmPassword,
      });
      router.replace('/student/login?reason=password_reset');
    } catch (requestError: unknown) {
      const message = getApiErrorMessage(requestError, 'The password could not be reset.');
      setError(message);
      if (message.toLowerCase().includes('invalid or expired')) {
        setLinkExpired(true);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="rounded-xl bg-white p-6 shadow-sm sm:p-8">
      {invalidLink ? (
        <div className="space-y-4">
          <p className="rounded-lg bg-amber-50 p-4 text-amber-900" role="alert">
            This password-reset link is missing, invalid, or expired. Request a new link to continue.
          </p>
          <Link href="/student/forgot-password" className="font-semibold text-primary-700 underline">
            Request another link
          </Link>
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <Input
            type="password"
            label="New password"
            autoComplete="new-password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            required
          />
          <Input
            type="password"
            label="Confirm new password"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            required
          />
          {error && <p className="rounded-lg bg-red-50 p-4 text-sm text-red-800" role="alert">{error}</p>}
          <Button type="submit" className="w-full" isLoading={submitting}>
            {submitting ? 'Updating password…' : 'Set new password'}
          </Button>
        </form>
      )}
    </section>
  );
}

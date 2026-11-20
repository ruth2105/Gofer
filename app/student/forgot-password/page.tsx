'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { PublicPageShell } from '@/components/layout/PublicPageShell';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { api } from '@/lib/api/client';
import { getApiErrorMessage } from '@/lib/api/errors';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setMessage('');
    setError('');
    try {
      const result = await api.auth.requestPasswordReset(email);
      setMessage(result.message);
    } catch (requestError: unknown) {
      setError(getApiErrorMessage(requestError, 'The reset request could not be processed.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PublicPageShell
      title="Password assistance"
      description="Request a secure password-reset link."
    >
      <section className="rounded-xl bg-white p-6 shadow-sm sm:p-8">
        <form onSubmit={submit} className="space-y-4">
          <Input
            type="email"
            label="Account email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          {message && <p className="rounded-lg bg-blue-50 p-4 text-sm text-blue-900" role="status">{message}</p>}
          {error && <p className="rounded-lg bg-red-50 p-4 text-sm text-red-800" role="alert">{error}</p>}
          <Button type="submit" className="w-full" isLoading={submitting}>
            {submitting ? 'Requesting…' : 'Request password reset'}
          </Button>
        </form>
        <p className="mt-5 text-sm text-gray-600">
          If no message arrives, contact{' '}
          <a className="underline" href="mailto:info@goferexam.com">Gofer Exam support</a>.
        </p>
        <Link href="/student/login" className="mt-5 inline-block font-semibold text-primary-700 underline">
          Return to sign in
        </Link>
      </section>
    </PublicPageShell>
  );
}

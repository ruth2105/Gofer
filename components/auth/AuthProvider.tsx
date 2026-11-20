'use client';

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { usePathname } from 'next/navigation';
import axios from 'axios';
import { api, UserApiRecord } from '@/lib/api/client';

type AuthStatus = 'loading' | 'authenticated' | 'anonymous' | 'error';

interface AuthContextValue {
  user: UserApiRecord | null;
  status: AuthStatus;
  sessionExpired: boolean;
  error: string;
  retry: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [user, setUser] = useState<UserApiRecord | null>(null);
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [sessionExpired, setSessionExpired] = useState(false);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const [resolvedPathname, setResolvedPathname] = useState('');

  const retry = useCallback(() => {
    setResolvedPathname('');
    setRevision((value) => value + 1);
  }, []);

  useEffect(() => {
    let active = true;

    api.auth.getCurrentUser()
      .then((profile) => {
        if (!active) return;
        setUser(profile);
        setSessionExpired(false);
        setError('');
        setStatus('authenticated');
        setResolvedPathname(pathname);
      })
      .catch((requestError: unknown) => {
        if (!active) return;
        if (axios.isAxiosError(requestError) && [401, 403].includes(requestError.response?.status ?? 0)) {
          setUser(null);
          setStatus('anonymous');
          setResolvedPathname(pathname);
          return;
        }
        setUser(null);
        setError('Your account could not be checked. Try again when your connection is available.');
        setStatus('error');
        setResolvedPathname(pathname);
      });

    return () => {
      active = false;
    };
  }, [pathname, revision]);

  useEffect(() => {
    const handleSessionExpired = () => {
      setUser(null);
      setSessionExpired(true);
      setStatus('anonymous');
      setResolvedPathname(pathname);
    };
    const handleAuthChanged = () => retry();
    window.addEventListener('gofer:auth-changed', handleAuthChanged);
    window.addEventListener('gofer:session-expired', handleSessionExpired);
    return () => {
      window.removeEventListener('gofer:auth-changed', handleAuthChanged);
      window.removeEventListener('gofer:session-expired', handleSessionExpired);
    };
  }, [pathname, retry]);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    status: resolvedPathname === pathname ? status : 'loading',
    sessionExpired,
    error,
    retry,
  }), [error, pathname, resolvedPathname, retry, sessionExpired, status, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider.');
  return context;
}

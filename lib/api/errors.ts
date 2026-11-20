import axios from 'axios';

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && !axios.isAxiosError(error)) return error.message || fallback;
  if (!axios.isAxiosError(error)) return fallback;

  if (error.code === 'ECONNABORTED') {
    return 'The service took too long to respond. Please try again.';
  }

  if (!error.response) {
    return 'The service could not be reached. Check your connection and try again.';
  }

  if (error.response.status === 404) {
    return `${fallback} The requested API route or record was not found.`;
  }

  if (error.response.status >= 500) {
    return 'The service is temporarily unavailable. Please try again later.';
  }

  const data: unknown = error.response?.data;
  if (typeof data === 'string') return data;
  if (!data || typeof data !== 'object') return fallback;

  for (const value of Object.values(data as Record<string, unknown>)) {
    if (typeof value === 'string') return value;
    if (Array.isArray(value)) {
      const message = value.find((item): item is string => typeof item === 'string');
      if (message) return message;
    }
  }
  return fallback;
}

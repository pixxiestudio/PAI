/**
 * React Query Configuration
 * Global settings for React Query with error handling
 */

import { QueryClient, DefaultOptions } from '@tanstack/react-query';
import { isRetryableError, exponentialBackoffDelay } from './error-handler';

/**
 * Default query options
 */
export const defaultQueryOptions: DefaultOptions = {
  queries: {
    // Cache data for 5 minutes
    staleTime: 1000 * 60 * 5,
    // Keep unused cache for 10 minutes
    gcTime: 1000 * 60 * 10,
    // Retry retryable errors up to 3 times
    retry: (failureCount, error) => {
      if (failureCount >= 3) return false;
      return isRetryableError(error);
    },
    // Exponential backoff for retries
    retryDelay: (attemptIndex) => exponentialBackoffDelay(attemptIndex + 1),
  },
  mutations: {
    // Don't retry mutations by default (they can have side effects)
    retry: false,
  },
};

/**
 * Create configured React Query client
 */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: defaultQueryOptions,
  });
}

/**
 * Singleton query client instance
 */
let queryClientInstance: QueryClient | null = null;

export function getQueryClient(): QueryClient {
  if (!queryClientInstance) {
    queryClientInstance = createQueryClient();
  }
  return queryClientInstance;
}

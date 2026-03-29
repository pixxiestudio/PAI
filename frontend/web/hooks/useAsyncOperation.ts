'use client';

import React, { useState, useCallback, useRef } from 'react';
import { ApiErrorWithContext } from '@/lib/error-handler';

interface AsyncState<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
}

/**
 * Hook for handling async operations with error and loading states
 * Useful for manual async operations that aren't covered by React Query
 */
export function useAsyncOperation<T>() {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const execute = useCallback(async (asyncFn: () => Promise<T>) => {
    setState({ data: null, isLoading: true, error: null });

    try {
      const result = await asyncFn();
      setState({ data: result, isLoading: false, error: null });
      return result;
    } catch (error) {
      const apiError =
        error instanceof ApiErrorWithContext
          ? error
          : new ApiErrorWithContext(
              error instanceof Error ? error.message : 'Unknown error',
              undefined,
              undefined,
              error instanceof Error ? error : undefined
            );

      setState({ data: null, isLoading: false, error: apiError });
      throw apiError;
    }
  }, []);

  const reset = useCallback(() => {
    setState({ data: null, isLoading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

/**
 * Hook for handling errors from queries/mutations
 * Automatically manages error toast/alert visibility
 */
export function useErrorHandler() {
  const [error, setError] = useState<Error | null>(null);

  const handleError = useCallback((err: unknown) => {
    if (err instanceof Error) {
      setError(err);
    } else {
      setError(new Error(String(err)));
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    error,
    handleError,
    clearError,
    hasError: !!error,
  };
}

/**
 * Hook for debounced async operations (e.g., search, filter)
 */
export function useDebouncedAsyncOperation<T>(delay: number = 500) {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const timeoutRef = useRef<NodeJS.Timeout>();

  const execute = useCallback(
    async (asyncFn: () => Promise<T>) => {
      setState({ data: null, isLoading: true, error: null });

      // Clear previous timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      return new Promise<T>((resolve, reject) => {
        timeoutRef.current = setTimeout(async () => {
          try {
            const result = await asyncFn();
            setState({ data: result, isLoading: false, error: null });
            resolve(result);
          } catch (error) {
            const apiError =
              error instanceof ApiErrorWithContext
                ? error
                : new ApiErrorWithContext(
                    error instanceof Error ? error.message : 'Unknown error'
                  );

            setState({ data: null, isLoading: false, error: apiError });
            reject(apiError);
          }
        }, delay);
      });
    },
    [delay]
  );

  const reset = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setState({ data: null, isLoading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

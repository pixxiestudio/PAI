'use client';

import { RetryButton } from './LoadingStates';

/**
 * Error display components for showing errors to users
 */

interface ErrorDisplayProps {
  error: Error | string | null;
  onRetry?: () => void;
  isRetrying?: boolean;
  title?: string;
}

/**
 * Inline error alert component
 */
export function ErrorAlert({
  error,
  onRetry,
  isRetrying = false,
  title = 'Error',
}: ErrorDisplayProps) {
  if (!error) return null;

  const message = typeof error === 'string' ? error : error.message;

  return (
    <div className="border border-red-200 bg-red-50 rounded-lg p-4 mb-4">
      <div className="flex gap-3">
        <div className="flex-shrink-0">
          <svg
            className="w-5 h-5 text-red-600"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-red-900">{title}</h3>
          <p className="text-red-700 text-sm mt-1">{message}</p>
          {onRetry && (
            <div className="mt-3">
              <RetryButton
                onClick={onRetry}
                isLoading={isRetrying}
                message="Try again"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Error toast notification
 */
export function ErrorToast({
  error,
  onDismiss,
}: {
  error: string;
  onDismiss: () => void;
}) {
  return (
    <div className="fixed bottom-4 right-4 max-w-md bg-red-600 text-white rounded-lg shadow-lg p-4 animate-slide-in z-40">
      <div className="flex items-start justify-between gap-3">
        <p className="flex-1">{error}</p>
        <button
          onClick={onDismiss}
          className="text-red-200 hover:text-white flex-shrink-0"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}

/**
 * Error state display for entire sections
 */
export function ErrorState({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  onRetry,
  isRetrying = false,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
  isRetrying?: boolean;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <svg
        className="w-16 h-16 text-red-400 mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-center mb-6 max-w-sm">{message}</p>
      {onRetry && (
        <RetryButton
          onClick={onRetry}
          isLoading={isRetrying}
          message="Try again"
        />
      )}
    </div>
  );
}

/**
 * 404 Not Found error
 */
export function NotFoundError({
  title = 'Page not found',
  message = 'The page you are looking for does not exist.',
  action,
}: {
  title?: string;
  message?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <h1 className="text-6xl font-bold text-gray-900 mb-2">404</h1>
      <h2 className="text-2xl font-semibold text-gray-800 mb-2">{title}</h2>
      <p className="text-gray-600 mb-8 text-center max-w-sm">{message}</p>
      {action && <div>{action}</div>}
    </div>
  );
}

/**
 * Unauthorized error (401)
 */
export function UnauthorizedError({
  title = 'Session expired',
  message = 'Your session has expired. Please log in again.',
  onLogin,
}: {
  title?: string;
  message?: string;
  onLogin?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <svg
        className="w-16 h-16 text-yellow-600 mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
        />
      </svg>
      <h2 className="text-2xl font-semibold text-gray-800 mb-2">{title}</h2>
      <p className="text-gray-600 mb-8 text-center max-w-sm">{message}</p>
      {onLogin && (
        <button
          onClick={onLogin}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition-colors"
        >
          Go to Login
        </button>
      )}
    </div>
  );
}

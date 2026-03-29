/**
 * Error Handler Utilities
 * Centralized error handling and user-friendly messages
 */

export class ApiErrorWithContext extends Error {
  constructor(
    public message: string,
    public status?: number,
    public data?: Record<string, any>,
    public originalError?: Error
  ) {
    super(message);
    this.name = 'ApiErrorWithContext';
  }
}

/**
 * Get user-friendly error message based on status code and error data
 */
export function getErrorMessage(
  error: unknown,
  defaultMessage: string = 'An unexpected error occurred'
): string {
  if (error instanceof ApiErrorWithContext) {
    return error.message;
  }

  if (error instanceof Error) {
    // Handle specific error types
    if (error.message.includes('401') || error.message.includes('Unauthorized')) {
      return 'Your session has expired. Please log in again.';
    }
    if (error.message.includes('429') || error.message.includes('Too Many Requests')) {
      return 'Too many requests. Please try again in a moment.';
    }
    if (error.message.includes('503') || error.message.includes('Service Unavailable')) {
      return 'Service temporarily unavailable. Please try again later.';
    }
    if (error.message.includes('Network') || error.message.includes('fetch')) {
      return 'Network error. Please check your connection and try again.';
    }
    if (error.message.includes('timeout') || error.message.includes('Timeout')) {
      return 'Request timed out. Please try again.';
    }

    return error.message || defaultMessage;
  }

  return defaultMessage;
}

/**
 * Determine if error is retryable
 */
export function isRetryableError(error: unknown): boolean {
  if (error instanceof ApiErrorWithContext) {
    // Don't retry 401 (auth), 403 (forbidden), 404 (not found)
    if (error.status === 401 || error.status === 403 || error.status === 404) {
      return false;
    }
    // Retry 429 (rate limit), 500+, and network errors
    if (error.status === 429 || (error.status && error.status >= 500)) {
      return true;
    }
  }

  if (error instanceof Error) {
    // Retry on network errors
    if (
      error.message.includes('Network') ||
      error.message.includes('fetch') ||
      error.message.includes('timeout')
    ) {
      return true;
    }
  }

  return false;
}

/**
 * Calculate exponential backoff delay
 */
export function exponentialBackoffDelay(attemptNumber: number): number {
  // 1st retry: 1s, 2nd retry: 2s, 3rd retry: 4s
  return Math.pow(2, attemptNumber - 1) * 1000;
}

/**
 * Log error to console with context
 */
export function logError(
  error: unknown,
  context: string = 'Unknown'
): void {
  const timestamp = new Date().toISOString();

  if (error instanceof ApiErrorWithContext) {
    console.error(`[${timestamp}] API Error in ${context}:`, {
      message: error.message,
      status: error.status,
      data: error.data,
      originalError: error.originalError,
    });
  } else if (error instanceof Error) {
    console.error(`[${timestamp}] Error in ${context}:`, {
      name: error.name,
      message: error.message,
      stack: error.stack,
    });
  } else {
    console.error(`[${timestamp}] Unknown error in ${context}:`, error);
  }
}

/**
 * Handle 401 Unauthorized errors
 */
export function handle401Error(): void {
  // Clear auth tokens
  if (typeof window !== 'undefined') {
    localStorage.removeItem('pai_token');
    localStorage.removeItem('pai_token_expires_at');
    localStorage.removeItem('pai_user');
  }

  // Optionally redirect to login
  if (typeof window !== 'undefined') {
    // Could emit event or trigger redirect here
    window.location.href = '/login';
  }
}

/**
 * Handle 429 Rate Limit errors
 */
export function handle429Error(
  retryAfterHeader?: string
): { retryAfter: number; message: string } {
  const retryAfter = retryAfterHeader ? parseInt(retryAfterHeader, 10) : 60;

  return {
    retryAfter,
    message: `Rate limited. Please try again in ${retryAfter} seconds.`,
  };
}

/**
 * Handle different HTTP status codes
 */
export function handleHttpError(
  status: number,
  data?: Record<string, any>
): ApiErrorWithContext {
  switch (status) {
    case 400:
      return new ApiErrorWithContext(
        data?.detail || 'Invalid request. Please check your input.',
        status,
        data
      );
    case 401:
      return new ApiErrorWithContext(
        'Unauthorized. Please log in again.',
        status,
        data
      );
    case 403:
      return new ApiErrorWithContext(
        'Access denied. You do not have permission for this action.',
        status,
        data
      );
    case 404:
      return new ApiErrorWithContext(
        'Resource not found.',
        status,
        data
      );
    case 409:
      return new ApiErrorWithContext(
        'Conflict. The resource has been modified. Please refresh and try again.',
        status,
        data
      );
    case 429:
      return new ApiErrorWithContext(
        'Too many requests. Please wait a moment and try again.',
        status,
        data
      );
    case 500:
      return new ApiErrorWithContext(
        'Server error. Please try again later.',
        status,
        data
      );
    case 502:
    case 503:
    case 504:
      return new ApiErrorWithContext(
        'Service temporarily unavailable. Please try again in a few moments.',
        status,
        data
      );
    default:
      return new ApiErrorWithContext(
        `An error occurred (${status}). Please try again.`,
        status,
        data
      );
  }
}

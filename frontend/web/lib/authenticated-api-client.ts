/**
 * Authenticated API Client
 * Automatically injects JWT token from localStorage into all requests
 * Handles token expiration validation before each request
 * Includes retry logic with exponential backoff
 */

import {
  ApiErrorWithContext,
  isRetryableError,
  exponentialBackoffDelay,
  handleHttpError,
} from './error-handler';

interface FetchOptions extends RequestInit {
  timeout?: number;
  maxRetries?: number;
}

const DEFAULT_TIMEOUT = 30000; // 30 seconds
const DEFAULT_MAX_RETRIES = 3;

/**
 * Get auth header from localStorage if token is valid
 */
function getAuthHeader(): { Authorization: string } | null {
  if (typeof window === 'undefined') {
    return null; // Server-side, no localStorage
  }

  try {
    const token = localStorage.getItem('pai_token');
    if (!token) {
      return null;
    }

    // Check if token is expired
    const expiresAt = localStorage.getItem('pai_token_expires_at');
    if (expiresAt && new Date().getTime() > parseInt(expiresAt, 10)) {
      // Token expired, clear it
      localStorage.removeItem('pai_token');
      localStorage.removeItem('pai_token_expires_at');
      return null;
    }

    return {
      Authorization: `Bearer ${token}`,
    };
  } catch (error) {
    console.error('Error getting auth header:', error);
    return null;
  }
}

/**
 * Sleep helper for retry delays
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Fetch wrapper with timeout, automatic auth header injection, retry logic, and error handling
 */
async function fetchWithAuth(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const {
    timeout = DEFAULT_TIMEOUT,
    maxRetries = DEFAULT_MAX_RETRIES,
    ...fetchOptions
  } = options;

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      // Merge auth header if available
      const headers = new Headers(fetchOptions.headers || {});
      const authHeader = getAuthHeader();
      if (authHeader) {
        headers.set('Authorization', authHeader.Authorization);
      }

      const response = await fetch(url, {
        ...fetchOptions,
        headers,
        signal: controller.signal,
      });

      if (!response.ok) {
        // Handle 401 - clear auth and don't retry
        if (response.status === 401) {
          localStorage.removeItem('pai_token');
          localStorage.removeItem('pai_token_expires_at');
          localStorage.removeItem('pai_user');
          const errorData = await response.json().catch(() => ({}));
          throw handleHttpError(401, errorData);
        }

        const errorData = await response.json().catch(() => ({}));
        const apiError = handleHttpError(response.status, errorData);

        // Check if error is retryable
        if (!isRetryableError(apiError) || attempt === maxRetries) {
          throw apiError;
        }

        // Retryable error - wait and retry
        lastError = apiError;
        const delayMs = exponentialBackoffDelay(attempt + 1);
        await sleep(delayMs);
        continue;
      }

      return response;
    } catch (error) {
      // Handle network/timeout errors
      if (error instanceof ApiErrorWithContext) {
        // API error already formatted
        if (!isRetryableError(error) || attempt === maxRetries) {
          throw error;
        }
        lastError = error;
        const delayMs = exponentialBackoffDelay(attempt + 1);
        await sleep(delayMs);
        continue;
      }

      // Network/timeout error
      if (error instanceof Error) {
        lastError = new ApiErrorWithContext(
          error.message,
          undefined,
          undefined,
          error
        );

        if (attempt === maxRetries) {
          throw lastError;
        }

        const delayMs = exponentialBackoffDelay(attempt + 1);
        await sleep(delayMs);
        continue;
      }

      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // Should never reach here, but just in case
  throw lastError || new Error('Unknown error during fetch');
}

// Re-export for backward compatibility
export { ApiErrorWithContext as AuthenticatedApiError } from './error-handler';

/**
 * Authenticated API client
 * Automatically injects JWT token into all requests
 */
export const authenticatedApiClient = {
  /**
   * GET request with automatic auth
   */
  async get<T>(path: string): Promise<T> {
    const url = `/api/proxy${path}`;
    const response = await fetchWithAuth(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.json() as Promise<T>;
  },

  /**
   * POST request with automatic auth
   */
  async post<T>(path: string, data?: Record<string, any>): Promise<T> {
    const url = `/api/proxy${path}`;
    const response = await fetchWithAuth(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    return response.json() as Promise<T>;
  },

  /**
   * PUT request with automatic auth
   */
  async put<T>(path: string, data?: Record<string, any>): Promise<T> {
    const url = `/api/proxy${path}`;
    const response = await fetchWithAuth(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    return response.json() as Promise<T>;
  },

  /**
   * DELETE request with automatic auth
   */
  async delete<T>(path: string): Promise<T> {
    const url = `/api/proxy${path}`;
    const response = await fetchWithAuth(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.json() as Promise<T>;
  },
};

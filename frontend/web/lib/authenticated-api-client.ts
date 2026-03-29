/**
 * Authenticated API Client
 * Automatically injects JWT token from localStorage into all requests
 * Handles token expiration validation before each request
 */

interface FetchOptions extends RequestInit {
  timeout?: number;
}

const DEFAULT_TIMEOUT = 30000; // 30 seconds

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
 * Fetch wrapper with timeout, automatic auth header injection, and error handling
 */
async function fetchWithAuth(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout = DEFAULT_TIMEOUT, ...fetchOptions } = options;

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
      // Handle 401 - token may have been invalidated
      if (response.status === 401) {
        localStorage.removeItem('pai_token');
        localStorage.removeItem('pai_token_expires_at');
        localStorage.removeItem('pai_user');
        throw new Error('Unauthorized - please log in again');
      }

      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail ||
          errorData.error ||
          `API error: ${response.status}`
      );
    }

    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

export class AuthenticatedApiError extends Error {
  constructor(
    public message: string,
    public status?: number,
    public data: Record<string, any> = {}
  ) {
    super(message);
    this.name = 'AuthenticatedApiError';
  }
}

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

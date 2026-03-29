/**
 * API Client for PAI Dashboard
 * All requests go through Next.js API routes for secure authentication
 */

interface FetchOptions extends RequestInit {
  timeout?: number;
  authHeader?: { Authorization: string } | null;
}

const DEFAULT_TIMEOUT = 30000; // 30 seconds

/**
 * Fetch wrapper with timeout and error handling
 */
async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout = DEFAULT_TIMEOUT, authHeader, ...fetchOptions } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    // Merge auth header if provided
    const headers = new Headers(fetchOptions.headers || {});
    if (authHeader) {
      headers.set('Authorization', authHeader.Authorization);
    }

    const response = await fetch(url, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new ApiError(
        `API error: ${response.status}`,
        response.status,
        await response.json().catch(() => ({}))
      );
    }

    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

export class ApiError extends Error {
  constructor(
    public message: string,
    public status: number,
    public data: Record<string, any> = {}
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export const apiClient = {
  /**
   * GET request
   */
  async get<T>(path: string): Promise<T> {
    const url = `/api/proxy${path}`;
    const response = await fetchWithTimeout(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.json() as Promise<T>;
  },

  /**
   * POST request
   */
  async post<T>(path: string, data?: Record<string, any>): Promise<T> {
    const url = `/api/proxy${path}`;
    const response = await fetchWithTimeout(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    return response.json() as Promise<T>;
  },

  /**
   * PUT request
   */
  async put<T>(path: string, data?: Record<string, any>): Promise<T> {
    const url = `/api/proxy${path}`;
    const response = await fetchWithTimeout(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    return response.json() as Promise<T>;
  },

  /**
   * DELETE request
   */
  async delete<T>(path: string): Promise<T> {
    const url = `/api/proxy${path}`;
    const response = await fetchWithTimeout(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.json() as Promise<T>;
  },
};

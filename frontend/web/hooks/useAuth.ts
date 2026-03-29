'use client';

import { useState, useCallback } from 'react';
import { User, useUser } from '@/contexts/UserContext';

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
}

interface UseAuthReturn {
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (userId: string) => Promise<boolean>;
  logout: () => void;
  getAuthHeader: () => { Authorization: string } | null;
}

/**
 * Hook for authentication with Phase 2 backend
 * Manages JWT token lifecycle
 */
export function useAuth(): UseAuthReturn {
  const { user, setUser } = useUser();
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('pai_token')
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Login by requesting JWT token from backend
   */
  const login = useCallback(async (userId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      // Call backend auth endpoint via proxy
      const response = await fetch('/api/proxy/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userId }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Authentication failed');
      }

      const data: AuthToken = await response.json();

      // Store token
      localStorage.setItem('pai_token', data.access_token);
      setToken(data.access_token);

      // Store token expiration time
      const expiresAt = new Date().getTime() + data.expires_in * 1000;
      localStorage.setItem('pai_token_expires_at', expiresAt.toString());

      // Update user with full data
      if (user) {
        const updatedUser: User = {
          ...user,
          id: userId
        };
        setUser(updatedUser);
        localStorage.setItem('pai_user', JSON.stringify(updatedUser));
      }

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      console.error('Login failed:', errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [user, setUser]);

  /**
   * Logout by clearing token and user data
   */
  const logout = useCallback(() => {
    localStorage.removeItem('pai_token');
    localStorage.removeItem('pai_token_expires_at');
    localStorage.removeItem('pai_user');
    setToken(null);
    setUser(null);
  }, [setUser]);

  /**
   * Get Authorization header for API requests
   */
  const getAuthHeader = useCallback((): { Authorization: string } | null => {
    if (!token) {
      return null;
    }

    // Check if token is expired
    const expiresAt = localStorage.getItem('pai_token_expires_at');
    if (expiresAt && new Date().getTime() > parseInt(expiresAt, 10)) {
      logout();
      return null;
    }

    return {
      Authorization: `Bearer ${token}`
    };
  }, [token, logout]);

  return {
    token,
    isLoading,
    error,
    login,
    logout,
    getAuthHeader
  };
}

'use client';

import React, { createContext, useContext, ReactNode, useState, useEffect } from 'react';

export interface User {
  id: string;
  email?: string;
  name?: string;
  paiInstanceId: string;
}

interface UserContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize user from localStorage or session
  useEffect(() => {
    const initializeUser = async () => {
      try {
        // Check if user exists in localStorage
        const storedUser = localStorage.getItem('pai_user');
        if (storedUser) {
          setUser(JSON.parse(storedUser));
        }

        // For now, if no user, create a default one for development
        // In production, this would verify authentication
        if (!storedUser) {
          const defaultUser: User = {
            id: `user-${Date.now()}`,
            name: 'Developer',
            email: 'dev@example.com',
            paiInstanceId: 'default'
          };
          setUser(defaultUser);
          localStorage.setItem('pai_user', JSON.stringify(defaultUser));
        }
      } catch (error) {
        console.error('Failed to initialize user:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeUser();
  }, []);

  const value: UserContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    setUser
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}

'use client';

import React from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { createQueryClient } from '@/lib/react-query-config';

// Create a client with optimized settings
const queryClient = createQueryClient();

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

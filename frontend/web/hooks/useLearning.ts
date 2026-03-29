'use client';

import { useQuery } from '@tanstack/react-query';
import { authenticatedApiClient } from '@/lib/authenticated-api-client';

export interface LearningPattern {
  id: string;
  pattern: string;
  frequency: number;
  effectiveness: number; // 0-1
  lastOccurrence: string;
}

export interface Preference {
  id: string;
  preference: string;
  weight: number; // 0-1
  source: string;
}

export interface LearningReport {
  paiInstanceId: string;
  patterns: LearningPattern[];
  preferences: Preference[];
  totalInteractions: number;
  successRate: number; // 0-1
  lastUpdated: string;
}

/**
 * Hook to fetch and display learning patterns and metrics
 */
export function useLearning(paiInstanceId: string) {
  const learningQuery = useQuery({
    queryKey: ['learning', paiInstanceId],
    queryFn: async () => {
      const data = await authenticatedApiClient.get<LearningReport>(
        `/pai/${paiInstanceId}/learning`
      );
      return data;
    },
    enabled: !!paiInstanceId,
    staleTime: 60000, // 1 minute
  });

  return {
    learning: learningQuery.data,
    isLoading: learningQuery.isLoading,
    error: learningQuery.error,
    patterns: learningQuery.data?.patterns || [],
    preferences: learningQuery.data?.preferences || [],
    successRate: learningQuery.data?.successRate || 0,
    totalInteractions: learningQuery.data?.totalInteractions || 0,
  };
}

/**
 * Hook to fetch available skills
 */
export interface Skill {
  id: string;
  name: string;
  description: string;
  category: string;
  isEnabled: boolean;
  parameters: Record<string, any>;
}

export function useSkills(paiInstanceId: string) {
  const skillsQuery = useQuery({
    queryKey: ['skills', paiInstanceId],
    queryFn: async () => {
      const data = await authenticatedApiClient.get<Skill[]>(
        `/pai/${paiInstanceId}/skills`
      );
      return data;
    },
    enabled: !!paiInstanceId,
  });

  return {
    skills: skillsQuery.data || [],
    isLoading: skillsQuery.isLoading,
    error: skillsQuery.error,
  };
}

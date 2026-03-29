'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authenticatedApiClient } from '@/lib/authenticated-api-client';

export interface Memory {
  id: string;
  userId: string;
  content: string;
  importance: number; // 0-1
  category: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Hook to manage user memories
 */
export function useMemory(userId: string) {
  const queryClient = useQueryClient();

  // Fetch all memories
  const memoriesQuery = useQuery({
    queryKey: ['memory', userId],
    queryFn: async () => {
      const data = await authenticatedApiClient.get<Memory[]>(
        `/users/${userId}/memories`
      );
      return data;
    },
    enabled: !!userId,
  });

  // Save a memory
  const saveMemoryMutation = useMutation({
    mutationFn: async (memory: Omit<Memory, 'id' | 'userId' | 'createdAt' | 'updatedAt'>) => {
      return authenticatedApiClient.post<Memory>(
        `/users/${userId}/memories`,
        memory
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['memory', userId],
      });
    },
  });

  // Update memory importance
  const updateImportanceMutation = useMutation({
    mutationFn: async (data: { memoryId: string; importance: number }) => {
      return authenticatedApiClient.put<Memory>(
        `/users/${userId}/memories/${data.memoryId}`,
        { importance: data.importance }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['memory', userId],
      });
    },
  });

  // Delete memory
  const deleteMemoryMutation = useMutation({
    mutationFn: async (memoryId: string) => {
      return authenticatedApiClient.delete(`/users/${userId}/memories/${memoryId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['memory', userId],
      });
    },
  });

  return {
    memories: memoriesQuery.data || [],
    isLoading: memoriesQuery.isLoading,
    error: memoriesQuery.error,
    saveMemory: (memory: Omit<Memory, 'id' | 'userId' | 'createdAt' | 'updatedAt'>) =>
      saveMemoryMutation.mutate(memory),
    isSaving: saveMemoryMutation.isPending,
    updateImportance: (memoryId: string, importance: number) =>
      updateImportanceMutation.mutate({ memoryId, importance }),
    isUpdating: updateImportanceMutation.isPending,
    deleteMemory: (memoryId: string) =>
      deleteMemoryMutation.mutate(memoryId),
    isDeleting: deleteMemoryMutation.isPending,
  };
}

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

export interface Message {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatSession {
  id: string;
  userId: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Hook to manage chat session messages
 */
export function useChat(sessionId: string) {
  const queryClient = useQueryClient();

  // Fetch messages for the session
  const messagesQuery = useQuery({
    queryKey: ['chat', sessionId, 'messages'],
    queryFn: async () => {
      const data = await apiClient.get<Message[]>(
        `/sessions/${sessionId}/messages`
      );
      return data;
    },
    enabled: !!sessionId,
    staleTime: 10000, // 10 seconds
  });

  // Send a message
  const sendMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      return apiClient.post<Message>(
        `/sessions/${sessionId}/messages`,
        { content: message }
      );
    },
    onSuccess: (newMessage) => {
      // Update the messages list optimistically
      queryClient.setQueryData(
        ['chat', sessionId, 'messages'],
        (oldMessages: Message[] | undefined) => {
          return oldMessages ? [...oldMessages, newMessage] : [newMessage];
        }
      );
    },
  });

  return {
    messages: messagesQuery.data || [],
    isLoading: messagesQuery.isLoading,
    error: messagesQuery.error,
    sendMessage: (message: string) =>
      sendMessageMutation.mutate(message),
    isSending: sendMessageMutation.isPending,
  };
}

/**
 * Hook to manage chat sessions
 */
export function useSessions(userId: string) {
  const queryClient = useQueryClient();

  // Fetch all sessions
  const sessionsQuery = useQuery({
    queryKey: ['chat', userId, 'sessions'],
    queryFn: async () => {
      const data = await apiClient.get<ChatSession[]>(
        `/users/${userId}/sessions`
      );
      return data;
    },
    enabled: !!userId,
  });

  // Create a new session
  const createSessionMutation = useMutation({
    mutationFn: async (title: string) => {
      return apiClient.post<ChatSession>('/sessions', { title });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['chat', userId, 'sessions'],
      });
    },
  });

  return {
    sessions: sessionsQuery.data || [],
    isLoading: sessionsQuery.isLoading,
    error: sessionsQuery.error,
    createSession: (title: string) =>
      createSessionMutation.mutate(title),
    isCreating: createSessionMutation.isPending,
  };
}

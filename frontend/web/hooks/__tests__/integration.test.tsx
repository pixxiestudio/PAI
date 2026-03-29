/**
 * Integration Tests for Hooks
 * Tests for useChat, useMemory, useLearning with API calls
 */

import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import { useChat, useSessions } from '../useChat'
import { useMemory } from '../useMemory'
import { useLearning } from '../useLearning'

// Mock the authenticated API client
jest.mock('@/lib/authenticated-api-client', () => ({
  authenticatedApiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}))

import { authenticatedApiClient } from '@/lib/authenticated-api-client'

// Create a test wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('Integration Tests: useChat Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch messages successfully', async () => {
    const mockMessages = [
      {
        id: '1',
        sessionId: 'session-1',
        role: 'user' as const,
        content: 'Hello',
        timestamp: '2026-03-29T00:00:00Z',
      },
    ]

    ;(authenticatedApiClient.get as jest.Mock).mockResolvedValue(mockMessages)

    const { result } = renderHook(
      () => useChat('session-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.messages).toEqual(mockMessages)
    })
  })

  it('should handle API error when fetching messages', async () => {
    const error = new Error('API error')
    ;(authenticatedApiClient.get as jest.Mock).mockRejectedValue(error)

    const { result } = renderHook(
      () => useChat('session-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.error).toBeDefined()
    })
  })

  it('should send message successfully', async () => {
    const mockResponse = {
      id: '2',
      sessionId: 'session-1',
      role: 'assistant' as const,
      content: 'Response',
      timestamp: '2026-03-29T00:00:01Z',
    }

    ;(authenticatedApiClient.post as jest.Mock).mockResolvedValue(mockResponse)

    const { result } = renderHook(
      () => useChat('session-1'),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.sendMessage('Hello')
    })

    expect(authenticatedApiClient.post).toHaveBeenCalledWith(
      '/sessions/session-1/messages',
      { content: 'Hello' }
    )
  })
})

describe('Integration Tests: useSessions Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch sessions successfully', async () => {
    const mockSessions = [
      {
        id: 'session-1',
        userId: 'user-1',
        title: 'Chat 1',
        createdAt: '2026-03-29T00:00:00Z',
        updatedAt: '2026-03-29T00:00:00Z',
      },
    ]

    ;(authenticatedApiClient.get as jest.Mock).mockResolvedValue(mockSessions)

    const { result } = renderHook(
      () => useSessions('user-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.sessions).toEqual(mockSessions)
    })
  })

  it('should create session successfully', async () => {
    const mockSession = {
      id: 'session-new',
      userId: 'user-1',
      title: 'New Chat',
      createdAt: '2026-03-29T00:00:00Z',
      updatedAt: '2026-03-29T00:00:00Z',
    }

    ;(authenticatedApiClient.post as jest.Mock).mockResolvedValue(mockSession)

    const { result } = renderHook(
      () => useSessions('user-1'),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.createSession('New Chat')
    })

    expect(authenticatedApiClient.post).toHaveBeenCalledWith(
      '/sessions',
      { title: 'New Chat' }
    )
  })
})

describe('Integration Tests: useMemory Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch memories successfully', async () => {
    const mockMemories = [
      {
        id: '1',
        userId: 'user-1',
        content: 'Memory 1',
        importance: 0.8,
        category: 'preferences',
        createdAt: '2026-03-29T00:00:00Z',
        updatedAt: '2026-03-29T00:00:00Z',
      },
    ]

    ;(authenticatedApiClient.get as jest.Mock).mockResolvedValue(mockMemories)

    const { result } = renderHook(
      () => useMemory('user-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.memories).toEqual(mockMemories)
    })
  })

  it('should save memory successfully', async () => {
    const mockMemory = {
      id: 'new-memory',
      userId: 'user-1',
      content: 'New memory',
      importance: 0.5,
      category: 'knowledge',
      createdAt: '2026-03-29T00:00:00Z',
      updatedAt: '2026-03-29T00:00:00Z',
    }

    ;(authenticatedApiClient.post as jest.Mock).mockResolvedValue(mockMemory)

    const { result } = renderHook(
      () => useMemory('user-1'),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.saveMemory({
        content: 'New memory',
        category: 'knowledge',
        importance: 0.5,
      })
    })

    expect(authenticatedApiClient.post).toHaveBeenCalledWith(
      '/users/user-1/memories',
      expect.objectContaining({ content: 'New memory' })
    )
  })

  it('should delete memory successfully', async () => {
    ;(authenticatedApiClient.delete as jest.Mock).mockResolvedValue({})

    const { result } = renderHook(
      () => useMemory('user-1'),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.deleteMemory('memory-1')
    })

    expect(authenticatedApiClient.delete).toHaveBeenCalledWith(
      '/users/user-1/memories/memory-1'
    )
  })
})

describe('Integration Tests: useLearning Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch learning data successfully', async () => {
    const mockLearning = {
      paiInstanceId: 'pai-1',
      patterns: [
        {
          id: '1',
          pattern: 'Pattern 1',
          frequency: 10,
          effectiveness: 0.9,
          lastOccurrence: '2026-03-29T00:00:00Z',
        },
      ],
      preferences: [
        {
          id: '1',
          preference: 'Preference 1',
          weight: 0.8,
          source: 'interaction_history',
        },
      ],
      totalInteractions: 100,
      successRate: 0.85,
      lastUpdated: '2026-03-29T00:00:00Z',
    }

    ;(authenticatedApiClient.get as jest.Mock).mockResolvedValue(mockLearning)

    const { result } = renderHook(
      () => useLearning('pai-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.patterns).toEqual(mockLearning.patterns)
      expect(result.current.successRate).toBe(0.85)
    })
  })

  it('should handle loading state during fetch', async () => {
    ;(authenticatedApiClient.get as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({}), 100))
    )

    const { result } = renderHook(
      () => useLearning('pai-1'),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
  })
})

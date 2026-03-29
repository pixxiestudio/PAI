/**
 * Async Operation Hooks Tests
 * Tests for useAsyncOperation and useErrorHandler hooks
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { useAsyncOperation, useErrorHandler } from '../useAsyncOperation'

describe('useAsyncOperation', () => {
  it('should initialize with default state', () => {
    const { result } = renderHook(() => useAsyncOperation<string>())

    expect(result.current.data).toBeNull()
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('should handle successful async operation', async () => {
    const { result } = renderHook(() => useAsyncOperation<string>())

    const mockData = 'test data'
    const asyncFn = jest.fn().mockResolvedValue(mockData)

    await act(async () => {
      const data = await result.current.execute(asyncFn)
      expect(data).toBe(mockData)
    })

    expect(result.current.data).toBe(mockData)
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('should handle async operation failure', async () => {
    const { result } = renderHook(() => useAsyncOperation<string>())

    const error = new Error('Test error')
    const asyncFn = jest.fn().mockRejectedValue(error)

    await act(async () => {
      try {
        await result.current.execute(asyncFn)
      } catch (e) {
        // Expected to throw
      }
    })

    expect(result.current.data).toBeNull()
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeDefined()
  })

  it('should set isLoading to true during execution', async () => {
    const { result } = renderHook(() => useAsyncOperation<string>())

    const asyncFn = jest.fn(
      () => new Promise((resolve) => setTimeout(() => resolve('data'), 10))
    )

    act(() => {
      result.current.execute(asyncFn)
    })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
  })

  it('should reset state', async () => {
    const { result } = renderHook(() => useAsyncOperation<string>())

    const asyncFn = jest.fn().mockResolvedValue('data')

    await act(async () => {
      await result.current.execute(asyncFn)
    })

    expect(result.current.data).toBe('data')

    act(() => {
      result.current.reset()
    })

    expect(result.current.data).toBeNull()
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('should handle multiple executions', async () => {
    const { result } = renderHook(() => useAsyncOperation<number>())

    const asyncFn1 = jest.fn().mockResolvedValue(1)
    const asyncFn2 = jest.fn().mockResolvedValue(2)

    await act(async () => {
      await result.current.execute(asyncFn1)
    })
    expect(result.current.data).toBe(1)

    await act(async () => {
      await result.current.execute(asyncFn2)
    })
    expect(result.current.data).toBe(2)
  })
})

describe('useErrorHandler', () => {
  it('should initialize with no error', () => {
    const { result } = renderHook(() => useErrorHandler())

    expect(result.current.error).toBeNull()
    expect(result.current.hasError).toBe(false)
  })

  it('should handle Error instances', () => {
    const { result } = renderHook(() => useErrorHandler())

    const error = new Error('Test error')

    act(() => {
      result.current.handleError(error)
    })

    expect(result.current.error).toBeDefined()
    expect(result.current.hasError).toBe(true)
  })

  it('should handle non-Error values', () => {
    const { result } = renderHook(() => useErrorHandler())

    act(() => {
      result.current.handleError('String error')
    })

    expect(result.current.error).toBeDefined()
    expect(result.current.hasError).toBe(true)
  })

  it('should clear error', () => {
    const { result } = renderHook(() => useErrorHandler())

    const error = new Error('Test error')

    act(() => {
      result.current.handleError(error)
    })

    expect(result.current.hasError).toBe(true)

    act(() => {
      result.current.clearError()
    })

    expect(result.current.error).toBeNull()
    expect(result.current.hasError).toBe(false)
  })

  it('should replace previous error with new error', () => {
    const { result } = renderHook(() => useErrorHandler())

    const error1 = new Error('First error')
    const error2 = new Error('Second error')

    act(() => {
      result.current.handleError(error1)
    })
    expect(result.current.error?.message).toBe('First error')

    act(() => {
      result.current.handleError(error2)
    })
    expect(result.current.error?.message).toBe('Second error')
  })
})

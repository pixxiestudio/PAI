/**
 * React Query Configuration Tests
 * Tests for query client setup and default options
 */

import { createQueryClient } from '../react-query-config'
import { isRetryableError } from '../error-handler'

describe('React Query Configuration', () => {
  describe('createQueryClient', () => {
    it('should create a QueryClient instance', () => {
      const client = createQueryClient()
      expect(client).toBeDefined()
      expect(client.getDefaultOptions).toBeDefined()
    })

    it('should set staleTime to 5 minutes', () => {
      const client = createQueryClient()
      const options = client.getDefaultOptions()
      expect(options.queries?.staleTime).toBe(1000 * 60 * 5)
    })

    it('should set gcTime to 10 minutes', () => {
      const client = createQueryClient()
      const options = client.getDefaultOptions()
      expect(options.queries?.gcTime).toBe(1000 * 60 * 10)
    })

    it('should have retry configuration', () => {
      const client = createQueryClient()
      const options = client.getDefaultOptions()
      expect(options.queries?.retry).toBeDefined()
    })

    it('should disable retry for mutations', () => {
      const client = createQueryClient()
      const options = client.getDefaultOptions()
      expect(options.mutations?.retry).toBe(false)
    })
  })

  describe('Retry Configuration', () => {
    it('should only retry retryable errors', () => {
      const client = createQueryClient()
      const options = client.getDefaultOptions()
      const retryFn = options.queries?.retry as Function

      // Should retry network error
      const networkError = new Error('Network error')
      expect(retryFn?.(0, networkError)).toBe(true)

      // Should not retry 404
      const notFoundError = new Error('404')
      expect(retryFn?.(0, notFoundError)).toBe(false)
    })

    it('should max out at 3 retries', () => {
      const client = createQueryClient()
      const options = client.getDefaultOptions()
      const retryFn = options.queries?.retry as Function

      const error = new Error('Network error')

      // Attempt 0, 1, 2 should allow retry
      expect(retryFn?.(0, error)).toBe(true)
      expect(retryFn?.(1, error)).toBe(true)
      expect(retryFn?.(2, error)).toBe(true)

      // Attempt 3 should not retry
      expect(retryFn?.(3, error)).toBe(false)
    })

    it('should use exponential backoff for retries', () => {
      const client = createQueryClient()
      const options = client.getDefaultOptions()
      const retryDelayFn = options.queries?.retryDelay as Function

      expect(retryDelayFn?.(0)).toBe(1000) // 1s
      expect(retryDelayFn?.(1)).toBe(2000) // 2s
      expect(retryDelayFn?.(2)).toBe(4000) // 4s
    })
  })
})

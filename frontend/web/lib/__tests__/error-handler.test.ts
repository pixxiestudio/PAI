/**
 * Error Handler Tests
 * Tests for error utility functions and classification
 */

import {
  ApiErrorWithContext,
  getErrorMessage,
  isRetryableError,
  exponentialBackoffDelay,
  handleHttpError,
  handle401Error,
  handle429Error,
} from '../error-handler'

describe('Error Handler Utilities', () => {
  describe('ApiErrorWithContext', () => {
    it('should create error with message and status', () => {
      const error = new ApiErrorWithContext('Test error', 400, { detail: 'Bad request' })
      expect(error.message).toBe('Test error')
      expect(error.status).toBe(400)
      expect(error.data).toEqual({ detail: 'Bad request' })
      expect(error.name).toBe('ApiErrorWithContext')
    })

    it('should work as Error instance', () => {
      const error = new ApiErrorWithContext('Test')
      expect(error instanceof Error).toBe(true)
    })
  })

  describe('getErrorMessage', () => {
    it('should return ApiErrorWithContext message', () => {
      const error = new ApiErrorWithContext('Custom error message', 500)
      expect(getErrorMessage(error)).toBe('Custom error message')
    })

    it('should handle 401 errors', () => {
      const error = new Error('401 Unauthorized')
      expect(getErrorMessage(error)).toContain('session expired')
    })

    it('should handle 429 rate limit errors', () => {
      const error = new Error('429 Too Many Requests')
      expect(getErrorMessage(error)).toContain('Too many requests')
    })

    it('should handle network errors', () => {
      const error = new Error('Network request failed')
      expect(getErrorMessage(error)).toContain('Network error')
    })

    it('should handle timeout errors', () => {
      const error = new Error('Request timeout')
      expect(getErrorMessage(error)).toContain('timed out')
    })

    it('should return default message for unknown errors', () => {
      expect(getErrorMessage(null)).toBe('An unexpected error occurred')
    })
  })

  describe('isRetryableError', () => {
    it('should not retry 401 errors', () => {
      const error = new ApiErrorWithContext('Unauthorized', 401)
      expect(isRetryableError(error)).toBe(false)
    })

    it('should not retry 403 errors', () => {
      const error = new ApiErrorWithContext('Forbidden', 403)
      expect(isRetryableError(error)).toBe(false)
    })

    it('should not retry 404 errors', () => {
      const error = new ApiErrorWithContext('Not found', 404)
      expect(isRetryableError(error)).toBe(false)
    })

    it('should retry 429 errors', () => {
      const error = new ApiErrorWithContext('Rate limited', 429)
      expect(isRetryableError(error)).toBe(true)
    })

    it('should retry 500+ errors', () => {
      const error500 = new ApiErrorWithContext('Server error', 500)
      const error503 = new ApiErrorWithContext('Service unavailable', 503)
      expect(isRetryableError(error500)).toBe(true)
      expect(isRetryableError(error503)).toBe(true)
    })

    it('should retry network errors', () => {
      const error = new Error('Network request failed')
      expect(isRetryableError(error)).toBe(true)
    })

    it('should retry timeout errors', () => {
      const error = new Error('Request timeout')
      expect(isRetryableError(error)).toBe(true)
    })
  })

  describe('exponentialBackoffDelay', () => {
    it('should return 1000ms for first attempt', () => {
      expect(exponentialBackoffDelay(1)).toBe(1000)
    })

    it('should return 2000ms for second attempt', () => {
      expect(exponentialBackoffDelay(2)).toBe(2000)
    })

    it('should return 4000ms for third attempt', () => {
      expect(exponentialBackoffDelay(3)).toBe(4000)
    })

    it('should exponentially increase', () => {
      const delay1 = exponentialBackoffDelay(1)
      const delay2 = exponentialBackoffDelay(2)
      const delay3 = exponentialBackoffDelay(3)
      expect(delay2).toBe(delay1 * 2)
      expect(delay3).toBe(delay2 * 2)
    })
  })

  describe('handleHttpError', () => {
    it('should handle 400 Bad Request', () => {
      const error = handleHttpError(400, { detail: 'Invalid input' })
      expect(error.status).toBe(400)
      expect(error.message).toContain('Invalid request')
    })

    it('should handle 401 Unauthorized', () => {
      const error = handleHttpError(401)
      expect(error.status).toBe(401)
      expect(error.message).toContain('Unauthorized')
    })

    it('should handle 403 Forbidden', () => {
      const error = handleHttpError(403)
      expect(error.status).toBe(403)
      expect(error.message).toContain('Access denied')
    })

    it('should handle 404 Not Found', () => {
      const error = handleHttpError(404)
      expect(error.status).toBe(404)
      expect(error.message).toContain('not found')
    })

    it('should handle 429 Rate Limit', () => {
      const error = handleHttpError(429)
      expect(error.status).toBe(429)
      expect(error.message).toContain('Too many requests')
    })

    it('should handle 500 Server Error', () => {
      const error = handleHttpError(500)
      expect(error.status).toBe(500)
      expect(error.message).toContain('Server error')
    })

    it('should handle 503 Service Unavailable', () => {
      const error = handleHttpError(503)
      expect(error.status).toBe(503)
      expect(error.message).toContain('temporarily unavailable')
    })

    it('should include error data', () => {
      const data = { detail: 'Custom error' }
      const error = handleHttpError(400, data)
      expect(error.data).toEqual(data)
    })
  })

  describe('handle401Error', () => {
    it('should clear auth tokens from localStorage', () => {
      ;(localStorage.removeItem as jest.Mock).mockClear()
      handle401Error()
      expect(localStorage.removeItem).toHaveBeenCalledWith('pai_token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('pai_token_expires_at')
      expect(localStorage.removeItem).toHaveBeenCalledWith('pai_user')
    })
  })

  describe('handle429Error', () => {
    it('should parse retry-after header', () => {
      const result = handle429Error('30')
      expect(result.retryAfter).toBe(30)
      expect(result.message).toContain('30')
    })

    it('should default to 60 seconds if no header', () => {
      const result = handle429Error()
      expect(result.retryAfter).toBe(60)
    })

    it('should return appropriate message', () => {
      const result = handle429Error('45')
      expect(result.message).toContain('Rate limited')
    })
  })
})

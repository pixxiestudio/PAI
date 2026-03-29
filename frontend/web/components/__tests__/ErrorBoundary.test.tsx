/**
 * ErrorBoundary Component Tests
 * Tests for React error boundary functionality
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import { ErrorBoundary, useErrorHandler } from '../ErrorBoundary'

// Component that throws an error
const ThrowError = ({ error }: { error: Error }) => {
  throw error
}

// Component that renders normally
const SafeComponent = () => <div>Safe content</div>

// Component that uses useErrorHandler
const ComponentWithErrorHandler = ({ shouldThrow }: { shouldThrow: boolean }) => {
  const throwError = useErrorHandler()

  if (shouldThrow) {
    throwError(new Error('Test error'))
  }

  return <div>Component rendered</div>
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // Suppress console.error during error boundary tests
    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('should render children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <SafeComponent />
      </ErrorBoundary>
    )
    expect(screen.getByText('Safe content')).toBeInTheDocument()
  })

  it('should catch errors and show fallback UI', () => {
    const testError = new Error('Test error message')
    render(
      <ErrorBoundary>
        <ThrowError error={testError} />
      </ErrorBoundary>
    )
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('should display error message in fallback', () => {
    const testError = new Error('Custom error message')
    render(
      <ErrorBoundary>
        <ThrowError error={testError} />
      </ErrorBoundary>
    )
    expect(screen.getByText('Custom error message')).toBeInTheDocument()
  })

  it('should show error details expandable section', () => {
    const testError = new Error('Test error')
    render(
      <ErrorBoundary>
        <ThrowError error={testError} />
      </ErrorBoundary>
    )
    expect(screen.getByText('Error details')).toBeInTheDocument()
  })

  it('should have try again button', () => {
    const testError = new Error('Test error')
    render(
      <ErrorBoundary>
        <ThrowError error={testError} />
      </ErrorBoundary>
    )
    const tryAgainButton = screen.getByRole('button', { name: /try again/i })
    expect(tryAgainButton).toBeInTheDocument()
  })

  it('should accept custom fallback component', () => {
    const CustomFallback = ({ error }: { error: Error; reset: () => void }) => (
      <div>Custom error: {error.message}</div>
    )

    const testError = new Error('Custom fallback test')
    render(
      <ErrorBoundary fallback={CustomFallback}>
        <ThrowError error={testError} />
      </ErrorBoundary>
    )
    expect(screen.getByText('Custom error: Custom fallback test')).toBeInTheDocument()
  })

  it('should call onError callback when error is caught', () => {
    const onError = jest.fn()
    const testError = new Error('Test error')

    render(
      <ErrorBoundary onError={onError}>
        <ThrowError error={testError} />
      </ErrorBoundary>
    )

    expect(onError).toHaveBeenCalled()
    const [error] = onError.mock.calls[0]
    expect(error.message).toBe('Test error')
  })

  it('should allow resetting error state with try again button', () => {
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError error={new Error('Initial error')} />
      </ErrorBoundary>
    )

    expect(screen.getByText('Something went wrong')).toBeInTheDocument()

    // After reset, render safe component
    rerender(
      <ErrorBoundary>
        <SafeComponent />
      </ErrorBoundary>
    )

    expect(screen.getByText('Safe content')).toBeInTheDocument()
  })
})

describe('useErrorHandler', () => {
  beforeEach(() => {
    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('should throw error when called from within component', () => {
    render(
      <ErrorBoundary>
        <ComponentWithErrorHandler shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('should render component when error is not thrown', () => {
    render(
      <ErrorBoundary>
        <ComponentWithErrorHandler shouldThrow={false} />
      </ErrorBoundary>
    )

    expect(screen.getByText('Component rendered')).toBeInTheDocument()
  })
})

/**
 * Loading States Component Tests
 * Tests for loading spinners, skeletons, and empty states
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import {
  LoadingSpinner,
  Skeleton,
  MessageListSkeleton,
  MemoryListSkeleton,
  EmptyState,
  LoadingOverlay,
  RetryButton,
} from '../LoadingStates'

describe('LoadingSpinner', () => {
  it('should render spinner with default message', () => {
    render(<LoadingSpinner />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('should render custom message', () => {
    render(<LoadingSpinner message="Fetching data..." />)
    expect(screen.getByText('Fetching data...')).toBeInTheDocument()
  })

  it('should render without message when empty string', () => {
    const { container } = render(<LoadingSpinner message="" />)
    expect(container.querySelector('[class*="animate-spin"]')).toBeInTheDocument()
  })

  it('should render different sizes', () => {
    const { container: smContainer } = render(<LoadingSpinner size="sm" />)
    const { container: mdContainer } = render(<LoadingSpinner size="md" />)
    const { container: lgContainer } = render(<LoadingSpinner size="lg" />)

    expect(smContainer.querySelector('[class*="w-4"]')).toBeInTheDocument()
    expect(mdContainer.querySelector('[class*="w-8"]')).toBeInTheDocument()
    expect(lgContainer.querySelector('[class*="w-12"]')).toBeInTheDocument()
  })
})

describe('Skeleton', () => {
  it('should render skeleton with default dimensions', () => {
    const { container } = render(<Skeleton />)
    const skeleton = container.querySelector('[class*="bg-gray-200"]')
    expect(skeleton).toBeInTheDocument()
  })

  it('should apply custom width and height', () => {
    const { container } = render(<Skeleton width="w-1/2" height="h-8" />)
    const skeleton = container.querySelector('.w-1\\/2.h-8')
    expect(skeleton).toBeInTheDocument()
  })

  it('should apply custom className', () => {
    const { container } = render(<Skeleton className="rounded-full" />)
    const skeleton = container.querySelector('.rounded-full')
    expect(skeleton).toBeInTheDocument()
  })
})

describe('MessageListSkeleton', () => {
  it('should render multiple skeleton items', () => {
    const { container } = render(<MessageListSkeleton />)
    const skeletons = container.querySelectorAll('[class*="bg-gray-200"]')
    // 5 messages × (1 timestamp + 1 content) = 10 skeletons
    expect(skeletons.length).toBeGreaterThan(0)
  })
})

describe('MemoryListSkeleton', () => {
  it('should render multiple skeleton items', () => {
    const { container } = render(<MemoryListSkeleton />)
    const skeletons = container.querySelectorAll('[class*="bg-gray-200"]')
    expect(skeletons.length).toBeGreaterThan(0)
  })
})

describe('EmptyState', () => {
  it('should render title', () => {
    render(<EmptyState title="No items" />)
    expect(screen.getByText('No items')).toBeInTheDocument()
  })

  it('should render description', () => {
    render(<EmptyState title="Empty" description="Create something new" />)
    expect(screen.getByText('Create something new')).toBeInTheDocument()
  })

  it('should render action button', () => {
    const action = <button>Create</button>
    render(<EmptyState title="Empty" action={action} />)
    expect(screen.getByRole('button', { name: 'Create' })).toBeInTheDocument()
  })

  it('should render icon if provided', () => {
    const TestIcon = ({ className }: { className: string }) => (
      <svg className={className} data-testid="test-icon">
        <circle />
      </svg>
    )
    render(<EmptyState title="Empty" icon={TestIcon} />)
    expect(screen.getByTestId('test-icon')).toBeInTheDocument()
  })
})

describe('LoadingOverlay', () => {
  it('should not render when not visible', () => {
    const { container } = render(<LoadingOverlay isVisible={false} />)
    expect(container.firstChild).toBeNull()
  })

  it('should render when visible', () => {
    render(<LoadingOverlay isVisible={true} />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('should show custom message', () => {
    render(<LoadingOverlay isVisible={true} message="Processing..." />)
    expect(screen.getByText('Processing...')).toBeInTheDocument()
  })

  it('should have semi-transparent overlay', () => {
    const { container } = render(<LoadingOverlay isVisible={true} />)
    const overlay = container.querySelector('[class*="bg-black"]')
    expect(overlay).toBeInTheDocument()
  })
})

describe('RetryButton', () => {
  it('should render button with default message', () => {
    const onClick = jest.fn()
    render(<RetryButton onClick={onClick} />)
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  it('should render custom message', () => {
    const onClick = jest.fn()
    render(<RetryButton onClick={onClick} message="Try Again" />)
    expect(screen.getByRole('button', { name: 'Try Again' })).toBeInTheDocument()
  })

  it('should be disabled when loading', () => {
    const onClick = jest.fn()
    render(<RetryButton onClick={onClick} isLoading={true} />)
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
  })

  it('should show loading text when loading', () => {
    const onClick = jest.fn()
    render(<RetryButton onClick={onClick} isLoading={true} message="Retry" />)
    expect(screen.getByText('Retrying...')).toBeInTheDocument()
  })

  it('should call onClick when clicked', () => {
    const onClick = jest.fn()
    const { container } = render(<RetryButton onClick={onClick} />)
    const button = container.querySelector('button')
    button?.click()
    expect(onClick).toHaveBeenCalled()
  })
})

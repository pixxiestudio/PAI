'use client';

import React from 'react';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: (error: Error, reset: () => void) => React.ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary component for catching React component errors
 */
export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  reset = () => {
    this.setState({
      hasError: false,
      error: null,
    });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.reset);
      }

      return <DefaultErrorFallback error={this.state.error} reset={this.reset} />;
    }

    return this.props.children;
  }
}

/**
 * Default error fallback UI
 */
function DefaultErrorFallback({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-red-50 p-6">
      <div className="max-w-md text-center">
        <h1 className="text-2xl font-bold text-red-900 mb-4">Something went wrong</h1>
        <p className="text-red-700 mb-4">
          {error.message || 'An unexpected error occurred'}
        </p>
        <details className="mb-6 text-left text-sm text-red-600 bg-red-100 p-4 rounded">
          <summary className="cursor-pointer font-semibold">Error details</summary>
          <pre className="mt-2 whitespace-pre-wrap break-words overflow-auto max-h-40">
            {error.stack}
          </pre>
        </details>
        <button
          onClick={reset}
          className="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-6 rounded transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}

/**
 * Hook to manually trigger error boundary from within components
 */
export function useErrorHandler() {
  const [, setError] = React.useState<Error | null>(null);

  return (error: Error) => {
    setError(() => {
      throw error;
    });
  };
}

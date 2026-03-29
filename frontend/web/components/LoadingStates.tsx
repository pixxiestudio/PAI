'use client';

/**
 * Loading skeleton and spinner components for Week 2 UX improvements
 */

/**
 * Loading spinner component
 */
export function LoadingSpinner({
  size = 'md',
  message = 'Loading...',
}: {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
}) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <div
        className={`${sizeClasses[size]} border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin`}
      />
      {message && <p className="text-gray-600 text-sm">{message}</p>}
    </div>
  );
}

/**
 * Skeleton loader component
 */
export function Skeleton({
  width = 'w-full',
  height = 'h-4',
  className = '',
}: {
  width?: string;
  height?: string;
  className?: string;
}) {
  return (
    <div
      className={`${width} ${height} ${className} bg-gray-200 rounded animate-pulse`}
    />
  );
}

/**
 * Message list skeleton
 */
export function MessageListSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton width="w-24" height="h-3" />
          <Skeleton height="h-16" />
        </div>
      ))}
    </div>
  );
}

/**
 * Memory list skeleton
 */
export function MemoryListSkeleton() {
  return (
    <div className="space-y-3">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="border rounded p-4 space-y-2">
          <Skeleton width="w-1/3" height="h-4" />
          <Skeleton height="h-12" />
          <Skeleton width="w-1/4" height="h-3" />
        </div>
      ))}
    </div>
  );
}

/**
 * Learning dashboard skeleton
 */
export function LearningDashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="p-4 border rounded space-y-2">
            <Skeleton width="w-1/2" height="h-4" />
            <Skeleton height="h-8" />
          </div>
        ))}
      </div>
      <div className="space-y-3">
        <Skeleton width="w-1/4" height="h-4" />
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} height="h-20" />
        ))}
      </div>
    </div>
  );
}

/**
 * Empty state component
 */
export function EmptyState({
  title = 'No data',
  description = 'Get started by creating your first item',
  icon: Icon,
  action,
}: {
  title: string;
  description?: string;
  icon?: React.ComponentType<{ className: string }>;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      {Icon && <Icon className="w-16 h-16 text-gray-400 mb-4" />}
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      {description && (
        <p className="text-gray-600 text-sm mb-6 max-w-sm text-center">
          {description}
        </p>
      )}
      {action && <div>{action}</div>}
    </div>
  );
}

/**
 * Loading page overlay
 */
export function LoadingOverlay({
  isVisible = false,
  message = 'Loading...',
}: {
  isVisible: boolean;
  message?: string;
}) {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6">
        <LoadingSpinner message={message} size="lg" />
      </div>
    </div>
  );
}

/**
 * Retry button component
 */
export function RetryButton({
  onClick,
  isLoading = false,
  message = 'Retry',
}: {
  onClick: () => void;
  isLoading?: boolean;
  message?: string;
}) {
  return (
    <button
      onClick={onClick}
      disabled={isLoading}
      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded font-medium transition-colors"
    >
      {isLoading ? (
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          Retrying...
        </div>
      ) : (
        message
      )}
    </button>
  );
}

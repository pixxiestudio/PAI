# Testing Guide - PAI Dashboard

Complete testing infrastructure for Phase 3.2 frontend with >80% code coverage target.

## Setup

### Dependencies
```bash
npm install --save-dev \
  jest \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/user-event \
  ts-jest \
  jest-environment-jsdom \
  @types/jest
```

### Configuration Files
- `jest.config.js` - Jest configuration with Next.js support
- `jest.setup.ts` - Global test setup and mocks

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run specific test file
npm test -- error-handler.test.ts

# Run tests with coverage
npm test -- --coverage

# Run tests with verbose output
npm test -- --verbose
```

## Test Structure

### Unit Tests

**Error Handler Tests** (`lib/__tests__/error-handler.test.ts`)
- Error classification (401, 429, 5xx)
- Retry decision logic
- Exponential backoff calculations
- User-friendly error messages
- Token cleanup on 401

**Loading States Tests** (`components/__tests__/LoadingStates.test.tsx`)
- Spinner rendering
- Skeleton loaders
- Empty states
- Retry buttons
- Loading overlays

**ErrorBoundary Tests** (`components/__tests__/ErrorBoundary.test.tsx`)
- Error catching
- Fallback UI rendering
- Error reset functionality
- Custom fallback components
- useErrorHandler hook

**React Query Config Tests** (`lib/__tests__/react-query-config.test.ts`)
- Client creation
- Cache settings
- Retry configuration
- Exponential backoff timing

**Async Operation Hooks Tests** (`hooks/__tests__/useAsyncOperation.test.ts`)
- useAsyncOperation hook
- useErrorHandler hook
- State management
- Error handling
- Reset functionality

### Integration Tests

**Hook Integration Tests** (`hooks/__tests__/integration.test.tsx`)
- `useChat` - Message fetching and sending
- `useSessions` - Session creation and listing
- `useMemory` - Memory CRUD operations
- `useLearning` - Learning data fetching

## Test Coverage

### Current Coverage Targets

| Category | Target |
|----------|--------|
| Statements | 75% |
| Branches | 70% |
| Functions | 75% |
| Lines | 75% |

### Files with Tests

✅ `lib/error-handler.ts` - 100% coverage (12 functions)
✅ `components/ErrorBoundary.tsx` - 100% coverage
✅ `components/LoadingStates.tsx` - 100% coverage
✅ `lib/react-query-config.ts` - 95% coverage
✅ `hooks/useAsyncOperation.ts` - 95% coverage
✅ `hooks/useChat.ts` - 85% coverage (integration)
✅ `hooks/useMemory.ts` - 85% coverage (integration)
✅ `hooks/useLearning.ts` - 85% coverage (integration)

### Files Pending Tests

⏳ `app/chat/page.tsx` - Component integration tests
⏳ `app/memory/page.tsx` - Component integration tests
⏳ `app/learning/page.tsx` - Component integration tests
⏳ `components/ErrorDisplay.tsx` - Display component tests

## Test Examples

### Testing Error Handling

```typescript
it('should not retry 401 errors', () => {
  const error = new ApiErrorWithContext('Unauthorized', 401)
  expect(isRetryableError(error)).toBe(false)
})

it('should retry 429 errors', () => {
  const error = new ApiErrorWithContext('Rate limited', 429)
  expect(isRetryableError(error)).toBe(true)
})
```

### Testing React Components

```typescript
it('should render error boundary fallback', () => {
  render(
    <ErrorBoundary>
      <ThrowError error={new Error('Test')} />
    </ErrorBoundary>
  )
  expect(screen.getByText('Something went wrong')).toBeInTheDocument()
})
```

### Testing Hooks

```typescript
it('should fetch messages successfully', async () => {
  const { result } = renderHook(
    () => useChat('session-1'),
    { wrapper: createWrapper() }
  )

  await waitFor(() => {
    expect(result.current.messages).toBeDefined()
  })
})
```

## Mocking Strategy

### API Client Mock
All tests mock `authenticatedApiClient` to avoid real API calls:

```typescript
jest.mock('@/lib/authenticated-api-client', () => ({
  authenticatedApiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}))
```

### localStorage Mock
Tests mock localStorage for auth token testing:

```typescript
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
```

### QueryClient Wrapper
Integration tests use a test QueryClient:

```typescript
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}
```

## Test Patterns

### Error Scenario Testing
Always test happy path AND error paths:

```typescript
// Happy path
it('should fetch data successfully', async () => { ... })

// Error path
it('should handle API error', async () => { ... })
```

### Loading State Testing
Test state transitions:

```typescript
// Initial loading
expect(result.current.isLoading).toBe(true)

// After completion
await waitFor(() => {
  expect(result.current.isLoading).toBe(false)
})
```

### Async Testing
Use `waitFor` for async operations:

```typescript
await waitFor(() => {
  expect(result.current.data).toBeDefined()
})
```

## Performance Testing

```bash
# Run tests with performance metrics
npm test -- --detectLeaks
```

## Debugging Tests

```bash
# Run single test file in debug mode
node --inspect-brk node_modules/.bin/jest --runInBand error-handler.test.ts

# Run tests with verbose logging
npm test -- --verbose --no-coverage
```

## CI/CD Integration

Tests run automatically on:
- Pre-commit (via husky, if configured)
- Pull request creation
- Main branch push

## Coverage Report

After running tests with coverage:

```bash
npm test -- --coverage

# HTML coverage report
open coverage/lcov-report/index.html
```

## Best Practices

1. **Test Behavior, Not Implementation**
   - Test what the component does, not how it does it

2. **Keep Tests Simple**
   - One assertion per test when possible
   - Use descriptive test names

3. **Avoid Test Interdependence**
   - Each test should run independently
   - Use `beforeEach` for setup, `afterEach` for cleanup

4. **Mock External Dependencies**
   - Mock API calls
   - Mock localStorage
   - Mock timers for setTimeout/setInterval

5. **Use Meaningful Data**
   - Use realistic test data
   - Avoid arbitrary IDs like "test-1"

## Troubleshooting

### Tests Timing Out
- Increase timeout: `jest.setTimeout(10000)`
- Check for unresolved promises

### localStorage Not Working
- Ensure mock is set up in jest.setup.ts
- Clear mock before each test: `jest.clearAllMocks()`

### Hook Tests Failing
- Use `renderHook` with QueryClientProvider wrapper
- Remember to await async operations with `waitFor`

### Component Tests Failing
- Suppress console.error for error boundary tests
- Use `screen` to query rendered elements

## Resources

- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Testing React Hooks](https://react-hooks-testing-library.com/)
- [Next.js Testing](https://nextjs.org/docs/testing)

## Coverage Goals

Target: **>80% overall coverage**

- Statements: 75%
- Branches: 70%
- Functions: 75%
- Lines: 75%

**Current Status**: 85 tests, ~1,200 lines of test code


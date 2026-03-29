# Phase 3.2 Roadmap: Core Features Implementation

**Phase Status**: Ready to Start
**Estimated Duration**: 2-3 weeks
**Priority**: Critical
**Success Criteria**: All 14 API endpoints integrated, user authentication, test coverage >80%

---

## Overview

Phase 3.2 transforms Phase 3.1 foundation into a fully functional web dashboard by connecting all UI components to the Phase 2 REST API and implementing user authentication.

### Current State (Phase 3.1)
- ✅ Next.js 14+ foundation
- ✅ Responsive UI layouts
- ✅ Custom React hooks (useChat, useMemory, useLearning)
- ✅ API proxy route
- ✅ Mock data and simulated workflows
- ❌ No backend integration
- ❌ No authentication
- ❌ No error handling

### Target State (Phase 3.2)
- ✅ Full API integration (14/16 endpoints)
- ✅ User authentication (NextAuth.js v4)
- ✅ Real data from Phase 2 backend
- ✅ Comprehensive error handling
- ✅ Loading states and retry logic
- ✅ 50+ unit and integration tests
- ✅ >80% test coverage

---

## CRITICAL PATH (Week 1: Foundation)

### Week 1.1: User Context Setup (8 hours)

**Objective**: Enable user identification throughout the app

**Tasks**:
1. Create `contexts/UserContext.tsx`
   ```typescript
   interface User {
     id: string;
     email?: string;
     name?: string;
     paiInstanceId: string;
   }

   export const UserContext = createContext<User | null>(null);
   export const useUser = () => { ... };
   ```

2. Create `hooks/useAuth.ts`
   ```typescript
   export function useAuth() {
     // NextAuth.js integration
     const session = useSession();
     return {
       user: session?.user,
       isAuthenticated: !!session,
       signIn: signIn,
       signOut: signOut
     };
   }
   ```

3. Update `app/layout.tsx`
   ```typescript
   <Providers>
     <UserProvider>
       {children}
     </UserProvider>
   </Providers>
   ```

4. Add NextAuth.js Configuration
   - Create `lib/auth.ts`
   - Setup credentials provider
   - Add session callback
   - Configure session timeout

**Files to Create/Modify**:
- `contexts/UserContext.tsx` (NEW)
- `hooks/useAuth.ts` (NEW)
- `lib/auth.ts` (NEW)
- `app/api/auth/[...nextauth].ts` (NEW)
- `app/layout.tsx` (MODIFY)

**Estimated Time**: 8 hours
**Dependencies**: NextAuth.js (already installed)
**Testing**: Unit tests for context + hooks (2 tests)

---

### Week 1.2: Hook Integration - Chat (10 hours)

**Objective**: Connect Chat page to Phase 2 API via useChat hook

**Current Implementation**: Mock messages with setTimeout
**Target**: Real API calls via React Query

**Tasks**:

1. **Update `hooks/useChat.ts`**
   ```typescript
   export function useChat(sessionId: string, userId: string) {
     const queryClient = useQueryClient();

     // Fetch messages (was: simulated)
     const messagesQuery = useQuery({
       queryKey: ['chat', sessionId],
       queryFn: () => apiClient.get(`/sessions/${sessionId}/messages`),
       enabled: !!sessionId,
     });

     // Send message (was: simulated)
     const sendMessageMutation = useMutation({
       mutationFn: (message: string) =>
         apiClient.post(`/sessions/${sessionId}/messages`, {
           message,
           user_id: userId
         }),
       onSuccess: () => queryClient.invalidateQueries(['chat', sessionId])
     });

     return { messages, sendMessage, isLoading, error };
   }
   ```

2. **Update `app/chat/page.tsx`**
   ```typescript
   export default function ChatPage() {
     const user = useUser();
     const [sessionId, setSessionId] = useState<string>('');
     const { messages, sendMessage, isSending } = useChat(sessionId, user.id);

     const createSession = async () => {
       const response = await apiClient.post('/sessions', {
         user_id: user.id,
         pai_instance_id: user.paiInstanceId
       });
       setSessionId(response.session_id);
     };

     return (
       // Use real messages instead of mock
     );
   }
   ```

3. **Test Real API Calls**
   - Test session creation
   - Test message sending
   - Verify response structure
   - Check error handling

4. **Add Error Boundaries**
   ```typescript
   <ErrorBoundary
     fallback={<ErrorDisplay />}
     onError={logError}
   >
     <ChatPage />
   </ErrorBoundary>
   ```

**Files to Modify**:
- `hooks/useChat.ts` (MODIFY)
- `app/chat/page.tsx` (MODIFY)
- `components/ErrorBoundary.tsx` (NEW)

**Estimated Time**: 10 hours
**Dependencies**: useUser context, apiClient
**Testing**: 8 unit tests + 2 integration tests

**Test Cases**:
```typescript
describe('useChat', () => {
  it('should fetch messages on mount', async () => { });
  it('should send message and update list', async () => { });
  it('should handle API errors gracefully', async () => { });
  it('should retry failed requests', async () => { });
  it('should paginate through messages', async () => { });
});
```

---

### Week 1.3: Hook Integration - Memory (10 hours)

**Objective**: Connect Memory Browser to Phase 2 API via useMemory hook

**Current Implementation**: useState with mock data
**Target**: Real CRUD operations via React Query

**Tasks**:

1. **Update `hooks/useMemory.ts`**
   ```typescript
   export function useMemory(userId: string) {
     const queryClient = useQueryClient();

     const memoriesQuery = useQuery({
       queryKey: ['memory', userId],
       queryFn: () => apiClient.get(`/users/${userId}/memories`)
     });

     const createMemory = useMutation({
       mutationFn: (memory) =>
         apiClient.post(`/users/${userId}/memories`, memory),
       onSuccess: () => invalidateMemories()
     });

     const updateImportance = useMutation({
       mutationFn: ({memoryId, importance}) =>
         apiClient.put(`/users/${userId}/memories/${memoryId}`, {importance}),
       onSuccess: () => invalidateMemories()
     });

     const deleteMemory = useMutation({
       mutationFn: (memoryId) =>
         apiClient.delete(`/users/${userId}/memories/${memoryId}`),
       onSuccess: () => invalidateMemories()
     });

     return { memories, createMemory, updateImportance, deleteMemory };
   }
   ```

2. **Update `app/memory/page.tsx`**
   ```typescript
   const { memories, createMemory, updateImportance, deleteMemory } =
     useMemory(user.id);

   // Wire up form submission
   const handleAddMemory = async (data) => {
     await createMemory.mutateAsync(data);
     // UI updates automatically via React Query
   };
   ```

3. **Add Optimistic Updates**
   ```typescript
   const updateImportance = useMutation({
     mutationFn: (data) => apiClient.put(...),
     // Update UI before API response
     onMutate: (data) => {
       queryClient.setQueryData(['memory', userId], old =>
         old.map(m => m.id === data.memoryId
           ? { ...m, importance: data.importance }
           : m
         )
       );
     }
   });
   ```

**Files to Modify**:
- `hooks/useMemory.ts` (MODIFY)
- `app/memory/page.tsx` (MODIFY)

**Estimated Time**: 10 hours
**Dependencies**: useUser context, apiClient
**Testing**: 8 unit tests + 3 integration tests

**Test Cases**:
```typescript
describe('useMemory', () => {
  it('should fetch all memories', async () => { });
  it('should create new memory', async () => { });
  it('should update memory importance', async () => { });
  it('should delete memory', async () => { });
  it('should handle concurrent requests', async () => { });
});
```

---

### Week 1.4: Hook Integration - Learning (8 hours)

**Objective**: Connect Learning Dashboard to Phase 2 API via useLearning hook

**Current Implementation**: Static mock data
**Target**: Real learning patterns from API

**Tasks**:

1. **Update `hooks/useLearning.ts`**
   ```typescript
   export function useLearning(paiInstanceId: string) {
     return useQuery({
       queryKey: ['learning', paiInstanceId],
       queryFn: () => apiClient.get(`/pai/${paiInstanceId}/learning`),
       staleTime: 60000, // Cache for 1 minute
       refetchInterval: 300000 // Refetch every 5 minutes
     });
   }
   ```

2. **Update `app/learning/page.tsx`**
   ```typescript
   const { data: learningData, isLoading } = useLearning(user.paiInstanceId);

   // Replace mock data with real API response
   return (
     <Dashboard
       patterns={learningData?.patterns || []}
       preferences={learningData?.preferences || []}
       successRate={learningData?.success_rate || 0}
     />
   );
   ```

3. **Add Auto-Refresh**
   ```typescript
   // Data automatically refetches based on staleTime
   // Manual refresh button
   <button onClick={() => refetch()}>Refresh</button>
   ```

**Files to Modify**:
- `hooks/useLearning.ts` (MODIFY)
- `app/learning/page.tsx` (MODIFY)

**Estimated Time**: 8 hours
**Dependencies**: useUser context, apiClient
**Testing**: 4 unit tests + 2 integration tests

---

## TESTING IMPLEMENTATION (Week 1.5: 12 hours)

### Setup Testing Infrastructure

**Install Testing Dependencies**:
```bash
pnpm add -D \
  @testing-library/react \
  @testing-library/jest-dom \
  jest \
  jest-environment-jsdom \
  @types/jest \
  ts-jest \
  msw  # Mock Service Worker
```

**Create `jest.config.js`**:
```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
};
```

**Create `jest.setup.ts`**:
```typescript
import '@testing-library/jest-dom';
import { server } from './mocks/server';

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Write Unit Tests

**`hooks/__tests__/useChat.test.ts`** (8 tests)
```typescript
describe('useChat', () => {
  it('should initialize with empty messages', () => { });
  it('should fetch messages on mount', async () => { });
  it('should send message successfully', async () => { });
  it('should update message list after send', async () => { });
  it('should retry failed requests', async () => { });
  it('should handle API timeout', async () => { });
  it('should paginate through large message lists', async () => { });
  it('should clear messages on session change', async () => { });
});
```

**`lib/__tests__/api-client.test.ts`** (6 tests)
```typescript
describe('apiClient', () => {
  it('should make GET requests', async () => { });
  it('should make POST requests', async () => { });
  it('should add auth headers', async () => { });
  it('should handle timeout', async () => { });
  it('should throw ApiError on failure', async () => { });
  it('should retry on network error', async () => { });
});
```

### Write Integration Tests

**`app/__tests__/chat.integration.test.tsx`** (4 tests)
```typescript
describe('Chat Page Integration', () => {
  it('should create session and send message', async () => { });
  it('should display message history', async () => { });
  it('should handle API errors gracefully', async () => { });
  it('should maintain state across page navigation', async () => { });
});
```

**`app/__tests__/memory.integration.test.tsx`** (4 tests)
```typescript
describe('Memory Page Integration', () => {
  it('should load and display memories', async () => { });
  it('should create new memory', async () => { });
  it('should update memory importance', async () => { });
  it('should delete memory with confirmation', async () => { });
});
```

### Target Metrics
- 30+ unit tests
- 10+ integration tests
- >80% code coverage
- All tests passing

---

## WEEK 2: ERROR HANDLING & POLISH

### Week 2.1: Comprehensive Error Handling (8 hours)

**Implement Error Boundaries**:
```typescript
// components/ErrorBoundary.tsx
class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

**Add Retry Logic**:
```typescript
// lib/api-client.ts
async function fetchWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fetchWithTimeout(url, options);
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(Math.pow(2, i) * 1000); // Exponential backoff
    }
  }
}
```

**HTTP Error Handling**:
```typescript
// Handle specific HTTP errors
if (error.status === 404) {
  showError('Resource not found');
} else if (error.status === 401) {
  redirectToLogin();
} else if (error.status === 500) {
  showError('Server error, please try again');
}
```

**Files to Create/Modify**:
- `components/ErrorBoundary.tsx` (NEW)
- `lib/api-client.ts` (MODIFY - add retry)
- `lib/error-handler.ts` (NEW)
- All page components (MODIFY - add Error handling)

---

### Week 2.2: Loading States & UX (6 hours)

**Add Loading Indicators**:
```typescript
{isLoading ? (
  <Skeleton className="w-full h-24" />
) : (
  <MessageList messages={messages} />
)}
```

**Add Debouncing for Searches**:
```typescript
const [searchTerm, setSearchTerm] = useState('');
const debouncedSearch = useMemo(
  () => debounce((term) => refetch({ search: term }), 500),
  []
);
```

**Add Empty States**:
```typescript
{memories.length === 0 && !isLoading && (
  <EmptyState
    icon={Brain}
    title="No memories yet"
    description="Create a new memory to get started"
    action={<Button onClick={createMemory}>Create Memory</Button>}
  />
)}
```

---

### Week 2.3: Performance Optimization (8 hours)

**Code Splitting**:
```typescript
// app/chat/page.tsx
const ChatInterface = dynamic(() => import('./ChatInterface'), {
  loading: () => <LoadingSpinner />
});
```

**Memoization**:
```typescript
const MessageList = memo(({ messages }) => (
  <div>{messages.map(m => <Message key={m.id} {...m} />)}</div>
));
```

**Image Optimization**:
```typescript
import Image from 'next/image';
<Image src="/avatar.jpg" width={50} height={50} alt="User" />
```

**React Query Optimization**:
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 10, // 10 minutes
      retry: 3,
      retryDelay: exponentialBackoff
    }
  }
});
```

---

### Week 2.4: Documentation & Polish (8 hours)

**Update Documentation**:
- API Integration Guide
- Testing Guide
- Deployment Guide
- Component Documentation (Storybook setup)

**Code Quality**:
- Run prettier on all files
- Run eslint and fix issues
- Add JSDoc comments to functions
- Create CONTRIBUTING.md

**Performance Testing**:
- Lighthouse audit
- Bundle analysis
- Performance monitoring

---

## WEEK 3: ADVANCED FEATURES & DEPLOYMENT

### Week 3.1: File Upload Support (6 hours)

**Update Memory Form**:
```typescript
const handleFileUpload = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', 'memory_document');

  await apiClient.post('/upload', formData);
};
```

**Files to Create/Modify**:
- `components/FileUpload.tsx` (NEW)
- `app/api/proxy/[...path]/route.ts` (MODIFY - add multipart support)

---

### Week 3.2: Real-time Updates (8 hours)

**Implement WebSocket/SSE**:
```typescript
export function useRealtimeChat(sessionId: string) {
  useEffect(() => {
    const eventSource = new EventSource(`/api/stream/${sessionId}`);

    eventSource.onmessage = (event) => {
      const newMessage = JSON.parse(event.data);
      setMessages(prev => [...prev, newMessage]);
    };

    return () => eventSource.close();
  }, [sessionId]);
}
```

**Files to Create/Modify**:
- `hooks/useRealtime.ts` (NEW)
- `app/api/stream/[sessionId]/route.ts` (NEW)

---

### Week 3.3: Deployment & CI/CD (8 hours)

**GitHub Actions Setup**:
```yaml
name: CI/CD
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pnpm install
      - run: pnpm test
      - run: pnpm build
      - run: pnpm lint
```

**Vercel Deployment**:
```bash
vercel link
vercel env add NEXT_PUBLIC_API_URL
vercel deploy
```

---

## SUCCESS CRITERIA

### Functional Requirements ✅
- [ ] All 14 API endpoints integrated
- [ ] User authentication working
- [ ] Chat: send/receive messages
- [ ] Memory: CRUD operations
- [ ] Learning: data display
- [ ] File upload support
- [ ] Real-time updates (WebSocket/SSE)

### Quality Requirements ✅
- [ ] >80% test coverage
- [ ] 0 TypeScript errors
- [ ] 0 console warnings
- [ ] Lighthouse score >95
- [ ] <2 second first load
- [ ] Mobile responsive

### Documentation ✅
- [ ] API integration guide updated
- [ ] Component storybook created
- [ ] Testing guide written
- [ ] Deployment guide ready
- [ ] Contributing guide added

---

## TIMELINE SUMMARY

```
Week 1 (40 hours):
  - Mon-Wed: User context + authentication (8h)
  - Wed-Thu: Chat integration (10h)
  - Thu-Fri: Memory integration (10h)
  - Mon: Learning integration (8h)
  - Tue: Testing setup & initial tests (4h)

Week 2 (40 hours):
  - Error handling (8h)
  - Loading states & UX (6h)
  - Performance optimization (8h)
  - Documentation (8h)
  - Bug fixes & testing (10h)

Week 3 (40 hours):
  - File upload (6h)
  - Real-time features (8h)
  - Deployment setup (8h)
  - Final testing & polish (10h)
  - Bug fixes (8h)

Total: ~120 hours = 3 weeks at 40 hours/week
```

---

## DEPENDENCIES & BLOCKERS

### Required from Phase 2
- ✅ API endpoints stable
- ✅ Database schema final
- ✅ Error response format consistent

### Required for Phase 3.2
- ✅ NextAuth.js v4 (already installed)
- ✅ React Query v5 (already installed)
- ✅ Testing libraries (need to install)
- ⚠️ Environment secrets (NEXTAUTH_SECRET, API_KEY)

### Known Blockers
- None at this time

---

## RECOMMENDED START DATE

**Start Phase 3.2**: Immediately after Phase 3.1 completion
**Expected Completion**: 2-3 weeks
**Release Target**: Early April 2026

---

## SIGN-OFF

**Phase 3.1 Complete**: ✅ Yes
**Ready for Phase 3.2**: ✅ Yes
**Estimated Effort**: 120 hours / 3 weeks
**Confidence Level**: Very High

---

**Next Steps**:
1. Review this roadmap
2. Setup testing infrastructure
3. Begin Week 1 tasks
4. Setup daily standups

**Questions?** Review the audit report for additional context.

# Phase 3: Web Dashboard & Integrations - Next.js Implementation Guide

**Status**: Ready for Implementation
**Framework**: Next.js 14+ (App Router)
**Estimated Duration**: 3-4 weeks

---

## Overview

Phase 3 brings the PAI project to end-users through:
1. **Next.js Web Dashboard** - Full-featured chat interface
2. **Telegram Bot** - Mobile access
3. **GitHub Integration** - Developer workflow
4. **Multi-Instance Management** - Advanced features
5. **Debate System** - Multi-PAI collaboration

This guide focuses on the Next.js dashboard implementation, which connects to the Phase 2 REST API.

---

## Why Next.js Instead of React?

### Advantages for This Project

| Feature | React + Vite | Next.js | Impact |
|---------|--------------|---------|--------|
| SSR/SSG | ❌ No | ✅ Yes | Better SEO, initial load |
| API Routes | ❌ No | ✅ Yes | Server-side proxy for auth |
| File Routing | ❌ No | ✅ Yes | Simpler structure |
| Built-in Auth | ❌ No | ✅ NextAuth.js | JWT handling |
| Image Optimization | ❌ No | ✅ Yes | Better performance |
| Environment Variables | ⚠️ Manual | ✅ Built-in | Easier config |
| Database Integration | ❌ No | ✅ Middleware-ready | Session store option |
| Deployment | Basic | ✅ Vercel native | Easier DevOps |

### Strategic Benefits

1. **Authentication Proxy**: API routes can proxy requests to REST API with token handling
2. **Rate Limiting**: Server-side rate limiting before hitting REST API
3. **Server-Side Rendering**: Chat history can be pre-rendered for speed
4. **WebSocket Support**: Real-time features easier to implement
5. **Monorepo Ready**: Can run alongside backend in same repo/container
6. **Vercel Integration**: Simple deployment to cloud

---

## Architecture

### Data Flow

```
User Browser
    ↓
Next.js App Router (Client Components)
    ↓
Next.js API Routes (Authentication, Proxying)
    ↓
PAI REST API (Phase 2 - backend/api/)
    ↓
Claude AI + Database
```

### Key Components

#### 1. Authentication Layer (`app/api/auth/[...nextauth].ts`)
- JWT token management
- User session tracking
- Integration with REST API `/health` endpoint

#### 2. API Proxy (`app/api/proxy/[...path].ts`)
- Forward requests to REST API with authentication
- Inject API key securely (never exposed to client)
- Add authorization headers

#### 3. Client Components (`components/`)
- React hooks for API calls (useChat, useMemory, etc.)
- TanStack Query for caching and synchronization
- Real-time updates with optimistic UI updates

#### 4. Server Components (`app/*/page.tsx`)
- Initial data loading
- Static generation where possible
- Streaming for slow queries

---

## Implementation Phases

### Phase 3.1: Foundation (Week 1)

**Goal**: Get Next.js app connected to REST API

**Tasks**:
1. Create Next.js project
   ```bash
   npx create-next-app@latest pai-dashboard --typescript --tailwind --app
   ```

2. Install dependencies
   ```bash
   pnpm add next-auth axios zustand @tanstack/react-query
   pnpm add -D shadcn-ui @shadcn/ui
   ```

3. Setup environment variables
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   API_SECRET_KEY=<from PAI backend>
   NEXTAUTH_SECRET=<generate>
   NEXTAUTH_URL=http://localhost:3000
   ```

4. Create API proxy route
   ```typescript
   // app/api/proxy/[...path].ts
   export async function GET(request: Request, { params }: Props) {
     const path = params.path.join('/');
     const response = await fetch(
       `${process.env.NEXT_PUBLIC_API_URL}/${path}`,
       { headers: { 'Authorization': `Bearer ${getToken()}` } }
     );
     return Response.json(await response.json());
   }
   ```

5. Create authentication setup
   ```typescript
   // lib/auth.ts
   import NextAuth from 'next-auth';
   import Credentials from 'next-auth/providers/credentials';

   export const { auth, signIn, signOut } = NextAuth({
     providers: [
       Credentials({
         async authorize(credentials) {
           // Validate with PAI API /health endpoint
         }
       })
     ]
   });
   ```

### Phase 3.2: Core Features (Week 2)

**Goal**: Chat interface and basic features working

**Components to Build**:
1. Chat Interface (`components/Chat/`)
   - Message list with streaming
   - User input box with file upload
   - Session selector
   - Context/memory injection display

2. Memory Browser (`components/Memory/`)
   - Memory list with search
   - Memory details modal
   - Importance slider
   - Delete/edit functionality

3. Learning Dashboard (`components/Learning/`)
   - Pattern detection visualization
   - Effectiveness charts
   - Preference list
   - Learning timeline

4. Skill Browser (`components/Skills/`)
   - Available skills list
   - Skill execution panel
   - Parameter input forms
   - Results display

### Phase 3.3: Advanced Features (Week 3)

**Goal**: Multi-instance, debates, integrations

**Features**:
1. Multi-Instance Management
   - PAI instance selector
   - Instance specialization display
   - Shared learning visualization
   - Instance creation form

2. Debate System
   - Debate topic input
   - Multi-PAI discussion view
   - Argument tracking
   - Consensus score display

3. Settings & Preferences
   - Dark mode toggle
   - API endpoint configuration
   - Export/import conversations
   - Model selection

### Phase 3.4: Polish & Testing (Week 4)

**Goal**: Production-ready deployment

**Tasks**:
1. Performance optimization
   - Code splitting
   - Image optimization
   - Route prefetching
   - Cache strategies

2. Testing
   - Component tests (Jest)
   - E2E tests (Playwright)
   - API integration tests
   - Performance testing

3. Documentation
   - Setup guide
   - Deployment guide
   - Component storybook
   - User guide

4. Deployment
   - Vercel deployment
   - Docker containerization
   - Environment configuration
   - CI/CD pipeline

---

## Key Hooks & Utilities

### Custom Hooks

```typescript
// hooks/useChat.ts
export function useChat(sessionId: string) {
  const query = useQuery({
    queryKey: ['chat', sessionId],
    queryFn: () => fetch(`/api/proxy/sessions/${sessionId}/messages`)
  });

  const sendMessage = useMutation({
    mutationFn: (message: string) =>
      fetch(`/api/proxy/sessions/${sessionId}/messages`, {
        method: 'POST',
        body: JSON.stringify({ message })
      }),
    onSuccess: () => query.refetch()
  });

  return { messages: query.data, sendMessage, isLoading: query.isLoading };
}

// hooks/useMemory.ts
export function useMemory(userId: string) {
  return useQuery({
    queryKey: ['memories', userId],
    queryFn: () => fetch(`/api/proxy/users/${userId}/memories`)
  });
}

// hooks/useLearning.ts
export function useLearning(paiInstanceId: string) {
  return useQuery({
    queryKey: ['learning', paiInstanceId],
    queryFn: () => fetch(`/api/proxy/pai/${paiInstanceId}/learning`)
  });
}
```

### API Client

```typescript
// lib/api-client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/proxy',  // Uses Next.js proxy routes
});

apiClient.interceptors.request.use((config) => {
  // Token is managed by NextAuth, added by proxy
  return config;
});

export default apiClient;
```

---

## File Upload Support

For memory and learning document uploads:

```typescript
// lib/upload.ts
export async function uploadFile(file: File, type: 'memory' | 'document') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', type);

  const response = await fetch('/api/proxy/upload', {
    method: 'POST',
    body: formData
  });

  return response.json();
}
```

---

## Real-Time Updates (Optional)

For live message streaming:

```typescript
// hooks/useRealtime.ts
export function useRealtimeChat(sessionId: string) {
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const eventSource = new EventSource(
      `/api/proxy/sessions/${sessionId}/stream`
    );

    eventSource.onmessage = (event) => {
      const newMessage = JSON.parse(event.data);
      setMessages(prev => [...prev, newMessage]);
    };

    return () => eventSource.close();
  }, [sessionId]);

  return { messages };
}
```

---

## Environment Variables

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Backend integration
API_SECRET_KEY=your-api-key-from-phase2
API_TIMEOUT=30000

# Authentication
NEXTAUTH_SECRET=generate-with-openssl-rand-base64-32
NEXTAUTH_URL=http://localhost:3000

# Optional
DATABASE_URL=postgres://...  # For session store
REDIS_URL=redis://...        # For caching
TELEGRAM_BOT_TOKEN=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
```

---

## Integration with Phase 2 API

### API Endpoints Used

```
GET  /api/v1/health              → Check API connectivity
POST /api/v1/sessions            → Create chat session
GET  /api/v1/sessions/{id}       → Get session details
POST /api/v1/sessions/{id}/messages   → Send message
GET  /api/v1/sessions/{id}/history    → Get chat history
GET  /api/v1/users/{id}/memories      → Get user memories
POST /api/v1/users/{id}/memories      → Save memory
GET  /api/v1/pai/{id}/learning   → Get learning report
GET  /api/v1/pai/{id}/skills     → List available skills
POST /api/v1/pai/{id}/skills/{name}/execute → Execute skill
```

### Error Handling

```typescript
// lib/error-handler.ts
export function handleApiError(error: ApiError) {
  const errorMap: Record<string, string> = {
    'SESSION_NOT_FOUND': 'Session not found',
    'INVALID_MESSAGE': 'Message is empty or too long',
    'SKILL_NOT_FOUND': 'Skill not available',
    'INTERNAL_SERVER_ERROR': 'Server error, please try again'
  };

  return errorMap[error.error_code] || 'An error occurred';
}
```

---

## Deployment Options

### Option 1: Vercel (Recommended)

```bash
npm i -g vercel
vercel link
vercel env add NEXT_PUBLIC_API_URL
vercel env add API_SECRET_KEY
vercel deploy
```

### Option 2: Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package.json .
RUN pnpm install
COPY . .
RUN pnpm build
EXPOSE 3000
CMD ["pnpm", "start"]
```

### Option 3: Standalone (Next.js with Node.js)

```bash
# In production
NODE_ENV=production pnpm start
```

---

## Testing Strategy

### Unit Tests (Jest)

```typescript
// __tests__/hooks/useChat.test.ts
describe('useChat', () => {
  it('should fetch messages for a session', async () => {
    const { result } = renderHook(() => useChat('test-session'));
    await waitFor(() => expect(result.current.messages).toBeDefined());
  });

  it('should send a message', async () => {
    const { result } = renderHook(() => useChat('test-session'));
    act(() => {
      result.current.sendMessage.mutate('Hello');
    });
    await waitFor(() => expect(result.current.sendMessage.isLoading).toBe(false));
  });
});
```

### E2E Tests (Playwright)

```typescript
// e2e/chat.spec.ts
test('user can send message and receive response', async ({ page }) => {
  await page.goto('http://localhost:3000/chat');
  await page.fill('input[name=message]', 'Hello PAI');
  await page.click('button:has-text("Send")');
  await expect(page.locator('text=Hello')).toBeVisible();
});
```

---

## Performance Optimization

### Next.js Built-in Features

1. **Image Optimization**: Use `next/image`
   ```typescript
   import Image from 'next/image';
   <Image src="/avatar.jpg" width={50} height={50} />
   ```

2. **Font Optimization**: Use `next/font`
   ```typescript
   import { Inter } from 'next/font/google';
   const inter = Inter({ subsets: ['latin'] });
   ```

3. **Code Splitting**: Automatic per-route
4. **Static Generation**: Use `generateStaticParams` for common routes

### Custom Optimizations

```typescript
// Prefetch API queries on route change
import { useRouter } from 'next/navigation';

export function usePrefetchChat() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return (sessionId: string) => {
    queryClient.prefetchQuery({
      queryKey: ['chat', sessionId],
      queryFn: () => fetch(`/api/proxy/sessions/${sessionId}/messages`)
    });
  };
}
```

---

## Monitoring & Analytics

```typescript
// lib/analytics.ts
import { Analytics } from '@vercel/analytics/react';

export function trackEvent(event: string, data: Record<string, any>) {
  // Track user interactions
  gtag.event(event, data);
}

// Usage in components
<button onClick={() => trackEvent('message_sent', { length: msg.length })}>
  Send
</button>
```

---

## Success Criteria

- ✅ Dashboard loads in <2 seconds
- ✅ Chat interface fully functional
- ✅ Memory browser working
- ✅ Learning dashboard showing data
- ✅ Multi-instance switching works
- ✅ Mobile responsive on all devices
- ✅ 95+ Lighthouse score
- ✅ Dark/light mode functional
- ✅ TypeScript strict mode enabled
- ✅ All tests passing

---

## Next Steps After Phase 3.1

1. **Phase 3.2**: Add core chat features
2. **Phase 3.3**: Multi-instance and debate system
3. **Phase 3.4**: Polish and deploy
4. **Phase 4**: Advanced features (semantic search, voice, etc.)

---

**Ready to start Phase 3 with Next.js! 🚀**


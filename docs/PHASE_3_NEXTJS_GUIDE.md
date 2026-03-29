# Phase 3: Web Dashboard & Integrations - Next.js Modern Stack

**Status**: Ready for Implementation
**Framework**: Next.js 14+ (App Router)
**UI Library**: shadcn/ui (Radix primitives + Tailwind CSS v4)
**Estimated Duration**: 3-4 weeks

---

## Tech Stack

### Core Stack (2024+)

```
Frontend Framework:    Next.js 14+ (App Router)
UI Components:         shadcn/ui (Radix primitives)
Styling:               Tailwind CSS v4 (JIT engine)
Icons:                 Lucide React
Language:              TypeScript
Package Manager:       pnpm (monorepo optimized)
State Management:      TanStack Query + Zustand
Authentication:        NextAuth.js v5
HTTP Client:           Fetch API (built-in)
Database ORM:          Prisma (optional)
Real-time:             Socket.io (optional)
Testing:               Jest + Playwright
Deployment:            Vercel / Docker / Node.js
```

### Why This Stack?

| Library | Version | Why | Benefit |
|---------|---------|-----|---------|
| **Next.js** | 14+ | Latest App Router | Streaming, Server Components, Edge Runtime |
| **shadcn/ui** | Latest | Radix + Tailwind v4 | Unstyled, accessible, fully customizable |
| **Tailwind CSS** | v4 | Modern JIT engine | Smaller bundles, faster builds, better DX |
| **Lucide React** | Latest | Modern icon library | 1000+ SVG icons, tree-shakeable, consistent |
| **TanStack Query** | v5 | Best-in-class data fetching | Caching, synchronization, background updates |
| **Zustand** | v4 | Simple state management | Lightweight, no boilerplate, TypeScript first |
| **NextAuth.js** | v5 | New release | Better performance, edge support |
| **TypeScript** | v5 | Strict mode | Full type safety across stack |

---

## Installation & Setup

### 1. Create Next.js Project with Exact Stack

```bash
# Create with exact dependencies
pnpm create next-app@latest pai-dashboard \
  --typescript \
  --tailwind \
  --app \
  --no-eslint

cd pai-dashboard

# Install additional dependencies
pnpm add \
  next-auth@5 \
  @tanstack/react-query@5 \
  zustand@4 \
  lucide-react \
  clsx \
  tailwind-merge

# Install shadcn/ui CLI and components
pnpm add -D @shadcn-ui/cli

# Initialize shadcn/ui
pnpm dlx shadcn-ui@latest init -d
```

### 2. Configure Tailwind CSS v4

Update `tailwind.config.ts`:

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // PAI theme colors
        pai: {
          primary: '#3b82f6',    // Bright blue
          secondary: '#8b5cf6',  // Purple
          accent: '#ec4899',     // Pink
          dark: '#0f172a',       // Dark slate
          light: '#f8fafc',      // Light slate
        }
      },
      fontFamily: {
        sans: ['var(--font-inter)'],
      },
    },
  },
  plugins: [],
} satisfies Config

export default config
```

### 3. Setup shadcn/ui Components

```bash
# Add commonly needed components for PAI dashboard
pnpm dlx shadcn-ui@latest add button
pnpm dlx shadcn-ui@latest add card
pnpm dlx shadcn-ui@latest add input
pnpm dlx shadcn-ui@latest add textarea
pnpm dlx shadcn-ui@latest add select
pnpm dlx shadcn-ui@latest add dialog
pnpm dlx shadcn-ui@latest add dropdown-menu
pnpm dlx shadcn-ui@latest add tabs
pnpm dlx shadcn-ui@latest add avatar
pnpm dlx shadcn-ui@latest add badge
pnpm dlx shadcn-ui@latest add progress
pnpm dlx shadcn-ui@latest add tooltip
pnpm dlx shadcn-ui@latest add toast
pnpm dlx shadcn-ui@latest add scroll-area
```

### 4. Environment Configuration

Create `.env.local`:

```env
# API Integration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Backend Security
API_SECRET_KEY=your-secret-key-from-phase2
API_TIMEOUT=30000

# NextAuth.js v5
NEXTAUTH_SECRET=generate-with-openssl-rand-base64-32
NEXTAUTH_URL=http://localhost:3000

# Optional Services
TELEGRAM_BOT_TOKEN=your-telegram-token
GITHUB_CLIENT_ID=your-github-id
GITHUB_CLIENT_SECRET=your-github-secret
```

---

## Architecture with shadcn/ui

### Component Structure

```typescript
// components/ui/ - shadcn/ui components (generated, don't modify)
// components/PAI/  - Custom PAI components using shadcn/ui

// Example: Chat component using shadcn/ui Button
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Send } from 'lucide-react'

export function ChatInput() {
  const [message, setMessage] = useState('')

  return (
    <Card className="p-4">
      <div className="flex gap-2">
        <Input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          className="flex-1"
        />
        <Button size="icon" variant="default">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </Card>
  )
}
```

### Color System with Tailwind v4

```typescript
// Use PAI theme colors
<div className="bg-pai-primary text-pai-light">Primary</div>
<div className="bg-pai-secondary text-pai-light">Secondary</div>
<div className="bg-pai-accent text-white">Accent</div>

// Responsive with Tailwind v4
<div className="md:flex lg:grid-cols-3 dark:bg-pai-dark">
  Responsive content
</div>
```

### Icons with Lucide React

```typescript
import {
  MessageSquare,
  Brain,
  Zap,
  Settings,
  LogOut,
  Menu
} from 'lucide-react'

export function Navigation() {
  return (
    <nav className="flex gap-4">
      <button><MessageSquare className="w-5 h-5" /></button>
      <button><Brain className="w-5 h-5" /></button>
      <button><Zap className="w-5 h-5" /></button>
      <button><Settings className="w-5 h-5" /></button>
    </nav>
  )
}
```

---

## Project Structure

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


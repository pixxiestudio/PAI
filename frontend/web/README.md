# PAI Dashboard - Phase 3 Web Interface

Modern Next.js 14+ web dashboard for the Personal AI Instance (PAI) project.

## Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript 5
- **UI Library**: shadcn/ui (Radix primitives + Tailwind CSS)
- **Icons**: Lucide React
- **State Management**: TanStack Query + Zustand
- **Authentication**: NextAuth.js v5
- **Styling**: Tailwind CSS v4
- **Package Manager**: pnpm

## Quick Start

### Prerequisites

- Node.js 18+
- pnpm 8+

### Installation

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start
```

The dashboard will be available at `http://localhost:3000`

## Environment Variables

Copy `.env.example` to `.env.local` and update:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
API_SECRET_KEY=your-api-secret-key
NEXTAUTH_SECRET=your-nextauth-secret
```

## Project Structure

```
app/
  api/
    proxy/[...path]/      # API proxy routes
  layout.tsx              # Root layout with providers
  page.tsx                # Home page
  globals.css             # Global styles
  providers.tsx           # React Query provider

hooks/
  useChat.ts              # Chat management hook
  useMemory.ts            # Memory management hook
  useLearning.ts          # Learning patterns hook

lib/
  api-client.ts           # API client wrapper

components/
  ui/                     # shadcn/ui components (auto-generated)
  PAI/                    # Custom PAI components
```

## API Endpoints

The frontend connects to the Phase 2 backend API through `/api/proxy`:

- `GET /sessions` - List chat sessions
- `POST /sessions` - Create new session
- `GET /sessions/{id}/messages` - Get session messages
- `POST /sessions/{id}/messages` - Send message
- `GET /users/{id}/memories` - Get user memories
- `POST /users/{id}/memories` - Save memory
- `GET /pai/{id}/learning` - Get learning report
- `GET /pai/{id}/skills` - List available skills

## Features (Phase 3.1 - Foundation)

- ✅ Next.js 14+ setup with TypeScript
- ✅ Tailwind CSS v4 styling
- ✅ API proxy for secure authentication
- ✅ TanStack Query for data fetching
- ✅ Custom hooks for chat, memory, learning
- ✅ Home page with system status
- 🔄 Chat interface (coming in Phase 3.2)
- 🔄 Memory browser (coming in Phase 3.2)
- 🔄 Learning dashboard (coming in Phase 3.2)

## Development

### Creating Components with shadcn/ui

```bash
# Add a new component
pnpm dlx shadcn-ui@latest add button
pnpm dlx shadcn-ui@latest add card
pnpm dlx shadcn-ui@latest add input
```

### Testing

```bash
# Run tests
pnpm test

# E2E testing
pnpm test:e2e
```

### Build

```bash
# Production build
pnpm build

# Check bundle size
pnpm build --analyze
```

## Deployment

### Vercel (Recommended)

```bash
npm i -g vercel
vercel
```

### Docker

```bash
docker build -t pai-dashboard .
docker run -p 3000:3000 pai-dashboard
```

### Node.js

```bash
NODE_ENV=production pnpm start
```

## Documentation

See [PHASE_3_NEXTJS_GUIDE.md](../../docs/PHASE_3_NEXTJS_GUIDE.md) for comprehensive implementation guide.

## Contributing

1. Create feature branches from `main`
2. Make changes with TypeScript strict mode
3. Test before committing
4. Follow the existing code style

## License

Part of the PAI project.

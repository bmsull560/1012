# ValueVerse Frontend

Next.js-based frontend application for the ValueVerse Platform.

## Technology Stack

- **Framework**: Next.js 14 (App Router)
- **UI Library**: React 18 + TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand (global) + React Query (server state)
- **Real-time**: Socket.io-client
- **Charts**: Recharts + D3.js
- **Forms**: React Hook Form + Zod validation
- **Animation**: Framer Motion

## Project Structure

```
frontend/
├── src/
│   ├── app/                       # Next.js 14 App Router
│   │   ├── (auth)/                # Auth-protected routes
│   │   │   ├── layout.tsx
│   │   │   ├── pre-sales/         # Value Architect workspace
│   │   │   ├── sales/             # Value Committer workspace
│   │   │   ├── delivery/          # Value Executor workspace
│   │   │   └── success/           # Value Amplifier workspace
│   │   ├── (public)/              # Public routes
│   │   │   ├── login/
│   │   │   └── signup/
│   │   ├── api/                   # API routes (if needed)
│   │   ├── layout.tsx             # Root layout
│   │   └── page.tsx               # Home page
│   │
│   ├── components/                # React components
│   │   ├── ui/                    # shadcn/ui base components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   └── ...
│   │   │
│   │   ├── workspace/             # Unified Workspace components
│   │   │   ├── LeftBrain.tsx      # Conversational UI
│   │   │   ├── RightBrain.tsx     # Interactive Canvas
│   │   │   ├── AgentThread.tsx    # Chat interface
│   │   │   ├── ThoughtStream.tsx  # Agent reasoning display
│   │   │   └── Canvas.tsx         # Adaptive canvas
│   │   │
│   │   ├── value/                 # Value-specific components
│   │   │   ├── ValueDriverCard.tsx
│   │   │   ├── ROIChart.tsx
│   │   │   ├── ValueTimeline.tsx
│   │   │   └── MetricsPanel.tsx
│   │   │
│   │   ├── templates/             # Value visualization templates
│   │   │   ├── ImpactCascade.tsx
│   │   │   ├── TrinityDashboard.tsx
│   │   │   ├── StoryArcCanvas.tsx
│   │   │   ├── ScenarioMatrix.tsx
│   │   │   └── QuantumView.tsx
│   │   │
│   │   └── shared/                # Shared components
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── ErrorBoundary.tsx
│   │
│   ├── lib/                       # Utilities and configurations
│   │   ├── api.ts                 # API client
│   │   ├── websocket.ts           # WebSocket client
│   │   ├── utils.ts               # Helper functions
│   │   └── cn.ts                  # Class name utility
│   │
│   ├── hooks/                     # Custom React hooks
│   │   ├── useAgent.ts            # Agent interaction hook
│   │   ├── useValueGraph.ts       # Value graph operations
│   │   ├── useWebSocket.ts        # Real-time connection
│   │   └── useAdaptiveUI.ts       # Adaptive interface logic
│   │
│   ├── store/                     # Zustand stores
│   │   ├── workspace.ts           # Workspace state
│   │   ├── user.ts                # User preferences
│   │   └── valueGraph.ts          # Value graph cache
│   │
│   ├── types/                     # TypeScript types
│   │   ├── agent.ts
│   │   ├── value.ts
│   │   ├── workspace.ts
│   │   └── api.ts
│   │
│   └── styles/                    # Global styles
│       └── globals.css
│
├── public/                        # Static assets
│   ├── images/
│   └── icons/
│
├── tests/                         # Test suite
│   ├── components/
│   ├── hooks/
│   └── e2e/                       # Playwright E2E tests
│
├── .env.local.example             # Environment variables template
├── next.config.js                 # Next.js configuration
├── tailwind.config.js             # Tailwind CSS configuration
├── tsconfig.json                  # TypeScript configuration
├── package.json                   # Dependencies
└── README.md                      # This file
```

## Getting Started

### Prerequisites

- Node.js 22+ (LTS recommended)
- npm, pnpm, or yarn

### Installation

1. **Install dependencies**:

```bash
npm install
# or
pnpm install
# or
yarn install
```

2. **Set up environment variables**:

```bash
cp .env.local.example .env.local
# Edit .env.local with your configuration
```

3. **Run the development server**:

```bash
npm run dev
# or
pnpm dev
# or
yarn dev
```

4. **Open your browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Development

### Available Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Format code
npm run format

# Run tests
npm test

# Run E2E tests
npm run test:e2e

# Type check
npm run type-check
```

### Code Quality

```bash
# Format with Prettier
npm run format

# Lint with ESLint
npm run lint

# Fix linting issues
npm run lint:fix

# Type checking
npm run type-check
```

## Architecture

### Unified Workspace

The core of the ValueVerse UI is the **Unified Workspace**, which implements a dual-brain interface:

```tsx
<UnifiedWorkspace>
  <LeftBrain>
    {/* Conversational AI interface */}
    <AgentThread />
    <ThoughtStream />
    <InputField />
  </LeftBrain>

  <RightBrain>
    {/* Interactive Canvas */}
    <AdaptiveCanvas>
      {/* Dynamic component rendering based on template */}
      {renderTemplate(activeTemplate)}
    </AdaptiveCanvas>
  </RightBrain>
</UnifiedWorkspace>
```

### State Management

- **Zustand**: Global client-side state (workspace, user preferences)
- **React Query**: Server state, caching, and synchronization
- **WebSocket**: Real-time bidirectional updates

```typescript
// Example: Workspace store
import { create } from "zustand";

interface WorkspaceState {
  leftBrain: {
    messages: Message[];
    thinking: boolean;
  };
  rightBrain: {
    components: Component[];
    activeTemplate: ValueTemplate;
  };
  // Actions
  addMessage: (message: Message) => void;
  updateCanvas: (components: Component[]) => void;
}

export const useWorkspace = create<WorkspaceState>(/* ... */);
```

### Adaptive UI Levels

The interface adapts to user expertise:

1. **Guided Mode** (Beginner): Simplified with extensive tooltips
2. **Hybrid Mode** (Intermediate): Balanced view with all features
3. **Power Mode** (Expert): Dense, keyboard-driven interface

```typescript
// Hook to detect and adapt to user level
const { level, setLevel } = useAdaptiveUI()

// Components adjust based on level
{level === 'guided' && <TooltipSystem />}
{level === 'power' && <KeyboardShortcuts />}
```

### Real-time Synchronization

WebSocket connection ensures < 100ms updates:

```typescript
// WebSocket hook
const { sendMessage, subscribe } = useWebSocket();

// Subscribe to value graph updates
useEffect(() => {
  return subscribe("value_graph_update", (data) => {
    updateValueGraph(data);
  });
}, []);
```

## Styling

### Tailwind CSS + shadcn/ui

We use Tailwind CSS for utility-first styling and shadcn/ui for component primitives:

```tsx
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

<Card className="p-6">
  <Button variant="primary" size="lg">
    Build Value Model
  </Button>
</Card>;
```

### Theme Configuration

Theme is configured in `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          /* ... */
        },
        secondary: {
          /* ... */
        },
      },
    },
  },
};
```

## Testing

### Unit Tests (Jest + React Testing Library)

```bash
# Run all tests
npm test

# Run specific test
npm test -- ValueDriverCard

# Coverage report
npm test -- --coverage
```

### E2E Tests (Playwright)

```bash
# Run E2E tests
npm run test:e2e

# Run in headed mode
npm run test:e2e -- --headed

# Run specific test
npm run test:e2e -- tests/workspace.spec.ts
```

## Environment Variables

Key environment variables (see `.env.local.example`):

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_ENV=development
```

## Performance Optimization

### Target Metrics

- First Contentful Paint: < 1.5s
- Time to Interactive: < 3.5s
- Canvas update latency: < 100ms
- Agent response display: < 500ms

### Optimization Techniques

- ✅ Server-side rendering with Next.js App Router
- ✅ Code splitting and lazy loading
- ✅ Image optimization with next/image
- ✅ React Query for efficient data caching
- ✅ WebSocket for real-time updates (no polling)
- ✅ Memoization of expensive calculations

## Accessibility

- ✅ WCAG 2.1 AA compliance
- ✅ Keyboard navigation throughout
- ✅ Screen reader support
- ✅ Focus management
- ✅ Semantic HTML

## Security

- ✅ XSS prevention (React auto-escaping)
- ✅ CSRF tokens for mutations
- ✅ Content Security Policy headers
- ✅ Secure authentication flow
- ✅ Input validation with Zod

## Documentation

- Design specification: `/docs/design_brief.md`
- UX patterns: `/docs/operatingsystem.md`
- Component library: Run Storybook (TBD)

## Contributing

See the main project README and follow the established patterns in this codebase.

---

**Status**: 🚧 Under Development

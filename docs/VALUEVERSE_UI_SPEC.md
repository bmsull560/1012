# ValueVerse Enterprise UI Specification

## Overview
ValueVerse is a B2B Value Realization Operating System that transforms customer relationships through the Dual-Brain Architecture.

## Core Components Required

### 1. Living Value Graph Canvas (Priority: CRITICAL)
**Description**: Interactive D3.js/Recharts visualization showing customer value realization in real-time.

**Features**:
- Node-based graph visualization of value streams
- Real-time updates via WebSocket
- Drag-and-drop node positioning
- Zoom/pan controls
- Connection lines showing value dependencies
- Animated value flow indicators
- Click to expand node details
- Multi-tenant support with workspace isolation

**User Stories**:
- As a CSM, I want to see customer value in real-time to proactively address issues
- As an Executive, I want bird's-eye view of portfolio value health
- As a Sales Rep, I want to visualize potential value to close deals faster

**Technical Requirements**:
- D3.js for graph visualization
- WebSocket for real-time updates
- Zustand for state management
- React Query for API data
- Touch-optimized for tablets
- Accessible with keyboard navigation

### 2. Dual-Brain Layout (Priority: CRITICAL)
**Description**: Split-screen interface with AI Chat (left) and Value Canvas (right).

**Features**:
- Resizable panels with drag handle
- Responsive collapse on mobile
- Synchronized state between panels
- AI suggestions trigger canvas highlights
- Canvas selections populate chat context

**Layout**:
```
┌─────────────────────────────────────┐
│         Top Navigation Bar          │
├──────────────┬──────────────────────┤
│              │                      │
│   AI Chat    │   Value Canvas       │
│   (Left)     │   (Right)            │
│              │                      │
│  - Messages  │  - Graph Viz         │
│  - Input     │  - Controls          │
│  - History   │  - Details Panel     │
│              │                      │
└──────────────┴──────────────────────┘
```

### 3. Agentic Command Center (Priority: HIGH)
**Description**: AI agent orchestration dashboard showing Four-Agent Symphony in action.

**Agents**:
1. **Architect Agent**: Plans value initiatives
2. **Committer Agent**: Tracks commitments
3. **Executor Agent**: Monitors execution
4. **Amplifier Agent**: Identifies expansion opportunities

**Features**:
- Real-time agent status indicators
- Agent-generated insights feed
- Manual agent triggering
- Agent collaboration visualization
- Decision audit trail

### 4. Value Metrics Dashboard (Priority: HIGH)
**Description**: Executive dashboard with KPIs, trends, and alerts.

**Metrics**:
- Total Value Realized ($$)
- Value Velocity (rate of change)
- Risk Score
- Health Score
- Time to Value
- Customer Satisfaction

**Visualizations**:
- Line charts for trends
- Gauge charts for scores
- Heat maps for risk
- Sparklines for quick insights

### 5. Progressive Disclosure Interface (Priority: MEDIUM)
**Description**: Adaptive UI that adjusts complexity based on user expertise.

**Modes**:
- **Beginner**: Guided workflows, tooltips, simplified views
- **Intermediate**: Full features with contextual help
- **Expert**: Dense information, keyboard shortcuts, power tools

**Implementation**:
- User profile stores expertise level
- UI components adapt rendering based on mode
- Smooth transitions between modes
- Progressive feature unlocking

### 6. Collaborative Workspace (Priority: MEDIUM)
**Description**: Multi-user real-time collaboration with presence indicators.

**Features**:
- User avatars showing who's viewing
- Cursor tracking for co-viewers
- Comment threads on graph nodes
- @mentions for notifications
- Activity feed
- Role-based permissions

### 7. Navigation & Search (Priority: HIGH)
**Description**: Global navigation with command palette and intelligent search.

**Features**:
- Top navigation bar with workspaces dropdown
- Cmd+K command palette
- Full-text search across all data
- AI-powered semantic search
- Recent items
- Favorites/bookmarks

## Design System

### Colors
- Primary: Blue (#0066CC)
- Secondary: Purple (#6B46C1)
- Success: Green (#10B981)
- Warning: Orange (#F59E0B)
- Danger: Red (#EF4444)
- Neutral: Gray scale

### Typography
- Headings: Inter (Bold)
- Body: Inter (Regular)
- Mono: JetBrains Mono

### Components (shadcn/ui)
- Button, Input, Select
- Dialog, Sheet, Popover
- Card, Table, Badge
- Toast, Alert, Progress
- Command, Tabs, Accordion

## Accessibility Requirements
- WCAG 2.1 AA compliance
- Keyboard navigation for all features
- Screen reader support with ARIA labels
- Focus management
- Color contrast ratios > 4.5:1
- Reduced motion support

## Performance Targets
- Initial load: < 2s
- Time to Interactive: < 3s
- Canvas rendering: 60 FPS
- WebSocket latency: < 100ms
- API response: < 500ms

## Security Requirements
- JWT authentication
- RBAC authorization
- CSRF protection
- XSS prevention
- Input validation
- Secure WebSocket (WSS)

## API Integration Points
- `/api/v1/graph/nodes` - Get graph data
- `/api/v1/graph/connections` - Get connections
- `/api/v1/agents/status` - Agent status
- `/api/v1/metrics` - Dashboard metrics
- `/api/v1/workspaces` - Workspace data
- `wss://api/v1/ws/{workspaceId}` - Real-time updates

## Technology Stack
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript 5.2+ (strict mode)
- **Styling**: Tailwind CSS 3.x
- **UI Components**: shadcn/ui
- **State Management**: Zustand (global), React Query (server)
- **Real-time**: WebSocket with auto-reconnect
- **Charts**: Recharts, D3.js
- **Animations**: Framer Motion
- **Forms**: React Hook Form + Zod
- **Testing**: Jest, React Testing Library, Playwright

## File Structure
```
frontend/src/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── signup/
│   ├── (dashboard)/
│   │   ├── workspace/[id]/
│   │   ├── metrics/
│   │   └── agents/
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── graph/
│   │   ├── ValueGraph.tsx
│   │   ├── GraphNode.tsx
│   │   └── GraphControls.tsx
│   ├── chat/
│   │   ├── ChatPanel.tsx
│   │   ├── MessageList.tsx
│   │   └── ChatInput.tsx
│   ├── agents/
│   │   ├── AgentDashboard.tsx
│   │   └── AgentCard.tsx
│   ├── metrics/
│   │   ├── MetricsDashboard.tsx
│   │   └── MetricCard.tsx
│   └── layout/
│       ├── DualBrainLayout.tsx
│       ├── Navigation.tsx
│       └── CommandPalette.tsx
├── hooks/
│   ├── useWebSocket.ts
│   ├── useGraph.ts
│   └── useAgents.ts
├── stores/
│   ├── workspaceStore.ts
│   ├── graphStore.ts
│   └── userStore.ts
├── lib/
│   ├── api.ts
│   ├── websocket.ts
│   └── utils.ts
└── types/
    ├── graph.ts
    ├── agent.ts
    └── metrics.ts
```

## Implementation Priority
1. **Phase 1**: Dual-Brain Layout + Navigation (Week 1)
2. **Phase 2**: Living Value Graph Canvas (Week 2-3)
3. **Phase 3**: AI Chat Integration (Week 4)
4. **Phase 4**: Agentic Command Center (Week 5)
5. **Phase 5**: Metrics Dashboard (Week 6)
6. **Phase 6**: Polish & Accessibility (Week 7-8)

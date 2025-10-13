import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface CanvasComponent {
  id: string;
  type: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  data: any;
}

interface WorkspaceState {
  // Canvas state
  activeTemplate: string;
  canvasComponents: CanvasComponent[];
  canvasMode: 'view' | 'edit';
  zoomLevel: number;
  
  // Chat state
  messages: Array<{
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
    agent?: string;
  }>;
  isThinking: boolean;
  
  // Agent state
  activeAgent: 'architect' | 'committer' | 'executor' | 'amplifier';
  agentContext: Record<string, any>;
  
  // Actions
  setActiveTemplate: (template: string) => void;
  updateCanvas: (components: CanvasComponent[]) => void;
  setCanvasMode: (mode: 'view' | 'edit') => void;
  setZoomLevel: (level: number) => void;
  addMessage: (message: any) => void;
  clearMessages: () => void;
  setIsThinking: (thinking: boolean) => void;
  setActiveAgent: (agent: 'architect' | 'committer' | 'executor' | 'amplifier') => void;
  updateAgentContext: (context: Record<string, any>) => void;
}

export const useWorkspaceStore = create<WorkspaceState>()(
  devtools(
    persist(
      (set) => ({
        // Initial state
        activeTemplate: 'impact_cascade',
        canvasComponents: [],
        canvasMode: 'view',
        zoomLevel: 1,
        messages: [],
        isThinking: false,
        activeAgent: 'architect',
        agentContext: {},
        
        // Actions
        setActiveTemplate: (template) => set({ activeTemplate: template }),
        updateCanvas: (components) => set({ canvasComponents: components }),
        setCanvasMode: (mode) => set({ canvasMode: mode }),
        setZoomLevel: (level) => set({ zoomLevel: level }),
        addMessage: (message) => set((state) => ({ 
          messages: [...state.messages, message] 
        })),
        clearMessages: () => set({ messages: [] }),
        setIsThinking: (thinking) => set({ isThinking: thinking }),
        setActiveAgent: (agent) => set({ activeAgent: agent }),
        updateAgentContext: (context) => set((state) => ({ 
          agentContext: { ...state.agentContext, ...context } 
        })),
      }),
      {
        name: 'workspace-storage',
        partialize: (state) => ({
          activeTemplate: state.activeTemplate,
          canvasMode: state.canvasMode,
          zoomLevel: state.zoomLevel,
          activeAgent: state.activeAgent,
        }),
      }
    )
  )
);

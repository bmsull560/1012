import { io, Socket } from 'socket.io-client';

export interface AgentMessage {
  id: string;
  agent: string;
  type: 'thinking' | 'response' | 'artifact' | 'handoff' | 'error';
  content: any;
  timestamp: Date;
  metadata?: {
    confidence?: number;
    reasoning?: string[];
    sources?: string[];
    processingTime?: number;
  };
}

export interface AgentHandoff {
  fromAgent: string;
  toAgent: string;
  context: any;
  reason: string;
  requiresApproval: boolean;
}

class WebSocketService {
  private socket: Socket | null = null;
  private listeners: Map<string, Set<Function>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(url: string = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000') {
    if (this.socket?.connected) {
      console.log('WebSocket already connected');
      return;
    }

    this.socket = io(url, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
    });

    this.setupEventHandlers();
  }

  private setupEventHandlers() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.emit('connection', { status: 'connected' });
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.emit('connection', { status: 'disconnected', reason });
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    });

    // Agent-specific events
    this.socket.on('agent:thinking', (data: AgentMessage) => {
      this.emit('agent:thinking', data);
    });

    this.socket.on('agent:response', (data: AgentMessage) => {
      this.emit('agent:response', data);
    });

    this.socket.on('agent:artifact', (data: AgentMessage) => {
      this.emit('agent:artifact', data);
    });

    this.socket.on('agent:handoff', (data: AgentHandoff) => {
      this.emit('agent:handoff', data);
    });

    this.socket.on('agent:error', (data: AgentMessage) => {
      this.emit('agent:error', data);
    });

    // Value model events
    this.socket.on('value:update', (data: any) => {
      this.emit('value:update', data);
    });

    this.socket.on('value:milestone', (data: any) => {
      this.emit('value:milestone', data);
    });

    // Progress events
    this.socket.on('progress:update', (data: any) => {
      this.emit('progress:update', data);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  // Send message to agent
  sendToAgent(agent: string, message: string, context?: any) {
    if (!this.socket?.connected) {
      console.error('WebSocket not connected');
      return;
    }

    this.socket.emit('agent:message', {
      agent,
      message,
      context,
      timestamp: new Date(),
    });
  }

  // Request agent handoff
  requestHandoff(fromAgent: string, toAgent: string, context: any) {
    if (!this.socket?.connected) {
      console.error('WebSocket not connected');
      return;
    }

    this.socket.emit('agent:handoff:request', {
      fromAgent,
      toAgent,
      context,
      timestamp: new Date(),
    });
  }

  // Approve or reject handoff
  respondToHandoff(handoffId: string, approved: boolean, reason?: string) {
    if (!this.socket?.connected) {
      console.error('WebSocket not connected');
      return;
    }

    this.socket.emit('agent:handoff:response', {
      handoffId,
      approved,
      reason,
      timestamp: new Date(),
    });
  }

  // Create value model
  createValueModel(data: any) {
    if (!this.socket?.connected) {
      console.error('WebSocket not connected');
      return;
    }

    this.socket.emit('value:create', data);
  }

  // Update value model
  updateValueModel(modelId: string, updates: any) {
    if (!this.socket?.connected) {
      console.error('WebSocket not connected');
      return;
    }

    this.socket.emit('value:update', {
      modelId,
      updates,
      timestamp: new Date(),
    });
  }

  // Subscribe to events
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)?.add(callback);
  }

  // Unsubscribe from events
  off(event: string, callback: Function) {
    this.listeners.get(event)?.delete(callback);
  }

  // Emit events to local listeners
  private emit(event: string, data: any) {
    this.listeners.get(event)?.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in event listener for ${event}:`, error);
      }
    });
  }

  // Check connection status
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  // Get socket instance (for advanced usage)
  getSocket(): Socket | null {
    return this.socket;
  }
}

// Singleton instance
const wsService = new WebSocketService();
export default wsService;

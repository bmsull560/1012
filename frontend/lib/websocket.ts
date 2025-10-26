/**
 * Secure WebSocket Manager
 * Implements secure WebSocket connections with proper authentication
 */

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: string;
  [key: string]: any;
}

export interface WebSocketConfig {
  url: string;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  debug?: boolean;
}

export type WebSocketEventHandler = (message: WebSocketMessage) => void;
export type WebSocketErrorHandler = (error: Event) => void;
export type WebSocketStatusHandler = (status: 'connecting' | 'connected' | 'disconnected' | 'error') => void;

export class SecureWebSocketManager {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private reconnectAttempts = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private messageHandlers: Map<string, WebSocketEventHandler[]> = new Map();
  private errorHandlers: WebSocketErrorHandler[] = [];
  private statusHandlers: WebSocketStatusHandler[] = [];
  private isIntentionallyClosed = false;

  constructor(config: WebSocketConfig) {
    this.config = {
      url: config.url,
      reconnect: config.reconnect ?? true,
      reconnectInterval: config.reconnectInterval ?? 1000,
      maxReconnectAttempts: config.maxReconnectAttempts ?? 5,
      heartbeatInterval: config.heartbeatInterval ?? 30000,
      debug: config.debug ?? false,
    };
  }

  /**
   * Connect to WebSocket server
   * Uses WSS in production for encrypted connection
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.log('Already connected');
      return;
    }

    this.isIntentionallyClosed = false;
    
    // Ensure WSS in production
    let wsUrl = this.config.url;
    if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
      wsUrl = wsUrl.replace(/^ws:/, 'wss:');
    }

    this.log(`Connecting to ${wsUrl}`);
    this.updateStatus('connecting');

    try {
      this.ws = new WebSocket(wsUrl);
      this.setupEventHandlers();
    } catch (error) {
      this.log('Connection error:', error);
      this.handleError(error as Event);
      this.attemptReconnect();
    }
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      this.log('Connected');
      this.reconnectAttempts = 0;
      this.updateStatus('connected');
      
      // Send authentication message
      this.sendAuthMessage();
      
      // Start heartbeat
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        this.handleMessage(message);
      } catch (error) {
        this.log('Failed to parse message:', error);
      }
    };

    this.ws.onerror = (error) => {
      this.log('WebSocket error:', error);
      this.updateStatus('error');
      this.handleError(error);
    };

    this.ws.onclose = (event) => {
      this.log('Disconnected:', event.code, event.reason);
      this.updateStatus('disconnected');
      this.stopHeartbeat();
      
      if (!this.isIntentionallyClosed && this.config.reconnect) {
        this.attemptReconnect();
      }
    };
  }

  /**
   * Send authentication message after connection
   * Token is sent in message body, not URL
   */
  private sendAuthMessage(): void {
    // Authentication is handled via HttpOnly cookies
    // Send a simple auth message to trigger server-side validation
    this.send({
      type: 'auth',
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({
          type: 'ping',
          timestamp: new Date().toISOString(),
        });
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.log('Max reconnection attempts reached');
      this.updateStatus('error');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1),
      30000 // Max 30 seconds
    );

    this.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Send message through WebSocket
   */
  send(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      this.log('Cannot send message: WebSocket not connected');
    }
  }

  /**
   * Handle incoming message
   */
  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(message.type) || [];
    handlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        this.log('Error in message handler:', error);
      }
    });

    // Also call wildcard handlers
    const wildcardHandlers = this.messageHandlers.get('*') || [];
    wildcardHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        this.log('Error in wildcard handler:', error);
      }
    });
  }

  /**
   * Handle error
   */
  private handleError(error: Event): void {
    this.errorHandlers.forEach(handler => {
      try {
        handler(error);
      } catch (err) {
        this.log('Error in error handler:', err);
      }
    });
  }

  /**
   * Update connection status
   */
  private updateStatus(status: 'connecting' | 'connected' | 'disconnected' | 'error'): void {
    this.statusHandlers.forEach(handler => {
      try {
        handler(status);
      } catch (error) {
        this.log('Error in status handler:', error);
      }
    });
  }

  /**
   * Subscribe to messages of a specific type
   */
  on(type: string, handler: WebSocketEventHandler): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    
    this.messageHandlers.get(type)!.push(handler);
    
    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(type);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      }
    };
  }

  /**
   * Subscribe to errors
   */
  onError(handler: WebSocketErrorHandler): () => void {
    this.errorHandlers.push(handler);
    
    return () => {
      const index = this.errorHandlers.indexOf(handler);
      if (index > -1) {
        this.errorHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Subscribe to status changes
   */
  onStatus(handler: WebSocketStatusHandler): () => void {
    this.statusHandlers.push(handler);
    
    return () => {
      const index = this.statusHandlers.indexOf(handler);
      if (index > -1) {
        this.statusHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    this.isIntentionallyClosed = true;
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    this.stopHeartbeat();
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    
    this.messageHandlers.clear();
    this.errorHandlers = [];
    this.statusHandlers = [];
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get connection state
   */
  getState(): 'connecting' | 'open' | 'closing' | 'closed' {
    if (!this.ws) return 'closed';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'open';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'closed';
      default:
        return 'closed';
    }
  }

  /**
   * Log message (only in debug mode)
   */
  private log(...args: any[]): void {
    if (this.config.debug) {
      console.log('[SecureWebSocket]', ...args);
    }
  }
}

/**
 * Create a secure WebSocket connection
 */
export function createSecureWebSocket(config: WebSocketConfig): SecureWebSocketManager {
  return new SecureWebSocketManager(config);
}

// API Service Layer - Connects to the existing FastAPI backend
import { ValueModelData } from '@/components/value-model/ValueModelReport';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

// Token management
let accessToken: string | null = null;
let refreshToken: string | null = null;

// Set tokens from auth
export function setTokens(access: string, refresh?: string) {
  accessToken = access;
  if (refresh) refreshToken = refresh;
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', access);
    if (refresh) localStorage.setItem('refresh_token', refresh);
  }
}

// Get stored tokens
export function getTokens() {
  if (!accessToken && typeof window !== 'undefined') {
    accessToken = localStorage.getItem('access_token');
    refreshToken = localStorage.getItem('refresh_token');
  }
  return { accessToken, refreshToken };
}

// Clear tokens (logout)
export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
}

// Base fetch wrapper with auth
async function fetchWithAuth(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const { accessToken } = getTokens();
  
  const headers = {
    'Content-Type': 'application/json',
    ...(accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle token refresh if needed (401)
  if (response.status === 401 && refreshToken) {
    // TODO: Implement token refresh logic
    // For now, redirect to login
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  return response;
}

// =====================================================
// Authentication API
// =====================================================

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user?: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    tenant_id: string;
  };
}

export const authAPI = {
  // Login with email and password
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const formData = new FormData();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    setTokens(data.access_token);
    return data;
  },

  // Get current user
  async getCurrentUser() {
    const response = await fetchWithAuth('/api/v1/auth/me', {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error('Failed to get user');
    }

    return response.json();
  },

  // Logout
  async logout() {
    clearTokens();
    // TODO: Call backend logout endpoint if needed
  },
};

// =====================================================
// Value Models API
// =====================================================

export interface ValueModelCreate {
  name: string;
  description?: string;
  company_id?: string;
  target_value?: number;
  hypothesis: {
    company_name: string;
    industry: string;
    inputs: Record<string, number>;
    selectedDrivers: string[];
  };
}

export interface ValueModel {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  stage: string;
  status: string;
  target_value?: number;
  realized_value: number;
  confidence_score: number;
  hypothesis?: any; // Stores the model context and calculations
  created_at: string;
  updated_at: string;
}

export const valueModelsAPI = {
  // Create a new value model
  async create(model: ValueModelCreate): Promise<ValueModel> {
    const response = await fetchWithAuth('/api/v1/value-models', {
      method: 'POST',
      body: JSON.stringify(model),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create value model');
    }

    return response.json();
  },

  // List value models
  async list(filters?: { stage?: string; status?: string }): Promise<ValueModel[]> {
    const params = new URLSearchParams();
    if (filters?.stage) params.append('stage', filters.stage);
    if (filters?.status) params.append('status', filters.status);

    const response = await fetchWithAuth(`/api/v1/value-models?${params}`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error('Failed to list value models');
    }

    return response.json();
  },

  // Get a specific value model
  async get(modelId: string): Promise<ValueModel> {
    const response = await fetchWithAuth(`/api/v1/value-models/${modelId}`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error('Failed to get value model');
    }

    return response.json();
  },

  // Update a value model
  async update(modelId: string, updates: Partial<ValueModelCreate>): Promise<ValueModel> {
    const response = await fetchWithAuth(`/api/v1/value-models/${modelId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      throw new Error('Failed to update value model');
    }

    return response.json();
  },

  // Delete a value model
  async delete(modelId: string): Promise<void> {
    const response = await fetchWithAuth(`/api/v1/value-models/${modelId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete value model');
    }
  },

  // Export value model
  async export(modelId: string, format: 'pdf' | 'ppt' | 'excel'): Promise<Blob> {
    const response = await fetchWithAuth(`/api/v1/value-models/${modelId}/export?format=${format}`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to export value model as ${format}`);
    }

    return response.blob();
  },
};

// =====================================================
// WebSocket Connection for Agents
// =====================================================

export interface AgentMessage {
  type: 'agent:message' | 'agent:response' | 'agent:handoff' | 'agent:handoff:request' | 'value:update';
  agent?: string;
  message?: string;
  content?: string;
  context?: any;
  timestamp?: string;
  metadata?: {
    confidence?: number;
    reasoning?: string[];
    processingTime?: number;
  };
}

class WebSocketManager {
  private ws: WebSocket | null = null;
  private clientId: string | null = null;
  private messageHandlers: ((message: AgentMessage) => void)[] = [];
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  // Connect to WebSocket
  connect(clientId: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.clientId = clientId;
    const { accessToken } = getTokens();
    const wsUrl = `${WS_BASE_URL}/ws/${clientId}${accessToken ? `?token=${accessToken}` : ''}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      this.attemptReconnect();
    }
  }

  // Attempt to reconnect
  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

    this.reconnectTimeout = setTimeout(() => {
      console.log(`Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
      if (this.clientId) {
        this.connect(this.clientId);
      }
    }, delay);
  }

  // Send message through WebSocket
  send(message: AgentMessage) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not connected');
    }
  }

  // Handle incoming messages
  private handleMessage(message: AgentMessage) {
    this.messageHandlers.forEach(handler => handler(message));
  }

  // Subscribe to messages
  onMessage(handler: (message: AgentMessage) => void) {
    this.messageHandlers.push(handler);
    return () => {
      this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
    };
  }

  // Disconnect WebSocket
  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.messageHandlers = [];
    this.reconnectAttempts = 0;
  }

  // Get connection status
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsManager = new WebSocketManager();

// =====================================================
// Agent API
// =====================================================

export const agentAPI = {
  // Send message to agent
  async sendMessage(
    agent: string,
    message: string,
    context?: any
  ): Promise<void> {
    wsManager.send({
      type: 'agent:message',
      agent,
      message,
      context,
      timestamp: new Date().toISOString(),
    });
  },

  // Request agent handoff
  async requestHandoff(
    fromAgent: string,
    toAgent: string,
    context?: any
  ): Promise<void> {
    wsManager.send({
      type: 'agent:handoff:request',
      agent: fromAgent,
      context: {
        ...context,
        fromAgent,
        toAgent,
      },
      timestamp: new Date().toISOString(),
    });
  },

  // Subscribe to agent messages
  onMessage(handler: (message: AgentMessage) => void) {
    return wsManager.onMessage(handler);
  },

  // Connect to agent WebSocket
  connect(userId: string, tenantId?: string) {
    const clientId = tenantId ? `${tenantId}-${userId}` : userId;
    wsManager.connect(clientId);
  },

  // Disconnect from agent WebSocket
  disconnect() {
    wsManager.disconnect();
  },
};

// =====================================================
// Company Research API (if implemented in backend)
// =====================================================

export const companyAPI = {
  // Search for companies
  async search(query: string): Promise<any[]> {
    const response = await fetchWithAuth(`/api/v1/companies/search?q=${encodeURIComponent(query)}`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error('Failed to search companies');
    }

    return response.json();
  },

  // Get company details
  async getDetails(companyId: string): Promise<any> {
    const response = await fetchWithAuth(`/api/v1/companies/${companyId}`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error('Failed to get company details');
    }

    return response.json();
  },

  // Enrich company data from website
  async enrichFromWebsite(website: string): Promise<any> {
    const response = await fetchWithAuth('/api/v1/companies/enrich', {
      method: 'POST',
      body: JSON.stringify({ website }),
    });

    if (!response.ok) {
      throw new Error('Failed to enrich company data');
    }

    return response.json();
  },
};

// =====================================================
// Health Check
// =====================================================

export async function checkHealth(): Promise<{
  status: string;
  services: {
    database: string;
    cache: string;
    websocket: string;
  };
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    return response.json();
  } catch (error) {
    return {
      status: 'unhealthy',
      services: {
        database: 'unknown',
        cache: 'unknown',
        websocket: 'unknown',
      },
    };
  }
}

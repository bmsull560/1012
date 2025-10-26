// API Service Layer - Connects to the existing FastAPI backend
import { ValueModelData } from '@/components/value-model/ValueModelReport';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

// Token management - Now handled via HttpOnly cookies
// Tokens are no longer stored in localStorage for security

// Note: Tokens are now managed server-side via HttpOnly cookies
// This prevents XSS attacks from stealing authentication tokens

// Get CSRF token from cookie
function getCsrfToken(): string | null {
  if (typeof document === 'undefined') {
    return null;
  }
  
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrf_token_client') {
      return decodeURIComponent(value);
    }
  }
  
  return null;
}

// Base fetch wrapper with auth
// Tokens are automatically sent via HttpOnly cookies
async function fetchWithAuth(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add CSRF token for state-changing requests
  if (options.method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
  }

  let response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include', // Include HttpOnly cookies
  });

  // Handle token refresh if needed (401)
  if (response.status === 401) {
    // Try to refresh token
    const refreshResponse = await fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    });

    if (refreshResponse.ok) {
      // Retry original request with new token
      response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
        credentials: 'include',
      });
    } else {
      // Refresh failed, redirect to login
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
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
  // Now uses Next.js API route that sets HttpOnly cookies
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Login failed');
    }

    const data = await response.json();
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
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    });
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

// Import secure WebSocket manager
import { SecureWebSocketManager, createSecureWebSocket } from '@/lib/websocket';

class WebSocketManager {
  private wsManager: SecureWebSocketManager | null = null;
  private clientId: string | null = null;

  // Connect to WebSocket
  connect(clientId: string) {
    if (this.wsManager?.isConnected()) {
      return;
    }

    this.clientId = clientId;
    
    // Create secure WebSocket connection
    // Automatically uses WSS in production
    const wsUrl = `${WS_BASE_URL}/ws/${clientId}`;
    
    this.wsManager = createSecureWebSocket({
      url: wsUrl,
      reconnect: true,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
      debug: process.env.NODE_ENV === 'development',
    });

    // Connect
    this.wsManager.connect();
  }

  // Send message through WebSocket
  send(message: AgentMessage) {
    if (this.wsManager?.isConnected()) {
      this.wsManager.send({
        ...message,
        timestamp: message.timestamp || new Date().toISOString(),
      });
    } else {
      console.error('WebSocket not connected');
    }
  }

  // Subscribe to messages
  onMessage(handler: (message: AgentMessage) => void) {
    if (!this.wsManager) {
      console.error('WebSocket manager not initialized');
      return () => {};
    }
    
    return this.wsManager.on('*', handler);
  }

  // Disconnect WebSocket
  disconnect() {
    if (this.wsManager) {
      this.wsManager.disconnect();
      this.wsManager = null;
    }
  }

  // Get connection status
  isConnected(): boolean {
    return this.wsManager?.isConnected() || false;
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

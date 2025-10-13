// Agent API Service - REST endpoints for agent communication
// This connects the frontend to the backend microservices

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Agent service endpoints
const AGENT_ENDPOINTS = {
  'value-architect': `${API_BASE}/api/v1/value-models`,
  'value-committer': `${API_BASE}/api/v1/commitments`, 
  'value-executor': `${API_BASE}/api/v1/executions`,
  'value-amplifier': `${API_BASE}/api/v1/amplifications`
};

// Direct service endpoints (for development)
const DIRECT_ENDPOINTS = {
  'value-architect': 'http://localhost:8011',
  'value-committer': 'http://localhost:8012',
  'value-executor': 'http://localhost:8013',
  'value-amplifier': 'http://localhost:8014'
};

export interface AgentResponse {
  id: string;
  agent: string;
  content: any;
  status: 'success' | 'error';
  metadata?: {
    processingTime?: number;
    confidence?: number;
  };
}

export class AgentApiService {
  private useDirectEndpoints = true; // Use direct endpoints for now

  private getEndpoint(agent: string): string {
    const endpoints = this.useDirectEndpoints ? DIRECT_ENDPOINTS : AGENT_ENDPOINTS;
    return endpoints[agent as keyof typeof endpoints] || AGENT_ENDPOINTS['value-architect'];
  }

  async sendMessage(agent: string, message: string, context?: any): Promise<AgentResponse> {
    const endpoint = this.getEndpoint(agent);
    
    try {
      const response = await fetch(`${endpoint}/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          context,
          company_name: context?.company_name || 'Demo Company',
          industry: context?.industry || 'SaaS',
          company_size: context?.company_size || 'mid-market'
        })
      });

      if (!response.ok) {
        throw new Error(`Agent ${agent} returned ${response.status}`);
      }

      const data = await response.json();
      
      return {
        id: data.id || crypto.randomUUID(),
        agent,
        content: data,
        status: 'success',
        metadata: {
          processingTime: data.processing_time,
          confidence: data.confidence
        }
      };
    } catch (error) {
      console.error(`Error communicating with ${agent}:`, error);
      
      // Fallback to mock response for demo
      return this.getMockResponse(agent, message, context);
    }
  }

  async createValueModel(data: any): Promise<any> {
    try {
      const response = await fetch(`${DIRECT_ENDPOINTS['value-architect']}/api/v1/value-models`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        throw new Error(`Failed to create value model: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating value model:', error);
      // Return mock data for demo
      return this.getMockValueModel(data);
    }
  }

  async getHealth(agent: string): Promise<boolean> {
    const endpoint = this.getEndpoint(agent);
    
    try {
      const response = await fetch(`${endpoint}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  private getMockResponse(agent: string, message: string, context?: any): AgentResponse {
    const responses: Record<string, any> = {
      'value-architect': {
        value_drivers: [
          {
            name: 'Process Automation',
            potential_value: 250000,
            confidence: 0.85
          },
          {
            name: 'Customer Retention',
            potential_value: 180000,
            confidence: 0.75
          }
        ],
        total_potential: 430000,
        key_metrics: ['Time to Value: 3 months', 'ROI: 320%']
      },
      'value-committer': {
        commitment_id: crypto.randomUUID(),
        milestones: [
          { name: 'Phase 1', target_date: '2024-03-01', value: 100000 },
          { name: 'Phase 2', target_date: '2024-06-01', value: 150000 }
        ],
        contract_value: 250000
      },
      'value-executor': {
        execution_status: 'on_track',
        completed_tasks: 12,
        pending_tasks: 8,
        current_value_delivered: 75000
      },
      'value-amplifier': {
        success_stories: 3,
        references_generated: 5,
        expansion_opportunities: 2,
        amplification_score: 8.5
      }
    };

    return {
      id: crypto.randomUUID(),
      agent,
      content: responses[agent] || { message: 'Agent is processing your request...' },
      status: 'success',
      metadata: {
        processingTime: Math.random() * 2000 + 500,
        confidence: Math.random() * 0.3 + 0.7
      }
    };
  }

  private getMockValueModel(data: any) {
    return {
      id: crypto.randomUUID(),
      company_name: data.company_name,
      industry: data.industry,
      value_drivers: [
        {
          id: 'automation',
          name: 'Process Automation',
          category: 'efficiency',
          potential_value: 250000,
          effort_required: 'medium',
          time_to_value: 3
        },
        {
          id: 'retention',
          name: 'Customer Retention',
          category: 'growth',
          potential_value: 180000,
          effort_required: 'low',
          time_to_value: 1
        }
      ],
      total_potential_value: 430000,
      implementation_timeline: 6,
      confidence_score: 0.82,
      created_at: new Date().toISOString()
    };
  }
}

export const agentApi = new AgentApiService();

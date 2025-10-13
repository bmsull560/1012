import { useState, useCallback } from 'react';
import { agentApi } from '@/services/agentApi';

export interface AgentMessage {
  id: string;
  agent: string;
  type: 'user' | 'agent' | 'thinking';
  content: any;
  timestamp: Date;
}

interface UseAgentApiReturn {
  isConnected: boolean;
  isProcessing: boolean;
  currentThought: string | null;
  messages: AgentMessage[];
  artifacts: any[];
  sendMessage: (message: string, context?: any) => Promise<void>;
  clearMessages: () => void;
}

export function useAgentApi(agentName: string): UseAgentApiReturn {
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentThought, setCurrentThought] = useState<string | null>(null);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [artifacts, setArtifacts] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(true); // Assume connected for REST

  const sendMessage = useCallback(async (message: string, context?: any) => {
    // Add user message
    const userMessage: AgentMessage = {
      id: crypto.randomUUID(),
      agent: agentName,
      type: 'user',
      content: message,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    // Show thinking state
    setIsProcessing(true);
    setCurrentThought(`${agentName} is analyzing your request...`);

    try {
      // Call the REST API
      const response = await agentApi.sendMessage(agentName, message, context);
      
      // Add agent response
      const agentMessage: AgentMessage = {
        id: response.id,
        agent: agentName,
        type: 'agent',
        content: response.content,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, agentMessage]);
      
      // Store artifacts if present
      if (response.content.artifacts) {
        setArtifacts(prev => [...prev, ...response.content.artifacts]);
      }
    } catch (error) {
      console.error('Error sending message to agent:', error);
      
      // Add error message
      const errorMessage: AgentMessage = {
        id: crypto.randomUUID(),
        agent: agentName,
        type: 'agent',
        content: {
          error: 'Failed to process request. Please try again.',
          details: error
        },
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
      setCurrentThought(null);
    }
  }, [agentName]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setArtifacts([]);
  }, []);

  return {
    isConnected,
    isProcessing,
    currentThought,
    messages,
    artifacts,
    sendMessage,
    clearMessages
  };
}

// Export for backwards compatibility with existing code
export const useAgent = useAgentApi;

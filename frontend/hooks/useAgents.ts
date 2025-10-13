import { useEffect, useState, useCallback, useRef } from 'react';
import wsService, { AgentMessage, AgentHandoff } from '@/services/websocket';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: any) => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  messages: AgentMessage[];
  sendToAgent: (agent: string, message: string, context?: any) => void;
  requestHandoff: (fromAgent: string, toAgent: string, context: any) => void;
  respondToHandoff: (handoffId: string, approved: boolean, reason?: string) => void;
  clearMessages: () => void;
  subscribe: (event: string, callback: Function) => () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    autoConnect = true,
    onConnect,
    onDisconnect,
    onError
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const handlersRef = useRef<Map<string, Function>>(new Map());

  useEffect(() => {
    if (!autoConnect) return;

    // Connect to WebSocket
    wsService.connect();

    // Connection handlers
    const handleConnection = (data: { status: string; reason?: string }) => {
      const connected = data.status === 'connected';
      setIsConnected(connected);
      if (connected) {
        onConnect?.();
      } else {
        onDisconnect?.();
      }
    };

    const handleError = (error: any) => {
      console.error('WebSocket error:', error);
      onError?.(error);
    };

    // Agent message handlers
    const handleAgentThinking = (data: AgentMessage) => {
      setMessages(prev => [...prev, { ...data, type: 'thinking' }]);
    };

    const handleAgentResponse = (data: AgentMessage) => {
      setMessages(prev => [...prev, { ...data, type: 'response' }]);
    };

    const handleAgentArtifact = (data: AgentMessage) => {
      setMessages(prev => [...prev, { ...data, type: 'artifact' }]);
    };

    const handleAgentError = (data: AgentMessage) => {
      setMessages(prev => [...prev, { ...data, type: 'error' }]);
    };

    // Subscribe to events
    wsService.on('connection', handleConnection);
    wsService.on('error', handleError);
    wsService.on('agent:thinking', handleAgentThinking);
    wsService.on('agent:response', handleAgentResponse);
    wsService.on('agent:artifact', handleAgentArtifact);
    wsService.on('agent:error', handleAgentError);

    // Store handlers for cleanup
    handlersRef.current.set('connection', handleConnection);
    handlersRef.current.set('error', handleError);
    handlersRef.current.set('agent:thinking', handleAgentThinking);
    handlersRef.current.set('agent:response', handleAgentResponse);
    handlersRef.current.set('agent:artifact', handleAgentArtifact);
    handlersRef.current.set('agent:error', handleAgentError);

    // Check initial connection status
    setIsConnected(wsService.isConnected());

    return () => {
      // Cleanup event handlers
      handlersRef.current.forEach((handler, event) => {
        wsService.off(event, handler);
      });
      handlersRef.current.clear();
    };
  }, [autoConnect, onConnect, onDisconnect, onError]);

  const sendToAgent = useCallback((agent: string, message: string, context?: any) => {
    wsService.sendToAgent(agent, message, context);
  }, []);

  const requestHandoff = useCallback((fromAgent: string, toAgent: string, context: any) => {
    wsService.requestHandoff(fromAgent, toAgent, context);
  }, []);

  const respondToHandoff = useCallback((handoffId: string, approved: boolean, reason?: string) => {
    wsService.respondToHandoff(handoffId, approved, reason);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const subscribe = useCallback((event: string, callback: Function) => {
    wsService.on(event, callback);
    return () => wsService.off(event, callback);
  }, []);

  return {
    isConnected,
    messages,
    sendToAgent,
    requestHandoff,
    respondToHandoff,
    clearMessages,
    subscribe
  };
}

// Hook for agent-specific interactions
export function useAgent(agentName: string) {
  const { isConnected, messages, sendToAgent, subscribe } = useWebSocket();
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentThought, setCurrentThought] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<any[]>([]);

  useEffect(() => {
    const unsubThinking = subscribe('agent:thinking', (data: AgentMessage) => {
      if (data.agent === agentName) {
        setIsProcessing(true);
        setCurrentThought(data.content);
      }
    });

    const unsubResponse = subscribe('agent:response', (data: AgentMessage) => {
      if (data.agent === agentName) {
        setIsProcessing(false);
        setCurrentThought(null);
      }
    });

    const unsubArtifact = subscribe('agent:artifact', (data: AgentMessage) => {
      if (data.agent === agentName) {
        setArtifacts(prev => [...prev, data.content]);
      }
    });

    return () => {
      unsubThinking();
      unsubResponse();
      unsubArtifact();
    };
  }, [agentName, subscribe]);

  const sendMessage = useCallback((message: string, context?: any) => {
    sendToAgent(agentName, message, context);
  }, [agentName, sendToAgent]);

  const agentMessages = messages.filter(m => m.agent === agentName);

  return {
    isConnected,
    isProcessing,
    currentThought,
    messages: agentMessages,
    artifacts,
    sendMessage
  };
}

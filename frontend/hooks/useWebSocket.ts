import { useEffect, useState, useCallback, useRef } from 'react';
import io, { Socket } from 'socket.io-client';
import { useAuthStore } from '@/stores/authStore';

interface UseWebSocketReturn {
  socket: Socket | null;
  connected: boolean;
  connecting: boolean;
  error: string | null;
  sendMessage: (event: string, data: any) => void;
  disconnect: () => void;
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

    }
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    setTimeout(() => connect(), 100);
  }, [connect, disconnect]);

  const sendMessage = useCallback((event: string, data: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    } else {
      console.warn('Cannot send message: WebSocket not connected');
      setError('Not connected to server');
    }
  }, []);

  // Auto-connect on mount if authenticated
  useEffect(() => {
    if (token && user) {
      const socket = connect();
      
      return () => {
        socket?.disconnect();
      };
    }
  }, [token, user, connect]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    socket,
    connected,
    connecting,
    error,
    sendMessage,
    disconnect,
    reconnect,
  };
}

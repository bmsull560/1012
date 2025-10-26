"use client";

import React, { createContext, useContext, useEffect, useState } from 'react';
import { authAPI, agentAPI } from '@/services/api';

interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  tenant_id?: string;
  role_id?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error?: string }>;
  signUp: (email: string, password: string) => Promise<{ error?: string }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signIn: async () => ({ error: 'Not implemented' }),
  signUp: async () => ({ error: 'Not implemented' }),
  signOut: async () => {},
});

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    // Tokens are now in HttpOnly cookies, so we just try to get current user
    const checkUser = async () => {
      try {
        const currentUser = await authAPI.getCurrentUser();
        if (currentUser) {
          setUser(currentUser);
          // Connect to WebSocket for agent communication
          agentAPI.connect(currentUser.id, currentUser.tenant_id);
          
          // Start automatic token refresh
          const { startTokenRefresh } = await import('@/lib/token-refresh');
          await startTokenRefresh({
            onTokenExpired: () => {
              // Token expired, log out user
              signOut();
            },
          });
        }
      } catch (error) {
        const { logger } = await import('@/lib/logger');
        logger.error('Error checking auth', { error });
      } finally {
        setLoading(false);
      }
    };

    checkUser();

    // Cleanup on unmount
    return () => {
      agentAPI.disconnect();
    };
  }, []);

  const signIn = async (email: string, password: string): Promise<{ error?: string }> => {
    try {
      const response = await authAPI.login({ email, password });
      
      if (response.access_token) {
        // Get user details after successful login
        const userData = await authAPI.getCurrentUser();
        setUser(userData);
        
        // Connect to WebSocket for agent communication
        if (userData) {
          agentAPI.connect(userData.id, userData.tenant_id);
        }
        
        return {};
      }
      
      return { error: 'Login failed' };
    } catch (err: any) {
      const { logger } = await import('@/lib/logger');
      logger.error('Sign in error', { error: err });
      return { error: err.message || 'Sign in failed' };
    }
  };

  const signUp = async (email: string, password: string): Promise<{ error?: string }> => {
    // Note: Sign up needs to be implemented in your backend
    // For now, we'll redirect to sign in
    try {
      // TODO: Call backend signup endpoint when available
      // const response = await authAPI.signup({ email, password });
      return { error: 'Sign up not yet implemented. Please contact admin for account creation.' };
    } catch (err: any) {
      const { logger } = await import('@/lib/logger');
      logger.error('Sign up error', { error: err });
      return { error: err.message || 'Sign up failed' };
    }
  };

  const signOut = async () => {
    try {
      await authAPI.logout();
      agentAPI.disconnect();
      setUser(null);
      
      // Stop token refresh
      const { stopTokenRefresh } = await import('@/lib/token-refresh');
      stopTokenRefresh();
    } catch (error) {
      const { logger } = await import('@/lib/logger');
      logger.error('Sign out error', { error });
    }
  };

  const value = {
    user,
    loading,
    signIn,
    signUp,
    signOut,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

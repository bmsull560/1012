"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { AlertTriangle, Clock } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

interface SessionTimeoutProps {
  warningTime?: number; // Minutes before timeout to show warning
  timeoutDuration?: number; // Total session timeout in minutes
}

export const SessionTimeout: React.FC<SessionTimeoutProps> = ({
  warningTime = 5,
  timeoutDuration = 30,
}) => {
  const { signOut } = useAuth();
  const [showWarning, setShowWarning] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(timeoutDuration * 60);
  const [lastActivity, setLastActivity] = useState(Date.now());

  // Reset timer on user activity
  const resetTimer = useCallback(() => {
    setLastActivity(Date.now());
    setTimeRemaining(timeoutDuration * 60);
    setShowWarning(false);
  }, [timeoutDuration]);

  // Track user activity
  useEffect(() => {
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];
    
    const handleActivity = () => {
      const now = Date.now();
      const timeSinceLastActivity = (now - lastActivity) / 1000;
      
      // Only reset if it's been more than 1 second since last activity
      if (timeSinceLastActivity > 1) {
        resetTimer();
      }
    };

    events.forEach(event => {
      document.addEventListener(event, handleActivity);
    });

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleActivity);
      });
    };
  }, [lastActivity, resetTimer]);

  // Countdown timer
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const elapsed = (now - lastActivity) / 1000; // seconds
      const remaining = (timeoutDuration * 60) - elapsed;
      
      setTimeRemaining(Math.max(0, remaining));
      
      // Show warning when time is running out
      if (remaining <= warningTime * 60 && remaining > 0) {
        setShowWarning(true);
      }
      
      // Auto logout when time expires
      if (remaining <= 0) {
        handleTimeout();
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [lastActivity, timeoutDuration, warningTime]);

  const handleTimeout = async () => {
    setShowWarning(false);
    await signOut();
    // Show timeout message
    if (typeof window !== 'undefined') {
      window.location.href = '/login?timeout=true';
    }
  };

  const extendSession = () => {
    resetTimer();
    // Call backend to refresh token
    fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    });
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!showWarning) return null;

  return (
    <div className="fixed bottom-4 right-4 max-w-sm bg-white border border-orange-200 rounded-lg shadow-lg p-4 z-50">
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <AlertTriangle className="w-6 h-6 text-orange-500" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 mb-1">
            Session Expiring Soon
          </h3>
          <p className="text-sm text-gray-600 mb-3">
            Your session will expire in {formatTime(timeRemaining)} due to inactivity.
          </p>
          <div className="flex items-center space-x-2">
            <button
              onClick={extendSession}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
            >
              Stay Logged In
            </button>
            <button
              onClick={handleTimeout}
              className="px-3 py-1 border border-gray-300 text-gray-700 text-sm rounded hover:bg-gray-50 transition-colors"
            >
              Log Out
            </button>
          </div>
        </div>
      </div>
      <div className="mt-3 bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          className="h-full bg-orange-500 transition-all duration-1000"
          style={{
            width: `${(timeRemaining / (warningTime * 60)) * 100}%`,
          }}
        />
      </div>
    </div>
  );
};

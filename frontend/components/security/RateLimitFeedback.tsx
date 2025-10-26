"use client";

import React, { useState, useEffect } from 'react';
import { AlertCircle, Clock, Shield } from 'lucide-react';

interface RateLimitInfo {
  limited: boolean;
  retryAfter?: number; // seconds
  limit?: number;
  remaining?: number;
  reset?: number; // timestamp
}

export const RateLimitFeedback: React.FC = () => {
  const [rateLimitInfo, setRateLimitInfo] = useState<RateLimitInfo | null>(null);
  const [countdown, setCountdown] = useState(0);

  // Listen for rate limit events
  useEffect(() => {
    const handleRateLimit = (event: CustomEvent<RateLimitInfo>) => {
      setRateLimitInfo(event.detail);
      if (event.detail.retryAfter) {
        setCountdown(event.detail.retryAfter);
      }
    };

    window.addEventListener('rateLimit' as any, handleRateLimit);
    
    return () => {
      window.removeEventListener('rateLimit' as any, handleRateLimit);
    };
  }, []);

  // Countdown timer
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
      
      return () => clearTimeout(timer);
    } else if (countdown === 0 && rateLimitInfo?.limited) {
      // Reset when countdown reaches 0
      setRateLimitInfo(null);
    }
  }, [countdown, rateLimitInfo]);

  // Intercept 429 responses globally
  useEffect(() => {
    const originalFetch = window.fetch;
    
    window.fetch = async (...args) => {
      const response = await originalFetch(...args);
      
      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After');
        const rateLimitLimit = response.headers.get('X-RateLimit-Limit');
        const rateLimitRemaining = response.headers.get('X-RateLimit-Remaining');
        const rateLimitReset = response.headers.get('X-RateLimit-Reset');
        
        const event = new CustomEvent('rateLimit', {
          detail: {
            limited: true,
            retryAfter: retryAfter ? parseInt(retryAfter) : 60,
            limit: rateLimitLimit ? parseInt(rateLimitLimit) : undefined,
            remaining: rateLimitRemaining ? parseInt(rateLimitRemaining) : 0,
            reset: rateLimitReset ? parseInt(rateLimitReset) : undefined,
          },
        });
        
        window.dispatchEvent(event);
      }
      
      return response;
    };
    
    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  if (!rateLimitInfo?.limited) return null;

  return (
    <div className="fixed top-4 right-4 max-w-md bg-red-50 border border-red-200 rounded-lg shadow-lg p-4 z-50">
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <Shield className="w-6 h-6 text-red-500" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-red-900 mb-1">
            Rate Limit Exceeded
          </h3>
          <p className="text-sm text-red-700 mb-2">
            You've made too many requests. Please wait before trying again.
          </p>
          
          {countdown > 0 && (
            <div className="flex items-center space-x-2 text-sm text-red-600">
              <Clock className="w-4 h-4" />
              <span>
                Retry in {Math.floor(countdown / 60)}:{(countdown % 60).toString().padStart(2, '0')}
              </span>
            </div>
          )}
          
          {rateLimitInfo.limit && (
            <div className="mt-2 text-xs text-red-600">
              Limit: {rateLimitInfo.remaining || 0}/{rateLimitInfo.limit} requests
            </div>
          )}
        </div>
      </div>
      
      {countdown > 0 && (
        <div className="mt-3 bg-red-200 rounded-full h-2 overflow-hidden">
          <div
            className="h-full bg-red-500 transition-all duration-1000"
            style={{
              width: `${(countdown / (rateLimitInfo.retryAfter || 60)) * 100}%`,
            }}
          />
        </div>
      )}
    </div>
  );
};

// Helper hook to track rate limits
export function useRateLimit() {
  const [isLimited, setIsLimited] = useState(false);
  const [retryAfter, setRetryAfter] = useState(0);

  useEffect(() => {
    const handleRateLimit = (event: CustomEvent<RateLimitInfo>) => {
      setIsLimited(event.detail.limited);
      setRetryAfter(event.detail.retryAfter || 0);
    };

    window.addEventListener('rateLimit' as any, handleRateLimit);
    
    return () => {
      window.removeEventListener('rateLimit' as any, handleRateLimit);
    };
  }, []);

  return { isLimited, retryAfter };
}

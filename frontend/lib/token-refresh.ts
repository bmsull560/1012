/**
 * Token Refresh Manager
 * Handles automatic token refresh with retry logic and monitoring
 */

export interface TokenRefreshConfig {
  refreshEndpoint?: string;
  refreshBeforeExpiry?: number; // Seconds before expiry to refresh
  maxRetries?: number;
  retryDelay?: number;
  onRefreshSuccess?: () => void;
  onRefreshFailure?: (error: Error) => void;
  onTokenExpired?: () => void;
}

export class TokenRefreshManager {
  private config: Required<TokenRefreshConfig>;
  private refreshTimer: NodeJS.Timeout | null = null;
  private isRefreshing = false;
  private retryCount = 0;

  constructor(config: TokenRefreshConfig = {}) {
    this.config = {
      refreshEndpoint: config.refreshEndpoint || '/api/auth/refresh',
      refreshBeforeExpiry: config.refreshBeforeExpiry || 300, // 5 minutes
      maxRetries: config.maxRetries || 3,
      retryDelay: config.retryDelay || 5000, // 5 seconds
      onRefreshSuccess: config.onRefreshSuccess || (() => {}),
      onRefreshFailure: config.onRefreshFailure || (() => {}),
      onTokenExpired: config.onTokenExpired || (() => {}),
    };
  }

  /**
   * Start automatic token refresh
   * Schedules refresh based on token expiry time
   */
  async startAutoRefresh(): Promise<void> {
    // Stop any existing timer
    this.stopAutoRefresh();

    try {
      // Get token expiry time from server
      const expiryTime = await this.getTokenExpiryTime();
      
      if (!expiryTime) {
        console.warn('Could not determine token expiry time');
        return;
      }

      // Calculate when to refresh (before expiry)
      const now = Date.now();
      const refreshTime = expiryTime - (this.config.refreshBeforeExpiry * 1000);
      const delay = Math.max(0, refreshTime - now);

      console.log(`Token refresh scheduled in ${Math.round(delay / 1000)} seconds`);

      // Schedule refresh
      this.refreshTimer = setTimeout(async () => {
        await this.refreshToken();
      }, delay);
    } catch (error) {
      console.error('Failed to start auto refresh:', error);
    }
  }

  /**
   * Stop automatic token refresh
   */
  stopAutoRefresh(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * Manually refresh token
   */
  async refreshToken(): Promise<boolean> {
    if (this.isRefreshing) {
      console.log('Token refresh already in progress');
      return false;
    }

    this.isRefreshing = true;

    try {
      const response = await fetch(this.config.refreshEndpoint, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        console.log('Token refreshed successfully');
        this.retryCount = 0;
        this.config.onRefreshSuccess();
        
        // Schedule next refresh
        await this.startAutoRefresh();
        
        return true;
      } else if (response.status === 401) {
        // Refresh token expired or invalid
        console.error('Token refresh failed: Unauthorized');
        this.config.onTokenExpired();
        return false;
      } else {
        throw new Error(`Token refresh failed: ${response.status}`);
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      this.config.onRefreshFailure(error as Error);
      
      // Retry with exponential backoff
      if (this.retryCount < this.config.maxRetries) {
        this.retryCount++;
        const delay = this.config.retryDelay * Math.pow(2, this.retryCount - 1);
        
        console.log(`Retrying token refresh in ${delay}ms (attempt ${this.retryCount}/${this.config.maxRetries})`);
        
        setTimeout(async () => {
          await this.refreshToken();
        }, delay);
      } else {
        console.error('Max token refresh retries reached');
        this.config.onTokenExpired();
      }
      
      return false;
    } finally {
      this.isRefreshing = false;
    }
  }

  /**
   * Get token expiry time from server
   */
  private async getTokenExpiryTime(): Promise<number | null> {
    try {
      // This would call an endpoint that returns token info
      // For now, we'll estimate based on standard token lifetime
      // In production, the server should provide this info
      
      // Assume 15-minute access token
      return Date.now() + (15 * 60 * 1000);
    } catch (error) {
      console.error('Failed to get token expiry time:', error);
      return null;
    }
  }

  /**
   * Check if token needs refresh
   */
  async needsRefresh(): Promise<boolean> {
    const expiryTime = await this.getTokenExpiryTime();
    if (!expiryTime) return false;
    
    const now = Date.now();
    const timeUntilExpiry = expiryTime - now;
    const refreshThreshold = this.config.refreshBeforeExpiry * 1000;
    
    return timeUntilExpiry <= refreshThreshold;
  }
}

// Global token refresh manager instance
let tokenRefreshManager: TokenRefreshManager | null = null;

/**
 * Initialize token refresh manager
 */
export function initTokenRefresh(config?: TokenRefreshConfig): TokenRefreshManager {
  if (!tokenRefreshManager) {
    tokenRefreshManager = new TokenRefreshManager(config);
  }
  return tokenRefreshManager;
}

/**
 * Get token refresh manager instance
 */
export function getTokenRefreshManager(): TokenRefreshManager | null {
  return tokenRefreshManager;
}

/**
 * Start automatic token refresh
 */
export async function startTokenRefresh(config?: TokenRefreshConfig): Promise<void> {
  const manager = initTokenRefresh(config);
  await manager.startAutoRefresh();
}

/**
 * Stop automatic token refresh
 */
export function stopTokenRefresh(): void {
  if (tokenRefreshManager) {
    tokenRefreshManager.stopAutoRefresh();
  }
}

/**
 * Manually refresh token
 */
export async function refreshToken(): Promise<boolean> {
  if (!tokenRefreshManager) {
    tokenRefreshManager = new TokenRefreshManager();
  }
  return await tokenRefreshManager.refreshToken();
}

import { useEffect, useState } from 'react';
import { useTenantStore } from '@/stores/tenantStore';
import { useAuthStore } from '@/stores/authStore';
import { Tenant } from '@/types/tenant';

interface UseTenantReturn {
  tenant: Tenant | null;
  isLoading: boolean;
  error: string | null;
  switchTenant: (tenantId: string) => Promise<void>;
  canAccessTenant: (tenantId: string) => boolean;
  hasPermission: (resource: string, action: string) => boolean;
  isAdmin: boolean;
  isSuperAdmin: boolean;
}

export function useTenant(): UseTenantReturn {
  const { user } = useAuthStore();
  const { 
    currentTenant, 
    isLoading, 
    error,
    switchTenant: switchTenantStore,
    checkPermission,
  } = useTenantStore();
  
  const [isAdmin, setIsAdmin] = useState(false);
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);
  
  useEffect(() => {
    if (user) {
      setIsAdmin(user.role?.level >= 90);
      setIsSuperAdmin(user.role?.level >= 100);
    }
  }, [user]);
  
  const switchTenant = async (tenantId: string) => {
    try {
      await switchTenantStore(tenantId);
      
      // Update URL if using subdomain
      if (typeof window !== 'undefined') {
        const currentHost = window.location.hostname;
        const newSubdomain = currentTenant?.subdomain;
        
        if (newSubdomain && !currentHost.startsWith(newSubdomain)) {
          const newUrl = `${window.location.protocol}//${newSubdomain}.${currentHost.replace(/^[^.]+\./, '')}${window.location.pathname}`;
          window.location.href = newUrl;
        }
      }
    } catch (error) {
      console.error('Failed to switch tenant:', error);
      throw error;
    }
  };
  
  const canAccessTenant = (tenantId: string): boolean => {
    if (isSuperAdmin) return true;
    if (!user) return false;
    return user.tenantId === tenantId;
  };
  
  const hasPermission = (resource: string, action: string): boolean => {
    if (isSuperAdmin) return true;
    return checkPermission(resource, action);
  };
  
  return {
    tenant: currentTenant,
    isLoading,
    error,
    switchTenant,
    canAccessTenant,
    hasPermission,
    isAdmin,
    isSuperAdmin,
  };
}

// Hook for tenant-specific data fetching
export function useTenantData<T>(
  fetcher: (tenantId: string) => Promise<T>,
  dependencies: any[] = []
) {
  const { tenant } = useTenant();
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    if (!tenant) return;
    
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const result = await fetcher(tenant.id);
        setData(result);
      } catch (err) {
        setError(err.message || 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [tenant, ...dependencies]);
  
  return { data, loading, error, refetch: () => fetcher(tenant!.id) };
}

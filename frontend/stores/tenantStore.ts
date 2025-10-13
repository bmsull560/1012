import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { 
  Tenant, 
  User, 
  UserRole, 
  Permission, 
  AuditLog, 
  Invitation,
  TenantSubscription,
  TenantLimits 
} from '@/types/tenant';

interface TenantStore {
  // Current tenant context
  currentTenant: Tenant | null;
  tenants: Tenant[]; // For super admins managing multiple tenants
  
  // Users within current tenant
  users: User[];
  roles: UserRole[];
  invitations: Invitation[];
  
  // Audit logs
  auditLogs: AuditLog[];
  
  // Loading states
  isLoading: boolean;
  error: string | null;
  
  // Tenant management actions
  setCurrentTenant: (tenant: Tenant) => void;
  createTenant: (data: Partial<Tenant>) => Promise<Tenant>;
  updateTenant: (id: string, updates: Partial<Tenant>) => Promise<void>;
  deleteTenant: (id: string) => Promise<void>;
  switchTenant: (tenantId: string) => Promise<void>;
  
  // User management actions
  fetchUsers: () => Promise<void>;
  createUser: (userData: Partial<User>) => Promise<User>;
  updateUser: (userId: string, updates: Partial<User>) => Promise<void>;
  deleteUser: (userId: string) => Promise<void>;
  suspendUser: (userId: string, reason?: string) => Promise<void>;
  reactivateUser: (userId: string) => Promise<void>;
  
  // Role management
  createRole: (role: Partial<UserRole>) => Promise<UserRole>;
  updateRole: (roleId: string, updates: Partial<UserRole>) => Promise<void>;
  deleteRole: (roleId: string) => Promise<void>;
  assignRole: (userId: string, roleId: string) => Promise<void>;
  
  // Permission management
  grantPermission: (userId: string, permission: Permission) => Promise<void>;
  revokePermission: (userId: string, permissionId: string) => Promise<void>;
  checkPermission: (resource: string, action: string) => boolean;
  
  // Invitation management
  sendInvitation: (email: string, roleId: string) => Promise<void>;
  resendInvitation: (invitationId: string) => Promise<void>;
  revokeInvitation: (invitationId: string) => Promise<void>;
  acceptInvitation: (token: string) => Promise<void>;
  
  // Subscription management
  updateSubscription: (subscription: Partial<TenantSubscription>) => Promise<void>;
  upgradePlan: (plan: string) => Promise<void>;
  cancelSubscription: (reason?: string) => Promise<void>;
  
  // Usage tracking
  checkUsageLimits: () => TenantLimits | null;
  incrementUsage: (metric: keyof TenantLimits['currentUsage']) => void;
  
  // Audit logging
  logAction: (action: Partial<AuditLog>) => void;
  fetchAuditLogs: (filters?: any) => Promise<void>;
  
  // Utility functions
  clearError: () => void;
  reset: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const useTenantStore = create<TenantStore>()(
  persist(
    (set, get) => ({
      currentTenant: null,
      tenants: [],
      users: [],
      roles: [],
      invitations: [],
      auditLogs: [],
      isLoading: false,
      error: null,

      setCurrentTenant: (tenant) => {
        set({ currentTenant: tenant });
        // Set tenant context in API headers
        if (typeof window !== 'undefined') {
          localStorage.setItem('X-Tenant-ID', tenant.id);
        }
      },

      createTenant: async (data) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_URL}/api/v1/tenants`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
            body: JSON.stringify(data),
          });

          if (!response.ok) throw new Error('Failed to create tenant');
          
          const tenant = await response.json();
          set((state) => ({ 
            tenants: [...state.tenants, tenant],
            isLoading: false 
          }));
          
          get().logAction({
            action: 'tenant.create',
            resource: 'tenant',
            resourceId: tenant.id,
            status: 'success',
          });
          
          return tenant;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      updateTenant: async (id, updates) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_URL}/api/v1/tenants/${id}`, {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'X-Tenant-ID': get().currentTenant?.id || '',
            },
            body: JSON.stringify(updates),
          });

          if (!response.ok) throw new Error('Failed to update tenant');
          
          const updatedTenant = await response.json();
          set((state) => ({
            tenants: state.tenants.map(t => t.id === id ? updatedTenant : t),
            currentTenant: state.currentTenant?.id === id ? updatedTenant : state.currentTenant,
            isLoading: false,
          }));
          
          get().logAction({
            action: 'tenant.update',
            resource: 'tenant',
            resourceId: id,
            changes: updates,
            status: 'success',
          });
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      deleteTenant: async (id) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_URL}/api/v1/tenants/${id}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
          });

          if (!response.ok) throw new Error('Failed to delete tenant');
          
          set((state) => ({
            tenants: state.tenants.filter(t => t.id !== id),
            isLoading: false,
          }));
          
          get().logAction({
            action: 'tenant.delete',
            resource: 'tenant',
            resourceId: id,
            status: 'success',
          });
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      switchTenant: async (tenantId) => {
        const tenant = get().tenants.find(t => t.id === tenantId);
        if (tenant) {
          get().setCurrentTenant(tenant);
          await get().fetchUsers();
        }
      },

      fetchUsers: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_URL}/api/v1/users`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'X-Tenant-ID': get().currentTenant?.id || '',
            },
          });

          if (!response.ok) throw new Error('Failed to fetch users');
          
          const users = await response.json();
          set({ users, isLoading: false });
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      createUser: async (userData) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_URL}/api/v1/users`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'X-Tenant-ID': get().currentTenant?.id || '',
            },
            body: JSON.stringify({
              ...userData,
              tenantId: get().currentTenant?.id,
            }),
          });

          if (!response.ok) throw new Error('Failed to create user');
          
          const user = await response.json();
          set((state) => ({ 
            users: [...state.users, user],
            isLoading: false 
          }));
          
          get().logAction({
            action: 'user.create',
            resource: 'user',
            resourceId: user.id,
            status: 'success',
          });
          
          return user;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      updateUser: async (userId, updates) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_URL}/api/v1/users/${userId}`, {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'X-Tenant-ID': get().currentTenant?.id || '',
            },
            body: JSON.stringify(updates),
          });

          if (!response.ok) throw new Error('Failed to update user');
          
          const updatedUser = await response.json();
          set((state) => ({
            users: state.users.map(u => u.id === userId ? updatedUser : u),
            isLoading: false,
          }));
          
          get().logAction({
            action: 'user.update',
            resource: 'user',
            resourceId: userId,
            changes: updates,
            status: 'success',
          });
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      deleteUser: async (userId) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_URL}/api/v1/users/${userId}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'X-Tenant-ID': get().currentTenant?.id || '',
            },
          });

          if (!response.ok) throw new Error('Failed to delete user');
          
          set((state) => ({
            users: state.users.filter(u => u.id !== userId),
            isLoading: false,
          }));
          
          get().logAction({
            action: 'user.delete',
            resource: 'user',
            resourceId: userId,
            status: 'success',
          });
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      suspendUser: async (userId, reason) => {
        await get().updateUser(userId, { 
          status: 'suspended',
          metadata: { suspendReason: reason, suspendedAt: new Date() }
        });
      },

      reactivateUser: async (userId) => {
        await get().updateUser(userId, { 
          status: 'active',
          metadata: { reactivatedAt: new Date() }
        });
      },

      createRole: async (role) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_URL}/api/v1/roles`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'X-Tenant-ID': get().currentTenant?.id || '',
            },
            body: JSON.stringify({
              ...role,
              tenantId: get().currentTenant?.id,
            }),
          });

          if (!response.ok) throw new Error('Failed to create role');
          
          const newRole = await response.json();
          set((state) => ({ 
            roles: [...state.roles, newRole],
            isLoading: false 
          }));
          
          return newRole;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      updateRole: async (roleId, updates) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_URL}/api/v1/roles/${roleId}`, {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'X-Tenant-ID': get().currentTenant?.id || '',
            },
            body: JSON.stringify(updates),
          });

          if (!response.ok) throw new Error('Failed to update role');
          
          const updatedRole = await response.json();
          set((state) => ({
            roles: state.roles.map(r => r.id === roleId ? updatedRole : r),
            isLoading: false,
          }));
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      deleteRole: async (roleId) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_URL}/api/v1/roles/${roleId}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'X-Tenant-ID': get().currentTenant?.id || '',
            },
          });

          if (!response.ok) throw new Error('Failed to delete role');
          
          set((state) => ({
            roles: state.roles.filter(r => r.id !== roleId),
            isLoading: false,
          }));
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      assignRole: async (userId, roleId) => {
        const role = get().roles.find(r => r.id === roleId);
        if (role) {
          await get().updateUser(userId, { role });
        }
      },

      grantPermission: async (userId, permission) => {
        const user = get().users.find(u => u.id === userId);
        if (user) {
          await get().updateUser(userId, {
            permissions: [...user.permissions, permission],
          });
        }
      },

      revokePermission: async (userId, permissionId) => {
        const user = get().users.find(u => u.id === userId);
        if (user) {
          await get().updateUser(userId, {
            permissions: user.permissions.filter(p => p.id !== permissionId),
          });
        }
      },

      checkPermission: (resource, action) => {
        // This would typically check against the current user's permissions
        // For now, returning true for demo purposes
        return true;
      },

      sendInvitation: async (email, roleId) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_URL}/api/v1/invitations`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'X-Tenant-ID': get().currentTenant?.id || '',
            },
            body: JSON.stringify({
              email,
              roleId,
              tenantId: get().currentTenant?.id,
            }),
          });

          if (!response.ok) throw new Error('Failed to send invitation');
          
          const invitation = await response.json();
          set((state) => ({ 
            invitations: [...state.invitations, invitation],
            isLoading: false 
          }));
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      resendInvitation: async (invitationId) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_URL}/api/v1/invitations/${invitationId}/resend`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'X-Tenant-ID': get().currentTenant?.id || '',
            },
          });

          if (!response.ok) throw new Error('Failed to resend invitation');
          
          set({ isLoading: false });
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      revokeInvitation: async (invitationId) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_URL}/api/v1/invitations/${invitationId}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'X-Tenant-ID': get().currentTenant?.id || '',
            },
          });

          if (!response.ok) throw new Error('Failed to revoke invitation');
          
          set((state) => ({
            invitations: state.invitations.filter(i => i.id !== invitationId),
            isLoading: false,
          }));
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      acceptInvitation: async (token) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_URL}/api/v1/invitations/accept`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token }),
          });

          if (!response.ok) throw new Error('Failed to accept invitation');
          
          set({ isLoading: false });
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      updateSubscription: async (subscription) => {
        if (get().currentTenant) {
          await get().updateTenant(get().currentTenant!.id, { subscription });
        }
      },

      upgradePlan: async (plan) => {
        if (get().currentTenant) {
          await get().updateSubscription({ 
            plan: plan as any,
            status: 'active' 
          });
        }
      },

      cancelSubscription: async (reason) => {
        if (get().currentTenant) {
          await get().updateSubscription({ 
            status: 'canceled',
            canceledAt: new Date(),
          });
        }
      },

      checkUsageLimits: () => {
        return get().currentTenant?.limits || null;
      },

      incrementUsage: (metric) => {
        const tenant = get().currentTenant;
        if (tenant && tenant.limits.currentUsage[metric] !== undefined) {
          const newUsage = { ...tenant.limits.currentUsage };
          newUsage[metric]++;
          
          get().updateTenant(tenant.id, {
            limits: {
              ...tenant.limits,
              currentUsage: newUsage,
            },
          });
        }
      },

      logAction: (action) => {
        const log: AuditLog = {
          id: Date.now().toString(),
          tenantId: get().currentTenant?.id || '',
          userId: localStorage.getItem('userId') || '',
          action: action.action || '',
          resource: action.resource || '',
          resourceId: action.resourceId,
          changes: action.changes,
          ipAddress: '', // Would be set by backend
          userAgent: navigator.userAgent,
          timestamp: new Date(),
          status: action.status || 'success',
          errorMessage: action.errorMessage,
        };
        
        set((state) => ({
          auditLogs: [log, ...state.auditLogs].slice(0, 100), // Keep last 100 logs
        }));
        
        // Send to backend
        fetch(`${API_URL}/api/v1/audit-logs`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'X-Tenant-ID': get().currentTenant?.id || '',
          },
          body: JSON.stringify(log),
        }).catch(console.error);
      },

      fetchAuditLogs: async (filters) => {
        set({ isLoading: true, error: null });
        try {
          const params = new URLSearchParams(filters);
          const response = await fetch(`${API_URL}/api/v1/audit-logs?${params}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'X-Tenant-ID': get().currentTenant?.id || '',
            },
          });

          if (!response.ok) throw new Error('Failed to fetch audit logs');
          
          const logs = await response.json();
          set({ auditLogs: logs, isLoading: false });
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      clearError: () => set({ error: null }),

      reset: () => set({
        currentTenant: null,
        tenants: [],
        users: [],
        roles: [],
        invitations: [],
        auditLogs: [],
        isLoading: false,
        error: null,
      }),
    }),
    {
      name: 'tenant-storage',
      partialize: (state) => ({
        currentTenant: state.currentTenant,
      }),
    }
  )
);

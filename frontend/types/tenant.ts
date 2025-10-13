// Tenant and Multi-tenancy Types

export interface Tenant {
  id: string;
  name: string;
  slug: string; // URL-safe identifier
  domain: string; // Custom domain if configured
  subdomain: string; // Default subdomain
  logo?: string;
  primaryColor?: string;
  secondaryColor?: string;
  settings: TenantSettings;
  subscription: TenantSubscription;
  limits: TenantLimits;
  metadata: TenantMetadata;
  createdAt: Date;
  updatedAt: Date;
  status: TenantStatus;
}

export interface TenantSettings {
  allowSignup: boolean;
  requireEmailVerification: boolean;
  allowGoogleAuth: boolean;
  allowSAML: boolean;
  samlConfig?: SAMLConfig;
  passwordPolicy: PasswordPolicy;
  sessionTimeout: number; // minutes
  mfaRequired: boolean;
  ipWhitelist?: string[];
  customBranding: boolean;
  features: TenantFeatures;
}

export interface TenantFeatures {
  aiAgents: boolean;
  valueModeling: boolean;
  advancedAnalytics: boolean;
  customIntegrations: boolean;
  apiAccess: boolean;
  whiteLabeling: boolean;
  customReports: boolean;
  unlimitedUsers: boolean;
}

export interface TenantSubscription {
  plan: 'starter' | 'professional' | 'enterprise' | 'custom';
  status: 'active' | 'trialing' | 'past_due' | 'canceled' | 'suspended';
  currentPeriodStart: Date;
  currentPeriodEnd: Date;
  trialEndsAt?: Date;
  canceledAt?: Date;
  seats: number;
  monthlyPrice: number;
  billingEmail: string;
  paymentMethod?: PaymentMethod;
}

export interface TenantLimits {
  maxUsers: number;
  maxProjects: number;
  maxValueModels: number;
  maxApiCalls: number;
  maxStorageGB: number;
  maxMonthlyAgentCalls: number;
  currentUsage: {
    users: number;
    projects: number;
    valueModels: number;
    apiCalls: number;
    storageGB: number;
    agentCalls: number;
  };
}

export interface TenantMetadata {
  industry?: string;
  companySize?: string;
  country?: string;
  timezone?: string;
  language?: string;
  onboardingCompleted: boolean;
  lastActivityAt?: Date;
  tags?: string[];
}

export type TenantStatus = 'pending' | 'active' | 'suspended' | 'deleted';

export interface SAMLConfig {
  enabled: boolean;
  ssoUrl: string;
  issuer: string;
  certificate: string;
  signatureAlgorithm: string;
  attributeMapping: Record<string, string>;
}

export interface PasswordPolicy {
  minLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSpecialChars: boolean;
  preventReuse: number; // Number of previous passwords to check
  expirationDays?: number;
}

export interface PaymentMethod {
  type: 'card' | 'invoice' | 'ach';
  last4?: string;
  brand?: string;
  expiryMonth?: number;
  expiryYear?: number;
}

// User types with tenant context
export interface User {
  id: string;
  tenantId: string;
  email: string;
  firstName: string;
  lastName: string;
  avatar?: string;
  role: UserRole;
  permissions: Permission[];
  department?: string;
  title?: string;
  phone?: string;
  timezone?: string;
  language?: string;
  status: UserStatus;
  emailVerified: boolean;
  mfaEnabled: boolean;
  lastLoginAt?: Date;
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, any>;
}

export interface UserRole {
  id: string;
  name: string;
  description: string;
  level: number; // For hierarchy
  permissions: Permission[];
  isSystem: boolean; // Cannot be deleted
  tenantId?: string; // null for system roles
}

export interface Permission {
  id: string;
  resource: string;
  action: string;
  conditions?: Record<string, any>;
}

export type UserStatus = 'active' | 'inactive' | 'suspended' | 'pending';

// Predefined system roles
export const SYSTEM_ROLES = {
  SUPER_ADMIN: {
    name: 'Super Admin',
    level: 100,
    description: 'Full system access across all tenants',
  },
  TENANT_ADMIN: {
    name: 'Tenant Admin',
    level: 90,
    description: 'Full access within tenant',
  },
  MANAGER: {
    name: 'Manager',
    level: 70,
    description: 'Manage teams and projects',
  },
  USER: {
    name: 'User',
    level: 50,
    description: 'Standard user access',
  },
  VIEWER: {
    name: 'Viewer',
    level: 30,
    description: 'Read-only access',
  },
  GUEST: {
    name: 'Guest',
    level: 10,
    description: 'Limited guest access',
  },
};

// Permission resources and actions
export const PERMISSIONS = {
  TENANT: {
    resource: 'tenant',
    actions: ['create', 'read', 'update', 'delete', 'manage_billing', 'manage_settings'],
  },
  USER: {
    resource: 'user',
    actions: ['create', 'read', 'update', 'delete', 'suspend', 'manage_roles'],
  },
  PROJECT: {
    resource: 'project',
    actions: ['create', 'read', 'update', 'delete', 'share', 'export'],
  },
  VALUE_MODEL: {
    resource: 'value_model',
    actions: ['create', 'read', 'update', 'delete', 'approve', 'publish'],
  },
  AGENT: {
    resource: 'agent',
    actions: ['interact', 'configure', 'train', 'monitor'],
  },
  ANALYTICS: {
    resource: 'analytics',
    actions: ['view', 'export', 'create_report', 'schedule_report'],
  },
  API: {
    resource: 'api',
    actions: ['access', 'manage_keys', 'view_logs'],
  },
  BILLING: {
    resource: 'billing',
    actions: ['view', 'update_payment', 'change_plan', 'download_invoice'],
  },
};

// Audit log types
export interface AuditLog {
  id: string;
  tenantId: string;
  userId: string;
  action: string;
  resource: string;
  resourceId?: string;
  changes?: Record<string, any>;
  ipAddress: string;
  userAgent: string;
  timestamp: Date;
  status: 'success' | 'failure';
  errorMessage?: string;
}

// Invitation types
export interface Invitation {
  id: string;
  tenantId: string;
  email: string;
  role: string;
  invitedBy: string;
  invitedAt: Date;
  acceptedAt?: Date;
  expiresAt: Date;
  status: 'pending' | 'accepted' | 'expired' | 'revoked';
  token: string;
}

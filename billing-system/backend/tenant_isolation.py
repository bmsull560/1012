"""
Multi-Tenant Isolation System
Implements row-level security, data isolation, and tenant-aware queries
"""

import os
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum
import asyncpg
from sqlalchemy import event, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql import Select
from fastapi import HTTPException, status, Request
from pydantic import BaseModel, Field
import hashlib


class TenantIsolationLevel(str, Enum):
    """Levels of tenant isolation"""
    STRICT = "strict"  # Complete isolation, no cross-tenant access
    SHARED = "shared"  # Shared resources with access control
    GLOBAL = "global"  # Global resources accessible to all


class TenantContext(BaseModel):
    """Tenant context for requests"""
    tenant_id: UUID
    organization_id: UUID
    user_id: UUID
    roles: List[str] = []
    isolation_level: TenantIsolationLevel = TenantIsolationLevel.STRICT
    allowed_tenants: Set[UUID] = Field(default_factory=set)  # For multi-tenant users


class TenantIsolationSystem:
    """
    Multi-tenant isolation system with row-level security
    Ensures complete data isolation between tenants
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.db_pool: Optional[asyncpg.Pool] = None
        
        # Track current tenant context per request
        self._context_storage: Dict[str, TenantContext] = {}
        
        # Tables that require tenant isolation
        self.tenant_tables = {
            'users', 'invoices', 'payments', 'subscriptions',
            'billing_data', 'customer_data', 'api_keys',
            'audit_trail', 'documents', 'notifications'
        }
        
        # Tables that are shared across tenants
        self.shared_tables = {
            'roles', 'permissions', 'system_config',
            'feature_flags', 'pricing_plans'
        }
        
        # Sensitive columns that should be masked in cross-tenant queries
        self.sensitive_columns = {
            'ssn', 'tax_id', 'bank_account', 'credit_card',
            'api_secret', 'password_hash', 'encryption_key'
        }
    
    async def init(self):
        """Initialize tenant isolation system"""
        self.db_pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10
        )
        
        # Create tenant isolation schema
        await self._create_tenant_schema()
        
        # Setup SQLAlchemy query interceptors
        self._setup_query_interceptors()
    
    async def _create_tenant_schema(self):
        """Create tenant isolation database schema"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                -- Tenant management schema
                CREATE SCHEMA IF NOT EXISTS tenant_isolation;
                
                -- Tenants table
                CREATE TABLE IF NOT EXISTS tenant_isolation.tenants (
                    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    organization_id UUID NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    isolation_level VARCHAR(20) DEFAULT 'strict',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    metadata JSONB,
                    
                    -- Data limits per tenant
                    max_users INTEGER DEFAULT 100,
                    max_storage_gb INTEGER DEFAULT 100,
                    max_api_calls_per_month INTEGER DEFAULT 100000,
                    
                    -- Security settings
                    require_mfa BOOLEAN DEFAULT FALSE,
                    allowed_ip_ranges INET[],
                    blocked_countries VARCHAR(2)[],
                    
                    INDEX idx_org (organization_id),
                    INDEX idx_active (is_active)
                );
                
                -- Tenant access log
                CREATE TABLE IF NOT EXISTS tenant_isolation.access_log (
                    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL,
                    user_id UUID NOT NULL,
                    accessed_at TIMESTAMPTZ DEFAULT NOW(),
                    ip_address INET,
                    user_agent TEXT,
                    endpoint VARCHAR(255),
                    method VARCHAR(10),
                    status_code INTEGER,
                    cross_tenant_access BOOLEAN DEFAULT FALSE,
                    
                    INDEX idx_tenant (tenant_id),
                    INDEX idx_user (user_id),
                    INDEX idx_time (accessed_at)
                );
                
                -- Cross-tenant access permissions
                CREATE TABLE IF NOT EXISTS tenant_isolation.cross_tenant_access (
                    access_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    source_tenant_id UUID NOT NULL,
                    target_tenant_id UUID NOT NULL,
                    user_id UUID,
                    permission_type VARCHAR(50) NOT NULL,
                    resource_type VARCHAR(50),
                    granted_at TIMESTAMPTZ DEFAULT NOW(),
                    expires_at TIMESTAMPTZ,
                    granted_by UUID,
                    reason TEXT,
                    
                    UNIQUE(source_tenant_id, target_tenant_id, user_id, permission_type)
                );
                
                -- Row-level security policies function
                CREATE OR REPLACE FUNCTION tenant_isolation.get_current_tenant()
                RETURNS UUID AS $$
                BEGIN
                    -- Get tenant from session variable
                    RETURN current_setting('app.current_tenant_id', TRUE)::UUID;
                EXCEPTION
                    WHEN OTHERS THEN
                        RETURN NULL;
                END;
                $$ LANGUAGE plpgsql SECURITY DEFINER;
                
                -- Function to enforce tenant isolation
                CREATE OR REPLACE FUNCTION tenant_isolation.enforce_tenant_isolation()
                RETURNS TRIGGER AS $$
                BEGIN
                    -- For INSERT operations
                    IF TG_OP = 'INSERT' THEN
                        -- Ensure tenant_id is set
                        IF NEW.tenant_id IS NULL THEN
                            NEW.tenant_id := tenant_isolation.get_current_tenant();
                        END IF;
                        
                        -- Verify tenant matches current context
                        IF NEW.tenant_id != tenant_isolation.get_current_tenant() THEN
                            RAISE EXCEPTION 'Tenant isolation violation: Cannot insert data for different tenant';
                        END IF;
                    END IF;
                    
                    -- For UPDATE operations
                    IF TG_OP = 'UPDATE' THEN
                        -- Prevent changing tenant_id
                        IF OLD.tenant_id != NEW.tenant_id THEN
                            RAISE EXCEPTION 'Tenant isolation violation: Cannot change tenant_id';
                        END IF;
                        
                        -- Verify tenant matches current context
                        IF NEW.tenant_id != tenant_isolation.get_current_tenant() THEN
                            RAISE EXCEPTION 'Tenant isolation violation: Cannot update data for different tenant';
                        END IF;
                    END IF;
                    
                    -- For DELETE operations
                    IF TG_OP = 'DELETE' THEN
                        -- Verify tenant matches current context
                        IF OLD.tenant_id != tenant_isolation.get_current_tenant() THEN
                            RAISE EXCEPTION 'Tenant isolation violation: Cannot delete data for different tenant';
                        END IF;
                    END IF;
                    
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                
                -- Apply tenant isolation triggers to all tenant tables
                DO $$
                DECLARE
                    t_name TEXT;
                    tenant_tables TEXT[] := ARRAY[
                        'users', 'invoices', 'payments', 'subscriptions',
                        'billing_data', 'customer_data', 'api_keys'
                    ];
                BEGIN
                    FOREACH t_name IN ARRAY tenant_tables
                    LOOP
                        -- Check if table exists and has tenant_id column
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name = t_name 
                            AND column_name = 'tenant_id'
                        ) THEN
                            -- Drop existing trigger if exists
                            EXECUTE format('DROP TRIGGER IF EXISTS enforce_tenant_isolation ON %I', t_name);
                            
                            -- Create trigger
                            EXECUTE format(
                                'CREATE TRIGGER enforce_tenant_isolation 
                                BEFORE INSERT OR UPDATE OR DELETE ON %I 
                                FOR EACH ROW EXECUTE FUNCTION tenant_isolation.enforce_tenant_isolation()',
                                t_name
                            );
                        END IF;
                    END LOOP;
                END $$;
            """)
    
    def _setup_query_interceptors(self):
        """Setup SQLAlchemy query interceptors for automatic tenant filtering"""
        
        @event.listens_for(Query, "before_compile", propagate=True)
        def receive_before_compile(query, delete_context=None):
            """Automatically add tenant filter to queries"""
            # Get current tenant context
            tenant_context = self.get_current_context()
            if not tenant_context:
                return query
            
            # Check if query involves tenant-isolated tables
            for entity in query.column_descriptions:
                table_name = entity.get('type', '').__tablename__ if hasattr(entity.get('type', ''), '__tablename__') else ''
                
                if table_name in self.tenant_tables:
                    # Add tenant filter
                    if hasattr(entity['type'], 'tenant_id'):
                        query = query.filter(
                            entity['type'].tenant_id == tenant_context.tenant_id
                        )
            
            return query
    
    async def set_tenant_context(
        self,
        request: Request,
        tenant_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        roles: List[str] = None
    ):
        """Set tenant context for the current request"""
        # Create context
        context = TenantContext(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            roles=roles or []
        )
        
        # Check for cross-tenant access permissions
        if 'super_admin' in roles:
            context.isolation_level = TenantIsolationLevel.GLOBAL
            # Super admins can access all tenants
            context.allowed_tenants = set()  # Empty set means all
        else:
            # Check for specific cross-tenant permissions
            allowed = await self._get_allowed_tenants(user_id, tenant_id)
            context.allowed_tenants = allowed
            if allowed:
                context.isolation_level = TenantIsolationLevel.SHARED
        
        # Store context
        request_id = id(request)
        self._context_storage[str(request_id)] = context
        
        # Set database session variable
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "SET LOCAL app.current_tenant_id = $1",
                str(tenant_id)
            )
        
        # Log access
        await self._log_tenant_access(context, request)
    
    def get_current_context(self) -> Optional[TenantContext]:
        """Get current tenant context"""
        # In production, use proper request context management
        # This is simplified for demonstration
        if self._context_storage:
            return list(self._context_storage.values())[-1]
        return None
    
    async def validate_tenant_access(
        self,
        user_id: UUID,
        tenant_id: UUID,
        resource_type: str,
        action: str
    ) -> bool:
        """
        Validate if user can access tenant resources
        
        Args:
            user_id: User requesting access
            tenant_id: Target tenant
            resource_type: Type of resource
            action: Action to perform
            
        Returns:
            True if access allowed
        """
        context = self.get_current_context()
        if not context:
            return False
        
        # Check isolation level
        if context.isolation_level == TenantIsolationLevel.GLOBAL:
            return True  # Global access allowed
        
        # Check if accessing own tenant
        if context.tenant_id == tenant_id:
            return True
        
        # Check cross-tenant permissions
        if context.isolation_level == TenantIsolationLevel.SHARED:
            if not context.allowed_tenants or tenant_id in context.allowed_tenants:
                # Check specific permission
                return await self._check_cross_tenant_permission(
                    context.tenant_id,
                    tenant_id,
                    user_id,
                    f"{resource_type}:{action}"
                )
        
        return False
    
    async def grant_cross_tenant_access(
        self,
        source_tenant_id: UUID,
        target_tenant_id: UUID,
        user_id: UUID,
        permission_type: str,
        resource_type: Optional[str] = None,
        expires_in_days: int = 30,
        reason: str = None,
        granted_by: UUID = None
    ):
        """Grant temporary cross-tenant access"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO tenant_isolation.cross_tenant_access (
                    source_tenant_id, target_tenant_id, user_id,
                    permission_type, resource_type, expires_at,
                    granted_by, reason
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (source_tenant_id, target_tenant_id, user_id, permission_type)
                DO UPDATE SET 
                    expires_at = EXCLUDED.expires_at,
                    granted_at = NOW()
            """, source_tenant_id, target_tenant_id, user_id,
                permission_type, resource_type,
                datetime.utcnow() + timedelta(days=expires_in_days),
                granted_by, reason)
    
    async def revoke_cross_tenant_access(
        self,
        source_tenant_id: UUID,
        target_tenant_id: UUID,
        user_id: UUID,
        permission_type: Optional[str] = None
    ):
        """Revoke cross-tenant access"""
        async with self.db_pool.acquire() as conn:
            if permission_type:
                await conn.execute("""
                    DELETE FROM tenant_isolation.cross_tenant_access
                    WHERE source_tenant_id = $1 
                    AND target_tenant_id = $2
                    AND user_id = $3
                    AND permission_type = $4
                """, source_tenant_id, target_tenant_id, user_id, permission_type)
            else:
                # Revoke all permissions
                await conn.execute("""
                    DELETE FROM tenant_isolation.cross_tenant_access
                    WHERE source_tenant_id = $1 
                    AND target_tenant_id = $2
                    AND user_id = $3
                """, source_tenant_id, target_tenant_id, user_id)
    
    async def get_tenant_statistics(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get usage statistics for a tenant"""
        async with self.db_pool.acquire() as conn:
            # Get tenant info
            tenant = await conn.fetchrow("""
                SELECT * FROM tenant_isolation.tenants
                WHERE tenant_id = $1
            """, tenant_id)
            
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tenant not found"
                )
            
            # Get usage stats
            stats = {}
            
            # User count
            user_count = await conn.fetchval("""
                SELECT COUNT(*) FROM users WHERE tenant_id = $1
            """, tenant_id)
            stats['user_count'] = user_count
            stats['user_limit'] = tenant['max_users']
            stats['user_usage_percent'] = (user_count / tenant['max_users'] * 100) if tenant['max_users'] > 0 else 0
            
            # Storage usage (simplified)
            storage_gb = await conn.fetchval("""
                SELECT COALESCE(SUM(file_size_bytes) / 1073741824.0, 0)
                FROM documents WHERE tenant_id = $1
            """, tenant_id) or 0
            stats['storage_gb'] = round(storage_gb, 2)
            stats['storage_limit_gb'] = tenant['max_storage_gb']
            stats['storage_usage_percent'] = (storage_gb / tenant['max_storage_gb'] * 100) if tenant['max_storage_gb'] > 0 else 0
            
            # API calls this month
            api_calls = await conn.fetchval("""
                SELECT COUNT(*) FROM tenant_isolation.access_log
                WHERE tenant_id = $1
                AND accessed_at >= date_trunc('month', CURRENT_DATE)
            """, tenant_id)
            stats['api_calls_this_month'] = api_calls
            stats['api_calls_limit'] = tenant['max_api_calls_per_month']
            stats['api_usage_percent'] = (api_calls / tenant['max_api_calls_per_month'] * 100) if tenant['max_api_calls_per_month'] > 0 else 0
            
            # Security stats
            stats['require_mfa'] = tenant['require_mfa']
            stats['isolation_level'] = tenant['isolation_level']
            stats['is_active'] = tenant['is_active']
            
            return stats
    
    async def enforce_tenant_limits(self, tenant_id: UUID, resource_type: str) -> bool:
        """
        Enforce tenant resource limits
        
        Args:
            tenant_id: Tenant ID
            resource_type: Type of resource (users, storage, api_calls)
            
        Returns:
            True if within limits
            
        Raises:
            HTTPException if limit exceeded
        """
        stats = await self.get_tenant_statistics(tenant_id)
        
        if resource_type == 'users':
            if stats['user_count'] >= stats['user_limit']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User limit exceeded ({stats['user_limit']} users)"
                )
        
        elif resource_type == 'storage':
            if stats['storage_gb'] >= stats['storage_limit_gb']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Storage limit exceeded ({stats['storage_limit_gb']} GB)"
                )
        
        elif resource_type == 'api_calls':
            if stats['api_calls_this_month'] >= stats['api_calls_limit']:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"API call limit exceeded ({stats['api_calls_limit']} calls/month)"
                )
        
        return True
    
    async def _get_allowed_tenants(
        self,
        user_id: UUID,
        source_tenant_id: UUID
    ) -> Set[UUID]:
        """Get list of tenants user can access"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT DISTINCT target_tenant_id
                FROM tenant_isolation.cross_tenant_access
                WHERE user_id = $1
                AND source_tenant_id = $2
                AND (expires_at IS NULL OR expires_at > NOW())
            """, user_id, source_tenant_id)
            
            return {UUID(row['target_tenant_id']) for row in rows}
    
    async def _check_cross_tenant_permission(
        self,
        source_tenant_id: UUID,
        target_tenant_id: UUID,
        user_id: UUID,
        permission_type: str
    ) -> bool:
        """Check specific cross-tenant permission"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT COUNT(*) > 0
                FROM tenant_isolation.cross_tenant_access
                WHERE source_tenant_id = $1
                AND target_tenant_id = $2
                AND user_id = $3
                AND permission_type = $4
                AND (expires_at IS NULL OR expires_at > NOW())
            """, source_tenant_id, target_tenant_id, user_id, permission_type)
            
            return result
    
    async def _log_tenant_access(self, context: TenantContext, request: Request):
        """Log tenant access for audit"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO tenant_isolation.access_log (
                    tenant_id, user_id, ip_address, user_agent,
                    endpoint, method, cross_tenant_access
                ) VALUES ($1, $2, $3::inet, $4, $5, $6, $7)
            """, context.tenant_id, context.user_id,
                request.client.host if request.client else None,
                request.headers.get('User-Agent'),
                str(request.url.path),
                request.method,
                context.isolation_level != TenantIsolationLevel.STRICT)
    
    async def cleanup_expired_permissions(self):
        """Clean up expired cross-tenant permissions"""
        async with self.db_pool.acquire() as conn:
            deleted = await conn.execute("""
                DELETE FROM tenant_isolation.cross_tenant_access
                WHERE expires_at < NOW()
            """)
            return deleted


# Middleware for automatic tenant isolation
class TenantIsolationMiddleware:
    """Middleware to enforce tenant isolation on all requests"""
    
    def __init__(self, isolation_system: TenantIsolationSystem):
        self.isolation_system = isolation_system
    
    async def __call__(self, request: Request, call_next):
        """Process request with tenant isolation"""
        # Extract tenant context from request
        # This would typically come from JWT token or session
        tenant_id = request.headers.get('X-Tenant-ID')
        user_id = request.headers.get('X-User-ID')
        
        if tenant_id and user_id:
            # Set tenant context
            await self.isolation_system.set_tenant_context(
                request=request,
                tenant_id=UUID(tenant_id),
                organization_id=UUID(tenant_id),  # Simplified
                user_id=UUID(user_id),
                roles=[]  # Would come from auth
            )
        
        # Process request
        response = await call_next(request)
        
        # Clear context after request
        request_id = str(id(request))
        if request_id in self.isolation_system._context_storage:
            del self.isolation_system._context_storage[request_id]
        
        return response


# Export main components
__all__ = [
    'TenantIsolationSystem',
    'TenantIsolationMiddleware',
    'TenantContext',
    'TenantIsolationLevel'
]

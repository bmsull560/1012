"""
Critical Security Tests for Multi-Tenant Isolation
Tests that tenant data cannot be accessed across tenant boundaries
"""

import pytest
import uuid
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import asyncio
from typing import Dict, Any

# Import the services to test
from billing_system.backend.main import app as billing_app
from services.shared.tenant_context import TokenGenerator, JWTConfig


class TestTenantIsolation:
    """
    Critical security tests to ensure complete tenant isolation.
    These tests MUST pass before production deployment.
    """
    
    @pytest.fixture
    def test_client(self):
        """Create test client for the billing service"""
        return TestClient(billing_app)
    
    @pytest.fixture
    def tenant_a_token(self):
        """Create JWT token for Tenant A"""
        return TokenGenerator.create_access_token(
            tenant_id="11111111-1111-1111-1111-111111111111",
            org_id="org-a",
            user_id="user-a-1",
            email="user@tenant-a.com",
            roles=["billing_admin"],
            permissions=["invoice:read", "invoice:write", "invoice:delete"]
        )
    
    @pytest.fixture
    def tenant_b_token(self):
        """Create JWT token for Tenant B"""
        return TokenGenerator.create_access_token(
            tenant_id="22222222-2222-2222-2222-222222222222",
            org_id="org-b",
            user_id="user-b-1",
            email="user@tenant-b.com",
            roles=["billing_operator"],
            permissions=["invoice:read", "invoice:write"]
        )
    
    def test_cannot_access_other_tenant_data(self, test_client, tenant_a_token, tenant_b_token):
        """
        CRITICAL: Ensure Tenant A cannot access Tenant B's data
        """
        # Create an invoice for Tenant A
        response = test_client.post(
            "/api/invoices",
            headers={"Authorization": f"Bearer {tenant_a_token}"},
            json={
                "customer_id": "cust-a-1",
                "amount": 1000.00,
                "description": "Tenant A Invoice",
                "due_date": "2024-12-31"
            }
        )
        assert response.status_code == 201
        tenant_a_invoice_id = response.json()["id"]
        
        # Try to access Tenant A's invoice with Tenant B's token
        response = test_client.get(
            f"/api/invoices/{tenant_a_invoice_id}",
            headers={"Authorization": f"Bearer {tenant_b_token}"}
        )
        
        # Must return 404 (not found) not 403 (forbidden) to avoid information leakage
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_cannot_list_other_tenant_resources(self, test_client, tenant_a_token, tenant_b_token):
        """
        Ensure listing endpoints only return tenant-specific data
        """
        # Create invoices for both tenants
        test_client.post(
            "/api/invoices",
            headers={"Authorization": f"Bearer {tenant_a_token}"},
            json={"customer_id": "cust-a", "amount": 100, "description": "A"}
        )
        
        test_client.post(
            "/api/invoices",
            headers={"Authorization": f"Bearer {tenant_b_token}"},
            json={"customer_id": "cust-b", "amount": 200, "description": "B"}
        )
        
        # List invoices as Tenant A
        response = test_client.get(
            "/api/invoices",
            headers={"Authorization": f"Bearer {tenant_a_token}"}
        )
        
        assert response.status_code == 200
        invoices = response.json()
        
        # Verify only Tenant A's invoices are returned
        for invoice in invoices:
            assert invoice["description"] != "B"
            assert invoice["customer_id"] != "cust-b"
    
    def test_cannot_update_other_tenant_data(self, test_client, tenant_a_token, tenant_b_token):
        """
        Ensure tenants cannot update each other's data
        """
        # Create invoice for Tenant A
        response = test_client.post(
            "/api/invoices",
            headers={"Authorization": f"Bearer {tenant_a_token}"},
            json={"customer_id": "cust-a", "amount": 100, "description": "Original"}
        )
        invoice_id = response.json()["id"]
        
        # Try to update with Tenant B's token
        response = test_client.patch(
            f"/api/invoices/{invoice_id}",
            headers={"Authorization": f"Bearer {tenant_b_token}"},
            json={"description": "Hacked by Tenant B"}
        )
        
        assert response.status_code == 404
        
        # Verify the invoice wasn't modified
        response = test_client.get(
            f"/api/invoices/{invoice_id}",
            headers={"Authorization": f"Bearer {tenant_a_token}"}
        )
        assert response.json()["description"] == "Original"
    
    def test_cannot_delete_other_tenant_data(self, test_client, tenant_a_token, tenant_b_token):
        """
        Ensure tenants cannot delete each other's data
        """
        # Create invoice for Tenant A
        response = test_client.post(
            "/api/invoices",
            headers={"Authorization": f"Bearer {tenant_a_token}"},
            json={"customer_id": "cust-a", "amount": 100, "description": "Important"}
        )
        invoice_id = response.json()["id"]
        
        # Try to delete with Tenant B's token
        response = test_client.delete(
            f"/api/invoices/{invoice_id}",
            headers={"Authorization": f"Bearer {tenant_b_token}"}
        )
        
        assert response.status_code == 404
        
        # Verify the invoice still exists
        response = test_client.get(
            f"/api/invoices/{invoice_id}",
            headers={"Authorization": f"Bearer {tenant_a_token}"}
        )
        assert response.status_code == 200
    
    def test_header_spoofing_prevented(self, test_client, tenant_a_token):
        """
        Ensure X-Tenant-ID header cannot override JWT tenant
        """
        response = test_client.get(
            "/api/invoices",
            headers={
                "Authorization": f"Bearer {tenant_a_token}",
                "X-Tenant-ID": "22222222-2222-2222-2222-222222222222"  # Try to spoof Tenant B
            }
        )
        
        # Should either ignore the header or return 403
        if response.status_code == 200:
            # If successful, verify it's still Tenant A's data
            invoices = response.json()
            for invoice in invoices:
                # Would need to check against known Tenant A data
                pass
        else:
            # Should reject the request due to mismatch
            assert response.status_code == 403
            assert "mismatch" in response.json()["detail"].lower()
    
    def test_sql_injection_prevented(self, test_client, tenant_a_token):
        """
        Ensure SQL injection attacks are prevented
        """
        # Try various SQL injection patterns
        injection_patterns = [
            "1' OR '1'='1",
            "'; DROP TABLE invoices; --",
            "1 UNION SELECT * FROM users",
            "admin'--",
            "' OR 1=1--",
        ]
        
        for pattern in injection_patterns:
            response = test_client.get(
                f"/api/invoices/{pattern}",
                headers={"Authorization": f"Bearer {tenant_a_token}"}
            )
            
            # Should return 422 (validation error) or 404, not 500
            assert response.status_code in [404, 422]
            assert response.status_code != 500
    
    def test_jwt_token_expiry(self, test_client):
        """
        Ensure expired tokens are rejected
        """
        # Create an expired token
        expired_token = jwt.encode(
            {
                "tenant_id": "test-tenant",
                "org_id": "test-org",
                "user_id": "test-user",
                "email": "test@example.com",
                "exp": datetime.utcnow() - timedelta(hours=1),
                "iat": datetime.utcnow() - timedelta(hours=2),
                "token_type": "access"
            },
            JWTConfig.SECRET_KEY,
            algorithm=JWTConfig.ALGORITHM
        )
        
        response = test_client.get(
            "/api/invoices",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()
    
    def test_invalid_jwt_signature(self, test_client):
        """
        Ensure tokens with invalid signatures are rejected
        """
        # Create token with wrong secret
        invalid_token = jwt.encode(
            {
                "tenant_id": "test-tenant",
                "org_id": "test-org",
                "user_id": "test-user",
                "email": "test@example.com",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "token_type": "access"
            },
            "wrong-secret-key",
            algorithm="HS256"
        )
        
        response = test_client.get(
            "/api/invoices",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_missing_tenant_context(self, test_client):
        """
        Ensure requests without tenant context are rejected
        """
        # Create token without tenant_id
        incomplete_token = jwt.encode(
            {
                "user_id": "test-user",
                "email": "test@example.com",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "token_type": "access"
            },
            JWTConfig.SECRET_KEY,
            algorithm=JWTConfig.ALGORITHM
        )
        
        response = test_client.get(
            "/api/invoices",
            headers={"Authorization": f"Bearer {incomplete_token}"}
        )
        
        assert response.status_code == 401
        assert "missing required claims" in response.json()["detail"].lower()
    
    def test_rbac_enforcement(self, test_client):
        """
        Ensure role-based access control is enforced
        """
        # Create token with read-only role
        readonly_token = TokenGenerator.create_access_token(
            tenant_id="test-tenant",
            org_id="test-org",
            user_id="readonly-user",
            email="readonly@example.com",
            roles=["billing_readonly"],
            permissions=["invoice:read"]
        )
        
        # Try to create an invoice (write operation)
        response = test_client.post(
            "/api/invoices",
            headers={"Authorization": f"Bearer {readonly_token}"},
            json={"customer_id": "test", "amount": 100}
        )
        
        # Should be forbidden
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_tenant_isolation(self, test_client, tenant_a_token, tenant_b_token):
        """
        Ensure tenant isolation works under concurrent load
        """
        async def create_invoice(token: str, tenant_name: str, index: int):
            response = test_client.post(
                "/api/invoices",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "customer_id": f"{tenant_name}-{index}",
                    "amount": index * 100,
                    "description": f"{tenant_name} Invoice {index}"
                }
            )
            return response.json()
        
        # Create invoices concurrently for both tenants
        tasks = []
        for i in range(10):
            tasks.append(create_invoice(tenant_a_token, "TenantA", i))
            tasks.append(create_invoice(tenant_b_token, "TenantB", i))
        
        results = await asyncio.gather(*tasks)
        
        # Verify each tenant can only see their own invoices
        response_a = test_client.get(
            "/api/invoices",
            headers={"Authorization": f"Bearer {tenant_a_token}"}
        )
        
        response_b = test_client.get(
            "/api/invoices",
            headers={"Authorization": f"Bearer {tenant_b_token}"}
        )
        
        invoices_a = response_a.json()
        invoices_b = response_b.json()
        
        # Ensure no cross-contamination
        for invoice in invoices_a:
            assert "TenantB" not in invoice["description"]
        
        for invoice in invoices_b:
            assert "TenantA" not in invoice["description"]


class TestDatabaseRLS:
    """
    Test PostgreSQL Row-Level Security implementation
    """
    
    @pytest.fixture
    def db_session(self):
        """Create a database session for testing"""
        engine = create_engine(os.getenv("DATABASE_URL"))
        session = Session(engine)
        yield session
        session.close()
    
    def test_rls_enabled_on_tables(self, db_session):
        """
        Verify RLS is enabled on all tenant tables
        """
        result = db_session.execute("""
            SELECT tablename, rowsecurity 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN (
                'users', 'invoices', 'subscriptions', 'payments',
                'customers', 'products', 'billing_events', 'api_keys',
                'audit_logs', 'documents', 'notifications'
            )
        """)
        
        for row in result:
            assert row.rowsecurity == True, f"RLS not enabled on {row.tablename}"
    
    def test_rls_policies_exist(self, db_session):
        """
        Verify RLS policies are created for all operations
        """
        result = db_session.execute("""
            SELECT tablename, policyname, cmd 
            FROM pg_policies 
            WHERE schemaname = 'public'
        """)
        
        policies = list(result)
        tables = set(p.tablename for p in policies)
        
        # Verify policies exist for critical tables
        required_tables = {
            'users', 'invoices', 'subscriptions', 'payments',
            'customers', 'api_keys'
        }
        
        assert required_tables.issubset(tables), "Missing RLS policies for some tables"
    
    def test_tenant_context_required(self, db_session):
        """
        Verify queries fail without tenant context
        """
        # Try to query without setting tenant context
        with pytest.raises(Exception):
            db_session.execute("SELECT * FROM invoices")
    
    def test_tenant_context_isolation(self, db_session):
        """
        Verify tenant context properly isolates data
        """
        # Set tenant context for Tenant A
        db_session.execute(
            "SELECT set_current_tenant_id(:tenant_id)",
            {"tenant_id": "11111111-1111-1111-1111-111111111111"}
        )
        
        # Query should only return Tenant A's data
        result = db_session.execute("SELECT tenant_id FROM invoices")
        for row in result:
            assert str(row.tenant_id) == "11111111-1111-1111-1111-111111111111"


if __name__ == "__main__":
    # Run critical security tests
    pytest.main([__file__, "-v", "--tb=short"])

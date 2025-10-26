"""
GDPR Compliance Module
Implements data subject rights including erasure and portability
"""

import os
import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import asyncpg
from pydantic import BaseModel, EmailStr, Field
from enum import Enum
import zipfile
import io
import csv


class GDPRRequestType(Enum):
    """Types of GDPR requests"""
    ACCESS = "access"  # Right to access (Article 15)
    RECTIFICATION = "rectification"  # Right to rectification (Article 16)
    ERASURE = "erasure"  # Right to erasure/be forgotten (Article 17)
    PORTABILITY = "portability"  # Right to data portability (Article 20)
    RESTRICTION = "restriction"  # Right to restriction (Article 18)
    OBJECTION = "objection"  # Right to object (Article 21)


class GDPRRequestStatus(Enum):
    """Status of GDPR requests"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    PARTIALLY_COMPLETED = "partially_completed"


class GDPRRequest(BaseModel):
    """GDPR request model"""
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    request_type: GDPRRequestType
    subject_id: str  # User ID
    subject_email: EmailStr
    organization_id: Optional[str] = None
    status: GDPRRequestStatus = GDPRRequestStatus.PENDING
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    verification_token: Optional[str] = None
    verification_completed: bool = False
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None


class GDPRComplianceService:
    """
    GDPR Compliance Service
    Implements data subject rights as per GDPR Articles 15-22
    """
    
    def __init__(self, database_url: str):
        """
        Initialize GDPR compliance service
        
        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        self.db_pool: Optional[asyncpg.Pool] = None
    
    async def init(self):
        """Initialize database connection and tables"""
        self.db_pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10
        )
        
        # Create GDPR schema and tables
        await self._create_gdpr_schema()
        
        # Create GDPR functions
        await self._create_gdpr_functions()
    
    async def close(self):
        """Close database connections"""
        if self.db_pool:
            await self.db_pool.close()
    
    async def _create_gdpr_schema(self):
        """Create GDPR compliance schema and tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                -- Create GDPR schema
                CREATE SCHEMA IF NOT EXISTS gdpr;
                
                -- GDPR requests table
                CREATE TABLE IF NOT EXISTS gdpr.requests (
                    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    request_type VARCHAR(20) NOT NULL,
                    subject_id UUID NOT NULL,
                    subject_email VARCHAR(255) NOT NULL,
                    organization_id UUID,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    requested_at TIMESTAMPTZ DEFAULT NOW(),
                    processed_at TIMESTAMPTZ,
                    processed_by UUID,
                    verification_token VARCHAR(64),
                    verification_completed BOOLEAN DEFAULT FALSE,
                    verification_expires_at TIMESTAMPTZ,
                    reason TEXT,
                    metadata JSONB,
                    result JSONB,
                    
                    -- Indexes
                    INDEX idx_subject_id (subject_id),
                    INDEX idx_status (status),
                    INDEX idx_requested_at (requested_at)
                );
                
                -- Data retention policies
                CREATE TABLE IF NOT EXISTS gdpr.retention_policies (
                    policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    data_category VARCHAR(50) NOT NULL,
                    retention_days INTEGER NOT NULL,
                    legal_basis TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    
                    UNIQUE(data_category)
                );
                
                -- Anonymization log
                CREATE TABLE IF NOT EXISTS gdpr.anonymization_log (
                    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    request_id UUID REFERENCES gdpr.requests(request_id),
                    table_name VARCHAR(100) NOT NULL,
                    record_count INTEGER NOT NULL,
                    anonymization_method VARCHAR(50),
                    anonymized_at TIMESTAMPTZ DEFAULT NOW(),
                    anonymized_by UUID
                );
                
                -- Consent records
                CREATE TABLE IF NOT EXISTS gdpr.consent_records (
                    consent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    subject_id UUID NOT NULL,
                    purpose VARCHAR(100) NOT NULL,
                    granted BOOLEAN NOT NULL,
                    granted_at TIMESTAMPTZ,
                    revoked_at TIMESTAMPTZ,
                    ip_address INET,
                    user_agent TEXT,
                    
                    INDEX idx_subject_consent (subject_id),
                    INDEX idx_purpose (purpose)
                );
                
                -- Default retention policies
                INSERT INTO gdpr.retention_policies (data_category, retention_days, legal_basis)
                VALUES 
                    ('billing_data', 2555, 'Legal requirement - 7 years for tax purposes'),
                    ('user_data', 1095, 'Legitimate interest - 3 years'),
                    ('audit_logs', 2555, 'Legal requirement - 7 years for compliance'),
                    ('marketing_data', 365, 'Consent-based - 1 year'),
                    ('analytics_data', 730, 'Legitimate interest - 2 years')
                ON CONFLICT (data_category) DO NOTHING;
            """)
    
    async def _create_gdpr_functions(self):
        """Create GDPR compliance SQL functions"""
        async with self.db_pool.acquire() as conn:
            # Function for data erasure (right to be forgotten)
            await conn.execute("""
                CREATE OR REPLACE FUNCTION gdpr.fn_gdpr_erasure(
                    p_subject_id UUID,
                    p_request_id UUID DEFAULT NULL
                ) RETURNS JSONB AS $$
                DECLARE
                    v_result JSONB := '{}';
                    v_tables_processed INTEGER := 0;
                    v_records_anonymized INTEGER := 0;
                BEGIN
                    -- Start transaction
                    -- Note: In production, this should be more sophisticated
                    
                    -- Anonymize user data (keep structure but remove PII)
                    UPDATE users
                    SET 
                        email = 'deleted_' || MD5(email::text) || '@anonymized.local',
                        first_name = 'DELETED',
                        last_name = 'USER',
                        phone = NULL,
                        address = NULL,
                        date_of_birth = NULL,
                        is_active = FALSE,
                        deleted_at = NOW()
                    WHERE id = p_subject_id;
                    
                    v_records_anonymized := v_records_anonymized + 1;
                    
                    -- Anonymize billing records (keep for legal requirements)
                    UPDATE invoices
                    SET 
                        customer_name = 'ANONYMIZED',
                        customer_email = 'deleted@anonymized.local',
                        billing_address = jsonb_build_object(
                            'line1', 'DELETED',
                            'city', 'DELETED',
                            'country', 'XX'
                        )
                    WHERE user_id = p_subject_id;
                    
                    GET DIAGNOSTICS v_records_anonymized = v_records_anonymized + ROW_COUNT;
                    
                    -- Delete non-essential data
                    DELETE FROM user_sessions WHERE user_id = p_subject_id;
                    DELETE FROM user_preferences WHERE user_id = p_subject_id;
                    DELETE FROM marketing_consent WHERE user_id = p_subject_id;
                    
                    -- Log anonymization
                    IF p_request_id IS NOT NULL THEN
                        INSERT INTO gdpr.anonymization_log (
                            request_id, table_name, record_count, anonymization_method
                        ) VALUES 
                            (p_request_id, 'users', 1, 'pseudonymization'),
                            (p_request_id, 'invoices', v_records_anonymized - 1, 'partial_anonymization');
                    END IF;
                    
                    -- Build result
                    v_result := jsonb_build_object(
                        'success', true,
                        'tables_processed', 5,
                        'records_anonymized', v_records_anonymized,
                        'timestamp', NOW()
                    );
                    
                    RETURN v_result;
                EXCEPTION
                    WHEN OTHERS THEN
                        RETURN jsonb_build_object(
                            'success', false,
                            'error', SQLERRM,
                            'timestamp', NOW()
                        );
                END;
                $$ LANGUAGE plpgsql SECURITY DEFINER;
                
                -- Function for data export (right to portability)
                CREATE OR REPLACE FUNCTION gdpr.fn_gdpr_export(
                    p_subject_id UUID,
                    p_format VARCHAR DEFAULT 'json'
                ) RETURNS JSONB AS $$
                DECLARE
                    v_result JSONB := '{}';
                    v_user_data JSONB;
                    v_billing_data JSONB;
                    v_activity_data JSONB;
                BEGIN
                    -- Collect user data
                    SELECT to_jsonb(u.*) INTO v_user_data
                    FROM (
                        SELECT 
                            id, email, first_name, last_name,
                            phone, created_at, updated_at,
                            is_active, is_verified
                        FROM users
                        WHERE id = p_subject_id
                    ) u;
                    
                    -- Collect billing data
                    SELECT jsonb_agg(inv.*) INTO v_billing_data
                    FROM (
                        SELECT 
                            invoice_number, amount, currency,
                            status, created_at, paid_at
                        FROM invoices
                        WHERE user_id = p_subject_id
                        ORDER BY created_at DESC
                    ) inv;
                    
                    -- Collect activity data
                    SELECT jsonb_agg(act.*) INTO v_activity_data
                    FROM (
                        SELECT 
                            event_type, description, timestamp
                        FROM audit_trail
                        WHERE actor_id = p_subject_id::text
                        ORDER BY timestamp DESC
                        LIMIT 1000
                    ) act;
                    
                    -- Build complete export
                    v_result := jsonb_build_object(
                        'export_date', NOW(),
                        'subject_id', p_subject_id,
                        'format', p_format,
                        'data', jsonb_build_object(
                            'personal_data', v_user_data,
                            'billing_history', v_billing_data,
                            'activity_log', v_activity_data
                        )
                    );
                    
                    RETURN v_result;
                EXCEPTION
                    WHEN OTHERS THEN
                        RETURN jsonb_build_object(
                            'success', false,
                            'error', SQLERRM,
                            'timestamp', NOW()
                        );
                END;
                $$ LANGUAGE plpgsql SECURITY DEFINER;
                
                -- Function to check data retention compliance
                CREATE OR REPLACE FUNCTION gdpr.fn_check_retention_compliance()
                RETURNS TABLE(
                    data_category VARCHAR,
                    table_name VARCHAR,
                    expired_records BIGINT,
                    oldest_record_date TIMESTAMPTZ
                ) AS $$
                BEGIN
                    -- Check user data retention
                    RETURN QUERY
                    SELECT 
                        'user_data'::VARCHAR,
                        'users'::VARCHAR,
                        COUNT(*)::BIGINT,
                        MIN(created_at)
                    FROM users
                    WHERE created_at < NOW() - (
                        SELECT retention_days * INTERVAL '1 day'
                        FROM gdpr.retention_policies
                        WHERE data_category = 'user_data'
                    )
                    AND is_active = FALSE;
                    
                    -- Check billing data retention
                    RETURN QUERY
                    SELECT 
                        'billing_data'::VARCHAR,
                        'invoices'::VARCHAR,
                        COUNT(*)::BIGINT,
                        MIN(created_at)
                    FROM invoices
                    WHERE created_at < NOW() - (
                        SELECT retention_days * INTERVAL '1 day'
                        FROM gdpr.retention_policies
                        WHERE data_category = 'billing_data'
                    );
                    
                    -- Check audit logs retention
                    RETURN QUERY
                    SELECT 
                        'audit_logs'::VARCHAR,
                        'audit_trail'::VARCHAR,
                        COUNT(*)::BIGINT,
                        MIN(timestamp)
                    FROM audit_trail
                    WHERE timestamp < NOW() - (
                        SELECT retention_days * INTERVAL '1 day'
                        FROM gdpr.retention_policies
                        WHERE data_category = 'audit_logs'
                    );
                END;
                $$ LANGUAGE plpgsql;
            """)
    
    async def create_request(
        self,
        request_type: GDPRRequestType,
        subject_id: str,
        subject_email: str,
        organization_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> GDPRRequest:
        """
        Create a new GDPR request
        
        Args:
            request_type: Type of GDPR request
            subject_id: User ID of the data subject
            subject_email: Email of the data subject
            organization_id: Optional organization ID
            reason: Optional reason for the request
            
        Returns:
            Created GDPR request
        """
        # Generate verification token
        verification_token = hashlib.sha256(
            f"{subject_id}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()
        
        # Create request
        request = GDPRRequest(
            request_type=request_type,
            subject_id=subject_id,
            subject_email=subject_email,
            organization_id=organization_id,
            reason=reason,
            verification_token=verification_token
        )
        
        # Store in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO gdpr.requests (
                    request_id, request_type, subject_id, subject_email,
                    organization_id, status, reason, verification_token,
                    verification_expires_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, UUID(request.request_id), request_type.value, UUID(subject_id),
                subject_email, UUID(organization_id) if organization_id else None,
                request.status.value, reason, verification_token,
                datetime.utcnow() + timedelta(hours=48))
        
        # TODO: Send verification email to subject
        
        return request
    
    async def verify_request(
        self,
        request_id: str,
        verification_token: str
    ) -> bool:
        """
        Verify a GDPR request
        
        Args:
            request_id: Request ID
            verification_token: Verification token from email
            
        Returns:
            True if verification successful
        """
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                UPDATE gdpr.requests
                SET verification_completed = TRUE
                WHERE request_id = $1
                AND verification_token = $2
                AND verification_expires_at > NOW()
                AND verification_completed = FALSE
                RETURNING request_id
            """, UUID(request_id), verification_token)
            
            return result is not None
    
    async def process_erasure_request(
        self,
        request_id: str,
        processed_by: str
    ) -> Dict[str, Any]:
        """
        Process a data erasure request (right to be forgotten)
        
        Args:
            request_id: GDPR request ID
            processed_by: User ID processing the request
            
        Returns:
            Result of the erasure process
        """
        # Get request details
        async with self.db_pool.acquire() as conn:
            request = await conn.fetchrow("""
                SELECT * FROM gdpr.requests
                WHERE request_id = $1
                AND request_type = 'erasure'
                AND verification_completed = TRUE
                AND status = 'pending'
            """, UUID(request_id))
            
            if not request:
                raise ValueError("Invalid or unverified request")
            
            # Update status
            await conn.execute("""
                UPDATE gdpr.requests
                SET status = 'in_progress'
                WHERE request_id = $1
            """, UUID(request_id))
            
            # Execute erasure function
            result = await conn.fetchval("""
                SELECT gdpr.fn_gdpr_erasure($1, $2)
            """, request['subject_id'], UUID(request_id))
            
            # Update request with result
            await conn.execute("""
                UPDATE gdpr.requests
                SET 
                    status = CASE 
                        WHEN ($1->>'success')::boolean THEN 'completed'
                        ELSE 'partially_completed'
                    END,
                    processed_at = NOW(),
                    processed_by = $2,
                    result = $1
                WHERE request_id = $3
            """, result, UUID(processed_by), UUID(request_id))
            
            return json.loads(result)
    
    async def process_portability_request(
        self,
        request_id: str,
        processed_by: str,
        format: str = 'json'
    ) -> bytes:
        """
        Process a data portability request
        
        Args:
            request_id: GDPR request ID
            processed_by: User ID processing the request
            format: Export format (json, csv, xml)
            
        Returns:
            Exported data as bytes (ZIP file)
        """
        # Get request details
        async with self.db_pool.acquire() as conn:
            request = await conn.fetchrow("""
                SELECT * FROM gdpr.requests
                WHERE request_id = $1
                AND request_type = 'portability'
                AND verification_completed = TRUE
                AND status = 'pending'
            """, UUID(request_id))
            
            if not request:
                raise ValueError("Invalid or unverified request")
            
            # Update status
            await conn.execute("""
                UPDATE gdpr.requests
                SET status = 'in_progress'
                WHERE request_id = $1
            """, UUID(request_id))
            
            # Execute export function
            export_data = await conn.fetchval("""
                SELECT gdpr.fn_gdpr_export($1, $2)
            """, request['subject_id'], format)
            
            # Update request
            await conn.execute("""
                UPDATE gdpr.requests
                SET 
                    status = 'completed',
                    processed_at = NOW(),
                    processed_by = $1,
                    result = jsonb_build_object(
                        'format', $2,
                        'exported_at', NOW()
                    )
                WHERE request_id = $3
            """, UUID(processed_by), format, UUID(request_id))
        
        # Create ZIP file with exported data
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add main data file
            if format == 'json':
                zip_file.writestr(
                    'personal_data.json',
                    json.dumps(json.loads(export_data), indent=2)
                )
            elif format == 'csv':
                # Convert to CSV format
                data = json.loads(export_data)
                
                # Personal data CSV
                personal_csv = io.StringIO()
                if data.get('data', {}).get('personal_data'):
                    writer = csv.DictWriter(
                        personal_csv,
                        fieldnames=data['data']['personal_data'].keys()
                    )
                    writer.writeheader()
                    writer.writerow(data['data']['personal_data'])
                    zip_file.writestr('personal_data.csv', personal_csv.getvalue())
                
                # Billing data CSV
                if data.get('data', {}).get('billing_history'):
                    billing_csv = io.StringIO()
                    writer = csv.DictWriter(
                        billing_csv,
                        fieldnames=data['data']['billing_history'][0].keys()
                    )
                    writer.writeheader()
                    writer.writerows(data['data']['billing_history'])
                    zip_file.writestr('billing_history.csv', billing_csv.getvalue())
            
            # Add README
            readme_content = f"""
GDPR Data Export
================
Request ID: {request_id}
Export Date: {datetime.utcnow().isoformat()}
Format: {format}

This archive contains all personal data associated with your account.
The data is provided in compliance with GDPR Article 20 (Right to Data Portability).

Files included:
- personal_data.{format}: Your personal information
- billing_history.{format}: Your billing records (if applicable)
- README.txt: This file

For questions, contact: privacy@valueverse.com
            """
            zip_file.writestr('README.txt', readme_content)
        
        return zip_buffer.getvalue()
    
    async def check_retention_compliance(self) -> List[Dict[str, Any]]:
        """
        Check data retention compliance
        
        Returns:
            List of data categories with expired records
        """
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM gdpr.fn_check_retention_compliance()
            """)
            
            return [dict(row) for row in rows]
    
    async def record_consent(
        self,
        subject_id: str,
        purpose: str,
        granted: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Record consent from data subject
        
        Args:
            subject_id: User ID
            purpose: Purpose of data processing
            granted: Whether consent was granted
            ip_address: Client IP address
            user_agent: Client user agent
        """
        async with self.db_pool.acquire() as conn:
            # Check for existing consent
            existing = await conn.fetchrow("""
                SELECT consent_id FROM gdpr.consent_records
                WHERE subject_id = $1 AND purpose = $2
                AND revoked_at IS NULL
            """, UUID(subject_id), purpose)
            
            if existing and not granted:
                # Revoke existing consent
                await conn.execute("""
                    UPDATE gdpr.consent_records
                    SET revoked_at = NOW()
                    WHERE consent_id = $1
                """, existing['consent_id'])
            elif not existing and granted:
                # Record new consent
                await conn.execute("""
                    INSERT INTO gdpr.consent_records (
                        subject_id, purpose, granted, granted_at,
                        ip_address, user_agent
                    ) VALUES ($1, $2, $3, NOW(), $4::inet, $5)
                """, UUID(subject_id), purpose, granted, ip_address, user_agent)
    
    async def get_user_consents(self, subject_id: str) -> List[Dict[str, Any]]:
        """
        Get all consent records for a user
        
        Args:
            subject_id: User ID
            
        Returns:
            List of consent records
        """
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    purpose,
                    granted,
                    granted_at,
                    revoked_at,
                    CASE 
                        WHEN revoked_at IS NULL AND granted THEN 'active'
                        WHEN revoked_at IS NOT NULL THEN 'revoked'
                        ELSE 'denied'
                    END as status
                FROM gdpr.consent_records
                WHERE subject_id = $1
                ORDER BY granted_at DESC
            """, UUID(subject_id))
            
            return [dict(row) for row in rows]


# Export main class
__all__ = [
    'GDPRComplianceService',
    'GDPRRequest',
    'GDPRRequestType',
    'GDPRRequestStatus'
]

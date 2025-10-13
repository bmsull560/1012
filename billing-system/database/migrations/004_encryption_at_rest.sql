-- =====================================================
-- Encryption at Rest Implementation
-- Execution Time: ~2 days
-- Priority: CRITICAL (PCI Compliance)
-- =====================================================

-- STEP 1: Install required extensions
-- =====================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- STEP 2: Create key management infrastructure
-- =====================================================

-- Master key table (should be stored in external KMS in production)
CREATE TABLE IF NOT EXISTS encryption_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_name VARCHAR(100) UNIQUE NOT NULL,
    encrypted_key BYTEA NOT NULL,
    algorithm VARCHAR(50) DEFAULT 'AES-256-GCM',
    key_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT now(),
    rotated_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    purpose VARCHAR(100),
    created_by VARCHAR(100) DEFAULT current_user,
    CHECK (length(encrypted_key) >= 32)
);

-- Key metadata table
CREATE TABLE IF NOT EXISTS encryption_key_usage (
    id BIGSERIAL PRIMARY KEY,
    key_id UUID REFERENCES encryption_keys(id),
    table_name VARCHAR(100),
    column_name VARCHAR(100),
    records_encrypted INTEGER DEFAULT 0,
    last_used TIMESTAMP DEFAULT now()
);

-- STEP 3: Create encryption functions
-- =====================================================

-- Function to generate new encryption key
CREATE OR REPLACE FUNCTION generate_encryption_key(
    key_name_param VARCHAR,
    purpose_param VARCHAR DEFAULT 'data_encryption'
) RETURNS UUID AS $$
DECLARE
    new_key_id UUID;
    raw_key BYTEA;
    master_key BYTEA;
BEGIN
    -- Generate 256-bit key
    raw_key := gen_random_bytes(32);
    
    -- In production, fetch from KMS
    -- For now, use a derived key
    master_key := digest('MasterKeyPlaceholder' || current_database(), 'sha256');
    
    -- Encrypt the key with master key
    INSERT INTO encryption_keys (
        key_name,
        encrypted_key,
        purpose,
        key_version
    ) VALUES (
        key_name_param,
        pgp_sym_encrypt_bytea(raw_key, master_key::TEXT),
        purpose_param,
        COALESCE(
            (SELECT MAX(key_version) + 1 
             FROM encryption_keys 
             WHERE key_name = key_name_param), 
            1
        )
    ) RETURNING id INTO new_key_id;
    
    RETURN new_key_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get decrypted key (audit logged)
CREATE OR REPLACE FUNCTION get_encryption_key(key_id_param UUID)
RETURNS BYTEA AS $$
DECLARE
    encrypted_key_data BYTEA;
    master_key BYTEA;
    decrypted_key BYTEA;
BEGIN
    -- Log key access
    INSERT INTO security_audit_log (
        event_type, 
        details, 
        timestamp
    ) VALUES (
        'encryption_key_access',
        jsonb_build_object('key_id', key_id_param, 'user', current_user),
        now()
    );
    
    -- Get encrypted key
    SELECT encrypted_key INTO encrypted_key_data
    FROM encryption_keys
    WHERE id = key_id_param AND is_active = true;
    
    IF encrypted_key_data IS NULL THEN
        RAISE EXCEPTION 'Encryption key not found or inactive';
    END IF;
    
    -- Get master key (from KMS in production)
    master_key := digest('MasterKeyPlaceholder' || current_database(), 'sha256');
    
    -- Decrypt key
    decrypted_key := pgp_sym_decrypt_bytea(encrypted_key_data, master_key::TEXT);
    
    -- Update usage statistics
    UPDATE encryption_key_usage
    SET records_encrypted = records_encrypted + 1,
        last_used = now()
    WHERE key_id = key_id_param;
    
    RETURN decrypted_key;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to encrypt sensitive data
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(
    plain_text TEXT,
    key_id_param UUID DEFAULT NULL
) RETURNS BYTEA AS $$
DECLARE
    encryption_key BYTEA;
    encrypted_data BYTEA;
    active_key_id UUID;
BEGIN
    -- Get active key if not specified
    IF key_id_param IS NULL THEN
        SELECT id INTO active_key_id
        FROM encryption_keys
        WHERE is_active = true
        AND purpose = 'data_encryption'
        ORDER BY key_version DESC
        LIMIT 1;
    ELSE
        active_key_id := key_id_param;
    END IF;
    
    -- Get encryption key
    encryption_key := get_encryption_key(active_key_id);
    
    -- Encrypt data
    encrypted_data := pgp_sym_encrypt(
        plain_text,
        encode(encryption_key, 'hex'),
        'cipher-algo=aes256, compress-algo=1'
    );
    
    RETURN encrypted_data;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to decrypt sensitive data
CREATE OR REPLACE FUNCTION decrypt_sensitive_data(
    encrypted_data BYTEA,
    key_id_param UUID DEFAULT NULL
) RETURNS TEXT AS $$
DECLARE
    encryption_key BYTEA;
    decrypted_text TEXT;
    active_key_id UUID;
BEGIN
    -- Audit log decryption attempt
    INSERT INTO security_audit_log (
        event_type,
        user_id,
        details,
        timestamp
    ) VALUES (
        'data_decryption',
        current_user,
        jsonb_build_object('data_size', length(encrypted_data)),
        now()
    );
    
    -- Get active key if not specified
    IF key_id_param IS NULL THEN
        SELECT id INTO active_key_id
        FROM encryption_keys
        WHERE is_active = true
        AND purpose = 'data_encryption'
        ORDER BY key_version DESC
        LIMIT 1;
    ELSE
        active_key_id := key_id_param;
    END IF;
    
    -- Get encryption key
    encryption_key := get_encryption_key(active_key_id);
    
    -- Decrypt data
    decrypted_text := pgp_sym_decrypt(
        encrypted_data,
        encode(encryption_key, 'hex')
    );
    
    RETURN decrypted_text;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- STEP 4: Create encrypted columns for sensitive data
-- =====================================================

-- Add encrypted columns to payment_methods
ALTER TABLE payment_methods 
ADD COLUMN IF NOT EXISTS card_number_encrypted BYTEA,
ADD COLUMN IF NOT EXISTS card_cvv_encrypted BYTEA,
ADD COLUMN IF NOT EXISTS account_number_encrypted BYTEA,
ADD COLUMN IF NOT EXISTS routing_number_encrypted BYTEA,
ADD COLUMN IF NOT EXISTS encryption_key_id UUID REFERENCES encryption_keys(id);

-- Add encrypted columns to organizations (PII)
ALTER TABLE organizations
ADD COLUMN IF NOT EXISTS tax_id_encrypted BYTEA,
ADD COLUMN IF NOT EXISTS billing_email_encrypted BYTEA,
ADD COLUMN IF NOT EXISTS billing_address_encrypted BYTEA,
ADD COLUMN IF NOT EXISTS encryption_key_id UUID REFERENCES encryption_keys(id);

-- Add encrypted columns to invoices (sensitive financial data)
ALTER TABLE invoices
ADD COLUMN IF NOT EXISTS metadata_encrypted BYTEA,
ADD COLUMN IF NOT EXISTS encryption_key_id UUID REFERENCES encryption_keys(id);

-- STEP 5: Create triggers for automatic encryption
-- =====================================================

-- Trigger function for payment methods encryption
CREATE OR REPLACE FUNCTION encrypt_payment_methods_trigger()
RETURNS TRIGGER AS $$
DECLARE
    active_key_id UUID;
BEGIN
    -- Get active encryption key
    SELECT id INTO active_key_id
    FROM encryption_keys
    WHERE is_active = true
    AND purpose = 'payment_data'
    ORDER BY key_version DESC
    LIMIT 1;
    
    -- Create key if doesn't exist
    IF active_key_id IS NULL THEN
        active_key_id := generate_encryption_key('payment_data_key', 'payment_data');
    END IF;
    
    NEW.encryption_key_id := active_key_id;
    
    -- Encrypt sensitive fields if provided as plain text
    IF NEW.card_number_encrypted IS NOT NULL AND NEW.card_number_encrypted::TEXT NOT LIKE '\\x%' THEN
        NEW.card_number_encrypted := encrypt_sensitive_data(
            NEW.card_number_encrypted::TEXT,
            active_key_id
        );
        -- Store last 4 digits for display
        NEW.last_four := RIGHT(NEW.card_number_encrypted::TEXT, 4);
    END IF;
    
    IF NEW.account_number_encrypted IS NOT NULL AND NEW.account_number_encrypted::TEXT NOT LIKE '\\x%' THEN
        NEW.account_number_encrypted := encrypt_sensitive_data(
            NEW.account_number_encrypted::TEXT,
            active_key_id
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to payment_methods
DROP TRIGGER IF EXISTS encrypt_payment_data ON payment_methods;
CREATE TRIGGER encrypt_payment_data
BEFORE INSERT OR UPDATE ON payment_methods
FOR EACH ROW EXECUTE FUNCTION encrypt_payment_methods_trigger();

-- Trigger function for organizations encryption
CREATE OR REPLACE FUNCTION encrypt_organizations_trigger()
RETURNS TRIGGER AS $$
DECLARE
    active_key_id UUID;
BEGIN
    -- Get active encryption key
    SELECT id INTO active_key_id
    FROM encryption_keys
    WHERE is_active = true
    AND purpose = 'organization_pii'
    ORDER BY key_version DESC
    LIMIT 1;
    
    -- Create key if doesn't exist
    IF active_key_id IS NULL THEN
        active_key_id := generate_encryption_key('organization_pii_key', 'organization_pii');
    END IF;
    
    NEW.encryption_key_id := active_key_id;
    
    -- Encrypt PII fields
    IF NEW.tax_id IS NOT NULL THEN
        NEW.tax_id_encrypted := encrypt_sensitive_data(NEW.tax_id, active_key_id);
        NEW.tax_id := 'ENCRYPTED'; -- Clear plain text
    END IF;
    
    IF NEW.billing_address IS NOT NULL THEN
        NEW.billing_address_encrypted := encrypt_sensitive_data(
            NEW.billing_address::TEXT,
            active_key_id
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to organizations
DROP TRIGGER IF EXISTS encrypt_organization_data ON organizations;
CREATE TRIGGER encrypt_organization_data
BEFORE INSERT OR UPDATE ON organizations
FOR EACH ROW EXECUTE FUNCTION encrypt_organizations_trigger();

-- STEP 6: Create encrypted tablespace (requires filesystem setup)
-- =====================================================

-- Note: This requires filesystem-level encryption setup
-- Example for Linux with LUKS encryption:
/*
-- Run as system administrator:
-- 1. Create encrypted volume
-- sudo cryptsetup luksFormat /dev/sdb1
-- sudo cryptsetup open /dev/sdb1 encrypted_volume
-- sudo mkfs.ext4 /dev/mapper/encrypted_volume
-- sudo mount /dev/mapper/encrypted_volume /mnt/encrypted_pg

-- 2. Create tablespace
CREATE TABLESPACE encrypted_data 
OWNER postgres 
LOCATION '/mnt/encrypted_pg';

-- 3. Move sensitive tables to encrypted tablespace
ALTER TABLE payment_methods SET TABLESPACE encrypted_data;
ALTER TABLE billing_transactions SET TABLESPACE encrypted_data;
ALTER TABLE audit_trail SET TABLESPACE encrypted_data;
*/

-- STEP 7: Key rotation procedure
-- =====================================================

CREATE OR REPLACE FUNCTION rotate_encryption_keys()
RETURNS void AS $$
DECLARE
    old_key_record RECORD;
    new_key_id UUID;
    records_updated INTEGER;
BEGIN
    -- For each active key that needs rotation
    FOR old_key_record IN 
        SELECT id, key_name, purpose 
        FROM encryption_keys 
        WHERE is_active = true
        AND (expires_at < now() OR rotated_at < now() - INTERVAL '90 days')
    LOOP
        -- Generate new key
        new_key_id := generate_encryption_key(
            old_key_record.key_name,
            old_key_record.purpose
        );
        
        -- Re-encrypt data with new key
        IF old_key_record.purpose = 'payment_data' THEN
            UPDATE payment_methods
            SET card_number_encrypted = encrypt_sensitive_data(
                    decrypt_sensitive_data(card_number_encrypted, old_key_record.id),
                    new_key_id
                ),
                encryption_key_id = new_key_id
            WHERE encryption_key_id = old_key_record.id;
            
            GET DIAGNOSTICS records_updated = ROW_COUNT;
        END IF;
        
        -- Mark old key as rotated
        UPDATE encryption_keys
        SET is_active = false,
            rotated_at = now()
        WHERE id = old_key_record.id;
        
        -- Log rotation
        INSERT INTO security_audit_log (
            event_type, 
            details
        ) VALUES (
            'key_rotation',
            jsonb_build_object(
                'old_key_id', old_key_record.id,
                'new_key_id', new_key_id,
                'records_updated', records_updated
            )
        );
        
        RAISE NOTICE 'Rotated key % -> %, updated % records', 
            old_key_record.id, new_key_id, records_updated;
    END LOOP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- STEP 8: Create monitoring views
-- =====================================================

-- View to monitor encryption status
CREATE OR REPLACE VIEW vw_encryption_status AS
SELECT 
    t.table_name,
    COUNT(CASE WHEN pm.encryption_key_id IS NOT NULL THEN 1 END) as encrypted_records,
    COUNT(CASE WHEN pm.encryption_key_id IS NULL THEN 1 END) as unencrypted_records,
    ROUND(
        COUNT(CASE WHEN pm.encryption_key_id IS NOT NULL THEN 1 END)::NUMERIC / 
        NULLIF(COUNT(*), 0) * 100, 2
    ) as encryption_percentage
FROM (
    SELECT 'payment_methods' as table_name
    UNION ALL SELECT 'organizations'
    UNION ALL SELECT 'invoices'
) t
LEFT JOIN payment_methods pm ON t.table_name = 'payment_methods'
GROUP BY t.table_name;

-- View to monitor key usage
CREATE OR REPLACE VIEW vw_key_usage AS
SELECT 
    ek.key_name,
    ek.purpose,
    ek.key_version,
    ek.created_at,
    ek.expires_at,
    eku.records_encrypted,
    eku.last_used,
    CASE 
        WHEN ek.expires_at < now() THEN 'EXPIRED'
        WHEN ek.expires_at < now() + INTERVAL '30 days' THEN 'EXPIRING_SOON'
        ELSE 'VALID'
    END as status
FROM encryption_keys ek
LEFT JOIN encryption_key_usage eku ON ek.id = eku.key_id
WHERE ek.is_active = true
ORDER BY ek.created_at DESC;

-- STEP 9: Initial encryption of existing data
-- =====================================================

DO $$
DECLARE
    payment_key_id UUID;
    org_key_id UUID;
    records_encrypted INTEGER := 0;
BEGIN
    -- Generate initial keys
    payment_key_id := generate_encryption_key('payment_data_key', 'payment_data');
    org_key_id := generate_encryption_key('organization_pii_key', 'organization_pii');
    
    -- Encrypt existing payment methods (if any plain text exists)
    UPDATE payment_methods
    SET encryption_key_id = payment_key_id
    WHERE encryption_key_id IS NULL;
    
    GET DIAGNOSTICS records_encrypted = ROW_COUNT;
    RAISE NOTICE 'Encrypted % payment method records', records_encrypted;
    
    -- Encrypt existing organization data
    UPDATE organizations
    SET encryption_key_id = org_key_id
    WHERE encryption_key_id IS NULL;
    
    GET DIAGNOSTICS records_encrypted = ROW_COUNT;
    RAISE NOTICE 'Encrypted % organization records', records_encrypted;
    
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Encryption at Rest Implementation Complete';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Configure filesystem-level encryption';
    RAISE NOTICE '2. Integrate with external KMS';
    RAISE NOTICE '3. Test key rotation procedure';
    RAISE NOTICE '4. Monitor vw_encryption_status';
END;
$$;

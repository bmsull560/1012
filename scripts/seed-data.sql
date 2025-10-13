-- ============================================================================
-- ValueVerse Platform - Sample Data Seeding Script
-- ============================================================================

\c valueverse;

-- ============================================================================
-- SAMPLE USERS
-- ============================================================================

INSERT INTO users (email, name, password_hash, role, is_active, email_verified, last_login) VALUES
    ('demo@valueverse.ai', 'Demo User', crypt('demo123', gen_salt('bf')), 'user', true, true, CURRENT_TIMESTAMP),
    ('john.doe@acmecorp.com', 'John Doe', crypt('password123', gen_salt('bf')), 'user', true, true, CURRENT_TIMESTAMP - INTERVAL '2 days'),
    ('jane.smith@techstart.io', 'Jane Smith', crypt('password123', gen_salt('bf')), 'user', true, true, CURRENT_TIMESTAMP - INTERVAL '5 days'),
    ('mike.wilson@enterprise.co', 'Mike Wilson', crypt('password123', gen_salt('bf')), 'enterprise', true, true, CURRENT_TIMESTAMP - INTERVAL '1 day'),
    ('sarah.jones@fintech.ai', 'Sarah Jones', crypt('password123', gen_salt('bf')), 'user', true, true, CURRENT_TIMESTAMP - INTERVAL '3 days')
ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- SAMPLE COMPANIES
-- ============================================================================

INSERT INTO companies (id, name, industry, size, description, website) VALUES
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Acme Corp', 'SaaS', 'mid-market', 'Leading B2B SaaS platform for project management', 'https://acmecorp.com'),
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'TechStart Inc', 'FinTech', 'startup', 'Revolutionary payment processing for SMBs', 'https://techstart.io'),
    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'Enterprise Co', 'Healthcare', 'enterprise', 'Healthcare technology solutions provider', 'https://enterprise.co'),
    ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'CloudScale Systems', 'Cloud Infrastructure', 'growth', 'Next-gen cloud infrastructure platform', 'https://cloudscale.com'),
    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'DataFlow Analytics', 'Analytics', 'mid-market', 'Real-time business intelligence platform', 'https://dataflow.ai')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- SAMPLE VALUE MODELS
-- ============================================================================

INSERT INTO value_models (id, company_id, user_id, name, description, industry, company_size, status, total_potential_value, confidence_score, implementation_timeline) VALUES
    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 
     (SELECT id FROM users WHERE email = 'john.doe@acmecorp.com'),
     'Acme Digital Transformation Initiative', 
     'Comprehensive value analysis for digital transformation', 
     'SaaS', 'mid-market', 'active', 2500000, 0.85, 12),
    
    ('f1eebc99-9c0b-4ef8-bb6d-6bb9bd380a17', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12',
     (SELECT id FROM users WHERE email = 'jane.smith@techstart.io'),
     'TechStart Growth Acceleration Plan',
     'Strategic value drivers for rapid scaling',
     'FinTech', 'startup', 'active', 1800000, 0.78, 9),
    
    ('f2eebc99-9c0b-4ef8-bb6d-6bb9bd380a18', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13',
     (SELECT id FROM users WHERE email = 'mike.wilson@enterprise.co'),
     'Enterprise Healthcare Optimization',
     'Operational efficiency and patient outcome improvements',
     'Healthcare', 'enterprise', 'active', 5000000, 0.92, 18),
    
    ('f3eebc99-9c0b-4ef8-bb6d-6bb9bd380a19', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14',
     (SELECT id FROM users WHERE email = 'demo@valueverse.ai'),
     'CloudScale Infrastructure Modernization',
     'Cloud-native transformation roadmap',
     'Cloud Infrastructure', 'growth', 'draft', 3200000, 0.81, 15),
    
    ('f4eebc99-9c0b-4ef8-bb6d-6bb9bd380a20', 'e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15',
     (SELECT id FROM users WHERE email = 'sarah.jones@fintech.ai'),
     'DataFlow Revenue Optimization',
     'Analytics-driven revenue growth strategy',
     'Analytics', 'mid-market', 'active', 2100000, 0.88, 10)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- SAMPLE VALUE DRIVERS
-- ============================================================================

-- Value drivers for Acme Corp
INSERT INTO value_drivers (value_model_id, name, category, impact_area, potential_value, effort_required, time_to_value, confidence, description) VALUES
    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', 'Process Automation', 'efficiency', 'operational', 750000, 'medium', 3, 0.85,
     'Automate manual processes to reduce operational costs by 30%'),
    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', 'Customer Retention Improvement', 'growth', 'revenue', 500000, 'low', 2, 0.82,
     'Implement predictive analytics to reduce churn by 25%'),
    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', 'Sales Enablement Platform', 'growth', 'revenue', 600000, 'high', 6, 0.78,
     'Deploy AI-powered sales tools to increase conversion by 40%'),
    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', 'Cloud Cost Optimization', 'efficiency', 'cost', 400000, 'low', 1, 0.90,
     'Optimize cloud infrastructure to reduce costs by 35%'),
    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', 'Data Monetization', 'innovation', 'revenue', 250000, 'medium', 4, 0.75,
     'Create new revenue streams from data products');

-- Value drivers for TechStart Inc
INSERT INTO value_drivers (value_model_id, name, category, impact_area, potential_value, effort_required, time_to_value, confidence, description) VALUES
    ('f1eebc99-9c0b-4ef8-bb6d-6bb9bd380a17', 'Market Expansion', 'growth', 'revenue', 800000, 'high', 6, 0.77,
     'Expand to 3 new geographic markets'),
    ('f1eebc99-9c0b-4ef8-bb6d-6bb9bd380a17', 'Product Innovation', 'innovation', 'competitive', 600000, 'medium', 4, 0.81,
     'Launch 2 new product features for competitive advantage'),
    ('f1eebc99-9c0b-4ef8-bb6d-6bb9bd380a17', 'Partnership Development', 'growth', 'strategic', 400000, 'low', 3, 0.79,
     'Establish strategic partnerships for distribution');

-- Value drivers for Enterprise Co
INSERT INTO value_drivers (value_model_id, name, category, impact_area, potential_value, effort_required, time_to_value, confidence, description) VALUES
    ('f2eebc99-9c0b-4ef8-bb6d-6bb9bd380a18', 'Clinical Workflow Optimization', 'efficiency', 'operational', 1500000, 'high', 9, 0.91,
     'Streamline clinical workflows to improve patient throughput by 45%'),
    ('f2eebc99-9c0b-4ef8-bb6d-6bb9bd380a18', 'Predictive Healthcare Analytics', 'innovation', 'quality', 2000000, 'high', 12, 0.88,
     'Implement ML models for early disease detection'),
    ('f2eebc99-9c0b-4ef8-bb6d-6bb9bd380a18', 'Telemedicine Platform', 'growth', 'access', 1500000, 'medium', 6, 0.94,
     'Deploy comprehensive telehealth solution');

-- ============================================================================
-- SAMPLE COMMITMENTS
-- ============================================================================

INSERT INTO commitments (id, value_model_id, company_id, user_id, title, description, target_value, committed_value, status, start_date, end_date) VALUES
    ('a1eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
     (SELECT id FROM users WHERE email = 'john.doe@acmecorp.com'),
     'Q1 2024 Process Automation Initiative',
     'Implement RPA for top 5 manual processes',
     750000, 650000, 'active', '2024-01-01', '2024-12-31'),
    
    ('a2eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380a17', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12',
     (SELECT id FROM users WHERE email = 'jane.smith@techstart.io'),
     'Market Expansion Phase 1',
     'Launch in US West Coast markets',
     800000, 800000, 'active', '2024-02-01', '2024-07-31'),
    
    ('a3eebc99-9c0b-4ef8-bb6d-6bb9bd380a23', 'f2eebc99-9c0b-4ef8-bb6d-6bb9bd380a18', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13',
     (SELECT id FROM users WHERE email = 'mike.wilson@enterprise.co'),
     'Healthcare Digital Transformation',
     'Complete digital transformation of patient care systems',
     5000000, 4500000, 'active', '2024-01-01', '2025-06-30')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- SAMPLE MILESTONES
-- ============================================================================

-- Milestones for Acme Corp commitment
INSERT INTO milestones (commitment_id, name, description, target_date, target_value, status) VALUES
    ('a1eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'Process Mapping Complete', 'Document and analyze all target processes', '2024-03-31', 150000, 'completed'),
    ('a1eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'RPA Platform Selection', 'Select and deploy RPA platform', '2024-04-30', 200000, 'completed'),
    ('a1eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'First Process Automated', 'Deploy automation for invoice processing', '2024-06-30', 300000, 'in_progress'),
    ('a1eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'Full Rollout', 'All 5 processes automated and optimized', '2024-12-31', 100000, 'pending');

-- Milestones for TechStart Inc commitment
INSERT INTO milestones (commitment_id, name, description, target_date, target_value, status) VALUES
    ('a2eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'Market Research', 'Complete market analysis for target regions', '2024-02-28', 100000, 'completed'),
    ('a2eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'Sales Team Hiring', 'Build local sales teams', '2024-03-31', 250000, 'completed'),
    ('a2eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'Product Launch', 'Launch product in new markets', '2024-05-31', 350000, 'in_progress'),
    ('a2eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'Revenue Target', 'Achieve revenue targets', '2024-07-31', 100000, 'pending');

-- ============================================================================
-- SAMPLE EXECUTIONS
-- ============================================================================

INSERT INTO executions (commitment_id, milestone_id, user_id, title, description, status, progress_percentage, value_delivered) VALUES
    ('a1eebc99-9c0b-4ef8-bb6d-6bb9bd380a21',
     (SELECT id FROM milestones WHERE name = 'Process Mapping Complete' AND commitment_id = 'a1eebc99-9c0b-4ef8-bb6d-6bb9bd380a21'),
     (SELECT id FROM users WHERE email = 'john.doe@acmecorp.com'),
     'Process Documentation Completed',
     'Successfully documented all 5 target processes with detailed workflow diagrams',
     'completed', 100, 150000),
    
    ('a1eebc99-9c0b-4ef8-bb6d-6bb9bd380a21',
     (SELECT id FROM milestones WHERE name = 'First Process Automated' AND commitment_id = 'a1eebc99-9c0b-4ef8-bb6d-6bb9bd380a21'),
     (SELECT id FROM users WHERE email = 'john.doe@acmecorp.com'),
     'Invoice Processing Automation',
     'Implementing RPA for invoice processing workflow',
     'in_progress', 65, 195000),
    
    ('a2eebc99-9c0b-4ef8-bb6d-6bb9bd380a22',
     (SELECT id FROM milestones WHERE name = 'Product Launch' AND commitment_id = 'a2eebc99-9c0b-4ef8-bb6d-6bb9bd380a22'),
     (SELECT id FROM users WHERE email = 'jane.smith@techstart.io'),
     'West Coast Product Launch',
     'Rolling out product in California and Washington',
     'in_progress', 40, 140000)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- SAMPLE AMPLIFICATIONS
-- ============================================================================

INSERT INTO amplifications (execution_id, company_id, user_id, type, title, content, impact_summary, visibility) VALUES
    ((SELECT id FROM executions WHERE title = 'Process Documentation Completed'),
     'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
     (SELECT id FROM users WHERE email = 'john.doe@acmecorp.com'),
     'success_story',
     'Acme Corp Achieves 30% Cost Reduction Through Process Automation',
     'Acme Corp successfully automated their top 5 manual processes, resulting in significant operational improvements...',
     '30% cost reduction, 50% faster processing time, 90% error reduction',
     'public'),
    
    ((SELECT id FROM executions WHERE title = 'West Coast Product Launch'),
     'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12',
     (SELECT id FROM users WHERE email = 'jane.smith@techstart.io'),
     'case_study',
     'TechStart''s Successful Market Expansion Strategy',
     'How TechStart Inc leveraged data-driven insights to successfully expand into new markets...',
     '200% revenue growth, 150 new enterprise customers, 3 new markets',
     'internal')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- SAMPLE NOTIFICATIONS
-- ============================================================================

INSERT INTO notifications (user_id, type, title, message, data, read) VALUES
    ((SELECT id FROM users WHERE email = 'john.doe@acmecorp.com'),
     'milestone_complete',
     'Milestone Completed!',
     'Process Mapping Complete milestone has been successfully completed.',
     '{"milestone_id": "' || (SELECT id FROM milestones WHERE name = 'Process Mapping Complete' LIMIT 1) || '"}',
     false),
    
    ((SELECT id FROM users WHERE email = 'jane.smith@techstart.io'),
     'commitment_update',
     'Commitment Progress Update',
     'Your Market Expansion Phase 1 commitment is 75% complete.',
     '{"commitment_id": "a2eebc99-9c0b-4ef8-bb6d-6bb9bd380a22", "progress": 75}',
     false),
    
    ((SELECT id FROM users WHERE email = 'admin@valueverse.ai'),
     'system',
     'New User Registration',
     'A new user has registered: sarah.jones@fintech.ai',
     '{"user_email": "sarah.jones@fintech.ai"}',
     true)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- SAMPLE AUDIT LOGS
-- ============================================================================

INSERT INTO audit_logs (user_id, entity_type, entity_id, action, changes, ip_address, user_agent) VALUES
    ((SELECT id FROM users WHERE email = 'john.doe@acmecorp.com'),
     'value_model',
     'f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16',
     'update',
     '{"status": {"old": "draft", "new": "active"}}',
     '192.168.1.100',
     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0'),
    
    ((SELECT id FROM users WHERE email = 'admin@valueverse.ai'),
     'user',
     (SELECT id FROM users WHERE email = 'demo@valueverse.ai'),
     'create',
     '{"email": "demo@valueverse.ai", "role": "user"}',
     '10.0.0.1',
     'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Sample data seeding completed successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Created:';
    RAISE NOTICE '  - 6 Users (including admin)';
    RAISE NOTICE '  - 5 Companies';
    RAISE NOTICE '  - 5 Value Models';
    RAISE NOTICE '  - 14 Value Drivers';
    RAISE NOTICE '  - 3 Commitments';
    RAISE NOTICE '  - 8 Milestones';
    RAISE NOTICE '  - 3 Executions';
    RAISE NOTICE '  - 2 Amplifications';
    RAISE NOTICE '  - 3 Notifications';
    RAISE NOTICE '  - 2 Audit Log entries';
    RAISE NOTICE '';
    RAISE NOTICE 'Default login credentials:';
    RAISE NOTICE '  Admin: admin@valueverse.ai / admin123';
    RAISE NOTICE '  Demo:  demo@valueverse.ai / demo123';
END $$;

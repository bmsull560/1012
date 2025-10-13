# ValueVerse B2B SaaS Pay-As-You-Use Billing System Architecture

## Executive Summary

This document outlines the comprehensive architecture for a production-ready B2B SaaS pay-as-you-use subscription and billing system. The system is designed to handle enterprise-scale customers with complex billing requirements, supporting multiple pricing models, real-time usage tracking, and automated billing operations.

## System Architecture Overview

### Core Components

1. **Usage Metering Service** - Real-time event collection and aggregation
2. **Billing Engine** - Pricing calculations, proration, and invoice generation
3. **Subscription Manager** - Plan management and lifecycle operations
4. **Payment Gateway Service** - Multi-provider payment processing
5. **Customer Portal** - Self-service dashboard and management
6. **Admin Portal** - Billing operations and configuration
7. **Analytics Service** - Revenue reporting and forecasting
8. **Notification Service** - Alerts, invoices, and communications

### Microservices Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
│                    (Kong/AWS API Gateway)                        │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
    ┌────────▼────────┐                  ┌───────▼──────┐
    │  Load Balancer  │                  │   CDN        │
    │   (AWS ALB)     │                  │ (CloudFlare) │
    └────────┬────────┘                  └───────┬──────┘
             │                                    │
┌────────────┼────────────────────────────────────┼───────────────┐
│            │         Microservices Layer        │               │
│  ┌─────────▼─────────┐              ┌──────────▼──────────┐    │
│  │  Usage Metering   │              │  Customer Portal    │    │
│  │     Service       │              │    (Next.js)        │    │
│  └─────────┬─────────┘              └──────────┬──────────┘    │
│            │                                    │               │
│  ┌─────────▼─────────┐              ┌──────────▼──────────┐    │
│  │  Billing Engine   │              │   Admin Portal      │    │
│  │    (FastAPI)      │              │    (React)          │    │
│  └─────────┬─────────┘              └──────────────────────┘   │
│            │                                                    │
│  ┌─────────▼─────────┐              ┌─────────────────────┐    │
│  │   Subscription    │              │  Analytics Service  │    │
│  │     Manager       │              │   (FastAPI + BI)    │    │
│  └─────────┬─────────┘              └─────────────────────┘    │
│            │                                                    │
│  ┌─────────▼─────────┐              ┌─────────────────────┐    │
│  │  Payment Gateway  │              │ Notification Service│    │
│  │     Service       │              │  (Email/SMS/Push)   │    │
│  └───────────────────┘              └─────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
             │                                    │
┌────────────▼────────────────────────────────────▼───────────────┐
│                         Data Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  PostgreSQL  │  │   Redis      │  │   TimescaleDB      │    │
│  │  (Primary)   │  │   (Cache)    │  │  (Usage Events)    │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  Kafka       │  │ Elasticsearch │  │    S3 Storage      │    │
│  │ (Event Bus)  │  │  (Logging)    │  │  (Documents/Files) │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

## Component Specifications

### 1. Usage Metering Service

**Responsibilities:**
- Collect usage events from all services
- Aggregate and store metrics in time-series database
- Provide real-time usage APIs
- Support multiple metric types (API calls, storage, compute, bandwidth)

**Key Features:**
- Event ingestion rate: 100,000+ events/second
- Sub-second aggregation latency
- Configurable aggregation windows
- Automatic data retention and archival

### 2. Billing Engine

**Responsibilities:**
- Calculate charges based on usage and pricing rules
- Handle proration for mid-cycle changes
- Apply discounts, credits, and adjustments
- Generate invoices and statements

**Pricing Models Supported:**
- Flat-rate subscriptions
- Per-unit pricing (API calls, storage GB, compute hours)
- Tiered pricing with volume discounts
- Package bundles with overage charges
- Commitment-based pricing with discounts
- Custom enterprise agreements

### 3. Subscription Manager

**Responsibilities:**
- Manage subscription lifecycle (trial, active, suspended, cancelled)
- Handle plan changes and upgrades/downgrades
- Enforce feature flags and usage limits
- Manage billing cycles and renewals

### 4. Payment Gateway Service

**Integrations:**
- Stripe (primary)
- PayPal
- Wire transfers for enterprise
- ACH/SEPA direct debit
- Credit/debit cards
- Corporate purchase orders

**Features:**
- PCI DSS compliant tokenization
- Retry logic for failed payments
- Dunning management
- Chargeback handling

## Database Schema Design

### Core Tables

```sql
-- Organizations (Tenants)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    billing_email VARCHAR(255),
    tax_id VARCHAR(50),
    billing_address JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Subscription Plans
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    pricing_model VARCHAR(50), -- 'flat_rate', 'usage_based', 'hybrid'
    base_price DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    billing_period VARCHAR(20), -- 'monthly', 'annual', 'quarterly'
    trial_period_days INTEGER DEFAULT 0,
    features JSONB,
    limits JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    plan_id UUID REFERENCES subscription_plans(id),
    status VARCHAR(50), -- 'trialing', 'active', 'past_due', 'canceled', 'paused'
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    trial_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT false,
    canceled_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Usage Events (TimescaleDB Hypertable)
CREATE TABLE usage_events (
    id UUID DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    subscription_id UUID,
    metric_name VARCHAR(100) NOT NULL,
    quantity DECIMAL(20,6) NOT NULL,
    unit VARCHAR(50), -- 'api_call', 'gb_storage', 'compute_hour'
    timestamp TIMESTAMP NOT NULL,
    properties JSONB,
    idempotency_key VARCHAR(255) UNIQUE,
    PRIMARY KEY (timestamp, id)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('usage_events', 'timestamp');

-- Invoices
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    subscription_id UUID REFERENCES subscriptions(id),
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(50), -- 'draft', 'open', 'paid', 'void', 'uncollectible'
    currency VARCHAR(3) DEFAULT 'USD',
    subtotal DECIMAL(10,2),
    tax DECIMAL(10,2),
    total DECIMAL(10,2),
    amount_paid DECIMAL(10,2) DEFAULT 0,
    amount_due DECIMAL(10,2),
    billing_period_start TIMESTAMP,
    billing_period_end TIMESTAMP,
    due_date DATE,
    paid_at TIMESTAMP,
    payment_method VARCHAR(50),
    line_items JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Payment Methods
CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    type VARCHAR(50), -- 'card', 'bank_account', 'paypal', 'wire'
    provider VARCHAR(50), -- 'stripe', 'paypal', 'manual'
    provider_customer_id VARCHAR(255),
    provider_payment_method_id VARCHAR(255),
    is_default BOOLEAN DEFAULT false,
    last_four VARCHAR(4),
    brand VARCHAR(50),
    exp_month INTEGER,
    exp_year INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Billing Transactions
CREATE TABLE billing_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    invoice_id UUID REFERENCES invoices(id),
    payment_method_id UUID REFERENCES payment_methods(id),
    type VARCHAR(50), -- 'charge', 'refund', 'credit', 'adjustment'
    status VARCHAR(50), -- 'pending', 'processing', 'succeeded', 'failed'
    amount DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    provider_transaction_id VARCHAR(255),
    failure_reason TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Pricing Rules
CREATE TABLE pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES subscription_plans(id),
    metric_name VARCHAR(100),
    pricing_type VARCHAR(50), -- 'per_unit', 'tiered', 'volume', 'package'
    rules JSONB, -- Complex pricing configuration
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Usage Limits
CREATE TABLE usage_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID REFERENCES subscriptions(id),
    metric_name VARCHAR(100),
    limit_value DECIMAL(20,6),
    period VARCHAR(20), -- 'daily', 'monthly', 'total'
    action_on_exceed VARCHAR(50), -- 'block', 'allow_overage', 'notify'
    current_usage DECIMAL(20,6) DEFAULT 0,
    reset_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Specifications

### Core Billing Endpoints

```yaml
openapi: 3.0.0
info:
  title: ValueVerse Billing API
  version: 1.0.0
  
paths:
  /api/v1/billing/subscriptions:
    get:
      summary: List all subscriptions
      parameters:
        - name: organization_id
          in: query
          schema:
            type: string
        - name: status
          in: query
          schema:
            type: string
            enum: [active, canceled, past_due]
      responses:
        200:
          description: List of subscriptions
          
    post:
      summary: Create new subscription
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                organization_id:
                  type: string
                plan_id:
                  type: string
                payment_method_id:
                  type: string
                trial_period_days:
                  type: integer
                metadata:
                  type: object
                  
  /api/v1/billing/usage:
    post:
      summary: Record usage event
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                organization_id:
                  type: string
                metric_name:
                  type: string
                quantity:
                  type: number
                timestamp:
                  type: string
                  format: date-time
                idempotency_key:
                  type: string
                  
  /api/v1/billing/usage/summary:
    get:
      summary: Get usage summary
      parameters:
        - name: organization_id
          in: query
          required: true
          schema:
            type: string
        - name: start_date
          in: query
          schema:
            type: string
            format: date
        - name: end_date
          in: query
          schema:
            type: string
            format: date
        - name: metric_name
          in: query
          schema:
            type: string
            
  /api/v1/billing/invoices:
    get:
      summary: List invoices
      parameters:
        - name: organization_id
          in: query
          schema:
            type: string
        - name: status
          in: query
          schema:
            type: string
            
    post:
      summary: Create invoice
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                organization_id:
                  type: string
                subscription_id:
                  type: string
                line_items:
                  type: array
                  items:
                    type: object
                    
  /api/v1/billing/payment-methods:
    post:
      summary: Add payment method
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                organization_id:
                  type: string
                type:
                  type: string
                  enum: [card, bank_account, paypal]
                provider_token:
                  type: string
                is_default:
                  type: boolean
```

## Security & Compliance

### PCI DSS Compliance
- No credit card data stored in our systems
- All payment tokens handled by certified providers
- TLS 1.3 for all data transmission
- Regular security audits and penetration testing

### SOX Compliance
- Complete audit trail for all billing operations
- Role-based access control with segregation of duties
- Immutable transaction logs
- Regular compliance reporting

### Data Protection
- AES-256 encryption at rest
- Field-level encryption for sensitive data
- GDPR/CCPA compliant data handling
- Automated data retention and purging

## Monitoring & Observability

### Key Metrics
- Usage ingestion rate and latency
- Billing calculation accuracy
- Payment success/failure rates
- Invoice generation time
- API response times
- System resource utilization

### Alerting Rules
- Failed payment processing
- Abnormal usage patterns
- System errors and failures
- Capacity thresholds
- Security incidents

## Disaster Recovery

### Backup Strategy
- Real-time replication to standby region
- Daily automated backups with 30-day retention
- Point-in-time recovery capability
- Regular disaster recovery drills

### RTO/RPO Targets
- Recovery Time Objective (RTO): 4 hours
- Recovery Point Objective (RPO): 1 hour
- 99.99% uptime SLA

## Scalability Considerations

### Horizontal Scaling
- Microservices auto-scaling based on load
- Database read replicas for query distribution
- Caching layer with Redis clusters
- CDN for static assets

### Performance Optimization
- Database query optimization and indexing
- Batch processing for large operations
- Asynchronous job queues for heavy tasks
- Rate limiting and throttling

### Capacity Planning
- Support for 10,000+ concurrent organizations
- Process 1M+ usage events per minute
- Generate 100,000+ invoices per day
- Handle 10,000+ payment transactions per hour

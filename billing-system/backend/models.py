"""
Database models for ValueVerse Billing System
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID
import uuid
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    ForeignKey, JSON, Numeric, Date, Text, UniqueConstraint,
    Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

# ==================== Core Models ====================

class Organization(Base):
    """Multi-tenant organization model"""
    __tablename__ = "organizations"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(50), default="active")
    billing_email = Column(String(255))
    tax_id = Column(String(50))
    billing_address = Column(JSONB, default={})
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="organization", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="organization", cascade="all, delete-orphan")
    payment_methods = relationship("PaymentMethod", back_populates="organization", cascade="all, delete-orphan")
    usage_events = relationship("UsageEvent", back_populates="organization", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_organizations_status", "status"),
        CheckConstraint("status IN ('active', 'suspended', 'deleted')", name="check_org_status"),
    )
    
    @validates("billing_email")
    def validate_email(self, key, email):
        if email and "@" not in email:
            raise ValueError("Invalid email address")
        return email


class SubscriptionPlan(Base):
    """Subscription plan configuration"""
    __tablename__ = "subscription_plans"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    pricing_model = Column(String(50), nullable=False)  # flat_rate, usage_based, hybrid
    base_price = Column(Numeric(10, 2), default=Decimal("0.00"))
    currency = Column(String(3), default="USD")
    billing_period = Column(String(20), nullable=False)  # monthly, annual, quarterly
    trial_period_days = Column(Integer, default=0)
    features = Column(JSONB, default={})
    limits = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")
    pricing_rules = relationship("PricingRule", back_populates="plan", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_plans_active", "is_active"),
        CheckConstraint("pricing_model IN ('flat_rate', 'usage_based', 'hybrid')", name="check_pricing_model"),
        CheckConstraint("billing_period IN ('monthly', 'annual', 'quarterly')", name="check_billing_period"),
        CheckConstraint("base_price >= 0", name="check_base_price_positive"),
    )


class Subscription(Base):
    """Active subscriptions for organizations"""
    __tablename__ = "subscriptions"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(PostgresUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    plan_id = Column(PostgresUUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(String(50), nullable=False)
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    trial_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription")
    usage_limits = relationship("UsageLimit", back_populates="subscription", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_subscription_org_status", "organization_id", "status"),
        Index("idx_subscription_period", "current_period_start", "current_period_end"),
        CheckConstraint(
            "status IN ('trialing', 'active', 'past_due', 'canceled', 'paused')",
            name="check_subscription_status"
        ),
        CheckConstraint(
            "current_period_end > current_period_start",
            name="check_period_validity"
        ),
    )
    
    @hybrid_property
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status in ("active", "trialing") and (
            not self.cancel_at_period_end or datetime.utcnow() < self.current_period_end
        )


class UsageEvent(Base):
    """Time-series usage events (TimescaleDB hypertable)"""
    __tablename__ = "usage_events"
    
    id = Column(PostgresUUID(as_uuid=True), default=uuid.uuid4)
    organization_id = Column(PostgresUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    subscription_id = Column(PostgresUUID(as_uuid=True), ForeignKey("subscriptions.id"))
    metric_name = Column(String(100), nullable=False)
    quantity = Column(Numeric(20, 6), nullable=False)
    unit = Column(String(50))
    timestamp = Column(DateTime, nullable=False, primary_key=True)
    properties = Column(JSONB, default={})
    idempotency_key = Column(String(255), unique=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="usage_events")
    
    __table_args__ = (
        Index("idx_usage_org_metric_time", "organization_id", "metric_name", "timestamp"),
        Index("idx_usage_timestamp", "timestamp"),
        Index("idx_usage_idempotency", "idempotency_key"),
        CheckConstraint("quantity >= 0", name="check_quantity_positive"),
    )


class Invoice(Base):
    """Billing invoices"""
    __tablename__ = "invoices"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(PostgresUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    subscription_id = Column(PostgresUUID(as_uuid=True), ForeignKey("subscriptions.id"))
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(50), nullable=False)
    currency = Column(String(3), default="USD")
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), default=Decimal("0.00"))
    total = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=Decimal("0.00"))
    amount_due = Column(Numeric(10, 2), nullable=False)
    billing_period_start = Column(DateTime)
    billing_period_end = Column(DateTime)
    due_date = Column(Date)
    paid_at = Column(DateTime)
    payment_method = Column(String(50))
    line_items = Column(JSONB, default=[])
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="invoices")
    subscription = relationship("Subscription", back_populates="invoices")
    transactions = relationship("BillingTransaction", back_populates="invoice")
    
    __table_args__ = (
        Index("idx_invoice_org_status", "organization_id", "status"),
        Index("idx_invoice_due_date", "due_date"),
        CheckConstraint(
            "status IN ('draft', 'open', 'paid', 'void', 'uncollectible')",
            name="check_invoice_status"
        ),
        CheckConstraint("total >= 0", name="check_total_positive"),
        CheckConstraint("amount_due >= 0", name="check_amount_due_positive"),
    )
    
    @hybrid_property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return (
            self.status == "open" 
            and self.due_date 
            and datetime.utcnow().date() > self.due_date
        )


class PaymentMethod(Base):
    """Stored payment methods for organizations"""
    __tablename__ = "payment_methods"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(PostgresUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    type = Column(String(50), nullable=False)  # card, bank_account, paypal, wire
    provider = Column(String(50), nullable=False)  # stripe, paypal, manual
    provider_customer_id = Column(String(255))
    provider_payment_method_id = Column(String(255))
    is_default = Column(Boolean, default=False)
    last_four = Column(String(4))
    brand = Column(String(50))
    exp_month = Column(Integer)
    exp_year = Column(Integer)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="payment_methods")
    transactions = relationship("BillingTransaction", back_populates="payment_method")
    
    __table_args__ = (
        Index("idx_payment_method_org", "organization_id"),
        Index("idx_payment_method_default", "organization_id", "is_default"),
        CheckConstraint(
            "type IN ('card', 'bank_account', 'paypal', 'wire')",
            name="check_payment_type"
        ),
        CheckConstraint(
            "provider IN ('stripe', 'paypal', 'manual')",
            name="check_payment_provider"
        ),
    )


class BillingTransaction(Base):
    """Payment transactions and adjustments"""
    __tablename__ = "billing_transactions"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(PostgresUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    invoice_id = Column(PostgresUUID(as_uuid=True), ForeignKey("invoices.id"))
    payment_method_id = Column(PostgresUUID(as_uuid=True), ForeignKey("payment_methods.id"))
    type = Column(String(50), nullable=False)  # charge, refund, credit, adjustment
    status = Column(String(50), nullable=False)  # pending, processing, succeeded, failed
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    provider_transaction_id = Column(String(255))
    failure_reason = Column(Text)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="transactions")
    payment_method = relationship("PaymentMethod", back_populates="transactions")
    
    __table_args__ = (
        Index("idx_transaction_org_status", "organization_id", "status"),
        Index("idx_transaction_invoice", "invoice_id"),
        CheckConstraint(
            "type IN ('charge', 'refund', 'credit', 'adjustment')",
            name="check_transaction_type"
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'succeeded', 'failed')",
            name="check_transaction_status"
        ),
    )


class PricingRule(Base):
    """Complex pricing rules for usage-based billing"""
    __tablename__ = "pricing_rules"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(PostgresUUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)
    pricing_type = Column(String(50), nullable=False)  # per_unit, tiered, volume, package
    rules = Column(JSONB, nullable=False)  # Complex pricing configuration
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    plan = relationship("SubscriptionPlan", back_populates="pricing_rules")
    
    __table_args__ = (
        Index("idx_pricing_plan_metric", "plan_id", "metric_name"),
        UniqueConstraint("plan_id", "metric_name", name="unique_plan_metric"),
        CheckConstraint(
            "pricing_type IN ('per_unit', 'tiered', 'volume', 'package')",
            name="check_pricing_type"
        ),
    )
    
    @validates("rules")
    def validate_rules(self, key, rules):
        """Validate pricing rules structure"""
        if not isinstance(rules, dict):
            raise ValueError("Rules must be a dictionary")
        
        if self.pricing_type == "per_unit":
            if "unit_price" not in rules:
                raise ValueError("Per-unit pricing requires 'unit_price'")
        elif self.pricing_type in ("tiered", "volume"):
            if "tiers" not in rules or not isinstance(rules["tiers"], list):
                raise ValueError(f"{self.pricing_type} pricing requires 'tiers' list")
        elif self.pricing_type == "package":
            required_fields = ["package_size", "package_price"]
            if not all(field in rules for field in required_fields):
                raise ValueError(f"Package pricing requires {required_fields}")
        
        return rules


class UsageLimit(Base):
    """Usage limits and quotas for subscriptions"""
    __tablename__ = "usage_limits"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(PostgresUUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)
    limit_value = Column(Numeric(20, 6), nullable=False)
    period = Column(String(20), nullable=False)  # daily, monthly, total
    action_on_exceed = Column(String(50), nullable=False)  # block, allow_overage, notify
    current_usage = Column(Numeric(20, 6), default=Decimal("0.00"))
    reset_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="usage_limits")
    
    __table_args__ = (
        Index("idx_usage_limit_subscription_metric", "subscription_id", "metric_name"),
        UniqueConstraint("subscription_id", "metric_name", name="unique_subscription_metric_limit"),
        CheckConstraint("limit_value >= 0", name="check_limit_positive"),
        CheckConstraint(
            "period IN ('daily', 'monthly', 'total')",
            name="check_limit_period"
        ),
        CheckConstraint(
            "action_on_exceed IN ('block', 'allow_overage', 'notify')",
            name="check_limit_action"
        ),
    )


# ==================== Audit Models ====================

class AuditLog(Base):
    """Audit trail for compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(PostgresUUID(as_uuid=True))
    user_id = Column(PostgresUUID(as_uuid=True))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(PostgresUUID(as_uuid=True))
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index("idx_audit_org_timestamp", "organization_id", "timestamp"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
    )

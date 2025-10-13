"""
Unit tests for database models
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4

from backend.models import (
    Organization, SubscriptionPlan, Subscription,
    UsageEvent, Invoice, PaymentMethod,
    PricingRule, UsageLimit
)

class TestOrganizationModel:
    """Test Organization model"""
    
    def test_organization_creation(self):
        """Test creating an organization"""
        org = Organization(
            id=uuid4(),
            name="Test Corp",
            slug="test-corp",
            status="active",
            billing_email="billing@test.com"
        )
        
        assert org.name == "Test Corp"
        assert org.slug == "test-corp"
        assert org.status == "active"
    
    def test_organization_email_validation(self):
        """Test email validation"""
        org = Organization(id=uuid4(), name="Test", slug="test")
        
        # Valid email
        org.billing_email = "valid@email.com"
        assert org.billing_email == "valid@email.com"
        
        # Invalid email should raise
        with pytest.raises(ValueError):
            org.billing_email = "invalid-email"

class TestSubscriptionModel:
    """Test Subscription model"""
    
    def test_subscription_is_active_property(self):
        """Test is_active hybrid property"""
        now = datetime.utcnow()
        
        # Active subscription
        sub = Subscription(
            id=uuid4(),
            organization_id=uuid4(),
            plan_id=uuid4(),
            status="active",
            current_period_start=now,
            current_period_end=now + timedelta(days=30)
        )
        assert sub.is_active is True
        
        # Canceled subscription
        sub.status = "canceled"
        assert sub.is_active is False
        
        # Trialing subscription
        sub.status = "trialing"
        assert sub.is_active is True
    
    def test_subscription_cancel_at_period_end(self):
        """Test cancel_at_period_end behavior"""
        now = datetime.utcnow()
        sub = Subscription(
            id=uuid4(),
            organization_id=uuid4(),
            plan_id=uuid4(),
            status="active",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            cancel_at_period_end=True
        )
        
        # Should still be active until period ends
        assert sub.is_active is True

class TestPricingRuleModel:
    """Test PricingRule model"""
    
    def test_pricing_rule_validation_per_unit(self):
        """Test per-unit pricing rule validation"""
        rule = PricingRule(
            id=uuid4(),
            plan_id=uuid4(),
            metric_name="api_calls",
            pricing_type="per_unit"
        )
        
        # Valid rules
        rule.rules = {"unit_price": 0.001}
        assert rule.rules["unit_price"] == 0.001
        
        # Invalid rules (missing unit_price)
        with pytest.raises(ValueError):
            rule.rules = {}
    
    def test_pricing_rule_validation_tiered(self):
        """Test tiered pricing rule validation"""
        rule = PricingRule(
            id=uuid4(),
            plan_id=uuid4(),
            metric_name="storage_gb",
            pricing_type="tiered"
        )
        
        # Valid tiered rules
        rule.rules = {
            "tiers": [
                {"up_to": 100, "unit_price": 0.10},
                {"from": 100, "up_to": 1000, "unit_price": 0.08},
                {"from": 1000, "unit_price": 0.05}
            ]
        }
        assert len(rule.rules["tiers"]) == 3
        
        # Invalid rules (not a list)
        with pytest.raises(ValueError):
            rule.rules = {"tiers": "not a list"}
    
    def test_pricing_rule_validation_package(self):
        """Test package pricing rule validation"""
        rule = PricingRule(
            id=uuid4(),
            plan_id=uuid4(),
            metric_name="compute_hours",
            pricing_type="package"
        )
        
        # Valid package rules
        rule.rules = {
            "package_size": 100,
            "package_price": 50,
            "overage_unit_price": 0.75
        }
        assert rule.rules["package_size"] == 100
        
        # Invalid rules (missing required fields)
        with pytest.raises(ValueError):
            rule.rules = {"package_size": 100}  # Missing package_price

class TestInvoiceModel:
    """Test Invoice model"""
    
    def test_invoice_is_overdue_property(self):
        """Test is_overdue hybrid property"""
        today = datetime.utcnow().date()
        
        # Not overdue - future due date
        invoice = Invoice(
            id=uuid4(),
            organization_id=uuid4(),
            invoice_number="INV-001",
            status="open",
            currency="USD",
            subtotal=Decimal("100"),
            total=Decimal("100"),
            amount_due=Decimal("100"),
            due_date=today + timedelta(days=30)
        )
        assert invoice.is_overdue is False
        
        # Overdue - past due date
        invoice.due_date = today - timedelta(days=1)
        assert invoice.is_overdue is True
        
        # Paid invoice - not overdue even if past due date
        invoice.status = "paid"
        assert invoice.is_overdue is False

class TestUsageEventModel:
    """Test UsageEvent model"""
    
    @pytest.mark.asyncio
    async def test_usage_event_with_idempotency(self, test_db):
        """Test usage event with idempotency key"""
        event = UsageEvent(
            id=uuid4(),
            organization_id=uuid4(),
            metric_name="api_calls",
            quantity=Decimal("100"),
            unit="calls",
            timestamp=datetime.utcnow(),
            idempotency_key="unique-key-123"
        )
        
        test_db.add(event)
        await test_db.commit()
        
        # Try to add duplicate with same idempotency key
        duplicate = UsageEvent(
            id=uuid4(),
            organization_id=uuid4(),
            metric_name="api_calls",
            quantity=Decimal("200"),
            unit="calls",
            timestamp=datetime.utcnow(),
            idempotency_key="unique-key-123"
        )
        
        test_db.add(duplicate)
        
        # Should fail due to unique constraint
        with pytest.raises(Exception):
            await test_db.commit()

class TestUsageLimitModel:
    """Test UsageLimit model"""
    
    def test_usage_limit_creation(self):
        """Test creating usage limits"""
        limit = UsageLimit(
            id=uuid4(),
            subscription_id=uuid4(),
            metric_name="api_calls",
            limit_value=Decimal("10000"),
            period="monthly",
            action_on_exceed="block"
        )
        
        assert limit.limit_value == Decimal("10000")
        assert limit.period == "monthly"
        assert limit.action_on_exceed == "block"
        assert limit.current_usage == Decimal("0")
    
    def test_usage_limit_reset_at(self):
        """Test reset_at timestamp"""
        now = datetime.utcnow()
        next_month = now + timedelta(days=30)
        
        limit = UsageLimit(
            id=uuid4(),
            subscription_id=uuid4(),
            metric_name="storage_gb",
            limit_value=Decimal("1000"),
            period="monthly",
            action_on_exceed="notify",
            reset_at=next_month
        )
        
        assert limit.reset_at == next_month

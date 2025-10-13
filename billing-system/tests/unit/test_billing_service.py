"""
Unit tests for billing service functionality
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4

from backend.billing_service import BillingService, UsageEventCreate
from backend.models import UsageEvent, Invoice

@pytest.mark.asyncio
class TestBillingService:
    """Test suite for BillingService class"""
    
    async def test_record_usage_event_success(
        self, test_db, test_organization, test_subscription, mock_redis
    ):
        """Test successful usage event recording"""
        service = BillingService()
        service.redis_client = mock_redis
        
        event_data = UsageEventCreate(
            metric_name="api_calls",
            quantity=Decimal("100"),
            unit="calls",
            idempotency_key="test-123"
        )
        
        result = await service.record_usage(
            test_organization.id,
            event_data,
            test_db
        )
        
        assert result is not None
        assert result.metric_name == "api_calls"
        assert result.quantity == Decimal("100")
    
    async def test_record_usage_event_idempotency(
        self, test_db, test_organization, test_subscription, mock_redis
    ):
        """Test idempotency of usage event recording"""
        service = BillingService()
        service.redis_client = mock_redis
        
        event_data = UsageEventCreate(
            metric_name="api_calls",
            quantity=Decimal("100"),
            unit="calls",
            idempotency_key="test-duplicate"
        )
        
        # First call should succeed
        result1 = await service.record_usage(
            test_organization.id,
            event_data,
            test_db
        )
        assert result1 is not None
        
        # Second call with same idempotency key should return None
        result2 = await service.record_usage(
            test_organization.id,
            event_data,
            test_db
        )
        assert result2 is None
    
    async def test_calculate_usage_charges(
        self, test_db, test_subscription, test_usage_events, test_pricing_rules
    ):
        """Test usage charge calculation"""
        service = BillingService()
        
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        charges = await service.calculate_usage_charges(
            test_subscription.id,
            start_date,
            end_date,
            test_db
        )
        
        assert len(charges) > 0
        assert all("metric_name" in charge for charge in charges)
        assert all("total" in charge for charge in charges)
    
    async def test_calculate_tiered_pricing(self):
        """Test tiered pricing calculation"""
        service = BillingService()
        
        rule = type('PricingRule', (), {
            'pricing_type': 'tiered',
            'rules': {
                'tiers': [
                    {'up_to': 1000, 'unit_price': 0.01},
                    {'from': 1000, 'up_to': 10000, 'unit_price': 0.008},
                    {'from': 10000, 'unit_price': 0.005}
                ]
            }
        })()
        
        # Test with 15000 units
        charge = await service._calculate_charge_for_rule(rule, Decimal("15000"))
        
        # Should be: 1000*0.01 + 9000*0.008 + 5000*0.005 = 10 + 72 + 25 = 107
        assert charge["total"] == Decimal("107")
    
    async def test_calculate_volume_pricing(self):
        """Test volume-based pricing calculation"""
        service = BillingService()
        
        rule = type('PricingRule', (), {
            'pricing_type': 'volume',
            'rules': {
                'tiers': [
                    {'from': 0, 'up_to': 1000, 'unit_price': 0.01},
                    {'from': 1000, 'up_to': 10000, 'unit_price': 0.008},
                    {'from': 10000, 'up_to': float('inf'), 'unit_price': 0.005}
                ]
            }
        })()
        
        # Test with 5000 units - should use middle tier price for all units
        charge = await service._calculate_charge_for_rule(rule, Decimal("5000"))
        
        # Should be: 5000 * 0.008 = 40
        assert charge["total"] == Decimal("40")
    
    async def test_calculate_package_pricing(self):
        """Test package pricing with overage"""
        service = BillingService()
        
        rule = type('PricingRule', (), {
            'pricing_type': 'package',
            'rules': {
                'package_size': 1000,
                'package_price': 10,
                'overage_unit_price': 0.02
            }
        })()
        
        # Test with 2500 units - needs 3 packages, no overage
        charge = await service._calculate_charge_for_rule(rule, Decimal("2500"))
        
        # Should be: 3 packages * $10 = $30
        assert charge["total"] == Decimal("30")
    
    async def test_generate_invoice(
        self, test_db, test_subscription, test_pricing_rules, mock_redis
    ):
        """Test invoice generation"""
        service = BillingService()
        service.redis_client = mock_redis
        
        invoice = await service.generate_invoice(test_subscription.id, test_db)
        
        assert invoice is not None
        assert invoice.subscription_id == test_subscription.id
        assert invoice.status == "draft"
        assert invoice.invoice_number.startswith("INV-")
        assert len(invoice.line_items) > 0
    
    async def test_process_payment_success(
        self, test_db, test_organization, test_subscription,
        test_payment_method, mock_stripe
    ):
        """Test successful payment processing"""
        service = BillingService()
        
        # Create test invoice
        invoice = Invoice(
            id=uuid4(),
            organization_id=test_organization.id,
            subscription_id=test_subscription.id,
            invoice_number="INV-TEST-001",
            status="open",
            currency="USD",
            subtotal=Decimal("100"),
            tax=Decimal("0"),
            total=Decimal("100"),
            amount_due=Decimal("100"),
            amount_paid=Decimal("0")
        )
        test_db.add(invoice)
        await test_db.commit()
        
        transaction = await service.process_payment(
            invoice.id,
            test_payment_method.id,
            test_db
        )
        
        assert transaction is not None
        assert transaction.status == "succeeded"
        assert transaction.amount == Decimal("100")
    
    async def test_get_usage_for_period(
        self, test_db, test_organization, test_usage_events
    ):
        """Test usage aggregation for a period"""
        service = BillingService()
        
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        total = await service.get_usage_for_period(
            test_organization.id,
            "api_calls",
            start_date,
            end_date,
            test_db
        )
        
        assert total >= Decimal("0")
    
    async def test_generate_invoice_number(self, test_db):
        """Test invoice number generation"""
        service = BillingService()
        
        invoice_number = await service._generate_invoice_number(test_db)
        
        assert invoice_number.startswith("INV-")
        assert len(invoice_number.split("-")) == 4  # INV-YYYY-MM-00001

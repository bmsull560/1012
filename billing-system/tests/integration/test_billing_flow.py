"""
Integration tests for complete billing flows
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Organization, Subscription, Invoice, PaymentMethod
from backend.billing_service import BillingService

@pytest.mark.asyncio
class TestBillingIntegrationFlow:
    """Test complete billing workflow integration"""
    
    async def test_complete_billing_cycle(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        test_organization: Organization,
        test_plan,
        auth_headers: dict,
        mock_stripe
    ):
        """Test complete billing cycle from subscription to payment"""
        
        # Step 1: Create subscription
        subscription_data = {
            "plan_id": str(test_plan.id),
            "trial_period_days": 0
        }
        
        response = await client.post(
            "/api/v1/billing/subscriptions",
            json=subscription_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        subscription_response = response.json()
        assert subscription_response["status"] == "success"
        subscription_id = subscription_response["data"]["subscription_id"]
        
        # Step 2: Record usage events
        usage_events = [
            {"metric_name": "api_calls", "quantity": 10000, "unit": "calls"},
            {"metric_name": "storage_gb", "quantity": 50, "unit": "gb"},
            {"metric_name": "compute_hours", "quantity": 100, "unit": "hours"}
        ]
        
        for event in usage_events:
            response = await client.post(
                "/api/v1/billing/usage",
                json=event,
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Step 3: Generate invoice (would normally be automated)
        billing_service = BillingService()
        await billing_service.initialize()
        
        invoice = await billing_service.generate_invoice(
            uuid4().UUID(subscription_id),
            test_db
        )
        
        assert invoice is not None
        assert invoice.status == "draft"
        assert invoice.total > 0
        
        # Step 4: Add payment method
        payment_method_data = {
            "type": "card",
            "provider": "stripe",
            "provider_token": "tok_visa",
            "is_default": True
        }
        
        response = await client.post(
            "/api/v1/billing/payment-methods",
            json=payment_method_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        payment_method_id = response.json()["data"]["payment_method_id"]
        
        # Step 5: Process payment
        response = await client.post(
            f"/api/v1/billing/invoices/{invoice.id}/pay",
            json={"payment_method_id": payment_method_id},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        payment_response = response.json()
        assert payment_response["data"]["status"] == "succeeded"
    
    async def test_subscription_upgrade_proration(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        test_subscription: Subscription,
        test_plan,
        auth_headers: dict
    ):
        """Test subscription plan upgrade with proration"""
        
        # Create a higher tier plan
        from backend.models import SubscriptionPlan
        higher_plan = SubscriptionPlan(
            id=uuid4(),
            name="Enterprise Plan",
            code="ENTERPRISE",
            pricing_model="hybrid",
            base_price=Decimal("999.99"),
            currency="USD",
            billing_period="monthly",
            is_active=True
        )
        test_db.add(higher_plan)
        await test_db.commit()
        
        # Upgrade subscription
        response = await client.patch(
            f"/api/v1/billing/subscriptions/{test_subscription.id}",
            json={"plan_id": str(higher_plan.id)},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify proration is calculated
        response = await client.get(
            f"/api/v1/billing/subscriptions/{test_subscription.id}/proration",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        proration = response.json()["data"]
        assert proration["credit_amount"] > 0
        assert proration["charge_amount"] > 0
    
    async def test_usage_limits_enforcement(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        test_subscription: Subscription,
        auth_headers: dict
    ):
        """Test usage limits are enforced correctly"""
        
        # Set usage limit
        from backend.models import UsageLimit
        usage_limit = UsageLimit(
            id=uuid4(),
            subscription_id=test_subscription.id,
            metric_name="api_calls",
            limit_value=Decimal("1000"),
            period="monthly",
            action_on_exceed="block",
            current_usage=Decimal("900")
        )
        test_db.add(usage_limit)
        await test_db.commit()
        
        # Try to exceed limit
        response = await client.post(
            "/api/v1/billing/usage",
            json={
                "metric_name": "api_calls",
                "quantity": 200,
                "unit": "calls"
            },
            headers=auth_headers
        )
        
        # Should be blocked
        assert response.status_code == 429
        assert "limit exceeded" in response.json()["detail"].lower()
    
    async def test_dunning_process(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        test_invoice: Invoice,
        test_payment_method: PaymentMethod,
        auth_headers: dict,
        mock_stripe
    ):
        """Test dunning process for failed payments"""
        
        # Mock payment failure
        mock_stripe.PaymentIntent.create = lambda *args, **kwargs: {
            "id": "pi_failed",
            "status": "failed"
        }
        
        # Attempt payment
        response = await client.post(
            f"/api/v1/billing/invoices/{test_invoice.id}/pay",
            json={"payment_method_id": str(test_payment_method.id)},
            headers=auth_headers
        )
        
        assert response.status_code == 500  # Payment failed
        
        # Check dunning status
        response = await client.get(
            f"/api/v1/billing/invoices/{test_invoice.id}/dunning",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        dunning_status = response.json()["data"]
        assert dunning_status["retry_count"] == 1
        assert dunning_status["next_retry_at"] is not None

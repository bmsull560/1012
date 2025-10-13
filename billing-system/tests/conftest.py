"""
Pytest configuration and fixtures for ValueVerse Billing System tests
"""

import os
import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from faker import Faker
from httpx import AsyncClient

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_billing"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

from backend.database import Base
from backend.billing_service import app
from backend.models import (
    Organization, SubscriptionPlan, Subscription,
    UsageEvent, Invoice, PaymentMethod, PricingRule
)
from backend.auth import create_access_token, get_password_hash

fake = Faker()

# Event loop fixture
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Database fixtures
@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    # Create test engine
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        poolclass=NullPool,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()
    
    # Clean up
    await engine.dispose()

# Test client fixture
@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Authentication fixtures
@pytest_asyncio.fixture
async def test_organization(test_db: AsyncSession) -> Organization:
    """Create test organization"""
    org = Organization(
        id=uuid4(),
        name="Test Company",
        slug="test-company",
        status="active",
        billing_email="billing@test.com",
        tax_id="123456789",
        billing_address={
            "street": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip": "12345",
            "country": "US"
        }
    )
    test_db.add(org)
    await test_db.commit()
    await test_db.refresh(org)
    return org

@pytest_asyncio.fixture
async def auth_token(test_organization: Organization) -> str:
    """Create authenticated token for testing"""
    token_data = {
        "organization_id": str(test_organization.id),
        "user_id": str(uuid4()),
        "scopes": ["read", "write"]
    }
    return create_access_token(token_data)

@pytest_asyncio.fixture
async def auth_headers(auth_token: str) -> dict:
    """Create authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}

# Test data fixtures
@pytest_asyncio.fixture
async def test_plan(test_db: AsyncSession) -> SubscriptionPlan:
    """Create test subscription plan"""
    plan = SubscriptionPlan(
        id=uuid4(),
        name="Test Plan",
        code="TEST_PLAN",
        description="Test subscription plan",
        pricing_model="hybrid",
        base_price=Decimal("99.99"),
        currency="USD",
        billing_period="monthly",
        trial_period_days=14,
        features={
            "api_calls": 100000,
            "storage_gb": 100,
            "compute_hours": 1000
        },
        limits={
            "max_users": 10,
            "max_projects": 5
        },
        is_active=True
    )
    test_db.add(plan)
    await test_db.commit()
    await test_db.refresh(plan)
    return plan

@pytest_asyncio.fixture
async def test_subscription(
    test_db: AsyncSession,
    test_organization: Organization,
    test_plan: SubscriptionPlan
) -> Subscription:
    """Create test subscription"""
    now = datetime.utcnow()
    subscription = Subscription(
        id=uuid4(),
        organization_id=test_organization.id,
        plan_id=test_plan.id,
        status="active",
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        trial_end=None,
        cancel_at_period_end=False
    )
    test_db.add(subscription)
    await test_db.commit()
    await test_db.refresh(subscription)
    return subscription

@pytest_asyncio.fixture
async def test_pricing_rules(
    test_db: AsyncSession,
    test_plan: SubscriptionPlan
) -> list[PricingRule]:
    """Create test pricing rules"""
    rules = [
        PricingRule(
            id=uuid4(),
            plan_id=test_plan.id,
            metric_name="api_calls",
            pricing_type="tiered",
            rules={
                "tiers": [
                    {"up_to": 10000, "unit_price": 0.001},
                    {"from": 10000, "up_to": 100000, "unit_price": 0.0008},
                    {"from": 100000, "unit_price": 0.0005}
                ]
            },
            is_active=True
        ),
        PricingRule(
            id=uuid4(),
            plan_id=test_plan.id,
            metric_name="storage_gb",
            pricing_type="per_unit",
            rules={"unit_price": 0.02},
            is_active=True
        ),
        PricingRule(
            id=uuid4(),
            plan_id=test_plan.id,
            metric_name="compute_hours",
            pricing_type="per_unit",
            rules={"unit_price": 0.10},
            is_active=True
        )
    ]
    
    for rule in rules:
        test_db.add(rule)
    
    await test_db.commit()
    return rules

@pytest_asyncio.fixture
async def test_usage_events(
    test_db: AsyncSession,
    test_organization: Organization,
    test_subscription: Subscription
) -> list[UsageEvent]:
    """Create test usage events"""
    events = []
    now = datetime.utcnow()
    
    # Create various usage events
    for i in range(10):
        event = UsageEvent(
            id=uuid4(),
            organization_id=test_organization.id,
            subscription_id=test_subscription.id,
            metric_name=fake.random_element(["api_calls", "storage_gb", "compute_hours"]),
            quantity=Decimal(fake.random_int(1, 1000)),
            unit=fake.random_element(["calls", "gb", "hours"]),
            timestamp=now - timedelta(days=i),
            properties={"test": True},
            idempotency_key=f"test-event-{i}"
        )
        events.append(event)
        test_db.add(event)
    
    await test_db.commit()
    return events

@pytest_asyncio.fixture
async def test_payment_method(
    test_db: AsyncSession,
    test_organization: Organization
) -> PaymentMethod:
    """Create test payment method"""
    payment_method = PaymentMethod(
        id=uuid4(),
        organization_id=test_organization.id,
        type="card",
        provider="stripe",
        provider_customer_id="cus_test123",
        provider_payment_method_id="pm_test123",
        is_default=True,
        last_four="4242",
        brand="visa",
        exp_month=12,
        exp_year=2025,
        metadata={"test": True}
    )
    test_db.add(payment_method)
    await test_db.commit()
    await test_db.refresh(payment_method)
    return payment_method

# Mock external services
@pytest.fixture
def mock_stripe(monkeypatch):
    """Mock Stripe API calls"""
    class MockStripePaymentIntent:
        def __init__(self, *args, **kwargs):
            self.id = "pi_test123"
            self.status = "succeeded"
    
    class MockStripe:
        class PaymentIntent:
            @staticmethod
            def create(*args, **kwargs):
                return MockStripePaymentIntent()
    
    monkeypatch.setattr("stripe.PaymentIntent", MockStripe.PaymentIntent)
    return MockStripe

@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis client"""
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        async def get(self, key):
            return self.data.get(key)
        
        async def set(self, key, value, **kwargs):
            self.data[key] = value
            return True
        
        async def exists(self, key):
            return key in self.data
        
        async def delete(self, key):
            if key in self.data:
                del self.data[key]
                return 1
            return 0
        
        async def setex(self, key, ttl, value):
            self.data[key] = value
            return True
    
    mock_redis_instance = MockRedis()
    monkeypatch.setattr("redis.asyncio.from_url", lambda *args, **kwargs: mock_redis_instance)
    return mock_redis_instance

# Utility functions for tests
async def create_test_invoice(
    db: AsyncSession,
    organization: Organization,
    subscription: Subscription,
    amount: Decimal = Decimal("100.00")
) -> Invoice:
    """Helper to create test invoice"""
    invoice = Invoice(
        id=uuid4(),
        organization_id=organization.id,
        subscription_id=subscription.id,
        invoice_number=f"INV-{fake.random_int(1000, 9999)}",
        status="open",
        currency="USD",
        subtotal=amount,
        tax=Decimal("0.00"),
        total=amount,
        amount_paid=Decimal("0.00"),
        amount_due=amount,
        billing_period_start=subscription.current_period_start,
        billing_period_end=subscription.current_period_end,
        due_date=(datetime.utcnow() + timedelta(days=30)).date(),
        line_items=[
            {
                "description": "Test charge",
                "quantity": 1,
                "unit_price": float(amount),
                "total": float(amount)
            }
        ]
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice

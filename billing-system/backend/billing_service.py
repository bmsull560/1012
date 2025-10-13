"""
ValueVerse Billing Service - Core billing engine implementation
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
import asyncio
import logging

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import stripe
import redis.asyncio as redis

from .models import (
    Organization, Subscription, SubscriptionPlan,
    UsageEvent, Invoice, PaymentMethod, BillingTransaction,
    PricingRule, UsageLimit
)
from .database import get_db
from .auth import get_current_organization
from .events import EventBus
from .cache import CacheManager
from .middleware import configure_middleware

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ValueVerse Billing Service",
    version="1.0.0",
    description="Enterprise-grade billing and subscription management system",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure all middleware
configure_middleware(app)

# Initialize external services
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
event_bus = EventBus()
cache_manager = CacheManager()

# ==================== Pydantic Models ====================

class UsageEventCreate(BaseModel):
    """Model for creating usage events"""
    metric_name: str = Field(..., description="Name of the usage metric")
    quantity: Decimal = Field(..., gt=0, description="Quantity of usage")
    unit: str = Field(..., description="Unit of measurement")
    timestamp: Optional[datetime] = None
    properties: Optional[Dict[str, Any]] = {}
    idempotency_key: Optional[str] = None

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v

class SubscriptionCreate(BaseModel):
    """Model for creating subscriptions"""
    plan_id: UUID
    payment_method_id: Optional[UUID] = None
    trial_period_days: Optional[int] = 0
    metadata: Optional[Dict[str, Any]] = {}

class InvoiceCreate(BaseModel):
    """Model for creating invoices"""
    subscription_id: UUID
    line_items: List[Dict[str, Any]]
    tax_rate: Optional[Decimal] = Decimal("0.00")
    notes: Optional[str] = None

class PaymentMethodCreate(BaseModel):
    """Model for adding payment methods"""
    type: str = Field(..., pattern="^(card|bank_account|paypal|wire)$")
    provider: str = Field(..., pattern="^(stripe|paypal|manual)$")
    provider_token: str
    is_default: bool = False
    metadata: Optional[Dict[str, Any]] = {}

class UsageSummaryParams(BaseModel):
    """Parameters for usage summary queries"""
    start_date: datetime
    end_date: datetime
    metric_name: Optional[str] = None
    granularity: str = Field(default="daily", pattern="^(hourly|daily|monthly)$")

# ==================== Core Billing Service ====================

class BillingService:
    """Core billing service with all business logic"""
    
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv("REDIS_URL"))
        self.usage_buffer = []
        self.buffer_lock = asyncio.Lock()
        
    async def record_usage(
        self,
        organization_id: UUID,
        event: UsageEventCreate,
        db: AsyncSession
    ) -> UsageEvent:
        """Record a usage event with idempotency and buffering"""
        
        # Check idempotency
        if event.idempotency_key:
            cache_key = f"usage_event:{event.idempotency_key}"
            if await self.redis_client.exists(cache_key):
                logger.info(f"Duplicate usage event skipped: {event.idempotency_key}")
                return None
        
        # Create usage event
        usage_event = UsageEvent(
            organization_id=organization_id,
            metric_name=event.metric_name,
            quantity=event.quantity,
            unit=event.unit,
            timestamp=event.timestamp or datetime.utcnow(),
            properties=event.properties,
            idempotency_key=event.idempotency_key
        )
        
        # Buffer for batch insertion (improves performance)
        async with self.buffer_lock:
            self.usage_buffer.append(usage_event)
            
            if len(self.usage_buffer) >= 100:
                await self._flush_usage_buffer(db)
        
        # Set idempotency key in cache
        if event.idempotency_key:
            await self.redis_client.setex(
                cache_key, 
                86400,  # 24 hour TTL
                "1"
            )
        
        # Check usage limits
        await self._check_usage_limits(organization_id, event.metric_name, db)
        
        # Publish event for real-time updates
        await event_bus.publish("usage.recorded", {
            "organization_id": str(organization_id),
            "metric_name": event.metric_name,
            "quantity": float(event.quantity),
            "timestamp": event.timestamp.isoformat() if event.timestamp else None
        })
        
        return usage_event
    
    async def _flush_usage_buffer(self, db: AsyncSession):
        """Flush buffered usage events to database"""
        if not self.usage_buffer:
            return
            
        events_to_insert = self.usage_buffer.copy()
        self.usage_buffer.clear()
        
        try:
            db.add_all(events_to_insert)
            await db.commit()
            logger.info(f"Flushed {len(events_to_insert)} usage events to database")
        except Exception as e:
            logger.error(f"Failed to flush usage buffer: {e}")
            await db.rollback()
    
    async def _check_usage_limits(
        self,
        organization_id: UUID,
        metric_name: str,
        db: AsyncSession
    ):
        """Check and enforce usage limits"""
        
        # Get active subscription
        subscription = await db.execute(
            select(Subscription)
            .where(
                and_(
                    Subscription.organization_id == organization_id,
                    Subscription.status == "active"
                )
            )
        )
        subscription = subscription.scalar_one_or_none()
        
        if not subscription:
            return
        
        # Check usage limits
        usage_limit = await db.execute(
            select(UsageLimit)
            .where(
                and_(
                    UsageLimit.subscription_id == subscription.id,
                    UsageLimit.metric_name == metric_name
                )
            )
        )
        usage_limit = usage_limit.scalar_one_or_none()
        
        if not usage_limit:
            return
        
        # Calculate current usage
        current_usage = await self.get_usage_for_period(
            organization_id,
            metric_name,
            subscription.current_period_start,
            datetime.utcnow(),
            db
        )
        
        if current_usage >= usage_limit.limit_value:
            if usage_limit.action_on_exceed == "block":
                raise HTTPException(
                    status_code=429,
                    detail=f"Usage limit exceeded for {metric_name}"
                )
            elif usage_limit.action_on_exceed == "notify":
                await event_bus.publish("usage.limit_exceeded", {
                    "organization_id": str(organization_id),
                    "metric_name": metric_name,
                    "limit": float(usage_limit.limit_value),
                    "current": float(current_usage)
                })
    
    async def calculate_usage_charges(
        self,
        subscription_id: UUID,
        start_date: datetime,
        end_date: datetime,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Calculate charges based on usage for a billing period"""
        
        # Get subscription and plan
        subscription = await db.get(Subscription, subscription_id)
        plan = await db.get(SubscriptionPlan, subscription.plan_id)
        
        # Get pricing rules for the plan
        pricing_rules = await db.execute(
            select(PricingRule)
            .where(
                and_(
                    PricingRule.plan_id == plan.id,
                    PricingRule.is_active == True
                )
            )
        )
        pricing_rules = pricing_rules.scalars().all()
        
        charges = []
        
        for rule in pricing_rules:
            # Get usage for this metric
            usage_quantity = await self.get_usage_for_period(
                subscription.organization_id,
                rule.metric_name,
                start_date,
                end_date,
                db
            )
            
            # Calculate charge based on pricing type
            charge = await self._calculate_charge_for_rule(
                rule,
                usage_quantity
            )
            
            charges.append({
                "metric_name": rule.metric_name,
                "quantity": float(usage_quantity),
                "unit_price": float(charge["unit_price"]),
                "total": float(charge["total"]),
                "description": charge["description"]
            })
        
        return charges
    
    async def _calculate_charge_for_rule(
        self,
        rule: PricingRule,
        quantity: Decimal
    ) -> Dict[str, Any]:
        """Calculate charge based on pricing rule"""
        
        rules_config = rule.rules
        
        if rule.pricing_type == "per_unit":
            unit_price = Decimal(str(rules_config["unit_price"]))
            total = quantity * unit_price
            return {
                "unit_price": unit_price,
                "total": total,
                "description": f"{quantity} units @ ${unit_price}/unit"
            }
            
        elif rule.pricing_type == "tiered":
            # Graduated pricing tiers
            total = Decimal("0.00")
            remaining = quantity
            description_parts = []
            
            for tier in rules_config["tiers"]:
                tier_max = Decimal(str(tier.get("up_to", float('inf'))))
                tier_price = Decimal(str(tier["unit_price"]))
                
                if remaining <= 0:
                    break
                
                tier_quantity = min(remaining, tier_max)
                tier_total = tier_quantity * tier_price
                total += tier_total
                remaining -= tier_quantity
                
                description_parts.append(
                    f"{tier_quantity} units @ ${tier_price}/unit"
                )
            
            return {
                "unit_price": total / quantity if quantity > 0 else Decimal("0"),
                "total": total,
                "description": " + ".join(description_parts)
            }
            
        elif rule.pricing_type == "volume":
            # Volume-based pricing (entire quantity at tier price)
            unit_price = Decimal("0.00")
            
            for tier in rules_config["tiers"]:
                tier_min = Decimal(str(tier.get("from", 0)))
                tier_max = Decimal(str(tier.get("up_to", float('inf'))))
                
                if tier_min <= quantity <= tier_max:
                    unit_price = Decimal(str(tier["unit_price"]))
                    break
            
            total = quantity * unit_price
            return {
                "unit_price": unit_price,
                "total": total,
                "description": f"{quantity} units @ ${unit_price}/unit (volume pricing)"
            }
            
        elif rule.pricing_type == "package":
            # Package pricing with overage
            package_size = Decimal(str(rules_config["package_size"]))
            package_price = Decimal(str(rules_config["package_price"]))
            overage_price = Decimal(str(rules_config.get("overage_unit_price", 0)))
            
            packages_needed = int(quantity / package_size) + (1 if quantity % package_size else 0)
            included_quantity = packages_needed * package_size
            overage_quantity = max(Decimal("0"), quantity - included_quantity)
            
            total = (packages_needed * package_price) + (overage_quantity * overage_price)
            
            return {
                "unit_price": total / quantity if quantity > 0 else Decimal("0"),
                "total": total,
                "description": f"{packages_needed} packages @ ${package_price}/package"
            }
        
        return {
            "unit_price": Decimal("0.00"),
            "total": Decimal("0.00"),
            "description": "Unknown pricing type"
        }
    
    async def generate_invoice(
        self,
        subscription_id: UUID,
        db: AsyncSession
    ) -> Invoice:
        """Generate invoice for a subscription's current billing period"""
        
        subscription = await db.get(Subscription, subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")
        
        # Calculate usage charges
        usage_charges = await self.calculate_usage_charges(
            subscription_id,
            subscription.current_period_start,
            subscription.current_period_end,
            db
        )
        
        # Get base subscription charge
        plan = await db.get(SubscriptionPlan, subscription.plan_id)
        
        line_items = []
        
        # Add base subscription fee
        if plan.base_price > 0:
            line_items.append({
                "type": "subscription",
                "description": f"{plan.name} - Base Fee",
                "quantity": 1,
                "unit_price": float(plan.base_price),
                "total": float(plan.base_price)
            })
        
        # Add usage charges
        for charge in usage_charges:
            line_items.append({
                "type": "usage",
                "description": f"{charge['metric_name']} - {charge['description']}",
                "quantity": charge['quantity'],
                "unit_price": charge['unit_price'],
                "total": charge['total']
            })
        
        # Calculate totals
        subtotal = sum(Decimal(str(item["total"])) for item in line_items)
        tax_rate = Decimal("0.00")  # TODO: Implement tax calculation
        tax = subtotal * tax_rate
        total = subtotal + tax
        
        # Generate invoice number
        invoice_number = await self._generate_invoice_number(db)
        
        # Create invoice
        invoice = Invoice(
            organization_id=subscription.organization_id,
            subscription_id=subscription_id,
            invoice_number=invoice_number,
            status="draft",
            currency=plan.currency,
            subtotal=subtotal,
            tax=tax,
            total=total,
            amount_due=total,
            billing_period_start=subscription.current_period_start,
            billing_period_end=subscription.current_period_end,
            due_date=subscription.current_period_end + timedelta(days=30),
            line_items=line_items
        )
        
        db.add(invoice)
        await db.commit()
        
        # Publish event
        await event_bus.publish("invoice.created", {
            "organization_id": str(subscription.organization_id),
            "invoice_id": str(invoice.id),
            "total": float(total)
        })
        
        return invoice
    
    async def process_payment(
        self,
        invoice_id: UUID,
        payment_method_id: UUID,
        db: AsyncSession
    ) -> BillingTransaction:
        """Process payment for an invoice"""
        
        invoice = await db.get(Invoice, invoice_id)
        payment_method = await db.get(PaymentMethod, payment_method_id)
        
        if not invoice or not payment_method:
            raise ValueError("Invoice or payment method not found")
        
        if invoice.status == "paid":
            raise ValueError("Invoice is already paid")
        
        # Create transaction record
        transaction = BillingTransaction(
            organization_id=invoice.organization_id,
            invoice_id=invoice_id,
            payment_method_id=payment_method_id,
            type="charge",
            status="processing",
            amount=invoice.amount_due,
            currency=invoice.currency
        )
        
        db.add(transaction)
        await db.commit()
        
        try:
            # Process payment based on provider
            if payment_method.provider == "stripe":
                result = await self._process_stripe_payment(
                    payment_method,
                    invoice.amount_due,
                    invoice.currency
                )
            elif payment_method.provider == "paypal":
                result = await self._process_paypal_payment(
                    payment_method,
                    invoice.amount_due,
                    invoice.currency
                )
            else:
                raise ValueError(f"Unsupported payment provider: {payment_method.provider}")
            
            # Update transaction and invoice
            transaction.status = "succeeded"
            transaction.provider_transaction_id = result["transaction_id"]
            
            invoice.status = "paid"
            invoice.amount_paid = invoice.total
            invoice.amount_due = Decimal("0.00")
            invoice.paid_at = datetime.utcnow()
            invoice.payment_method = payment_method.type
            
            await db.commit()
            
            # Publish success event
            await event_bus.publish("payment.succeeded", {
                "organization_id": str(invoice.organization_id),
                "invoice_id": str(invoice_id),
                "amount": float(invoice.total)
            })
            
        except Exception as e:
            # Update transaction with failure
            transaction.status = "failed"
            transaction.failure_reason = str(e)
            await db.commit()
            
            # Publish failure event
            await event_bus.publish("payment.failed", {
                "organization_id": str(invoice.organization_id),
                "invoice_id": str(invoice_id),
                "reason": str(e)
            })
            
            raise
        
        return transaction
    
    async def _process_stripe_payment(
        self,
        payment_method: PaymentMethod,
        amount: Decimal,
        currency: str
    ) -> Dict[str, str]:
        """Process payment through Stripe"""
        
        try:
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency.lower(),
                customer=payment_method.provider_customer_id,
                payment_method=payment_method.provider_payment_method_id,
                confirm=True,
                off_session=True
            )
            
            return {
                "transaction_id": intent.id,
                "status": intent.status
            }
            
        except stripe.error.CardError as e:
            raise ValueError(f"Card was declined: {e.user_message}")
        except stripe.error.StripeError as e:
            raise ValueError(f"Stripe error: {str(e)}")
    
    async def get_usage_for_period(
        self,
        organization_id: UUID,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        db: AsyncSession
    ) -> Decimal:
        """Get total usage for a specific period"""
        
        result = await db.execute(
            select(func.sum(UsageEvent.quantity))
            .where(
                and_(
                    UsageEvent.organization_id == organization_id,
                    UsageEvent.metric_name == metric_name,
                    UsageEvent.timestamp >= start_date,
                    UsageEvent.timestamp < end_date
                )
            )
        )
        
        total = result.scalar_one_or_none()
        return Decimal(str(total)) if total else Decimal("0.00")
    
    async def _generate_invoice_number(self, db: AsyncSession) -> str:
        """Generate unique invoice number"""
        
        # Get last invoice number
        result = await db.execute(
            select(Invoice.invoice_number)
            .order_by(Invoice.created_at.desc())
            .limit(1)
        )
        
        last_number = result.scalar_one_or_none()
        
        if last_number:
            # Extract number and increment
            number_part = int(last_number.split("-")[-1])
            new_number = number_part + 1
        else:
            new_number = 1
        
        # Format: INV-YYYY-MM-00001
        now = datetime.utcnow()
        invoice_number = f"INV-{now.year}-{now.month:02d}-{new_number:05d}"
        
        return invoice_number

# Initialize service
billing_service = BillingService()

# ==================== API Endpoints ====================

@app.post("/api/v1/billing/usage")
async def record_usage_event(
    event: UsageEventCreate,
    organization: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Record a usage event for the organization"""
    
    usage_event = await billing_service.record_usage(
        organization.id,
        event,
        db
    )
    
    return {
        "status": "success",
        "message": "Usage event recorded",
        "data": {
            "metric_name": event.metric_name,
            "quantity": float(event.quantity),
            "timestamp": event.timestamp.isoformat() if event.timestamp else None
        }
    }

@app.get("/api/v1/billing/usage/summary")
async def get_usage_summary(
    params: UsageSummaryParams = Depends(),
    organization: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get usage summary for a time period"""
    
    # Build query
    query = select(
        UsageEvent.metric_name,
        func.sum(UsageEvent.quantity).label("total_quantity"),
        func.count(UsageEvent.id).label("event_count")
    ).where(
        and_(
            UsageEvent.organization_id == organization.id,
            UsageEvent.timestamp >= params.start_date,
            UsageEvent.timestamp < params.end_date
        )
    )
    
    if params.metric_name:
        query = query.where(UsageEvent.metric_name == params.metric_name)
    
    query = query.group_by(UsageEvent.metric_name)
    
    result = await db.execute(query)
    summary = result.all()
    
    return {
        "status": "success",
        "data": {
            "period": {
                "start": params.start_date.isoformat(),
                "end": params.end_date.isoformat()
            },
            "metrics": [
                {
                    "metric_name": row.metric_name,
                    "total_quantity": float(row.total_quantity),
                    "event_count": row.event_count
                }
                for row in summary
            ]
        }
    }

@app.post("/api/v1/billing/subscriptions")
async def create_subscription(
    subscription_data: SubscriptionCreate,
    organization: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Create a new subscription for the organization"""
    
    # Check if organization already has an active subscription
    existing = await db.execute(
        select(Subscription)
        .where(
            and_(
                Subscription.organization_id == organization.id,
                Subscription.status.in_(["active", "trialing"])
            )
        )
    )
    
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Organization already has an active subscription"
        )
    
    # Get plan details
    plan = await db.get(SubscriptionPlan, subscription_data.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(
            status_code=404,
            detail="Plan not found or inactive"
        )
    
    # Create subscription
    now = datetime.utcnow()
    trial_end = None
    status = "active"
    
    if subscription_data.trial_period_days > 0:
        trial_end = now + timedelta(days=subscription_data.trial_period_days)
        status = "trialing"
    
    subscription = Subscription(
        organization_id=organization.id,
        plan_id=subscription_data.plan_id,
        status=status,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),  # Monthly billing
        trial_end=trial_end,
        metadata=subscription_data.metadata
    )
    
    db.add(subscription)
    await db.commit()
    
    # Publish event
    await event_bus.publish("subscription.created", {
        "organization_id": str(organization.id),
        "subscription_id": str(subscription.id),
        "plan_name": plan.name,
        "status": status
    })
    
    return {
        "status": "success",
        "data": {
            "subscription_id": str(subscription.id),
            "plan_name": plan.name,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end.isoformat(),
            "trial_end": trial_end.isoformat() if trial_end else None
        }
    }

@app.post("/api/v1/billing/invoices/{invoice_id}/pay")
async def pay_invoice(
    invoice_id: UUID,
    payment_method_id: UUID,
    organization: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Process payment for an invoice"""
    
    # Verify invoice belongs to organization
    invoice = await db.get(Invoice, invoice_id)
    if not invoice or invoice.organization_id != organization.id:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )
    
    # Process payment
    transaction = await billing_service.process_payment(
        invoice_id,
        payment_method_id,
        db
    )
    
    return {
        "status": "success",
        "data": {
            "transaction_id": str(transaction.id),
            "status": transaction.status,
            "amount": float(transaction.amount)
        }
    }

# ==================== Health Check Endpoints ====================

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "billing-api",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe endpoint"""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness_probe(
    db: AsyncSession = Depends(get_db)
):
    """Kubernetes readiness probe - checks database connectivity"""
    try:
        # Check database connection
        await db.execute("SELECT 1")
        
        # Check Redis connection
        if billing_service.redis_client:
            await billing_service.redis_client.ping()
        
        # Check event bus
        if hasattr(event_bus, '_running') and not event_bus._running:
            raise HTTPException(
                status_code=503,
                detail="Event bus not ready"
            )
        
        return {
            "status": "ready",
            "checks": {
                "database": "connected",
                "cache": "connected",
                "event_bus": "ready"
            }
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: {str(e)}"
        )

@app.get("/health/startup")
async def startup_probe():
    """Kubernetes startup probe"""
    # Check if all services are initialized
    if not hasattr(billing_service, 'redis_client'):
        raise HTTPException(
            status_code=503,
            detail="Service still initializing"
        )
    return {"status": "started"}

# ==================== WebSocket Endpoints ====================

@app.websocket("/ws/billing/{organization_id}")
async def billing_websocket(
    websocket: WebSocket,
    organization_id: UUID,
    token: str = Query(...)
):
    """WebSocket endpoint for real-time billing updates"""
    
    # Verify token and organization access
    try:
        from .auth import verify_token
        token_data = await verify_token(token, token_type="access")
        
        if token_data.organization_id != str(organization_id):
            await websocket.close(code=1008, reason="Unauthorized")
            return
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    await websocket.accept()
    logger.info(f"WebSocket connected for organization {organization_id}")
    
    # Create a unique client ID for this connection
    client_id = str(uuid4())
    
    # Subscribe to organization's billing events
    async def handle_event(event: Dict[str, Any]):
        """Handle events and send to WebSocket client"""
        try:
            await websocket.send_json({
                "type": "billing_event",
                "event": event
            })
        except Exception as e:
            logger.error(f"Failed to send event to WebSocket: {e}")
    
    await event_bus.subscribe(f"billing.org.{organization_id}.*", handle_event)
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            # Receive message from client (ping/pong or commands)
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "subscribe":
                # Handle subscription to specific event types
                event_type = data.get("event_type")
                if event_type:
                    await event_bus.subscribe(
                        f"billing.{event_type}.{organization_id}",
                        handle_event
                    )
                    await websocket.send_json({
                        "type": "subscribed",
                        "event_type": event_type
                    })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for organization {organization_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal error")

# ==================== Startup and Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting ValueVerse Billing Service...")
    
    # Initialize event bus
    await event_bus.start()
    logger.info("Event bus started")
    
    # Initialize cache
    await cache_manager.connect()
    logger.info("Cache connected")
    
    # Initialize billing service connections
    await billing_service.initialize()
    logger.info("Billing service initialized")
    
    logger.info("ValueVerse Billing Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down ValueVerse Billing Service...")
    
    # Stop event bus
    await event_bus.stop()
    
    # Disconnect cache
    await cache_manager.disconnect()
    
    # Cleanup billing service
    await billing_service.cleanup()
    
    logger.info("ValueVerse Billing Service shut down successfully")

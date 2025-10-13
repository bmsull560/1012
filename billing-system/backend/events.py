"""
Event bus implementation for ValueVerse Billing System
Handles asynchronous event publishing and subscription using Kafka
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from uuid import uuid4

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError
import orjson

logger = logging.getLogger(__name__)

class EventBus:
    """
    Asynchronous event bus for microservice communication
    """
    
    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", 
            "localhost:9092"
        )
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.handlers: Dict[str, List[Callable]] = {}
        self._running = False
        
    async def start(self):
        """Start the event bus producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: orjson.dumps(v),
                compression_type="gzip",
                acks="all",
                retry_backoff_ms=100,
                request_timeout_ms=30000,
            )
            await self.producer.start()
            self._running = True
            logger.info(f"Event bus started with servers: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to start event bus: {e}")
            raise
    
    async def stop(self):
        """Stop the event bus and all consumers"""
        self._running = False
        
        # Stop all consumers
        for consumer in self.consumers.values():
            await consumer.stop()
        
        # Stop producer
        if self.producer:
            await self.producer.stop()
        
        logger.info("Event bus stopped")
    
    async def publish(self, event_type: str, data: Dict[str, Any], key: Optional[str] = None):
        """
        Publish an event to the event bus
        
        Args:
            event_type: Type of event (used as topic name)
            data: Event payload
            key: Optional partition key for ordering
        """
        if not self.producer:
            logger.warning("Event bus not started, skipping publish")
            return
        
        try:
            # Add metadata to event
            event = {
                "event_id": str(uuid4()),
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            # Determine topic from event type
            topic = f"billing.{event_type.replace('.', '_')}"
            
            # Send event
            await self.producer.send(
                topic=topic,
                value=event,
                key=key.encode() if key else None
            )
            
            logger.debug(f"Published event {event_type} to topic {topic}")
            
        except KafkaError as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            raise
    
    async def subscribe(self, event_pattern: str, handler: Callable):
        """
        Subscribe to events matching a pattern
        
        Args:
            event_pattern: Event pattern to match (supports wildcards)
            handler: Async function to handle matching events
        """
        # Convert pattern to topic name
        topic = f"billing.{event_pattern.replace('.', '_').replace('*', '.*')}"
        
        if topic not in self.handlers:
            self.handlers[topic] = []
        
        self.handlers[topic].append(handler)
        
        # Create consumer if not exists
        if topic not in self.consumers:
            await self._create_consumer(topic)
        
        logger.info(f"Subscribed to events matching pattern: {event_pattern}")
    
    async def _create_consumer(self, topic: str):
        """Create a Kafka consumer for a topic"""
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=f"billing-service-{topic}",
                value_deserializer=lambda v: orjson.loads(v),
                auto_offset_reset="latest",
                enable_auto_commit=True,
            )
            
            await consumer.start()
            self.consumers[topic] = consumer
            
            # Start consumer loop
            asyncio.create_task(self._consume_loop(topic, consumer))
            
        except Exception as e:
            logger.error(f"Failed to create consumer for topic {topic}: {e}")
            raise
    
    async def _consume_loop(self, topic: str, consumer: AIOKafkaConsumer):
        """Consumer loop to process events"""
        try:
            async for message in consumer:
                event = message.value
                
                # Call all registered handlers
                if topic in self.handlers:
                    for handler in self.handlers[topic]:
                        try:
                            await handler(event)
                        except Exception as e:
                            logger.error(f"Handler error for event {event.get('event_type')}: {e}")
                            
        except Exception as e:
            logger.error(f"Consumer loop error for topic {topic}: {e}")
        finally:
            await consumer.stop()

# In-memory event bus for testing/development
class InMemoryEventBus:
    """
    Simple in-memory event bus for testing and development
    """
    
    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = {}
        self.events: List[Dict[str, Any]] = []
        
    async def start(self):
        """Start the event bus (no-op for in-memory)"""
        logger.info("In-memory event bus started")
    
    async def stop(self):
        """Stop the event bus (no-op for in-memory)"""
        logger.info("In-memory event bus stopped")
    
    async def publish(self, event_type: str, data: Dict[str, Any], key: Optional[str] = None):
        """Publish an event"""
        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "key": key
        }
        
        self.events.append(event)
        
        # Call matching handlers
        for pattern, handlers in self.handlers.items():
            if self._matches_pattern(event_type, pattern):
                for handler in handlers:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Handler error for event {event_type}: {e}")
    
    async def subscribe(self, event_pattern: str, handler: Callable):
        """Subscribe to events"""
        if event_pattern not in self.handlers:
            self.handlers[event_pattern] = []
        self.handlers[event_pattern].append(handler)
        logger.info(f"Subscribed to events matching pattern: {event_pattern}")
    
    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if event type matches pattern"""
        import re
        pattern_regex = pattern.replace(".", r"\.").replace("*", ".*")
        return bool(re.match(f"^{pattern_regex}$", event_type))

# Factory function to get appropriate event bus
def get_event_bus() -> EventBus:
    """
    Get event bus instance based on environment
    """
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "development" or env == "test":
        return InMemoryEventBus()
    else:
        return EventBus()

# Global event bus instance
event_bus = get_event_bus()

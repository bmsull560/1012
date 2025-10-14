"""
Kafka Event Ingestion for High-Throughput Processing
Decouples event ingestion from processing for 10M+ events/minute capability
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from dataclasses import dataclass, asdict
import pickle

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
import orjson
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = ["localhost:9092", "localhost:9093", "localhost:9094"]
KAFKA_TOPICS = {
    "usage_events": "billing.usage.events",
    "usage_events_dlq": "billing.usage.events.dlq",
    "payment_events": "billing.payment.events",
    "invoice_events": "billing.invoice.events",
    "subscription_events": "billing.subscription.events",
    "audit_events": "billing.audit.events"
}

class UsageEventKafka(BaseModel):
    """Usage event model for Kafka"""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str
    metric_name: str
    quantity: float
    unit: str = "units"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    properties: Dict[str, Any] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }

class KafkaEventProducer:
    """
    High-performance Kafka producer for event ingestion
    Handles batching, compression, and reliability
    """
    
    def __init__(
        self,
        bootstrap_servers: List[str] = None,
        batch_size: int = 1000,
        linger_ms: int = 100
    ):
        self.bootstrap_servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
        self.batch_size = batch_size
        self.linger_ms = linger_ms
        self.producer: Optional[AIOKafkaProducer] = None
        self._initialized = False
        self._metrics = {
            "events_sent": 0,
            "events_failed": 0,
            "batch_count": 0
        }
        
    async def initialize(self):
        """Initialize Kafka producer with optimized settings"""
        if self._initialized:
            return
            
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                
                # Serialization
                value_serializer=lambda v: orjson.dumps(v),
                key_serializer=lambda k: k.encode() if k else None,
                
                # Batching for throughput
                batch_size=self.batch_size * 1024,  # Convert to bytes
                linger_ms=self.linger_ms,  # Wait time for batching
                
                # Compression for network efficiency
                compression_type="lz4",  # Fast compression
                
                # Reliability settings
                acks="all",  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=5,
                
                # Performance tuning
                buffer_memory=67108864,  # 64MB buffer
                send_buffer_bytes=131072,  # 128KB send buffer
                receive_buffer_bytes=131072,  # 128KB receive buffer
                
                # Idempotence for exactly-once semantics
                enable_idempotence=True,
                
                # Timeout settings
                request_timeout_ms=30000,
                metadata_max_age_ms=300000
            )
            
            await self.producer.start()
            self._initialized = True
            logger.info("Kafka producer initialized")
            
            # Create topics if they don't exist
            await self._ensure_topics()
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    async def _ensure_topics(self):
        """Ensure required topics exist with proper configuration"""
        admin = AIOKafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers
        )
        await admin.start()
        
        try:
            # Define topics with partitions for parallelism
            topics = [
                NewTopic(
                    name=KAFKA_TOPICS["usage_events"],
                    num_partitions=10,  # For parallel processing
                    replication_factor=3,  # For fault tolerance
                    topic_configs={
                        "retention.ms": str(7 * 24 * 60 * 60 * 1000),  # 7 days
                        "compression.type": "lz4",
                        "min.insync.replicas": "2",
                        "segment.ms": str(6 * 60 * 60 * 1000),  # 6 hours
                        "cleanup.policy": "delete"
                    }
                ),
                NewTopic(
                    name=KAFKA_TOPICS["usage_events_dlq"],
                    num_partitions=3,
                    replication_factor=3,
                    topic_configs={
                        "retention.ms": str(30 * 24 * 60 * 60 * 1000),  # 30 days
                    }
                )
            ]
            
            # Create topics (ignore if already exists)
            try:
                await admin.create_topics(topics)
                logger.info("Kafka topics created")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    raise
                    
        finally:
            await admin.close()
    
    async def send_usage_event(
        self,
        event: UsageEventKafka,
        partition_key: Optional[str] = None
    ) -> bool:
        """
        Send single usage event to Kafka
        
        Args:
            event: Usage event to send
            partition_key: Key for partition routing (default: organization_id)
        
        Returns:
            Success status
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Use organization_id as partition key for ordering per tenant
            key = partition_key or event.organization_id
            
            # Add processing metadata
            event.processing_metadata.update({
                "ingested_at": datetime.utcnow().isoformat(),
                "producer_id": self.producer._client_id,
                "batch_id": str(uuid4())
            })
            
            # Send to Kafka
            await self.producer.send_and_wait(
                KAFKA_TOPICS["usage_events"],
                key=key,
                value=event.dict(),
                headers=[
                    ("idempotency_key", event.idempotency_key.encode() if event.idempotency_key else b""),
                    ("event_type", b"usage_event"),
                    ("version", b"1.0")
                ]
            )
            
            self._metrics["events_sent"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to send event to Kafka: {e}")
            self._metrics["events_failed"] += 1
            
            # Send to DLQ for retry
            await self._send_to_dlq(event, str(e))
            return False
    
    async def send_batch(
        self,
        events: List[UsageEventKafka]
    ) -> Dict[str, Any]:
        """
        Send batch of events for maximum throughput
        
        Args:
            events: List of usage events
        
        Returns:
            Batch processing results
        """
        if not self._initialized:
            await self.initialize()
        
        batch_id = str(uuid4())
        results = {
            "batch_id": batch_id,
            "total": len(events),
            "succeeded": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # Create batch transaction
            async with self.producer.transaction():
                for event in events:
                    try:
                        event.processing_metadata["batch_id"] = batch_id
                        
                        await self.producer.send(
                            KAFKA_TOPICS["usage_events"],
                            key=event.organization_id,
                            value=event.dict()
                        )
                        results["succeeded"] += 1
                        
                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append({
                            "event_id": event.event_id,
                            "error": str(e)
                        })
                        await self._send_to_dlq(event, str(e))
            
            self._metrics["batch_count"] += 1
            self._metrics["events_sent"] += results["succeeded"]
            self._metrics["events_failed"] += results["failed"]
            
        except Exception as e:
            logger.error(f"Batch transaction failed: {e}")
            results["failed"] = len(events)
            results["errors"].append({"batch_error": str(e)})
        
        return results
    
    async def _send_to_dlq(self, event: UsageEventKafka, error: str):
        """Send failed event to Dead Letter Queue"""
        try:
            dlq_event = event.dict()
            dlq_event["error"] = error
            dlq_event["failed_at"] = datetime.utcnow().isoformat()
            
            await self.producer.send(
                KAFKA_TOPICS["usage_events_dlq"],
                key=event.organization_id,
                value=dlq_event
            )
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get producer metrics"""
        return {
            **self._metrics,
            "throughput": self._metrics["events_sent"] / max(self._metrics["batch_count"], 1),
            "error_rate": self._metrics["events_failed"] / max(self._metrics["events_sent"] + self._metrics["events_failed"], 1)
        }
    
    async def close(self):
        """Clean shutdown of producer"""
        if self.producer:
            await self.producer.stop()
            self._initialized = False

class KafkaEventConsumer:
    """
    Kafka consumer for processing events with parallelism
    """
    
    def __init__(
        self,
        topic: str,
        group_id: str,
        bootstrap_servers: List[str] = None,
        batch_size: int = 100
    ):
        self.topic = topic
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
        self.batch_size = batch_size
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._running = False
        self._processed_count = 0
        
    async def initialize(self):
        """Initialize consumer with optimized settings"""
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            
            # Deserialization
            value_deserializer=lambda v: orjson.loads(v),
            key_deserializer=lambda k: k.decode() if k else None,
            
            # Performance settings
            fetch_min_bytes=1024,  # Min bytes per fetch
            fetch_max_wait_ms=100,  # Max wait for fetch
            max_poll_records=self.batch_size,
            
            # Reliability
            enable_auto_commit=False,  # Manual commit for control
            auto_offset_reset="earliest",
            
            # Session timeout
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000,
            
            # Parallelism
            max_poll_interval_ms=300000  # 5 minutes for processing
        )
        
        await self.consumer.start()
        logger.info(f"Kafka consumer initialized for topic: {self.topic}")
    
    async def consume_batch(
        self,
        process_func,
        error_handler=None
    ):
        """
        Consume and process events in batches
        
        Args:
            process_func: Async function to process batch of events
            error_handler: Optional error handler function
        """
        self._running = True
        
        try:
            while self._running:
                # Fetch batch of messages
                batch = await self.consumer.getmany(
                    timeout_ms=1000,
                    max_records=self.batch_size
                )
                
                if not batch:
                    continue
                
                # Process each partition's messages
                for tp, messages in batch.items():
                    events = []
                    
                    for msg in messages:
                        try:
                            event = UsageEventKafka(**msg.value)
                            events.append(event)
                        except Exception as e:
                            logger.error(f"Failed to parse message: {e}")
                            if error_handler:
                                await error_handler(msg, e)
                    
                    if events:
                        # Process batch
                        try:
                            await process_func(events)
                            self._processed_count += len(events)
                            
                            # Commit offsets after successful processing
                            await self.consumer.commit()
                            
                        except Exception as e:
                            logger.error(f"Batch processing failed: {e}")
                            if error_handler:
                                await error_handler(events, e)
                            # Don't commit - messages will be reprocessed
                
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            raise
        finally:
            await self.close()
    
    async def close(self):
        """Clean shutdown of consumer"""
        self._running = False
        if self.consumer:
            await self.consumer.stop()

class EventStreamProcessor:
    """
    Main event stream processor coordinating producers and consumers
    """
    
    def __init__(self):
        self.producer = KafkaEventProducer()
        self.consumers = []
        self.metrics = {
            "total_ingested": 0,
            "total_processed": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }
        
    async def initialize(self):
        """Initialize event streaming"""
        await self.producer.initialize()
        
        # Create multiple consumers for parallel processing
        for i in range(3):  # 3 consumer instances
            consumer = KafkaEventConsumer(
                topic=KAFKA_TOPICS["usage_events"],
                group_id=f"usage_processor_group",
                batch_size=1000
            )
            await consumer.initialize()
            self.consumers.append(consumer)
        
        logger.info("Event stream processor initialized")
    
    async def ingest_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Ingest single event into stream
        """
        try:
            event = UsageEventKafka(**event_data)
            success = await self.producer.send_usage_event(event)
            
            if success:
                self.metrics["total_ingested"] += 1
            else:
                self.metrics["errors"] += 1
                
            return success
            
        except Exception as e:
            logger.error(f"Event ingestion failed: {e}")
            self.metrics["errors"] += 1
            return False
    
    async def ingest_batch(self, events_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ingest batch of events for high throughput
        """
        events = [UsageEventKafka(**data) for data in events_data]
        results = await self.producer.send_batch(events)
        
        self.metrics["total_ingested"] += results["succeeded"]
        self.metrics["errors"] += results["failed"]
        
        return results
    
    async def start_processors(self, process_func):
        """
        Start event processors
        """
        # Start consumers in parallel
        tasks = []
        for consumer in self.consumers:
            task = asyncio.create_task(
                consumer.consume_batch(process_func)
            )
            tasks.append(task)
        
        # Wait for all consumers
        await asyncio.gather(*tasks)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get streaming metrics"""
        runtime = (datetime.utcnow() - self.metrics["start_time"]).total_seconds()
        
        return {
            **self.metrics,
            "ingestion_rate": self.metrics["total_ingested"] / max(runtime, 1),
            "processing_rate": self.metrics["total_processed"] / max(runtime, 1),
            "error_rate": self.metrics["errors"] / max(self.metrics["total_ingested"], 1),
            "producer_metrics": await self.producer.get_metrics(),
            "consumer_count": len(self.consumers),
            "runtime_seconds": runtime
        }
    
    async def shutdown(self):
        """Clean shutdown"""
        await self.producer.close()
        for consumer in self.consumers:
            await consumer.close()

# Usage Example
async def example_usage():
    """Example of using Kafka event ingestion"""
    
    # Initialize stream processor
    processor = EventStreamProcessor()
    await processor.initialize()
    
    # Ingest events
    for i in range(10000):
        event = {
            "organization_id": f"org_{i % 100}",  # 100 different orgs
            "metric_name": "api_calls",
            "quantity": i * 1.5,
            "unit": "requests",
            "properties": {
                "endpoint": f"/api/v1/endpoint_{i % 10}",
                "method": "POST"
            },
            "idempotency_key": f"test_{i}"
        }
        
        # High-speed ingestion
        await processor.ingest_event(event)
    
    # Batch ingestion for even higher throughput
    batch = []
    for i in range(10000, 20000):
        batch.append({
            "organization_id": f"org_{i % 100}",
            "metric_name": "storage",
            "quantity": i * 0.001,
            "unit": "GB"
        })
        
        if len(batch) >= 1000:
            await processor.ingest_batch(batch)
            batch = []
    
    # Get metrics
    metrics = await processor.get_metrics()
    print(f"Ingestion metrics: {json.dumps(metrics, indent=2)}")
    
    # Shutdown
    await processor.shutdown()

if __name__ == "__main__":
    asyncio.run(example_usage())

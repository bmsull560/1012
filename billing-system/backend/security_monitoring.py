"""
Security Monitoring and Threat Detection System
Implements real-time security monitoring, anomaly detection, and alerting
"""

import os
import json
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum
import asyncio
import redis.asyncio as redis
import asyncpg
from pydantic import BaseModel, Field
import hashlib
from collections import defaultdict
import statistics


class ThreatLevel(str, Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(str, Enum):
    """Types of security events to monitor"""
    # Authentication events
    FAILED_LOGIN = "failed_login"
    BRUTE_FORCE = "brute_force"
    ACCOUNT_LOCKOUT = "account_lockout"
    SUSPICIOUS_LOGIN = "suspicious_login"
    
    # Authorization events
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERMISSION_VIOLATION = "permission_violation"
    
    # Data events
    MASS_DATA_ACCESS = "mass_data_access"
    DATA_EXFILTRATION = "data_exfiltration"
    SUSPICIOUS_QUERY = "suspicious_query"
    
    # System events
    RATE_LIMIT_VIOLATION = "rate_limit_violation"
    API_ABUSE = "api_abuse"
    INJECTION_ATTEMPT = "injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    
    # Compliance events
    PCI_VIOLATION = "pci_violation"
    GDPR_VIOLATION = "gdpr_violation"
    AUDIT_TAMPERING = "audit_tampering"


class SecurityAlert(BaseModel):
    """Security alert model"""
    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: SecurityEventType
    threat_level: ThreatLevel
    title: str
    description: str
    
    # Context
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    
    # Detection details
    detection_method: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    evidence: Dict[str, Any] = {}
    
    # Response
    auto_response_taken: bool = False
    response_actions: List[str] = []
    requires_human_review: bool = True
    
    # Status
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class SecurityMonitoringSystem:
    """
    Real-time security monitoring and threat detection system
    """
    
    def __init__(
        self,
        database_url: str,
        redis_url: str = "redis://localhost:6379"
    ):
        self.database_url = database_url
        self.redis_url = redis_url
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Detection thresholds
        self.thresholds = {
            "failed_login_attempts": 5,  # Within 5 minutes
            "api_calls_per_minute": 100,
            "data_export_rows": 10000,
            "concurrent_sessions": 5,
            "query_time_seconds": 10,
        }
        
        # Behavioral baselines (would be ML-based in production)
        self.baselines: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Active monitoring tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        
        # Alert channels
        self.alert_channels: List[str] = ["database", "redis", "webhook"]
    
    async def init(self):
        """Initialize monitoring system"""
        # Initialize connections
        self.db_pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10
        )
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=False)
        
        # Create monitoring schema
        await self._create_monitoring_schema()
        
        # Load baselines
        await self._load_baselines()
        
        # Start monitoring tasks
        await self.start_monitoring()
    
    async def _create_monitoring_schema(self):
        """Create security monitoring database schema"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                -- Security monitoring schema
                CREATE SCHEMA IF NOT EXISTS security_monitoring;
                
                -- Security alerts table
                CREATE TABLE IF NOT EXISTS security_monitoring.alerts (
                    alert_id UUID PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    threat_level VARCHAR(20) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    
                    -- Context
                    user_id UUID,
                    tenant_id UUID,
                    ip_address INET,
                    user_agent TEXT,
                    endpoint VARCHAR(255),
                    
                    -- Detection
                    detection_method VARCHAR(100),
                    confidence_score FLOAT,
                    evidence JSONB,
                    
                    -- Response
                    auto_response_taken BOOLEAN DEFAULT FALSE,
                    response_actions TEXT[],
                    requires_human_review BOOLEAN DEFAULT TRUE,
                    
                    -- Status
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_by UUID,
                    acknowledged_at TIMESTAMPTZ,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMPTZ,
                    resolved_by UUID,
                    resolution_notes TEXT,
                    
                    -- Indexes
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_event_type (event_type),
                    INDEX idx_threat_level (threat_level),
                    INDEX idx_user (user_id),
                    INDEX idx_tenant (tenant_id),
                    INDEX idx_unresolved (resolved) WHERE resolved = FALSE
                );
                
                -- Security metrics table (for baselines)
                CREATE TABLE IF NOT EXISTS security_monitoring.metrics (
                    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    metric_name VARCHAR(100) NOT NULL,
                    user_id UUID,
                    tenant_id UUID,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    value FLOAT NOT NULL,
                    metadata JSONB,
                    
                    INDEX idx_metric_name (metric_name),
                    INDEX idx_metric_time (timestamp)
                );
                
                -- Threat intelligence table
                CREATE TABLE IF NOT EXISTS security_monitoring.threat_intelligence (
                    threat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    threat_type VARCHAR(50) NOT NULL,
                    indicator VARCHAR(255) NOT NULL,
                    indicator_type VARCHAR(50) NOT NULL, -- ip, domain, hash, pattern
                    threat_level VARCHAR(20) NOT NULL,
                    source VARCHAR(100),
                    first_seen TIMESTAMPTZ DEFAULT NOW(),
                    last_seen TIMESTAMPTZ DEFAULT NOW(),
                    is_active BOOLEAN DEFAULT TRUE,
                    metadata JSONB,
                    
                    UNIQUE(indicator, indicator_type),
                    INDEX idx_indicator (indicator),
                    INDEX idx_active (is_active)
                );
                
                -- Incident response playbooks
                CREATE TABLE IF NOT EXISTS security_monitoring.playbooks (
                    playbook_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    event_type VARCHAR(50) NOT NULL,
                    threat_level VARCHAR(20) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    auto_execute BOOLEAN DEFAULT FALSE,
                    steps JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    
                    UNIQUE(event_type, threat_level)
                );
                
                -- Insert default playbooks
                INSERT INTO security_monitoring.playbooks (event_type, threat_level, name, steps, auto_execute)
                VALUES 
                    ('brute_force', 'high', 'Brute Force Response', 
                     '[{"action": "lock_account", "duration_minutes": 30}, {"action": "alert_admin"}, {"action": "log_incident"}]', 
                     TRUE),
                    ('data_exfiltration', 'critical', 'Data Exfiltration Response',
                     '[{"action": "terminate_session"}, {"action": "lock_account"}, {"action": "alert_security_team"}, {"action": "preserve_evidence"}]',
                     TRUE),
                    ('injection_attempt', 'high', 'Injection Attack Response',
                     '[{"action": "block_ip", "duration_minutes": 60}, {"action": "alert_admin"}, {"action": "increase_monitoring"}]',
                     TRUE)
                ON CONFLICT (event_type, threat_level) DO NOTHING;
            """)
    
    async def start_monitoring(self):
        """Start all monitoring tasks"""
        # Start continuous monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._monitor_authentication()),
            asyncio.create_task(self._monitor_api_usage()),
            asyncio.create_task(self._monitor_data_access()),
            asyncio.create_task(self._monitor_system_health()),
            asyncio.create_task(self._process_redis_events()),
        ]
    
    async def stop_monitoring(self):
        """Stop all monitoring tasks"""
        for task in self.monitoring_tasks:
            task.cancel()
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
    
    # ==================== DETECTION METHODS ====================
    
    async def detect_brute_force(
        self,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[SecurityAlert]:
        """Detect brute force attacks"""
        key = f"failed_login:{user_id or ip_address}"
        
        # Get recent failed attempts
        attempts = await self.redis_client.get(key)
        if attempts and int(attempts) >= self.thresholds["failed_login_attempts"]:
            return SecurityAlert(
                event_type=SecurityEventType.BRUTE_FORCE,
                threat_level=ThreatLevel.HIGH,
                title="Brute Force Attack Detected",
                description=f"Multiple failed login attempts detected from {ip_address or user_id}",
                user_id=user_id,
                ip_address=ip_address,
                detection_method="threshold_based",
                confidence_score=0.9,
                evidence={
                    "failed_attempts": int(attempts),
                    "threshold": self.thresholds["failed_login_attempts"],
                    "time_window": "5 minutes"
                }
            )
        return None
    
    async def detect_data_exfiltration(
        self,
        user_id: str,
        query_count: int,
        data_volume: int
    ) -> Optional[SecurityAlert]:
        """Detect potential data exfiltration"""
        # Get user's baseline
        baseline = self.baselines.get(user_id, {})
        avg_queries = baseline.get("avg_queries_per_hour", 10)
        avg_volume = baseline.get("avg_data_volume", 1000)
        
        # Check for anomalies (simplified - would use ML in production)
        query_anomaly = query_count > avg_queries * 5
        volume_anomaly = data_volume > avg_volume * 10
        
        if query_anomaly and volume_anomaly:
            return SecurityAlert(
                event_type=SecurityEventType.DATA_EXFILTRATION,
                threat_level=ThreatLevel.CRITICAL,
                title="Potential Data Exfiltration",
                description=f"Unusual data access pattern detected for user {user_id}",
                user_id=user_id,
                detection_method="anomaly_detection",
                confidence_score=0.85,
                evidence={
                    "query_count": query_count,
                    "baseline_queries": avg_queries,
                    "data_volume": data_volume,
                    "baseline_volume": avg_volume
                }
            )
        return None
    
    async def detect_injection(self, query: str, endpoint: str) -> Optional[SecurityAlert]:
        """Detect SQL/NoSQL injection attempts"""
        # Simplified injection detection patterns
        injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|CREATE|ALTER)\b)",
            r"(--|#|\/\*|\*\/)",
            r"(\bOR\b\s*\d+\s*=\s*\d+)",
            r"(\bAND\b\s*\d+\s*=\s*\d+)",
            r"(';|\";\s*(--|#))",
            r"(\bEXEC\b|\bEXECUTE\b)",
            r"(<script|javascript:|onerror=|onload=)",
        ]
        
        import re
        for pattern in injection_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return SecurityAlert(
                    event_type=SecurityEventType.INJECTION_ATTEMPT,
                    threat_level=ThreatLevel.HIGH,
                    title="Injection Attack Attempt",
                    description=f"Potential injection attack detected at {endpoint}",
                    endpoint=endpoint,
                    detection_method="pattern_matching",
                    confidence_score=0.8,
                    evidence={
                        "query_sample": query[:200],
                        "matched_pattern": pattern
                    }
                )
        return None
    
    async def detect_privilege_escalation(
        self,
        user_id: str,
        old_roles: List[str],
        new_roles: List[str]
    ) -> Optional[SecurityAlert]:
        """Detect unauthorized privilege escalation"""
        # Check for unexpected role changes
        added_roles = set(new_roles) - set(old_roles)
        high_privilege_roles = {"admin", "super_admin", "billing_admin"}
        
        if added_roles & high_privilege_roles:
            return SecurityAlert(
                event_type=SecurityEventType.PRIVILEGE_ESCALATION,
                threat_level=ThreatLevel.CRITICAL,
                title="Privilege Escalation Detected",
                description=f"User {user_id} gained high-privilege roles",
                user_id=user_id,
                detection_method="rule_based",
                confidence_score=0.95,
                evidence={
                    "old_roles": old_roles,
                    "new_roles": new_roles,
                    "added_roles": list(added_roles)
                }
            )
        return None
    
    # ==================== MONITORING TASKS ====================
    
    async def _monitor_authentication(self):
        """Monitor authentication events"""
        while True:
            try:
                # Check for brute force attacks
                pattern = "failed_login:*"
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(
                        cursor, match=pattern.encode(), count=100
                    )
                    
                    for key in keys:
                        identifier = key.decode().split(":")[-1]
                        alert = await self.detect_brute_force(ip_address=identifier)
                        if alert:
                            await self.raise_alert(alert)
                    
                    if cursor == 0:
                        break
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Error in authentication monitoring: {e}")
                await asyncio.sleep(30)
    
    async def _monitor_api_usage(self):
        """Monitor API usage patterns"""
        while True:
            try:
                # Check rate limits
                async with self.db_pool.acquire() as conn:
                    # Find users exceeding API limits
                    rows = await conn.fetch("""
                        SELECT user_id, COUNT(*) as request_count
                        FROM audit_immutable.audit_trail
                        WHERE timestamp > NOW() - INTERVAL '1 minute'
                        GROUP BY user_id
                        HAVING COUNT(*) > $1
                    """, self.thresholds["api_calls_per_minute"])
                    
                    for row in rows:
                        alert = SecurityAlert(
                            event_type=SecurityEventType.API_ABUSE,
                            threat_level=ThreatLevel.MEDIUM,
                            title="API Rate Limit Exceeded",
                            description=f"User {row['user_id']} exceeded API rate limit",
                            user_id=str(row['user_id']),
                            detection_method="threshold_based",
                            confidence_score=1.0,
                            evidence={
                                "request_count": row['request_count'],
                                "threshold": self.thresholds["api_calls_per_minute"],
                                "time_window": "1 minute"
                            }
                        )
                        await self.raise_alert(alert)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error in API monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_data_access(self):
        """Monitor data access patterns"""
        while True:
            try:
                async with self.db_pool.acquire() as conn:
                    # Check for mass data access
                    rows = await conn.fetch("""
                        SELECT 
                            actor_id as user_id,
                            COUNT(*) as query_count,
                            SUM((metadata->>'row_count')::int) as total_rows
                        FROM audit_immutable.audit_trail
                        WHERE timestamp > NOW() - INTERVAL '1 hour'
                        AND event_type IN ('data.read', 'data.export')
                        GROUP BY actor_id
                        HAVING SUM((metadata->>'row_count')::int) > $1
                    """, self.thresholds["data_export_rows"])
                    
                    for row in rows:
                        if row['user_id']:
                            alert = await self.detect_data_exfiltration(
                                str(row['user_id']),
                                row['query_count'],
                                row['total_rows'] or 0
                            )
                            if alert:
                                await self.raise_alert(alert)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"Error in data access monitoring: {e}")
                await asyncio.sleep(300)
    
    async def _monitor_system_health(self):
        """Monitor system health and performance"""
        while True:
            try:
                async with self.db_pool.acquire() as conn:
                    # Check for slow queries
                    rows = await conn.fetch("""
                        SELECT query, duration, usename
                        FROM pg_stat_statements
                        WHERE duration > $1
                        ORDER BY duration DESC
                        LIMIT 10
                    """, self.thresholds["query_time_seconds"] * 1000)  # Convert to ms
                    
                    for row in rows:
                        # Check for potential injection in slow queries
                        alert = await self.detect_injection(
                            row['query'],
                            "database_query"
                        )
                        if alert:
                            alert.user_id = row['usename']
                            await self.raise_alert(alert)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                # pg_stat_statements might not be available
                await asyncio.sleep(60)
    
    async def _process_redis_events(self):
        """Process security events from Redis pub/sub"""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("security_events")
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    event = json.loads(message['data'])
                    await self.process_security_event(event)
                except Exception as e:
                    print(f"Error processing Redis event: {e}")
    
    # ==================== ALERT MANAGEMENT ====================
    
    async def raise_alert(self, alert: SecurityAlert):
        """Raise a security alert"""
        # Store in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO security_monitoring.alerts (
                    alert_id, timestamp, event_type, threat_level,
                    title, description, user_id, tenant_id,
                    ip_address, user_agent, endpoint,
                    detection_method, confidence_score, evidence,
                    auto_response_taken, response_actions,
                    requires_human_review
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            """, UUID(alert.alert_id), alert.timestamp, alert.event_type.value,
                alert.threat_level.value, alert.title, alert.description,
                UUID(alert.user_id) if alert.user_id else None,
                UUID(alert.tenant_id) if alert.tenant_id else None,
                alert.ip_address, alert.user_agent, alert.endpoint,
                alert.detection_method, alert.confidence_score,
                json.dumps(alert.evidence), alert.auto_response_taken,
                alert.response_actions, alert.requires_human_review)
        
        # Execute automatic response if configured
        if alert.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            await self.execute_response_playbook(alert)
        
        # Send notifications
        await self.send_alert_notifications(alert)
        
        # Update metrics
        await self.update_security_metrics(alert)
    
    async def execute_response_playbook(self, alert: SecurityAlert):
        """Execute automated response playbook"""
        async with self.db_pool.acquire() as conn:
            # Get playbook for this event type
            playbook = await conn.fetchrow("""
                SELECT steps, auto_execute
                FROM security_monitoring.playbooks
                WHERE event_type = $1 AND threat_level = $2
            """, alert.event_type.value, alert.threat_level.value)
            
            if playbook and playbook['auto_execute']:
                steps = json.loads(playbook['steps'])
                executed_actions = []
                
                for step in steps:
                    action = step['action']
                    
                    if action == 'lock_account' and alert.user_id:
                        duration = step.get('duration_minutes', 30)
                        await self.lock_user_account(alert.user_id, duration)
                        executed_actions.append(f"locked_account_{duration}min")
                    
                    elif action == 'block_ip' and alert.ip_address:
                        duration = step.get('duration_minutes', 60)
                        await self.block_ip_address(alert.ip_address, duration)
                        executed_actions.append(f"blocked_ip_{duration}min")
                    
                    elif action == 'terminate_session' and alert.user_id:
                        await self.terminate_user_sessions(alert.user_id)
                        executed_actions.append("terminated_sessions")
                    
                    elif action == 'alert_admin':
                        await self.send_admin_alert(alert)
                        executed_actions.append("alerted_admin")
                
                # Update alert with executed actions
                alert.auto_response_taken = True
                alert.response_actions = executed_actions
    
    async def send_alert_notifications(self, alert: SecurityAlert):
        """Send alert notifications to configured channels"""
        # Publish to Redis for real-time notifications
        await self.redis_client.publish(
            "security_alerts",
            json.dumps({
                "alert_id": alert.alert_id,
                "event_type": alert.event_type.value,
                "threat_level": alert.threat_level.value,
                "title": alert.title,
                "timestamp": alert.timestamp.isoformat()
            })
        )
        
        # For critical alerts, send immediate notifications
        if alert.threat_level == ThreatLevel.CRITICAL:
            # In production, integrate with PagerDuty, Slack, email, etc.
            pass
    
    async def acknowledge_alert(self, alert_id: str, user_id: str):
        """Acknowledge a security alert"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE security_monitoring.alerts
                SET acknowledged = TRUE,
                    acknowledged_by = $1,
                    acknowledged_at = NOW()
                WHERE alert_id = $2
            """, UUID(user_id), UUID(alert_id))
    
    async def resolve_alert(
        self,
        alert_id: str,
        user_id: str,
        resolution_notes: str
    ):
        """Resolve a security alert"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE security_monitoring.alerts
                SET resolved = TRUE,
                    resolved_by = $1,
                    resolved_at = NOW(),
                    resolution_notes = $2
                WHERE alert_id = $3
            """, UUID(user_id), UUID(alert_id), resolution_notes)
    
    # ==================== HELPER METHODS ====================
    
    async def _load_baselines(self):
        """Load behavioral baselines for anomaly detection"""
        async with self.db_pool.acquire() as conn:
            # Load user baselines
            rows = await conn.fetch("""
                SELECT 
                    user_id,
                    AVG(value) as avg_value,
                    STDDEV(value) as std_value,
                    metric_name
                FROM security_monitoring.metrics
                WHERE timestamp > NOW() - INTERVAL '30 days'
                GROUP BY user_id, metric_name
            """)
            
            for row in rows:
                user_id = str(row['user_id'])
                metric = row['metric_name']
                self.baselines[user_id][f"avg_{metric}"] = row['avg_value']
                self.baselines[user_id][f"std_{metric}"] = row['std_value']
    
    async def update_security_metrics(self, alert: SecurityAlert):
        """Update security metrics for reporting"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO security_monitoring.metrics (
                    metric_name, user_id, tenant_id, value, metadata
                ) VALUES ($1, $2, $3, $4, $5)
            """, f"alert_{alert.event_type.value}",
                UUID(alert.user_id) if alert.user_id else None,
                UUID(alert.tenant_id) if alert.tenant_id else None,
                1.0,
                json.dumps({"threat_level": alert.threat_level.value}))
    
    async def lock_user_account(self, user_id: str, duration_minutes: int):
        """Lock a user account temporarily"""
        locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE users
                SET locked_until = $1,
                    is_active = FALSE
                WHERE id = $2
            """, locked_until, UUID(user_id))
    
    async def block_ip_address(self, ip_address: str, duration_minutes: int):
        """Block an IP address temporarily"""
        # Store in Redis with expiration
        key = f"blocked_ip:{ip_address}"
        await self.redis_client.setex(
            key,
            duration_minutes * 60,
            "blocked"
        )
    
    async def terminate_user_sessions(self, user_id: str):
        """Terminate all sessions for a user"""
        # Blacklist all user tokens
        pattern = f"session:*:{user_id}"
        cursor = 0
        while True:
            cursor, keys = await self.redis_client.scan(
                cursor, match=pattern.encode(), count=100
            )
            
            for key in keys:
                await self.redis_client.delete(key)
            
            if cursor == 0:
                break
    
    async def send_admin_alert(self, alert: SecurityAlert):
        """Send alert to administrators"""
        # In production, integrate with notification services
        print(f"ADMIN ALERT: {alert.title} - {alert.description}")
    
    async def process_security_event(self, event: Dict[str, Any]):
        """Process incoming security event"""
        event_type = event.get("type")
        
        if event_type == "failed_login":
            alert = await self.detect_brute_force(
                user_id=event.get("user_id"),
                ip_address=event.get("ip_address")
            )
        elif event_type == "suspicious_query":
            alert = await self.detect_injection(
                event.get("query", ""),
                event.get("endpoint", "")
            )
        else:
            alert = None
        
        if alert:
            await self.raise_alert(alert)
    
    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security dashboard data"""
        async with self.db_pool.acquire() as conn:
            # Get alert statistics
            alert_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_alerts,
                    COUNT(*) FILTER (WHERE threat_level = 'critical') as critical_alerts,
                    COUNT(*) FILTER (WHERE threat_level = 'high') as high_alerts,
                    COUNT(*) FILTER (WHERE NOT resolved) as unresolved_alerts,
                    COUNT(*) FILTER (WHERE timestamp > NOW() - INTERVAL '24 hours') as alerts_24h
                FROM security_monitoring.alerts
                WHERE timestamp > NOW() - INTERVAL '30 days'
            """)
            
            # Get top threats
            top_threats = await conn.fetch("""
                SELECT event_type, COUNT(*) as count
                FROM security_monitoring.alerts
                WHERE timestamp > NOW() - INTERVAL '7 days'
                GROUP BY event_type
                ORDER BY count DESC
                LIMIT 5
            """)
            
            # Get recent critical alerts
            recent_critical = await conn.fetch("""
                SELECT alert_id, timestamp, title, resolved
                FROM security_monitoring.alerts
                WHERE threat_level = 'critical'
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            
            return {
                "statistics": dict(alert_stats) if alert_stats else {},
                "top_threats": [dict(t) for t in top_threats],
                "recent_critical_alerts": [dict(a) for a in recent_critical],
                "monitoring_status": "active",
                "last_update": datetime.utcnow().isoformat()
            }


# Export main components
__all__ = [
    'SecurityMonitoringSystem',
    'SecurityAlert',
    'ThreatLevel',
    'SecurityEventType'
]

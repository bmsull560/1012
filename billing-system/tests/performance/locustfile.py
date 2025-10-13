"""
Load testing for ValueVerse Billing System
Target: 1M events per minute (16,667 events per second)
"""

import random
import time
import json
from datetime import datetime, timedelta
from uuid import uuid4
from decimal import Decimal
from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging

# Setup logging
setup_logging("INFO", None)

class BillingLoadTest(HttpUser):
    wait_time = between(0.001, 0.01)  # Very short wait for high throughput
    
    def on_start(self):
        """Login and get authentication token"""
        # In production, implement proper auth
        self.headers = {
            "Authorization": f"Bearer {self.get_auth_token()}",
            "Content-Type": "application/json"
        }
        self.organization_id = str(uuid4())
        self.metrics = ["api_calls", "storage_gb", "compute_hours", "bandwidth_gb"]
        
    def get_auth_token(self):
        """Get authentication token"""
        # Mock authentication - replace with actual auth flow
        response = self.client.post("/api/v1/auth/login", json={
            "email": "loadtest@valueverse.com",
            "password": "LoadTest123!"
        })
        if response.status_code == 200:
            return response.json().get("access_token", "mock_token")
        return "mock_token_for_testing"
    
    @task(80)
    def record_usage_event(self):
        """Record a usage event - highest frequency task"""
        metric = random.choice(self.metrics)
        quantity = random.uniform(1, 1000)
        
        event_data = {
            "metric_name": metric,
            "quantity": quantity,
            "unit": self.get_unit_for_metric(metric),
            "timestamp": datetime.utcnow().isoformat(),
            "idempotency_key": str(uuid4()),
            "properties": {
                "source": "load_test",
                "region": random.choice(["us-east-1", "eu-west-1", "ap-south-1"])
            }
        }
        
        with self.client.post(
            "/api/v1/billing/usage",
            json=event_data,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(15)
    def get_usage_summary(self):
        """Get usage summary - medium frequency"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "metric_name": random.choice(self.metrics + [None])
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        with self.client.get(
            "/api/v1/billing/usage/summary",
            params=params,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(3)
    def health_check(self):
        """Health check endpoint - low frequency"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure("Health check failed")
    
    @task(2)
    def get_invoices(self):
        """Get invoices - low frequency"""
        with self.client.get(
            "/api/v1/billing/invoices",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    def get_unit_for_metric(self, metric):
        """Get appropriate unit for metric"""
        units = {
            "api_calls": "calls",
            "storage_gb": "gb",
            "compute_hours": "hours",
            "bandwidth_gb": "gb"
        }
        return units.get(metric, "units")

class HighVolumeUser(BillingLoadTest):
    """User simulating high-volume batch operations"""
    wait_time = between(0.0001, 0.001)  # Even faster for stress testing
    
    @task
    def batch_usage_events(self):
        """Send batch of usage events"""
        batch_size = random.randint(10, 100)
        events = []
        
        for _ in range(batch_size):
            metric = random.choice(self.metrics)
            events.append({
                "metric_name": metric,
                "quantity": random.uniform(1, 1000),
                "unit": self.get_unit_for_metric(metric),
                "timestamp": datetime.utcnow().isoformat(),
                "idempotency_key": str(uuid4())
            })
        
        with self.client.post(
            "/api/v1/billing/usage/batch",
            json={"events": events},
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Batch failed with status {response.status_code}")

# Custom event handlers for detailed metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Custom request handler for detailed metrics"""
    if exception:
        print(f"Request {name} failed with exception: {exception}")
    elif response_time > 100:  # Log slow requests
        print(f"Slow request: {name} took {response_time}ms")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print final statistics"""
    print("\n" + "="*50)
    print("LOAD TEST RESULTS")
    print("="*50)
    
    # Calculate events per minute
    total_requests = environment.stats.total.num_requests
    total_time = time.time() - environment.stats.start_time
    events_per_minute = (total_requests / total_time) * 60
    
    print(f"Total Requests: {total_requests:,}")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Events per Minute: {events_per_minute:,.0f}")
    print(f"Target: 1,000,000 events/minute")
    print(f"Achievement: {(events_per_minute / 1_000_000) * 100:.1f}%")
    
    # Response time percentiles
    if environment.stats.total.response_times:
        print(f"\nResponse Time Percentiles:")
        print(f"  50%: {environment.stats.total.get_response_time_percentile(0.5):.0f}ms")
        print(f"  90%: {environment.stats.total.get_response_time_percentile(0.9):.0f}ms")
        print(f"  95%: {environment.stats.total.get_response_time_percentile(0.95):.0f}ms")
        print(f"  99%: {environment.stats.total.get_response_time_percentile(0.99):.0f}ms")
    
    # Error rate
    error_rate = (environment.stats.total.num_failures / max(total_requests, 1)) * 100
    print(f"\nError Rate: {error_rate:.2f}%")
    print("="*50)

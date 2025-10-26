/**
 * K6 Load Testing Script for ValueVerse Platform
 * 
 * Usage:
 *   k6 run k6-load-test.js
 *   k6 run --vus 100 --duration 5m k6-load-test.js
 *   k6 cloud k6-load-test.js  # For cloud execution
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { randomString, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// ==================== Configuration ====================

// Test configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost';
const TEST_DURATION = __ENV.DURATION || '5m';
const VIRTUAL_USERS = __ENV.VUS || 50;

// Service endpoints
const SERVICES = {
  frontend: `${BASE_URL}:3000`,
  architect: `${BASE_URL}:8001`,
  committer: `${BASE_URL}:8002`,
  executor: `${BASE_URL}:8003`,
  billing: `${BASE_URL}:8004`
};

// Custom metrics
const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');
const dbLatency = new Trend('db_latency');

// Test scenarios
export const options = {
  scenarios: {
    // Smoke test - minimal load
    smoke: {
      executor: 'constant-vus',
      vus: 2,
      duration: '1m',
      tags: { scenario: 'smoke' }
    },
    
    // Average load test
    average_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 20 },  // Ramp up
        { duration: '5m', target: 20 },  // Stay at 20 users
        { duration: '2m', target: 0 },   // Ramp down
      ],
      tags: { scenario: 'average' }
    },
    
    // Stress test - high load
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },   // Ramp up
        { duration: '3m', target: 50 },   // Stay at 50 users
        { duration: '2m', target: 100 },  // Increase to 100
        { duration: '3m', target: 100 },  // Stay at 100
        { duration: '2m', target: 0 },    // Ramp down
      ],
      tags: { scenario: 'stress' }
    },
    
    // Spike test - sudden load increase
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 5 },   // Baseline
        { duration: '5s', target: 100 },  // Spike to 100 users
        { duration: '3m', target: 100 },  // Stay at 100
        { duration: '5s', target: 5 },    // Drop to baseline
        { duration: '10s', target: 0 },   // Ramp down
      ],
      tags: { scenario: 'spike' }
    },
    
    // Soak test - extended duration
    soak: {
      executor: 'constant-vus',
      vus: 30,
      duration: '30m',
      tags: { scenario: 'soak' }
    }
  },
  
  thresholds: {
    // Response time thresholds
    http_req_duration: [
      'p(50)<500',   // 50% of requests under 500ms
      'p(95)<2000',  // 95% of requests under 2s
      'p(99)<5000',  // 99% of requests under 5s
    ],
    
    // Error rate threshold
    errors: ['rate<0.05'],  // Less than 5% errors
    
    // Custom metric thresholds
    api_latency: ['p(95)<1000'],
    db_latency: ['p(95)<100'],
    
    // Request rate
    http_reqs: ['rate>100'],  // At least 100 requests per second
  }
};

// ==================== Helper Functions ====================

/**
 * Generate test user credentials
 */
function generateUser() {
  return {
    email: `test_${randomString(8)}@valueverse.com`,
    password: 'TestPassword123!',
    fullName: `Test User ${randomString(5)}`
  };
}

/**
 * Generate test value model
 */
function generateValueModel() {
  return {
    company_name: `Test Company ${randomString(6)}`,
    industry: ['Technology', 'Finance', 'Healthcare', 'Retail'][randomIntBetween(0, 3)],
    stage: ['startup', 'growth', 'enterprise'][randomIntBetween(0, 2)],
    inputs: {
      current_revenue: randomIntBetween(1000000, 10000000),
      target_growth: randomIntBetween(10, 50),
      implementation_cost: randomIntBetween(100000, 1000000),
      time_to_value: randomIntBetween(3, 12)
    }
  };
}

/**
 * Authenticate and get token
 */
function authenticate() {
  const user = generateUser();
  
  // Register user
  const registerRes = http.post(
    `${SERVICES.frontend}/api/auth/register`,
    JSON.stringify(user),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  if (registerRes.status !== 200) {
    // Try login with existing test user
    const loginRes = http.post(
      `${SERVICES.frontend}/api/auth/login`,
      JSON.stringify({
        email: 'loadtest@valueverse.com',
        password: 'LoadTest123!'
      }),
      { headers: { 'Content-Type': 'application/json' } }
    );
    
    if (loginRes.status === 200) {
      return loginRes.json('token');
    }
  }
  
  return registerRes.json('token');
}

// ==================== Test Scenarios ====================

/**
 * Test health check endpoints
 */
export function testHealthChecks() {
  const services = ['architect', 'committer', 'executor', 'billing'];
  
  services.forEach(service => {
    const res = http.get(`${SERVICES[service]}/health`);
    
    check(res, {
      'health check status is 200': (r) => r.status === 200,
      'health check response is healthy': (r) => r.json('status') === 'healthy'
    });
    
    errorRate.add(res.status !== 200);
    apiLatency.add(res.timings.duration);
  });
}

/**
 * Test value model creation workflow
 */
export function testValueModelCreation() {
  const token = authenticate();
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };
  
  // Create value model
  const model = generateValueModel();
  const createRes = http.post(
    `${SERVICES.architect}/api/v1/models`,
    JSON.stringify(model),
    { headers }
  );
  
  check(createRes, {
    'model creation successful': (r) => r.status === 200,
    'model has ID': (r) => r.json('id') !== undefined
  });
  
  errorRate.add(createRes.status !== 200);
  apiLatency.add(createRes.timings.duration);
  
  if (createRes.status === 200) {
    const modelId = createRes.json('id');
    
    // Analyze model
    const analyzeRes = http.post(
      `${SERVICES.architect}/api/v1/models/${modelId}/analyze`,
      null,
      { headers }
    );
    
    check(analyzeRes, {
      'analysis successful': (r) => r.status === 200,
      'analysis has recommendations': (r) => r.json('recommendations') !== undefined
    });
    
    // Commit model
    const commitRes = http.post(
      `${SERVICES.committer}/api/v1/commit`,
      JSON.stringify({
        model_id: modelId,
        message: 'Load test commit',
        version: '1.0.0'
      }),
      { headers }
    );
    
    check(commitRes, {
      'commit successful': (r) => r.status === 200,
      'commit has ID': (r) => r.json('commit_id') !== undefined
    });
  }
}

/**
 * Test strategy execution workflow
 */
export function testStrategyExecution() {
  const token = authenticate();
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };
  
  // Create strategy
  const strategy = {
    name: `Load Test Strategy ${randomString(6)}`,
    description: 'Strategy for load testing',
    target_value: randomIntBetween(100000, 1000000),
    timeline_days: randomIntBetween(30, 180),
    milestones: [
      { name: 'Phase 1', description: 'Initial phase' },
      { name: 'Phase 2', description: 'Implementation' },
      { name: 'Phase 3', description: 'Completion' }
    ]
  };
  
  const createRes = http.post(
    `${SERVICES.executor}/strategies`,
    JSON.stringify(strategy),
    { headers }
  );
  
  check(createRes, {
    'strategy creation successful': (r) => r.status === 200,
    'strategy has ID': (r) => r.json('id') !== undefined
  });
  
  if (createRes.status === 200) {
    const strategyId = createRes.json('id');
    
    // Execute strategy
    const executeRes = http.post(
      `${SERVICES.executor}/execute`,
      JSON.stringify({
        strategy_id: strategyId,
        executor_id: 'loadtest_user',
        priority: 'medium',
        auto_assign_tasks: true
      }),
      { headers }
    );
    
    check(executeRes, {
      'execution successful': (r) => r.status === 200,
      'execution has tasks': (r) => r.json('tasks') !== undefined && r.json('tasks').length > 0
    });
    
    errorRate.add(executeRes.status !== 200);
  }
}

/**
 * Test concurrent API calls
 */
export function testConcurrentRequests() {
  const endpoints = [
    `${SERVICES.architect}/health`,
    `${SERVICES.committer}/health`,
    `${SERVICES.executor}/health`,
    `${SERVICES.billing}/health`
  ];
  
  const responses = http.batch(
    endpoints.map(url => ['GET', url, null, { tags: { name: 'concurrent' } }])
  );
  
  responses.forEach(res => {
    check(res, {
      'concurrent request successful': (r) => r.status === 200
    });
    errorRate.add(res.status !== 200);
  });
}

/**
 * Test database operations under load
 */
export function testDatabaseOperations() {
  const token = authenticate();
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };
  
  // Perform multiple database operations
  const operations = [];
  
  for (let i = 0; i < 5; i++) {
    operations.push([
      'POST',
      `${SERVICES.architect}/api/v1/models`,
      JSON.stringify(generateValueModel()),
      { headers }
    ]);
  }
  
  const startTime = Date.now();
  const responses = http.batch(operations);
  const dbTime = Date.now() - startTime;
  
  dbLatency.add(dbTime);
  
  responses.forEach(res => {
    check(res, {
      'database operation successful': (r) => r.status === 200
    });
  });
}

// ==================== Main Test Function ====================

export default function() {
  // Select test based on scenario
  const scenario = __ENV.SCENARIO || 'mixed';
  
  switch(scenario) {
    case 'health':
      testHealthChecks();
      break;
    case 'models':
      testValueModelCreation();
      break;
    case 'execution':
      testStrategyExecution();
      break;
    case 'concurrent':
      testConcurrentRequests();
      break;
    case 'database':
      testDatabaseOperations();
      break;
    case 'mixed':
    default:
      // Run a mix of all tests
      const testChoice = randomIntBetween(1, 5);
      switch(testChoice) {
        case 1:
          testHealthChecks();
          break;
        case 2:
          testValueModelCreation();
          break;
        case 3:
          testStrategyExecution();
          break;
        case 4:
          testConcurrentRequests();
          break;
        case 5:
          testDatabaseOperations();
          break;
      }
  }
  
  // Random sleep between requests (0.5 - 2 seconds)
  sleep(randomIntBetween(0.5, 2));
}

// ==================== Lifecycle Hooks ====================

/**
 * Setup function - runs once per VU before the test
 */
export function setup() {
  console.log('Starting load test...');
  console.log(`Target: ${BASE_URL}`);
  console.log(`Duration: ${TEST_DURATION}`);
  console.log(`Virtual Users: ${VIRTUAL_USERS}`);
  
  // Create test user for authentication
  const testUser = {
    email: 'loadtest@valueverse.com',
    password: 'LoadTest123!',
    fullName: 'Load Test User'
  };
  
  http.post(
    `${SERVICES.frontend}/api/auth/register`,
    JSON.stringify(testUser),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  return { startTime: Date.now() };
}

/**
 * Teardown function - runs once after all VUs finish
 */
export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`Load test completed in ${duration} seconds`);
}

/**
 * Handle test results
 */
export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'summary.json': JSON.stringify(data),
    'summary.html': htmlReport(data)
  };
}

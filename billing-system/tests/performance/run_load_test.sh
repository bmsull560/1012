#!/bin/bash

# Load testing script for ValueVerse Billing System
# Target: 1M events per minute with <100ms p95 response time

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}ValueVerse Billing System - Load Test Runner${NC}"
echo -e "${GREEN}Target: 1M events/minute | <100ms p95${NC}"
echo -e "${GREEN}================================================${NC}"

# Configuration
API_HOST=${API_HOST:-"http://localhost:8000"}
USERS=${USERS:-1000}
SPAWN_RATE=${SPAWN_RATE:-50}
RUN_TIME=${RUN_TIME:-"5m"}
REPORT_DIR="./reports/$(date +%Y%m%d_%H%M%S)"

# Check if Locust is installed
if ! command -v locust &> /dev/null; then
    echo -e "${YELLOW}Installing Locust...${NC}"
    pip install locust
fi

# Create report directory
mkdir -p "$REPORT_DIR"

echo -e "${YELLOW}Starting load test with configuration:${NC}"
echo "  Host: $API_HOST"
echo "  Users: $USERS"
echo "  Spawn Rate: $SPAWN_RATE users/second"
echo "  Run Time: $RUN_TIME"
echo "  Report Directory: $REPORT_DIR"
echo ""

# Function to run progressive load test
run_progressive_test() {
    echo -e "${GREEN}Running Progressive Load Test...${NC}"
    
    # Stage 1: Warm-up (10% load)
    echo -e "${YELLOW}Stage 1: Warm-up (10% load)${NC}"
    locust -f locustfile.py \
        --host="$API_HOST" \
        --users=$((USERS / 10)) \
        --spawn-rate=$((SPAWN_RATE / 10)) \
        --run-time=1m \
        --headless \
        --html="${REPORT_DIR}/stage1_warmup.html" \
        --csv="${REPORT_DIR}/stage1_warmup"
    
    sleep 10
    
    # Stage 2: Normal load (50% load)
    echo -e "${YELLOW}Stage 2: Normal Load (50% load)${NC}"
    locust -f locustfile.py \
        --host="$API_HOST" \
        --users=$((USERS / 2)) \
        --spawn-rate=$((SPAWN_RATE / 2)) \
        --run-time=2m \
        --headless \
        --html="${REPORT_DIR}/stage2_normal.html" \
        --csv="${REPORT_DIR}/stage2_normal"
    
    sleep 10
    
    # Stage 3: Peak load (100% load)
    echo -e "${YELLOW}Stage 3: Peak Load (100% load)${NC}"
    locust -f locustfile.py \
        --host="$API_HOST" \
        --users="$USERS" \
        --spawn-rate="$SPAWN_RATE" \
        --run-time="$RUN_TIME" \
        --headless \
        --html="${REPORT_DIR}/stage3_peak.html" \
        --csv="${REPORT_DIR}/stage3_peak"
}

# Function to run stress test
run_stress_test() {
    echo -e "${GREEN}Running Stress Test...${NC}"
    
    # Stress test with 2x target load
    locust -f locustfile.py \
        --host="$API_HOST" \
        --users=$((USERS * 2)) \
        --spawn-rate=$((SPAWN_RATE * 2)) \
        --run-time=3m \
        --headless \
        --html="${REPORT_DIR}/stress_test.html" \
        --csv="${REPORT_DIR}/stress_test"
}

# Function to calculate events per minute
calculate_throughput() {
    local csv_file="$1"
    if [ -f "${csv_file}_stats.csv" ]; then
        # Extract total requests and calculate events per minute
        local total_requests=$(tail -n 1 "${csv_file}_stats.csv" | cut -d',' -f3)
        local total_time=$(tail -n 1 "${csv_file}_stats.csv" | cut -d',' -f14)
        
        if [ -n "$total_requests" ] && [ -n "$total_time" ]; then
            local events_per_minute=$(echo "scale=0; $total_requests * 60 / $total_time" | bc 2>/dev/null || echo "0")
            echo "Events per minute: $events_per_minute"
            
            # Check if target is met
            if [ "$events_per_minute" -ge 1000000 ]; then
                echo -e "${GREEN}✓ Target achieved: 1M+ events/minute${NC}"
            else
                local percentage=$(echo "scale=1; $events_per_minute * 100 / 1000000" | bc 2>/dev/null || echo "0")
                echo -e "${YELLOW}⚠ Below target: ${percentage}% of 1M events/minute${NC}"
            fi
        fi
    fi
}

# Function to check p95 response time
check_response_time() {
    local csv_file="$1"
    if [ -f "${csv_file}_stats.csv" ]; then
        # Extract p95 response time (in milliseconds)
        local p95=$(tail -n 1 "${csv_file}_stats.csv" | cut -d',' -f12)
        
        if [ -n "$p95" ]; then
            echo "P95 Response Time: ${p95}ms"
            
            # Check if target is met
            if [ "$(echo "$p95 < 100" | bc)" -eq 1 ]; then
                echo -e "${GREEN}✓ Target achieved: <100ms p95${NC}"
            else
                echo -e "${YELLOW}⚠ Above target: ${p95}ms > 100ms${NC}"
            fi
        fi
    fi
}

# Main execution
case "${1:-progressive}" in
    progressive)
        run_progressive_test
        ;;
    stress)
        run_stress_test
        ;;
    quick)
        echo -e "${GREEN}Running Quick Test (1 minute)...${NC}"
        locust -f locustfile.py \
            --host="$API_HOST" \
            --users=100 \
            --spawn-rate=10 \
            --run-time=1m \
            --headless \
            --html="${REPORT_DIR}/quick_test.html" \
            --csv="${REPORT_DIR}/quick_test"
        ;;
    *)
        echo "Usage: $0 {progressive|stress|quick}"
        exit 1
        ;;
esac

# Analyze results
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Load Test Results Analysis${NC}"
echo -e "${GREEN}================================================${NC}"

# Find the most recent CSV file
LATEST_CSV=$(ls -t "${REPORT_DIR}"/*_stats.csv 2>/dev/null | head -n1 | sed 's/_stats.csv//')

if [ -n "$LATEST_CSV" ]; then
    calculate_throughput "$LATEST_CSV"
    check_response_time "$LATEST_CSV"
    
    echo ""
    echo "Detailed reports available in: $REPORT_DIR"
    echo "Open HTML report: firefox ${LATEST_CSV}.html"
else
    echo -e "${RED}No results found to analyze${NC}"
fi

# Performance recommendations based on results
echo ""
echo -e "${GREEN}Performance Optimization Recommendations:${NC}"
echo "1. Enable connection pooling if not already done"
echo "2. Implement query result caching for frequently accessed data"
echo "3. Use batch processing for bulk operations"
echo "4. Consider horizontal scaling if CPU > 80%"
echo "5. Optimize database indexes for slow queries"

echo ""
echo -e "${GREEN}Load test completed successfully!${NC}"

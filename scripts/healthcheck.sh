#!/bin/bash

# ============================================
# Health Check Script for Docker Services
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:5173}"
MYSQL_CONTAINER="${MYSQL_CONTAINER:-student-management-mysql}"
MAX_RETRIES=30
RETRY_INTERVAL=2

# Functions
print_status() {
    local service=$1
    local status=$2
    local message=$3
    
    if [ "$status" = "ok" ]; then
        echo -e "${GREEN}✓${NC} $service: $message"
    elif [ "$status" = "warning" ]; then
        echo -e "${YELLOW}⚠${NC} $service: $message"
    else
        echo -e "${RED}✗${NC} $service: $message"
    fi
}

check_mysql() {
    echo -e "${BLUE}Checking MySQL...${NC}"
    
    if docker exec $MYSQL_CONTAINER mysqladmin ping -h localhost -u root -p123456 --silent 2>/dev/null; then
        print_status "MySQL" "ok" "Database is responding"
        return 0
    else
        print_status "MySQL" "error" "Database is not responding"
        return 1
    fi
}

check_backend() {
    echo -e "${BLUE}Checking Backend API...${NC}"
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" $BACKEND_URL/ 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        print_status "Backend" "ok" "API is responding (HTTP $response)"
        return 0
    else
        print_status "Backend" "error" "API is not responding (HTTP $response)"
        return 1
    fi
}

check_frontend() {
    echo -e "${BLUE}Checking Frontend...${NC}"
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" $FRONTEND_URL/ 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        print_status "Frontend" "ok" "Frontend is responding (HTTP $response)"
        return 0
    else
        print_status "Frontend" "error" "Frontend is not responding (HTTP $response)"
        return 1
    fi
}

check_containers() {
    echo -e "${BLUE}Checking Docker Containers...${NC}"
    
    local containers=$(docker-compose ps --services --filter "status=running" 2>/dev/null)
    local total=$(docker-compose ps --services 2>/dev/null | wc -l)
    local running=$(echo "$containers" | wc -l)
    
    if [ "$running" -eq "$total" ]; then
        print_status "Containers" "ok" "All containers are running ($running/$total)"
        return 0
    else
        print_status "Containers" "warning" "Some containers are not running ($running/$total)"
        return 1
    fi
}

wait_for_services() {
    echo -e "${BLUE}Waiting for services to be ready...${NC}"
    
    local retries=0
    while [ $retries -lt $MAX_RETRIES ]; do
        if check_mysql && check_backend && check_frontend; then
            echo -e "${GREEN}All services are ready!${NC}"
            return 0
        fi
        
        retries=$((retries + 1))
        echo -e "${YELLOW}Retry $retries/$MAX_RETRIES...${NC}"
        sleep $RETRY_INTERVAL
    done
    
    echo -e "${RED}Services failed to start within timeout${NC}"
    return 1
}

# Main execution
main() {
    echo "============================================"
    echo "Student Management System - Health Check"
    echo "============================================"
    echo ""
    
    if [ "$1" = "--wait" ]; then
        wait_for_services
    else
        check_containers
        echo ""
        check_mysql
        echo ""
        check_backend
        echo ""
        check_frontend
        echo ""
        
        if check_mysql && check_backend && check_frontend; then
            echo -e "${GREEN}✓ All services are healthy${NC}"
            exit 0
        else
            echo -e "${RED}✗ Some services are unhealthy${NC}"
            exit 1
        fi
    fi
}

main "$@"

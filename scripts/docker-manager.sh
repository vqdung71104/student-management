#!/bin/bash

# ============================================
# Student Management System - Docker Manager
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Development commands
dev_start() {
    print_info "Starting development environment..."
    docker-compose --env-file .env.docker up -d
    print_success "Development environment started"
    print_info "Frontend: http://localhost:5173"
    print_info "Backend: http://localhost:8000"
    print_info "phpMyAdmin: http://localhost:8080 (use --profile tools)"
}

dev_stop() {
    print_info "Stopping development environment..."
    docker-compose down
    print_success "Development environment stopped"
}

dev_restart() {
    print_info "Restarting development environment..."
    docker-compose restart
    print_success "Development environment restarted"
}

dev_logs() {
    docker-compose logs -f "${@}"
}

dev_build() {
    print_info "Building development images..."
    docker-compose build --no-cache
    print_success "Development images built"
}

# Production commands
prod_start() {
    print_info "Starting production environment..."
    docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
    print_success "Production environment started"
    print_info "Application: http://localhost:80"
}

prod_stop() {
    print_info "Stopping production environment..."
    docker-compose -f docker-compose.prod.yml down
    print_success "Production environment stopped"
}

prod_build() {
    print_info "Building production images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    print_success "Production images built"
}

# Database commands
db_backup() {
    print_info "Creating database backup..."
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    docker exec student-management-mysql mysqldump -u root -p123456 student_management > "$BACKUP_FILE"
    print_success "Database backup created: $BACKUP_FILE"
}

db_restore() {
    if [ -z "$1" ]; then
        print_error "Please provide backup file path"
        exit 1
    fi
    print_info "Restoring database from $1..."
    docker exec -i student-management-mysql mysql -u root -p123456 student_management < "$1"
    print_success "Database restored"
}

db_shell() {
    print_info "Opening MySQL shell..."
    docker exec -it student-management-mysql mysql -u root -p123456 student_management
}

# Cleanup commands
cleanup() {
    print_warning "This will remove all containers, volumes, and images. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_info "Cleaning up..."
        docker-compose down -v
        docker system prune -af --volumes
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

# Health check
health_check() {
    print_info "Checking service health..."
    docker-compose ps
    echo ""
    print_info "Backend health:"
    curl -f http://localhost:8000/ || print_error "Backend is not healthy"
    echo ""
    print_info "Frontend health:"
    curl -f http://localhost:5173/ || print_error "Frontend is not healthy"
}

# Show usage
usage() {
    cat << EOF
Student Management System - Docker Manager

Usage: $0 [COMMAND]

Development Commands:
  dev:start       Start development environment
  dev:stop        Stop development environment
  dev:restart     Restart development environment
  dev:logs        Show logs (optional: service name)
  dev:build       Rebuild development images

Production Commands:
  prod:start      Start production environment
  prod:stop       Stop production environment
  prod:build      Build production images

Database Commands:
  db:backup       Create database backup
  db:restore      Restore database from backup file
  db:shell        Open MySQL shell

Utility Commands:
  health          Check service health
  cleanup         Remove all containers, volumes, and images
  help            Show this help message

Examples:
  $0 dev:start
  $0 dev:logs backend
  $0 db:backup
  $0 db:restore backup_20260209.sql

EOF
}

# Main script
main() {
    check_docker

    case "${1}" in
        dev:start)
            dev_start
            ;;
        dev:stop)
            dev_stop
            ;;
        dev:restart)
            dev_restart
            ;;
        dev:logs)
            shift
            dev_logs "$@"
            ;;
        dev:build)
            dev_build
            ;;
        prod:start)
            prod_start
            ;;
        prod:stop)
            prod_stop
            ;;
        prod:build)
            prod_build
            ;;
        db:backup)
            db_backup
            ;;
        db:restore)
            db_restore "$2"
            ;;
        db:shell)
            db_shell
            ;;
        health)
            health_check
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h|"")
            usage
            ;;
        *)
            print_error "Unknown command: $1"
            usage
            exit 1
            ;;
    esac
}

main "$@"

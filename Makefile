# ============================================
# Student Management System - Makefile
# ============================================

.PHONY: help dev-start dev-stop dev-restart dev-logs dev-build prod-start prod-stop prod-build db-backup db-restore db-shell health cleanup

# Default target
.DEFAULT_GOAL := help

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Variables
COMPOSE_DEV := docker-compose --env-file .env.docker
COMPOSE_PROD := docker-compose -f docker-compose.prod.yml --env-file .env.production
BACKUP_DIR := backups
TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)

## help: Show this help message
help:
	@echo "$(BLUE)Student Management System - Docker Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Development Commands:$(NC)"
	@echo "  make dev-start       - Start development environment"
	@echo "  make dev-stop        - Stop development environment"
	@echo "  make dev-restart     - Restart development environment"
	@echo "  make dev-logs        - Show development logs"
	@echo "  make dev-build       - Rebuild development images"
	@echo ""
	@echo "$(GREEN)Production Commands:$(NC)"
	@echo "  make prod-start      - Start production environment"
	@echo "  make prod-stop       - Stop production environment"
	@echo "  make prod-build      - Build production images"
	@echo ""
	@echo "$(GREEN)Database Commands:$(NC)"
	@echo "  make db-backup       - Create database backup"
	@echo "  make db-restore FILE=<file> - Restore database from backup"
	@echo "  make db-shell        - Open MySQL shell"
	@echo ""
	@echo "$(GREEN)Utility Commands:$(NC)"
	@echo "  make health          - Check service health"
	@echo "  make cleanup         - Remove all containers and volumes"
	@echo "  make help            - Show this help message"

## dev-start: Start development environment
dev-start:
	@echo "$(BLUE)[INFO]$(NC) Starting development environment..."
	@$(COMPOSE_DEV) up -d
	@echo "$(GREEN)[SUCCESS]$(NC) Development environment started"
	@echo "$(BLUE)[INFO]$(NC) Frontend: http://localhost:5173"
	@echo "$(BLUE)[INFO]$(NC) Backend: http://localhost:8000"
	@echo "$(BLUE)[INFO]$(NC) phpMyAdmin: http://localhost:8080"

## dev-stop: Stop development environment
dev-stop:
	@echo "$(BLUE)[INFO]$(NC) Stopping development environment..."
	@$(COMPOSE_DEV) down
	@echo "$(GREEN)[SUCCESS]$(NC) Development environment stopped"

## dev-restart: Restart development environment
dev-restart:
	@echo "$(BLUE)[INFO]$(NC) Restarting development environment..."
	@$(COMPOSE_DEV) restart
	@echo "$(GREEN)[SUCCESS]$(NC) Development environment restarted"

## dev-logs: Show development logs
dev-logs:
	@$(COMPOSE_DEV) logs -f

## dev-build: Rebuild development images
dev-build:
	@echo "$(BLUE)[INFO]$(NC) Building development images..."
	@$(COMPOSE_DEV) build --no-cache
	@echo "$(GREEN)[SUCCESS]$(NC) Development images built"

## prod-start: Start production environment
prod-start:
	@echo "$(BLUE)[INFO]$(NC) Starting production environment..."
	@$(COMPOSE_PROD) up -d
	@echo "$(GREEN)[SUCCESS]$(NC) Production environment started"
	@echo "$(BLUE)[INFO]$(NC) Application: http://localhost:80"

## prod-stop: Stop production environment
prod-stop:
	@echo "$(BLUE)[INFO]$(NC) Stopping production environment..."
	@$(COMPOSE_PROD) down
	@echo "$(GREEN)[SUCCESS]$(NC) Production environment stopped"

## prod-build: Build production images
prod-build:
	@echo "$(BLUE)[INFO]$(NC) Building production images..."
	@$(COMPOSE_PROD) build --no-cache
	@echo "$(GREEN)[SUCCESS]$(NC) Production images built"

## db-backup: Create database backup
db-backup:
	@echo "$(BLUE)[INFO]$(NC) Creating database backup..."
	@mkdir -p $(BACKUP_DIR)
	@docker exec student-management-mysql mysqldump -u root -p123456 student_management > $(BACKUP_DIR)/backup_$(TIMESTAMP).sql
	@echo "$(GREEN)[SUCCESS]$(NC) Database backup created: $(BACKUP_DIR)/backup_$(TIMESTAMP).sql"

## db-restore: Restore database from backup
db-restore:
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)[ERROR]$(NC) Please provide backup file: make db-restore FILE=backup.sql"; \
		exit 1; \
	fi
	@echo "$(BLUE)[INFO]$(NC) Restoring database from $(FILE)..."
	@docker exec -i student-management-mysql mysql -u root -p123456 student_management < $(FILE)
	@echo "$(GREEN)[SUCCESS]$(NC) Database restored"

## db-shell: Open MySQL shell
db-shell:
	@echo "$(BLUE)[INFO]$(NC) Opening MySQL shell..."
	@docker exec -it student-management-mysql mysql -u root -p123456 student_management

## health: Check service health
health:
	@echo "$(BLUE)[INFO]$(NC) Checking service health..."
	@$(COMPOSE_DEV) ps
	@echo ""
	@echo "$(BLUE)[INFO]$(NC) Backend health:"
	@curl -f http://localhost:8000/ || echo "$(RED)[ERROR]$(NC) Backend is not healthy"
	@echo ""
	@echo "$(BLUE)[INFO]$(NC) Frontend health:"
	@curl -f http://localhost:5173/ || echo "$(RED)[ERROR]$(NC) Frontend is not healthy"

## cleanup: Remove all containers and volumes
cleanup:
	@echo "$(YELLOW)[WARNING]$(NC) This will remove all containers, volumes, and images."
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "$(BLUE)[INFO]$(NC) Cleaning up..."; \
		$(COMPOSE_DEV) down -v; \
		docker system prune -af --volumes; \
		echo "$(GREEN)[SUCCESS]$(NC) Cleanup completed"; \
	else \
		echo "$(BLUE)[INFO]$(NC) Cleanup cancelled"; \
	fi

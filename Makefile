# Enhanced Makefile for EMO Options Bot
# Supports environment-based configuration and deployment

# Configuration
PYTHON := python
PIP := $(PYTHON) -m pip
VENV_DIR := .venv
PROJECT_ROOT := $(shell pwd)

# Environment detection
EMO_ENV ?= dev
ENV_FILE := .env
ifneq ($(wildcard .env.$(EMO_ENV)),)
    ENV_FILE := .env.$(EMO_ENV)
endif

# Platform detection
ifeq ($(OS),Windows_NT)
    SHELL := powershell.exe
    .SHELLFLAGS := -NoProfile -Command
    VENV_PYTHON := $(VENV_DIR)/Scripts/python.exe
    VENV_ACTIVATE := & "$(VENV_DIR)/Scripts/Activate.ps1"
    RM := Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    MKDIR := New-Item -ItemType Directory -Force
else
    VENV_PYTHON := $(VENV_DIR)/bin/python
    VENV_ACTIVATE := . $(VENV_DIR)/bin/activate
    RM := rm -rf
    MKDIR := mkdir -p
endif

# Color output
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
NC := \033[0m

.PHONY: help venv install install-ml install-dev install-voice install-all clean
.PHONY: dev staging prod
.PHONY: test test-enhanced demo-enhanced test-voice validate-system lint format security
.PHONY: migrate run dashboard health
.PHONY: docker-build docker-run deploy
.PHONY: bump-patch bump-minor bump-major safe-tag patch minor major

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "$(CYAN)EMO Options Bot - Enhanced Build System$(NC)"
	@echo "$(YELLOW)Environment: $(EMO_ENV) (using $(ENV_FILE))$(NC)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ============================================================================
# Environment Setup
# ============================================================================

venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
ifeq ($(OS),Windows_NT)
	@if (!(Test-Path "$(VENV_DIR)")) { $(PYTHON) -m venv $(VENV_DIR) }
else
	@test -d $(VENV_DIR) || $(PYTHON) -m venv $(VENV_DIR)
endif
	@echo "$(GREEN)Virtual environment ready$(NC)"

install: venv ## Install core dependencies
	@echo "$(BLUE)Installing core dependencies...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); $(PIP) install --upgrade pip
	@$(VENV_ACTIVATE); $(PIP) install -r requirements.txt
else
	@$(VENV_ACTIVATE) && $(PIP) install --upgrade pip
	@$(VENV_ACTIVATE) && $(PIP) install -r requirements.txt
endif
	@echo "$(GREEN)Core dependencies installed$(NC)"

install-ml: install ## Install ML/AI dependencies
	@echo "$(BLUE)Installing ML dependencies...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); $(PIP) install -r requirements-ml.txt
else
	@$(VENV_ACTIVATE) && $(PIP) install -r requirements-ml.txt
endif
	@echo "$(GREEN)ML dependencies installed$(NC)"

install-dev: install ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); $(PIP) install -r requirements-dev.txt
else
	@$(VENV_ACTIVATE) && $(PIP) install -r requirements-dev.txt
endif
	@echo "$(GREEN)Development dependencies installed$(NC)"

install-voice: venv ## Install voice interface dependencies
	@echo "$(BLUE)Installing voice interface dependencies...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); $(PIP) install -r requirements-voice.txt
else
	@$(VENV_ACTIVATE) && $(PIP) install -r requirements-voice.txt
endif
	@echo "$(GREEN)Voice dependencies installed$(NC)"

install-all: install install-ml install-dev install-voice ## Install all dependencies (core + ML + dev + voice)
	@echo "$(GREEN)All dependencies installed successfully$(NC)"

# ============================================================================
# Enhanced Component Testing
# ============================================================================

test-enhanced: ## Run enhanced component test suite
	@echo "$(BLUE)Running enhanced component tests...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); python scripts/test_enhanced_components.py
else
	@$(VENV_ACTIVATE) && python scripts/test_enhanced_components.py
endif

demo-enhanced: ## Demo enhanced orchestrator capabilities
	@echo "$(BLUE)Running enhanced orchestrator demo...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); python scripts/demo_enhanced_orchestrator.py
else
	@$(VENV_ACTIVATE) && python scripts/demo_enhanced_orchestrator.py
endif

test-voice: ## Test voice interface capabilities
	@echo "$(BLUE)Testing voice interface...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); python -c "from src.voice.asr_tts import test_voice_capabilities; print(test_voice_capabilities())"
else
	@$(VENV_ACTIVATE) && python -c "from src.voice.asr_tts import test_voice_capabilities; print(test_voice_capabilities())"
endif

validate-system: test-enhanced demo-enhanced ## Validate complete enhanced system
	@echo "$(GREEN)System validation complete!$(NC)"

# ============================================================================
# Environment-Specific Setup
# ============================================================================

dev: ## Setup development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@EMO_ENV=dev $(MAKE) install
	@EMO_ENV=dev $(MAKE) migrate
	@echo "$(GREEN)Development environment ready$(NC)"

staging: ## Setup staging environment  
	@echo "$(BLUE)Setting up staging environment...$(NC)"
	@EMO_ENV=staging $(MAKE) install
	@EMO_ENV=staging $(MAKE) install-ml
	@EMO_ENV=staging $(MAKE) migrate
	@echo "$(GREEN)Staging environment ready$(NC)"

prod: ## Setup production environment
	@echo "$(BLUE)Setting up production environment...$(NC)"
	@EMO_ENV=prod $(MAKE) install
	@EMO_ENV=prod $(MAKE) install-ml
	@EMO_ENV=prod $(MAKE) migrate
	@echo "$(GREEN)Production environment ready$(NC)"

# ============================================================================
# Database Management
# ============================================================================

migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); if (Test-Path "alembic.ini") { alembic upgrade head } else { Write-Host "No alembic.ini found, skipping migrations" }
else
	@$(VENV_ACTIVATE) && if [ -f alembic.ini ]; then alembic upgrade head; else echo "No alembic.ini found, skipping migrations"; fi
endif
	@echo "$(GREEN)Database migrations complete$(NC)"

# ============================================================================
# Testing and Quality
# ============================================================================

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); pytest -v
else
	@$(VENV_ACTIVATE) && pytest -v
endif

release-check: ## Run Phase 3 release readiness check
	@echo "$(BLUE)Running Phase 3 release check...$(NC)"
ifeq ($(OS),Windows_NT)
	@powershell.exe -ExecutionPolicy Bypass -File "run_release_check.ps1"
else
	@chmod +x run_release_check.sh && ./run_release_check.sh
endif

release-check-verbose: ## Run Phase 3 release check with verbose output
	@echo "$(BLUE)Running Phase 3 release check (verbose)...$(NC)"
ifeq ($(OS),Windows_NT)
	@powershell.exe -ExecutionPolicy Bypass -File "run_release_check.ps1" -Verbose
else
	@chmod +x run_release_check.sh && ./run_release_check.sh --verbose
endif

validate-phase3: release-check ## Validate Phase 3 production readiness
	@echo "$(GREEN)Phase 3 validation complete!$(NC)"

lint: ## Run code linting
	@echo "$(BLUE)Running linter...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); flake8 src/ scripts/ --max-line-length=100
else
	@$(VENV_ACTIVATE) && flake8 src/ scripts/ --max-line-length=100
endif

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); black src/ scripts/ --line-length=100
	@$(VENV_ACTIVATE); isort src/ scripts/
else
	@$(VENV_ACTIVATE) && black src/ scripts/ --line-length=100
	@$(VENV_ACTIVATE) && isort src/ scripts/
endif

security: ## Run security scan
	@echo "$(BLUE)Running security scan...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); bandit -r src/ scripts/
else
	@$(VENV_ACTIVATE) && bandit -r src/ scripts/
endif

# ============================================================================
# Application Control
# ============================================================================

run: ## Run the main application
	@echo "$(BLUE)Starting EMO Options Bot...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); if (Test-Path "main.py") { python main.py } else { Write-Host "No main.py found" -ForegroundColor Red }
else
	@$(VENV_ACTIVATE) && if [ -f main.py ]; then python main.py; else echo "$(RED)No main.py found$(NC)"; fi
endif

dashboard: ## Start dashboard server
	@echo "$(BLUE)Starting dashboard...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); python dashboard/enhanced_dashboard.py --mode serve
else
	@$(VENV_ACTIVATE) && python dashboard/enhanced_dashboard.py --mode serve
endif

health: ## Start health service
	@echo "$(BLUE)Starting health service...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); python scripts/services/health_service.py
else
	@$(VENV_ACTIVATE) && python scripts/services/health_service.py
endif

# ============================================================================
# Deployment and Docker
# ============================================================================

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	@docker build -t emo-options-bot:$(EMO_ENV) .

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	@docker run -it --rm -p 8083:8083 --env-file $(ENV_FILE) emo-options-bot:$(EMO_ENV)

deploy: ## Deploy to production (requires setup)
	@echo "$(BLUE)Deploying to production...$(NC)"
	@echo "$(YELLOW)This target should be customized for your deployment method$(NC)"

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Clean up build artifacts
	@echo "$(YELLOW)Cleaning up...$(NC)"
ifeq ($(OS),Windows_NT)
	@if (Test-Path "$(VENV_DIR)") { $(RM) "$(VENV_DIR)" }
	@Get-ChildItem -Path . -Recurse -Name "__pycache__" | ForEach-Object { $(RM) $_ } 2>$$null || $$true
	@Get-ChildItem -Path . -Recurse -Name "*.pyc" | ForEach-Object { $(RM) $_ } 2>$$null || $$true
else
	@$(RM) $(VENV_DIR) 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec $(RM) {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
endif
	@echo "$(GREEN)Cleanup complete$(NC)"

# ============================================================================
# Version Management
# ============================================================================

bump-patch: ## Bump patch version and create git tag
	@echo "$(BLUE)Bumping patch version...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); python tools/git_tag_helper.py --bump patch
else
	@$(VENV_ACTIVATE) && python tools/git_tag_helper.py --bump patch
endif

bump-minor: ## Bump minor version and create git tag
	@echo "$(BLUE)Bumping minor version...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); python tools/git_tag_helper.py --bump minor
else
	@$(VENV_ACTIVATE) && python tools/git_tag_helper.py --bump minor
endif

bump-major: ## Bump major version and create git tag
	@echo "$(BLUE)Bumping major version...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); python tools/git_tag_helper.py --bump major
else
	@$(VENV_ACTIVATE) && python tools/git_tag_helper.py --bump major
endif

# Enhanced safe tagging with release gates
safe-tag: ## Safe tagging with release-check gate and dry-run option
	@echo "$(BLUE)Safe tagging with release gate...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); python tools/git_tag_helper.py
else
	@$(VENV_ACTIVATE) && python tools/git_tag_helper.py
endif

# Shortcut aliases for common workflows
patch: safe-tag ## Alias for safe-tag (default patch bump)

minor: ## Safe minor version bump with release gate
	@echo "$(BLUE)Safe minor version bump...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); python tools/git_tag_helper.py --bump minor
else
	@$(VENV_ACTIVATE) && python tools/git_tag_helper.py --bump minor
endif

major: ## Safe major version bump with release gate
	@echo "$(BLUE)Safe major version bump...$(NC)"
ifeq ($(OS),Windows_NT)
	@$(VENV_ACTIVATE); python tools/git_tag_helper.py --bump major
else
	@$(VENV_ACTIVATE) && python tools/git_tag_helper.py --bump major
endif
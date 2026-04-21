.PHONY: help venv install install-dev lint lint-unit-tests lint-integration-tests test-unit test-integration test-unit-coverage build check-dist upload-pypi clean check start

# Liquisketch — Python package under ./liquisketch/

PYTHON := python3
VENV := .venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTHON_VENV := $(VENV_BIN)/python
PYLINT := $(VENV_BIN)/pylint
PYTEST := $(VENV_BIN)/pytest
# Exit 0 when global score meets threshold (see pylint --fail-under).
PYLINTFLAGS_SRC := --fail-under=9
# Tests use many short functions without docstrings; threshold is looser.
PYLINTFLAGS_TESTS := --fail-under=8

SRC_DIR := liquisketch
TEST_DIR := tests
UNIT_TEST_DIR := $(TEST_DIR)/unit
INTEGRATION_TEST_DIR := $(TEST_DIR)/integration
BUILD_DIR := dist
REPORTS_DIR := reports

# Editable install supplies the package to pytest/pylint without extra PYTHONPATH.
export PYTHONPATH := .

# Pylint stats/cache (avoids writes under ~/.cache and keeps CI local).
export PYLINTHOME := $(CURDIR)/.pylint.d

help:
	@echo "Available targets:"
	@echo "  make venv                    - Create virtual environment ($(VENV)/)"
	@echo "  make install                 - Install project dependencies (editable)"
	@echo "  make install-dev             - Install project with optional dev dependencies"
	@echo "  make lint                    - Run pylint on $(SRC_DIR)/"
	@echo "  make lint-unit-tests         - Run pylint on $(UNIT_TEST_DIR)/"
	@echo "  make lint-integration-tests  - Run pylint on $(INTEGRATION_TEST_DIR)/ (if present)"
	@echo "  make test-unit               - Run unit tests (pytest, $(UNIT_TEST_DIR)/)"
	@echo "  make test-integration        - Run integration tests (pytest, $(INTEGRATION_TEST_DIR)/)"
	@echo "  make test-unit-coverage      - Unit tests with coverage (terminal + htmlcov/)"
	@echo "  make build                   - Build sdist and wheel in $(BUILD_DIR)/"
	@echo "  make check-dist              - Run twine check on $(BUILD_DIR)/* (after build)"
	@echo "  make upload-pypi             - twine upload $(BUILD_DIR)/* (set TWINE_*, see help)"
	@echo "  make clean                   - Remove caches, build artifacts, coverage reports"
	@echo "  make check                   - Run all lints plus unit and integration tests"
	@echo "  make start                   - Show liquisketch CLI --help (smoke check)"

venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
		echo "Virtual environment created. Activate with: source $(VENV_BIN)/activate"; \
	else \
		echo "Virtual environment already exists."; \
	fi

install: venv
	@echo "Installing project (editable)..."
	@$(PIP) install --upgrade pip
	@$(PIP) install -e .

install-dev: venv
	@echo "Installing project with dev dependencies (editable)..."
	@$(PIP) install --upgrade pip
	@$(PIP) install -e ".[dev]"

lint:
	@echo "Running pylint on $(SRC_DIR)/..."
	@test -d "$(VENV)" || (echo "Run 'make venv' first."; exit 1)
	@$(PYLINT) $(PYLINTFLAGS_SRC) "$(SRC_DIR)/"

lint-unit-tests:
	@echo "Running pylint on $(UNIT_TEST_DIR)/..."
	@test -d "$(VENV)" || (echo "Run 'make venv' first."; exit 1)
	@$(PYLINT) $(PYLINTFLAGS_TESTS) "$(UNIT_TEST_DIR)/"

lint-integration-tests:
	@echo "Running pylint on integration tests..."
	@test -d "$(VENV)" || (echo "Run 'make venv' first."; exit 1)
	@if [ -d "$(INTEGRATION_TEST_DIR)" ] && [ -n "$$(find $(INTEGRATION_TEST_DIR) -name 'test_*.py' 2>/dev/null | head -1)" ]; then \
		$(PYLINT) $(PYLINTFLAGS_TESTS) "$(INTEGRATION_TEST_DIR)/"; \
	else \
		echo "No integration tests found under $(INTEGRATION_TEST_DIR)."; \
	fi

test-unit:
	@echo "Running unit tests..."
	@test -d "$(VENV)" || (echo "Run 'make venv' first."; exit 1)
	@$(PYTEST) "$(UNIT_TEST_DIR)" -v

test-integration:
	@echo "Running integration tests..."
	@test -d "$(VENV)" || (echo "Run 'make venv' first."; exit 1)
	@if [ -d "$(INTEGRATION_TEST_DIR)" ] && [ -n "$$(find $(INTEGRATION_TEST_DIR) -name 'test_*.py' 2>/dev/null | head -1)" ]; then \
		$(PYTEST) "$(INTEGRATION_TEST_DIR)" -v; \
	else \
		echo "No integration tests found under $(INTEGRATION_TEST_DIR)."; \
	fi

test-unit-coverage:
	@echo "Running unit tests with coverage ($(SRC_DIR)/)..."
	@test -d "$(VENV)" || (echo "Run 'make venv' first."; exit 1)
	@mkdir -p "$(REPORTS_DIR)"
	@$(PYTEST) "$(UNIT_TEST_DIR)" \
		--cov="$(SRC_DIR)" \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=xml:"$(REPORTS_DIR)/coverage.xml" \
		-v
	@echo ""
	@echo "Coverage HTML: htmlcov/index.html"
	@echo "Coverage XML:  $(REPORTS_DIR)/coverage.xml"

build:
	@echo "Building sdist and wheel..."
	@test -d "$(VENV)" || (echo "Run 'make venv' first."; exit 1)
	@rm -rf $(BUILD_DIR) && mkdir -p $(BUILD_DIR)
	@$(PYTHON_VENV) -m build --outdir $(BUILD_DIR)
	@echo "Artifacts in $(BUILD_DIR)/:"
	@ls -la $(BUILD_DIR)

check-dist:
	@echo "Validating distributions with twine check..."
	@test -d "$(VENV)" || (echo "Run 'make venv' first."; exit 1)
	@files=$$(find "$(BUILD_DIR)" -maxdepth 1 -type f \( -name '*.whl' -o -name '*.tar.gz' \) | sort); \
	if [ -z "$$files" ]; then echo "No distributions in $(BUILD_DIR)/; run make build first."; exit 1; fi; \
	$(PYTHON_VENV) -m twine check --strict $$files

# Upload wheels/sdists in $(BUILD_DIR)/. Uses the same dist/ layout as make build.
# Environment (twine): TWINE_USERNAME, TWINE_PASSWORD, optional TWINE_REPOSITORY_URL
# (e.g. https://upload.pypi.org/legacy/ or https://test.pypi.org/legacy/), optional
# TWINE_NON_INTERACTIVE (defaults to 1 in the recipe for non-interactive uploads).
upload-pypi:
	@echo "Uploading distributions from $(BUILD_DIR)/ with twine..."
	@test -d "$(VENV)" || (echo "Run 'make venv' (and install-dev) first."; exit 1)
	@export TWINE_NON_INTERACTIVE=$${TWINE_NON_INTERACTIVE:-1}; \
	files=$$(find "$(BUILD_DIR)" -maxdepth 1 -type f \( -name '*.whl' -o -name '*.tar.gz' \) | sort); \
	if [ -z "$$files" ]; then echo "No distributions in $(BUILD_DIR)/; add artifacts or run make build."; exit 1; fi; \
	if [ -n "$$TWINE_REPOSITORY_URL" ]; then \
		$(PYTHON_VENV) -m twine upload --repository-url "$$TWINE_REPOSITORY_URL" $$files; \
	else \
		$(PYTHON_VENV) -m twine upload $$files; \
	fi

clean:
	@echo "Cleaning generated files..."
	@find . \( -path "./$(VENV)" -o -path "./.git" \) -prune -o -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . \( -path "./$(VENV)" -o -path "./.git" \) -prune -o -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	@rm -rf $(BUILD_DIR) $(REPORTS_DIR) .pylint.d
	@echo "Clean completed."

check: lint lint-unit-tests lint-integration-tests test-unit test-integration
	@echo "Check completed."

start:
	@echo "liquisketch CLI (smoke check):"
	@test -d "$(VENV)" || (echo "Run 'make venv' first."; exit 1)
	@$(PYTHON_VENV) -m liquisketch --help

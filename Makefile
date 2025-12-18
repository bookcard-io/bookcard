.PHONY: dev setup-uv kill-ports format formatjs formatpy test testjs testpy test-changed docs-build docs-serve docs-deploy

setup-uv:
	@if command -v uv >/dev/null 2>&1; then \
		echo "uv is already installed."; \
	else \
		echo "uv is not installed."; \
		UNAME_S=$$(uname -s 2>/dev/null || echo "Unknown"); \
		case "$$UNAME_S" in \
			Linux|Darwin) \
				echo "Would you like to install uv? (y/n)"; \
				read -r answer; \
				if [ "$$answer" = "y" ] || [ "$$answer" = "Y" ]; then \
					echo "Installing uv..."; \
					curl -LsSf https://astral.sh/uv/install.sh | sh; \
					echo "uv installed successfully."; \
					if [ -f "$$HOME/.cargo/env" ]; then \
						. "$$HOME/.cargo/env"; \
					fi; \
					if [ -f "$$HOME/.local/bin/uv" ]; then \
						export PATH="$$HOME/.local/bin:$$PATH"; \
					fi; \
				else \
					echo "Installation cancelled. Please install uv manually to continue."; \
					exit 1; \
				fi; \
				;; \
			MINGW*|MSYS*|CYGWIN*) \
				if command -v powershell >/dev/null 2>&1; then \
					echo "Would you like to install uv? (y/n)"; \
					read -r answer; \
					if [ "$$answer" = "y" ] || [ "$$answer" = "Y" ]; then \
						echo "Installing uv..."; \
						powershell -c "irm https://astral.sh/uv/install.ps1 | iex"; \
						echo "uv installed successfully."; \
					else \
						echo "Installation cancelled. Please install uv manually to continue."; \
						exit 1; \
					fi; \
				else \
					echo "Error: Windows detected but PowerShell is not available."; \
					echo "Please run this Makefile from PowerShell or Git Bash, or install uv manually."; \
					echo "To install manually, run: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""; \
					exit 1; \
				fi; \
				;; \
			*) \
				if [ "$$OS" = "Windows_NT" ] || [ -n "$$WINDIR" ]; then \
					if command -v powershell >/dev/null 2>&1; then \
						echo "Would you like to install uv? (y/n)"; \
						read -r answer; \
						if [ "$$answer" = "y" ] || [ "$$answer" = "Y" ]; then \
							echo "Installing uv..."; \
							powershell -c "irm https://astral.sh/uv/install.ps1 | iex"; \
							echo "uv installed successfully."; \
						else \
							echo "Installation cancelled. Please install uv manually to continue."; \
							exit 1; \
						fi; \
					else \
						echo "Error: Windows detected but PowerShell is not available."; \
						echo "Please run this Makefile from PowerShell or Git Bash, or install uv manually."; \
						echo "To install manually, run: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""; \
						exit 1; \
					fi; \
				else \
					echo "Unsupported operating system: $$UNAME_S"; \
					echo "Please install uv manually."; \
					exit 1; \
				fi; \
				;; \
		esac; \
		if [ ! -d .venv ]; then \
			echo "Creating virtual environment..."; \
			uv venv; \
		fi; \
		echo "Syncing dependencies..."; \
		uv sync; \
	fi

dev: setup-uv
	@echo "Starting Python API server and Next.js dev server..."; \
	set -a; \
	if [ -f .env ]; then \
		echo "Loading environment from .env file..."; \
		. ./.env; \
	fi; \
	set +a; \
	uv run uvicorn bookcard.api.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude tests --reload-exclude web --reload-exclude "**/test_*.py" --reload-exclude "**/*_test.py" & \
	PID1=$$!; \
	cd web && npm run dev & \
	PID2=$$!; \
	trap "echo 'Stopping servers...'; kill $$PID1 $$PID2 2>/dev/null; wait $$PID1 $$PID2" INT TERM; \
	echo "Python API: http://localhost:8000 (PID: $$PID1)"; \
	echo "Next.js: http://localhost:3000 (PID: $$PID2)"; \
	echo "Press Ctrl+C to stop both servers."; \
	wait $$PID1 $$PID2 || true

kill-ports:
	@echo "Killing processes on ports 3000 and 8000..."; \
	for port in 3000 8000; do \
		PIDS=$$(lsof -ti:$$port 2>/dev/null || true); \
		if [ -n "$$PIDS" ]; then \
			echo "Killing processes on port $$port: $$PIDS"; \
			for pid in $$PIDS; do \
				kill -9 $$pid 2>/dev/null || true; \
			done; \
		else \
			echo "No processes found on port $$port"; \
		fi; \
	done; \
	echo "Done."

format:
	@echo "Running format checks and fixes..."; \
	cd $(CURDIR) && uv run --frozen ruff check --fix; \
	cd $(CURDIR) && uv run --frozen ruff format; \
	cd $(CURDIR) && uv run --frozen ty check; \
	cd $(CURDIR)/web && npm run lint:fix -- --unsafe; \
	cd $(CURDIR)/web && npm run check:types

formatjs:
	@echo "Running JavaScript/TypeScript format checks and fixes..."; \
	cd $(CURDIR)/web && npm run lint:fix -- --unsafe; \
	cd $(CURDIR)/web && npm run check:types

formatpy:
	@echo "Running Python format checks and fixes..."; \
	cd $(CURDIR) && uv run --frozen ruff check --fix; \
	cd $(CURDIR) && uv run --frozen ruff format; \
	cd $(CURDIR) && uv run --frozen ty check

test:
	@echo "Running tests with coverage..."; \
	cd $(CURDIR) && uv run --frozen pytest --cov=bookcard --cov-report=term-missing -n auto; \
	cd $(CURDIR)/web && npm run test:coverage

testjs:
	@echo "Running JavaScript/TypeScript tests with coverage..."; \
	cd $(CURDIR)/web && npm run test:coverage

testpy:
	@echo "Running Python tests with coverage..."; \
	cd $(CURDIR) && uv run --frozen pytest --cov=bookcard --cov-report=term-missing -n auto

test-changed:
	@echo "Finding changed test files..."; \
	CHANGED_FILES=$$({ \
		git diff --name-only --cached --diff-filter=ACMR 2>/dev/null; \
		git diff --name-only --diff-filter=ACMR 2>/dev/null; \
	} | grep -E '(tests/.*test_.*\.py|web/.*\.test\.(ts|tsx))' | sort -u || true); \
	PYTHON_TESTS=$$(echo "$$CHANGED_FILES" | grep -E '^tests/.*test_.*\.py$$' || true); \
	JS_TESTS=$$(echo "$$CHANGED_FILES" | grep -E '^web/.*\.test\.(ts|tsx)$$' || true); \
	if [ -n "$$PYTHON_TESTS" ]; then \
		echo "Running pytest on changed Python test files:"; \
		echo "$$PYTHON_TESTS" | sed 's/^/  - /'; \
		cd $(CURDIR) && uv run --frozen pytest $$(echo "$$PYTHON_TESTS" | tr '\n' ' '); \
	else \
		echo "No changed Python test files found."; \
	fi; \
	if [ -n "$$JS_TESTS" ]; then \
		echo "Running npm test on changed JavaScript/TypeScript test files:"; \
		echo "$$JS_TESTS" | sed 's|^web/||' | sed 's/^/  - /'; \
		cd $(CURDIR)/web && npm run test -- $$(echo "$$JS_TESTS" | sed 's|^web/||' | tr '\n' ' '); \
	else \
		echo "No changed JavaScript/TypeScript test files found."; \
	fi; \
	if [ -z "$$PYTHON_TESTS" ] && [ -z "$$JS_TESTS" ]; then \
		echo "No changed test files found."; \
	fi

docs-build:
	@echo "Building documentation..."; \
	cd $(CURDIR) && uv run --frozen python scripts/build_docs.py

docs-serve:
	@echo "Serving documentation at http://127.0.0.1:8001"; \
	cd $(CURDIR) && uv run --frozen python scripts/build_docs.py serve

docs-deploy:
	@echo "Deploying documentation with versioning..."; \
	if [ -z "$$VERSION" ]; then \
		echo "Error: VERSION environment variable is required."; \
		echo "Usage: VERSION=0.1.0 make docs-deploy"; \
		exit 1; \
	fi; \
	cd $(CURDIR) && uv run --frozen python scripts/generate_openapi.py; \
	cd $(CURDIR) && uv run --frozen mike deploy $$VERSION latest; \
	cd $(CURDIR) && uv run --frozen mike set-default latest; \
	echo "Documentation deployed for version $$VERSION"

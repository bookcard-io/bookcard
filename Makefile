.PHONY: dev setup-uv kill-ports

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
	uv run uvicorn fundamental.api.main:app --host 0.0.0.0 --port 8000 --reload & \
	PID1=$$!; \
	cd web && npm run dev & \
	PID2=$$!; \
	trap "echo 'Stopping servers...'; kill $$PID1 $$PID2 2>/dev/null; exit" INT TERM; \
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

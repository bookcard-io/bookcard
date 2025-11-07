.PHONY: dev

dev:
	@echo "Checking database connectivity at localhost:5432..."
	@MAX_RETRIES=30; \
	RETRY_COUNT=0; \
	while [ $$RETRY_COUNT -lt $$MAX_RETRIES ]; do \
		if command -v pg_isready >/dev/null 2>&1; then \
			if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then \
				echo "Database is ready!"; \
				break; \
			fi; \
		elif command -v nc >/dev/null 2>&1; then \
			if nc -z localhost 5432 >/dev/null 2>&1; then \
				echo "Database port 5432 is open!"; \
				break; \
			fi; \
		elif python3 -c "import socket; socket.create_connection(('localhost', 5432), timeout=1)" 2>/dev/null; then \
			echo "Database port 5432 is reachable!"; \
			break; \
		fi; \
		RETRY_COUNT=$$((RETRY_COUNT + 1)); \
		if [ $$RETRY_COUNT -ge $$MAX_RETRIES ]; then \
			echo "Warning: Database not reachable at localhost:5432 after $$MAX_RETRIES attempts."; \
			echo "Make sure the database is running (e.g., docker-compose up -d db)"; \
			exit 1; \
		fi; \
		echo "Waiting for database... (attempt $$RETRY_COUNT/$$MAX_RETRIES)"; \
		sleep 1; \
	done; \
	echo "Starting Python API server and Next.js dev server..."; \
	set -a; \
	if [ -f .env ]; then \
		echo "Loading environment from .env file..."; \
		. ./.env; \
	fi; \
	set +a; \
	uvicorn fundamental.api.main:app --host 0.0.0.0 --port 8000 --reload & \
	PID1=$$!; \
	cd web && npm run dev & \
	PID2=$$!; \
	trap "echo 'Stopping servers...'; kill $$PID1 $$PID2 2>/dev/null; exit" INT TERM; \
	echo "Python API: http://localhost:8000 (PID: $$PID1)"; \
	echo "Next.js: http://localhost:3000 (PID: $$PID2)"; \
	echo "Press Ctrl+C to stop both servers."; \
	wait $$PID1 $$PID2 || true

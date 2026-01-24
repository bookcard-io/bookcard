# Development Setup

## Prerequisites

- Python 3.12+
- Node.js 22+ (compatible with 22.x, see `.nvmrc` / `.node-version`)
- Docker and Docker Compose (optional)
- uv (Python package manager)

## Initial Setup

1. **Clone the repository**

    ```bash
    git clone https://github.com/bookcard-io/bookcard.git
    cd bookcard
    ```

2. **Install dependencies**

    ```bash
    # Install uv if not already installed
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Create virtual environment and install dependencies
    uv venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    uv sync --group dev
    ```

3. **Set up frontend**

    ```bash
    # Ensure you are using the pinned Node version
    nvm install
    nvm use

    # (Optional) Enable Corepack (helps when using packageManager tooling)
    corepack enable || true

    cd web
    npm ci
    cd ..
    ```

4. **Configure environment**

    Create a `.env` file:

    ```bash
    BOOKCARD_JWT_SECRET=dev-secret-key
    ADMIN_USERNAME=admin
    ADMIN_EMAIL=admin@example.com
    ADMIN_PASSWORD=admin123
    ```

5. **Start development servers**

    ```bash
    make dev
    ```

This starts both the FastAPI backend (port 8000) and Next.js frontend (port 3000).

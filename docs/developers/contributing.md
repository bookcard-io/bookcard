# Contributing

Thank you for your interest in contributing to Bookcard!

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 22+
- Docker and Docker Compose (optional)
- uv (Python package manager)

### Initial Setup

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
cd web
npm install
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

5. **Run database migrations**

```bash
uv run migrate
```

6. **Start development servers**

```bash
make dev
```

This starts both the FastAPI backend (port 8000) and Next.js frontend (port 3000).

## Development Workflow

1. Create a feature branch from `main`
2. Make your changes
3. Write/update tests
4. Run tests: `make test`
5. Format code: `make format`
6. Submit a pull request

## Code Style

### Python

- Follow PEP 8
- Use numpy-style docstrings
- Run `ruff` for linting and formatting
- Type hints required for public APIs

```bash
make formatpy  # Format Python code
```

### TypeScript/JavaScript

- Follow project ESLint rules
- Use TypeScript for new code
- Run `npm run lint` in `web/` directory

```bash
make formatjs  # Format JS/TS code
```

## Testing

### Python Tests

```bash
make testpy  # Run Python tests
```

### Frontend Tests

```bash
make testjs  # Run frontend tests
```

### All Tests

```bash
make test  # Run all tests
```

## Documentation

- Update relevant documentation when adding features
- Follow the existing documentation structure
- Use clear, concise language

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Write a clear PR description
4. Reference any related issues
5. Request review from maintainers

## Questions?

Feel free to open an issue for questions or discussions.

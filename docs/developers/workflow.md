# Developer Workflow

## Too Long; Didn't Read

Contributing is easy.

1. Start the server: `make dev` -> go to `http://localhost:3000`
2. Make changes
3. Run tests: `make test`
4. Run lints: `make format`

That's it.

**Quick Start:**

- `make dev` - Start the development server
- `make format` - Lint and format both Python and JavaScript/TypeScript
    - `make formatpy` - Lint and format Python code
    - `make formatjs` - Lint and format JavaScript/TypeScript code
- `make test` - Run all unit tests
    - `make testpy` - Run Python unit tests
    - `make testjs` - Run JavaScript/TypeScript unit tests

## Typical Development Workflow

1. **Create a feature branch from `main`**

    ```bash
    git checkout main
    git pull origin main
    git checkout -b feature/your-feature-name
    ```

2. **Make your changes**

    - Write code following the [code style guidelines](code-style.md)
    - Make incremental commits with clear messages

3. **Write/update tests**

    - Add tests for new functionality
    - Update existing tests if behavior changes
    - Ensure tests are comprehensive and cover edge cases

4. **Run tests**

    ```bash
    make test  # Run all tests
    # Or run specific test suites:
    make testpy  # Python tests only
    make testjs  # Frontend tests only
    ```

5. **Format code**

    ```bash
    make format  # Format both Python and JavaScript/TypeScript
    # Or format individually:
    make formatpy  # Python only
    make formatjs  # JavaScript/TypeScript only
    ```

6. **Submit a pull request**

    - Ensure all tests pass
    - Update documentation if needed
    - Write a clear PR description
    - Reference any related issues
    - Request review from maintainers

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

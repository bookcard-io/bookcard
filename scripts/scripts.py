# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Scripts for running common development tasks."""

import shutil
import subprocess
import sys

import pytest


def test_coverage() -> None:
    """Run tests with coverage and multi-threading."""
    args = [
        "tests",
        "--cov=fundamental",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-n",
        "auto",
    ]
    exit_code = pytest.main(args)
    sys.exit(exit_code)


def test() -> None:
    """Run tests with multi-threading."""
    args = ["tests", "-n", "auto"]
    exit_code = pytest.main(args)
    sys.exit(exit_code)


def lint() -> None:
    """Run ruff linting with auto-fix."""
    ruff = shutil.which("ruff") or "ruff"
    result = subprocess.run(
        [ruff, "check", "--fix"],
        check=False,
    )
    sys.exit(result.returncode)


def lint_unsafe() -> None:
    """Run ruff linting with auto-fix including unsafe fixes."""
    ruff = shutil.which("ruff") or "ruff"
    result = subprocess.run(
        [ruff, "check", "--fix", "--unsafe-fixes"],
        check=False,
    )
    sys.exit(result.returncode)


def format_code() -> None:
    """Format code with ruff."""
    ruff = shutil.which("ruff") or "ruff"
    result = subprocess.run(
        [ruff, "format"],
        check=False,
    )
    sys.exit(result.returncode)


def type_check() -> None:
    """Run type checking with ty."""
    ty = shutil.which("ty") or "ty"
    result = subprocess.run(
        [ty, "check"],
        check=False,
    )
    sys.exit(result.returncode)


def serve() -> None:
    """Start the development server."""
    import uvicorn

    uvicorn.run(
        "fundamental.api.main:app",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        reload=True,
    )


def migrate() -> None:
    """Run database migrations."""
    alembic = shutil.which("alembic") or "alembic"
    result = subprocess.run(
        [alembic, "upgrade", "head"],
        check=False,
    )
    sys.exit(result.returncode)


def migrate_create() -> None:
    """Create a new migration."""
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: migrate-create <message>\n")
        sys.exit(1)

    alembic = shutil.which("alembic") or "alembic"
    message = sys.argv[1]
    result = subprocess.run(
        [alembic, "revision", "--autogenerate", "-m", message],
        check=False,
    )
    sys.exit(result.returncode)

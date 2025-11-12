# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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

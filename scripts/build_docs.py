# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Build and serve documentation locally.

This script provides utilities for building and serving MkDocs documentation
during development.
"""

import logging
import shutil
import subprocess
import sys
from pathlib import Path

# Add project root to path for imports
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Import generate_openapi_json directly from the file
# Using importlib to handle the import when script is run directly
import importlib.util  # noqa: E402

_generate_openapi_path = Path(__file__).parent / "generate_openapi.py"
_generate_openapi_spec = importlib.util.spec_from_file_location(
    "generate_openapi",
    _generate_openapi_path,
)
if _generate_openapi_spec is None or _generate_openapi_spec.loader is None:
    msg = f"Could not load generate_openapi from {_generate_openapi_path}"
    raise ImportError(msg)

_generate_openapi_module = importlib.util.module_from_spec(_generate_openapi_spec)
_generate_openapi_spec.loader.exec_module(_generate_openapi_module)
generate_openapi_json = _generate_openapi_module.generate_openapi_json

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def build_docs() -> None:
    """Build documentation using MkDocs.

    Generates OpenAPI JSON and builds static documentation site.
    """
    root = Path(__file__).parent.parent
    logger.info("Generating OpenAPI schema...")
    generate_openapi_json()

    logger.info("Building documentation...")
    # Check if mkdocs.yml is in docs/ or root
    config_file = None
    if (root / "docs" / "mkdocs.yml").exists():
        config_file = str(root / "docs" / "mkdocs.yml")
    elif (root / "mkdocs.yml").exists():
        config_file = str(root / "mkdocs.yml")
    else:
        logger.error("Error: mkdocs.yml not found in docs/ or root")
        sys.exit(1)

    mkdocs_path = shutil.which("mkdocs")
    if not mkdocs_path:
        logger.error("Error: mkdocs not found in PATH")
        sys.exit(1)

    cmd = [mkdocs_path, "build", "--config-file", config_file]
    result = subprocess.run(
        cmd,
        cwd=root,
        check=False,
    )  # ty:ignore[no-matching-overload]

    if result.returncode != 0:
        logger.error("Error: mkdocs build failed")
        sys.exit(1)

    logger.info("Documentation built successfully in ./site/")


def serve_docs(host: str = "127.0.0.1", port: int = 8001) -> None:
    """Serve documentation locally using MkDocs dev server.

    Parameters
    ----------
    host : str
        Host to bind to. Defaults to ``127.0.0.1``.
    port : int
        Port to bind to. Defaults to ``8001``.
    """
    root = Path(__file__).parent.parent
    logger.info("Generating OpenAPI schema...")
    generate_openapi_json()

    # Check if mkdocs.yml is in docs/ or root
    config_file = None
    if (root / "docs" / "mkdocs.yml").exists():
        config_file = str(root / "docs" / "mkdocs.yml")
    elif (root / "mkdocs.yml").exists():
        config_file = str(root / "mkdocs.yml")
    else:
        logger.error("Error: mkdocs.yml not found in docs/ or root")
        sys.exit(1)

    mkdocs_path = shutil.which("mkdocs")
    if not mkdocs_path:
        logger.error("Error: mkdocs not found in PATH")
        sys.exit(1)

    logger.info("Serving documentation at http://%s:%s", host, port)
    logger.info("Press Ctrl+C to stop the server")

    subprocess.run(
        [
            mkdocs_path,
            "serve",
            "--config-file",
            config_file,
            "--dev-addr",
            f"{host}:{port}",
        ],
        cwd=root,
    )  # ty:ignore[no-matching-overload]


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        host = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 8001
        serve_docs(host, port)
    else:
        build_docs()

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

"""Generate OpenAPI JSON schema from FastAPI application for documentation.

This script extracts the OpenAPI schema from the FastAPI application and writes
it to a JSON file that can be consumed by MkDocs for API documentation.
"""

import json
import logging
from contextlib import suppress
from pathlib import Path

# Ensure all route modules are imported to resolve ForwardRefs
# This is needed for OpenAPI schema generation to work properly
# Import create_app and create minimal config for schema generation
from bookcard.api.main import create_app
from bookcard.config import AppConfig

# Import models first to ensure they're available for ForwardRef resolution
from bookcard.models.auth import User

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def generate_openapi_json(output_path: Path | str = "docs/openapi.json") -> None:
    """Generate OpenAPI JSON schema from FastAPI app.

    Parameters
    ----------
    output_path : Path | str
        Path where the OpenAPI JSON will be written. Defaults to
        ``docs/openapi.json``.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Create minimal config for schema generation (no env vars required)
    # These dummy values are only used for app initialization, not for actual runtime
    minimal_config = AppConfig(
        jwt_secret="dummy-secret-for-schema-generation",  # noqa: S106
        jwt_algorithm="HS256",
        jwt_expires_minutes=131400,
        encryption_key="dummy-encryption-key-for-schema-generation",
        database_url="sqlite:///:memory:",
    )

    # Create app with minimal config (avoids requiring environment variables)
    app = create_app(config=minimal_config)

    # Patch ingest module to resolve ForwardRef "User" string annotation
    # Some routes use string annotations like "User" which create ForwardRefs
    # that need to be resolved by making User available in the module namespace
    with suppress(Exception):
        from bookcard.api.routes import ingest

        if not hasattr(ingest, "User"):
            ingest.User = User  # type: ignore[attr-defined, misc]

    openapi_schema = app.openapi()

    with output.open("w") as f:
        json.dump(openapi_schema, f, indent=2)

    logger.info("OpenAPI schema written to %s", output)


if __name__ == "__main__":
    generate_openapi_json()

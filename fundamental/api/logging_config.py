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

"""Logging configuration for the application.

Configures application-wide logging to output to stdout with formatted
output including timestamp, level, logger name, and message.
"""

import logging
import os
import sys


def setup_logging() -> None:
    """Configure application-wide logging to output to stdout.

    Sets up a console handler that outputs all log messages to stdout with
    a formatted output including timestamp, level, logger name, and message.
    This configuration ensures that all logging calls throughout the application
    will be visible in standard output when running with `make dev`.
    """
    # Get log level from environment, default to INFO for development
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Configure logging using basicConfig, which sets up root logger
    # force=True ensures it reconfigures even if logging was already configured
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,  # Override any existing configuration
    )

    # Configure application-specific logger
    app_logger = logging.getLogger("fundamental")
    app_logger.setLevel(numeric_level)
    app_logger.propagate = True

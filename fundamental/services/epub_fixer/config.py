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

"""EPUB fixer configuration dataclass.

Provides configuration object for dependency injection.
No hardcoded paths or environment-specific values.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fundamental.models.config import EPUBFixerConfig


@dataclass
class EPUBFixerSettings:
    """EPUB fixer settings configuration.

    Loads from EPUBFixerConfig model but can be created from
    environment variables for testing.

    Attributes
    ----------
    enabled : bool
        Master enable/disable flag.
    backup_enabled : bool
        Whether backups are enabled.
    backup_directory : Path
        Directory for storing backups.
    default_language : str
        Default language for fixes (default: 'en').
    skip_already_fixed : bool
        Skip EPUBs that were already fixed.
    skip_failed : bool
        Skip EPUBs that previously failed.
    """

    enabled: bool = True
    backup_enabled: bool = True
    backup_directory: Path = Path("/config/processed_books/fixed_originals")
    default_language: str = "en"
    skip_already_fixed: bool = True
    skip_failed: bool = True

    @classmethod
    def from_config_model(cls, config: "EPUBFixerConfig") -> "EPUBFixerSettings":
        """Create settings from EPUBFixerConfig model.

        Parameters
        ----------
        config : EPUBFixerConfig
            Configuration model instance.

        Returns
        -------
        EPUBFixerSettings
            Settings instance.
        """
        return cls(
            enabled=config.enabled,
            backup_enabled=config.backup_enabled,
            backup_directory=Path(config.backup_directory),
            default_language=config.default_language,
            skip_already_fixed=config.skip_already_fixed,
            skip_failed=config.skip_failed,
        )

    @classmethod
    def from_environment(cls) -> "EPUBFixerSettings":
        """Load settings from environment variables with defaults.

        Returns
        -------
        EPUBFixerSettings
            Settings instance.
        """
        import os

        return cls(
            enabled=os.getenv("EPUB_FIXER_ENABLED", "true").lower()
            in ("true", "1", "yes"),
            backup_enabled=os.getenv("EPUB_FIXER_BACKUP_ENABLED", "true").lower()
            in ("true", "1", "yes"),
            backup_directory=Path(
                os.getenv(
                    "EPUB_FIXER_BACKUP_DIR",
                    "/config/processed_books/fixed_originals",
                )
            ),
            default_language=os.getenv("EPUB_FIXER_DEFAULT_LANGUAGE", "en"),
            skip_already_fixed=os.getenv(
                "EPUB_FIXER_SKIP_ALREADY_FIXED", "true"
            ).lower()
            in ("true", "1", "yes"),
            skip_failed=os.getenv("EPUB_FIXER_SKIP_FAILED", "true").lower()
            in ("true", "1", "yes"),
        )

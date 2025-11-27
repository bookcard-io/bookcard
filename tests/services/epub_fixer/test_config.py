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

"""Tests for EPUB fixer configuration."""

import os
from pathlib import Path

from fundamental.models.config import EPUBFixerConfig
from fundamental.services.epub_fixer.config import EPUBFixerSettings


def test_epub_fixer_settings_defaults() -> None:
    """Test EPUBFixerSettings default values."""
    settings = EPUBFixerSettings()
    assert settings.enabled is True
    assert settings.backup_enabled is True
    assert settings.backup_directory == Path("/config/processed_books/fixed_originals")
    assert settings.default_language == "en"
    assert settings.skip_already_fixed is True
    assert settings.skip_failed is True


def test_epub_fixer_settings_from_config_model() -> None:
    """Test creating settings from EPUBFixerConfig model."""
    config = EPUBFixerConfig(
        enabled=False,
        backup_enabled=False,
        backup_directory="/custom/backup",
        default_language="fr",
        skip_already_fixed=False,
        skip_failed=False,
    )

    settings = EPUBFixerSettings.from_config_model(config)

    assert settings.enabled is False
    assert settings.backup_enabled is False
    assert settings.backup_directory == Path("/custom/backup")
    assert settings.default_language == "fr"
    assert settings.skip_already_fixed is False
    assert settings.skip_failed is False


def test_epub_fixer_settings_from_environment() -> None:
    """Test creating settings from environment variables."""
    # Set environment variables
    os.environ["EPUB_FIXER_ENABLED"] = "false"
    os.environ["EPUB_FIXER_BACKUP_ENABLED"] = "0"
    os.environ["EPUB_FIXER_BACKUP_DIR"] = "/env/backup"
    os.environ["EPUB_FIXER_DEFAULT_LANGUAGE"] = "de"
    os.environ["EPUB_FIXER_SKIP_ALREADY_FIXED"] = "no"
    os.environ["EPUB_FIXER_SKIP_FAILED"] = "false"

    try:
        settings = EPUBFixerSettings.from_environment()

        assert settings.enabled is False
        assert settings.backup_enabled is False
        assert settings.backup_directory == Path("/env/backup")
        assert settings.default_language == "de"
        assert settings.skip_already_fixed is False
        assert settings.skip_failed is False
    finally:
        # Clean up
        for key in [
            "EPUB_FIXER_ENABLED",
            "EPUB_FIXER_BACKUP_ENABLED",
            "EPUB_FIXER_BACKUP_DIR",
            "EPUB_FIXER_DEFAULT_LANGUAGE",
            "EPUB_FIXER_SKIP_ALREADY_FIXED",
            "EPUB_FIXER_SKIP_FAILED",
        ]:
            os.environ.pop(key, None)


def test_epub_fixer_settings_from_environment_defaults() -> None:
    """Test environment variable parsing with defaults."""
    # Clear environment variables
    for key in [
        "EPUB_FIXER_ENABLED",
        "EPUB_FIXER_BACKUP_ENABLED",
        "EPUB_FIXER_BACKUP_DIR",
        "EPUB_FIXER_DEFAULT_LANGUAGE",
        "EPUB_FIXER_SKIP_ALREADY_FIXED",
        "EPUB_FIXER_SKIP_FAILED",
    ]:
        os.environ.pop(key, None)

    settings = EPUBFixerSettings.from_environment()

    assert settings.enabled is True
    assert settings.backup_enabled is True
    assert settings.backup_directory == Path("/config/processed_books/fixed_originals")
    assert settings.default_language == "en"
    assert settings.skip_already_fixed is True
    assert settings.skip_failed is True


def test_epub_fixer_settings_from_environment_truthy_values() -> None:
    """Test environment variable parsing with various truthy values."""
    for truthy_value in ["true", "1", "yes", "True", "TRUE", "YES"]:
        os.environ["EPUB_FIXER_ENABLED"] = truthy_value
        try:
            settings = EPUBFixerSettings.from_environment()
            assert settings.enabled is True
        finally:
            os.environ.pop("EPUB_FIXER_ENABLED", None)


def test_epub_fixer_settings_from_environment_falsy_values() -> None:
    """Test environment variable parsing with various falsy values."""
    for falsy_value in ["false", "0", "no", "False", "FALSE", "NO", ""]:
        os.environ["EPUB_FIXER_ENABLED"] = falsy_value
        try:
            settings = EPUBFixerSettings.from_environment()
            assert settings.enabled is False
        finally:
            os.environ.pop("EPUB_FIXER_ENABLED", None)

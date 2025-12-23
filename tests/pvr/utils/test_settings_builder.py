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

"""Tests for settings builder utilities."""

import pytest
from pydantic import ValidationError

from bookcard.models.pvr import DownloadClientDefinition, DownloadClientType
from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.utils.settings_builder import SettingsBuilder

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def client_definition() -> DownloadClientDefinition:
    """Create a DownloadClientDefinition for testing."""
    return DownloadClientDefinition(
        id=1,
        name="Test Client",
        client_type=DownloadClientType.QBITTORRENT,
        host="localhost",
        port=8080,
        username="admin",
        password="secret",
        use_ssl=False,
        timeout_seconds=30,
        category="bookcard",
        download_path="/downloads",
        enabled=True,
        priority=0,
    )


@pytest.fixture
def client_definition_minimal() -> DownloadClientDefinition:
    """Create a minimal DownloadClientDefinition for testing."""
    return DownloadClientDefinition(
        id=1,
        name="Test Client",
        client_type=DownloadClientType.QBITTORRENT,
        host="localhost",
        port=8080,
    )


# ============================================================================
# SettingsBuilder Tests
# ============================================================================


class TestSettingsBuilderInit:
    """Test SettingsBuilder initialization."""

    def test_init(self) -> None:
        """Test SettingsBuilder initialization."""
        builder = SettingsBuilder(DownloadClientSettings)
        assert builder._class == DownloadClientSettings
        assert builder._fields == {}


class TestSettingsBuilderWithBaseFields:
    """Test SettingsBuilder.with_base_fields method."""

    def test_with_base_fields(
        self, client_definition: DownloadClientDefinition
    ) -> None:
        """Test with_base_fields adds all base fields."""
        builder = SettingsBuilder(DownloadClientSettings)
        result = builder.with_base_fields(client_definition)
        assert result is builder  # Returns self for chaining
        assert builder._fields["host"] == "localhost"
        assert builder._fields["port"] == 8080
        assert builder._fields["username"] == "admin"
        assert builder._fields["password"] == "secret"
        assert builder._fields["use_ssl"] is False
        assert builder._fields["timeout_seconds"] == 30
        assert builder._fields["category"] == "bookcard"
        assert builder._fields["download_path"] == "/downloads"

    def test_with_base_fields_minimal(
        self, client_definition_minimal: DownloadClientDefinition
    ) -> None:
        """Test with_base_fields with minimal client definition."""
        builder = SettingsBuilder(DownloadClientSettings)
        builder.with_base_fields(client_definition_minimal)
        assert builder._fields["host"] == "localhost"
        assert builder._fields["port"] == 8080
        assert builder._fields["username"] is None
        assert builder._fields["password"] is None
        assert builder._fields["use_ssl"] is False
        assert builder._fields["timeout_seconds"] == 30  # Default value
        assert builder._fields["category"] is None
        assert builder._fields["download_path"] is None


class TestSettingsBuilderWithOptional:
    """Test SettingsBuilder.with_optional method."""

    def test_with_optional_field_exists(self) -> None:
        """Test with_optional when field exists in source dict."""
        builder = SettingsBuilder(DownloadClientSettings)
        source = {"url_base": "/api"}
        result = builder.with_optional("url_base", source)
        assert result is builder
        assert builder._fields["url_base"] == "/api"

    def test_with_optional_field_missing(self) -> None:
        """Test with_optional when field missing from source dict."""
        builder = SettingsBuilder(DownloadClientSettings)
        source = {"other_field": "value"}
        builder.with_optional("url_base", source)
        assert "url_base" not in builder._fields

    def test_with_optional_with_default(self) -> None:
        """Test with_optional with default value."""
        builder = SettingsBuilder(DownloadClientSettings)
        source = {"other_field": "value"}
        builder.with_optional("url_base", source, default="/default")
        assert builder._fields["url_base"] == "/default"

    def test_with_optional_with_default_field_exists(self) -> None:
        """Test with_optional with default when field exists."""
        builder = SettingsBuilder(DownloadClientSettings)
        source = {"url_base": "/api"}
        builder.with_optional("url_base", source, default="/default")
        assert builder._fields["url_base"] == "/api"  # Existing value takes precedence

    def test_with_optional_with_transform(self) -> None:
        """Test with_optional with transform function."""
        builder = SettingsBuilder(DownloadClientSettings)
        source = {"url_base": "api"}
        builder.with_optional("url_base", source, transform=lambda x: f"/{x}")
        assert builder._fields["url_base"] == "/api"

    def test_with_optional_with_transform_none_value(self) -> None:
        """Test with_optional with transform when value is None."""
        builder = SettingsBuilder(DownloadClientSettings)
        source = {"url_base": None}
        builder.with_optional("url_base", source, transform=lambda x: f"/{x}")
        # None values should not be transformed or added
        assert "url_base" not in builder._fields

    def test_with_optional_none_source_dict(self) -> None:
        """Test with_optional with None source dict."""
        builder = SettingsBuilder(DownloadClientSettings)
        result = builder.with_optional("url_base", None)
        assert result is builder
        assert "url_base" not in builder._fields

    def test_with_optional_none_source_dict_with_default(self) -> None:
        """Test with_optional with None source dict and default."""
        builder = SettingsBuilder(DownloadClientSettings)
        builder.with_optional("url_base", None, default="/default")
        assert builder._fields["url_base"] == "/default"

    def test_with_optional_none_source_dict_with_default_none(self) -> None:
        """Test with_optional with None source dict and None default."""
        builder = SettingsBuilder(DownloadClientSettings)
        builder.with_optional("url_base", None, default=None)
        assert "url_base" not in builder._fields

    def test_with_optional_value_none_after_transform(self) -> None:
        """Test with_optional when transform returns None."""
        builder = SettingsBuilder(DownloadClientSettings)
        source = {"url_base": "api"}
        builder.with_optional("url_base", source, transform=lambda x: None)
        # None values should not be added
        assert "url_base" not in builder._fields


class TestSettingsBuilderWithField:
    """Test SettingsBuilder.with_field method."""

    def test_with_field(self) -> None:
        """Test with_field adds field directly."""
        builder = SettingsBuilder(DownloadClientSettings)
        result = builder.with_field("url_base", "/api")
        assert result is builder
        assert builder._fields["url_base"] == "/api"

    def test_with_field_overwrites(self) -> None:
        """Test with_field overwrites existing field."""
        builder = SettingsBuilder(DownloadClientSettings)
        builder.with_field("url_base", "/api")
        builder.with_field("url_base", "/new")
        assert builder._fields["url_base"] == "/new"

    def test_with_field_various_types(self) -> None:
        """Test with_field with various value types."""
        builder = SettingsBuilder(DownloadClientSettings)
        builder.with_field("string_field", "test")
        builder.with_field("int_field", 42)
        builder.with_field("bool_field", True)
        builder.with_field("list_field", [1, 2, 3])
        assert builder._fields["string_field"] == "test"
        assert builder._fields["int_field"] == 42
        assert builder._fields["bool_field"] is True
        assert builder._fields["list_field"] == [1, 2, 3]


class TestSettingsBuilderBuild:
    """Test SettingsBuilder.build method."""

    def test_build_success(self, client_definition: DownloadClientDefinition) -> None:
        """Test build creates settings instance."""
        builder = SettingsBuilder(DownloadClientSettings)
        builder.with_base_fields(client_definition)
        settings = builder.build()
        assert isinstance(settings, DownloadClientSettings)
        assert settings.host == "localhost"
        assert settings.port == 8080
        assert settings.username == "admin"
        assert settings.password == "secret"

    def test_build_fluent_chaining(
        self, client_definition: DownloadClientDefinition
    ) -> None:
        """Test fluent method chaining."""
        builder = SettingsBuilder(DownloadClientSettings)
        settings = (
            builder
            .with_base_fields(client_definition)
            .with_optional("url_base", {"url_base": "/api"})
            .with_field("custom_field", "value")
            .build()
        )
        assert isinstance(settings, DownloadClientSettings)
        assert settings.host == "localhost"
        assert "url_base" in builder._fields
        assert "custom_field" in builder._fields

    def test_build_validation_error(self) -> None:
        """Test build raises ValidationError for invalid fields."""
        builder = SettingsBuilder(DownloadClientSettings)
        builder.with_field("port", 0)  # Invalid: port must be >= 1
        with pytest.raises(ValidationError):
            builder.build()

    def test_build_missing_required_fields(self) -> None:
        """Test build raises ValidationError for missing required fields."""
        builder = SettingsBuilder(DownloadClientSettings)
        # Missing required fields: host and port
        with pytest.raises(ValidationError):
            builder.build()

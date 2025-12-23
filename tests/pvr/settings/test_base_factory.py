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

"""Tests for base settings factory."""

from pydantic import Field

from bookcard.pvr.base import DownloadClientSettings, IndexerSettings
from bookcard.pvr.settings.base_factory import (
    IndexerSettingsFactory,
    SettingsFactory,
)

# ============================================================================
# Test Settings Classes
# ============================================================================


class CustomDownloadClientSettings(DownloadClientSettings):
    """Custom download client settings for testing."""

    url_base: str | None = Field(default=None, description="URL base path")


class CustomIndexerSettings(IndexerSettings):
    """Custom indexer settings for testing."""

    api_path: str | None = Field(default=None, description="API path")


# ============================================================================
# SettingsFactory Tests
# ============================================================================


class TestSettingsFactoryInit:
    """Test SettingsFactory initialization."""

    def test_init_without_extra_fields(self) -> None:
        """Test SettingsFactory initialization without extra fields."""
        factory = SettingsFactory(DownloadClientSettings)
        assert factory.settings_class == DownloadClientSettings
        assert factory.extra_fields == {}

    def test_init_with_extra_fields(self) -> None:
        """Test SettingsFactory initialization with extra fields."""
        extra_fields = {"url_base": ("url_base", None)}
        factory = SettingsFactory(CustomDownloadClientSettings, extra_fields)
        assert factory.settings_class == CustomDownloadClientSettings
        assert factory.extra_fields == extra_fields

    def test_init_with_none_extra_fields(self) -> None:
        """Test SettingsFactory initialization with None extra fields."""
        factory = SettingsFactory(DownloadClientSettings, None)
        assert factory.settings_class == DownloadClientSettings
        assert factory.extra_fields == {}


class TestSettingsFactoryCreate:
    """Test SettingsFactory.create method."""

    def test_create_basic(self) -> None:
        """Test create with basic fields only."""
        factory = SettingsFactory(DownloadClientSettings)
        settings = factory.create(
            host="localhost",
            port=8080,
            username="admin",
            password="secret",
            use_ssl=False,
            timeout_seconds=30,
            category="bookcard",
            download_path="/downloads",
        )
        assert isinstance(settings, DownloadClientSettings)
        assert settings.host == "localhost"
        assert settings.port == 8080
        assert settings.username == "admin"
        assert settings.password == "secret"
        assert settings.use_ssl is False
        assert settings.timeout_seconds == 30
        assert settings.category == "bookcard"
        assert settings.download_path == "/downloads"

    def test_create_with_none_values(self) -> None:
        """Test create with None values for optional fields."""
        factory = SettingsFactory(DownloadClientSettings)
        settings = factory.create(
            host="localhost",
            port=8080,
            username=None,
            password=None,
            use_ssl=False,
            timeout_seconds=30,
            category=None,
            download_path=None,
        )
        assert settings.username is None
        assert settings.password is None
        assert settings.category is None
        assert settings.download_path is None

    def test_create_with_extra_fields_no_additional_settings(self) -> None:
        """Test create with extra fields but no additional_settings."""
        factory = SettingsFactory(
            CustomDownloadClientSettings, {"url_base": ("url_base", "/api")}
        )
        settings = factory.create(
            host="localhost",
            port=8080,
            username=None,
            password=None,
            use_ssl=False,
            timeout_seconds=30,
            category=None,
            download_path=None,
        )
        assert settings.url_base == "/api"  # Uses default

    def test_create_with_extra_fields_with_additional_settings(self) -> None:
        """Test create with extra fields and additional_settings."""
        factory = SettingsFactory(
            CustomDownloadClientSettings, {"url_base": ("url_base", "/api")}
        )
        settings = factory.create(
            host="localhost",
            port=8080,
            username=None,
            password=None,
            use_ssl=False,
            timeout_seconds=30,
            category=None,
            download_path=None,
            additional_settings={"url_base": "/custom"},
        )
        assert settings.url_base == "/custom"  # Uses value from additional_settings

    def test_create_with_extra_fields_missing_in_additional_settings(
        self,
    ) -> None:
        """Test create with extra fields but key missing in additional_settings."""
        factory = SettingsFactory(
            CustomDownloadClientSettings, {"url_base": ("url_base", "/api")}
        )
        settings = factory.create(
            host="localhost",
            port=8080,
            username=None,
            password=None,
            use_ssl=False,
            timeout_seconds=30,
            category=None,
            download_path=None,
            additional_settings={"other_field": "value"},
        )
        assert settings.url_base == "/api"  # Uses default

    def test_create_with_extra_fields_none_value(self) -> None:
        """Test create with extra fields when value is None."""
        factory = SettingsFactory(
            CustomDownloadClientSettings, {"url_base": ("url_base", None)}
        )
        settings = factory.create(
            host="localhost",
            port=8080,
            username=None,
            password=None,
            use_ssl=False,
            timeout_seconds=30,
            category=None,
            download_path=None,
            additional_settings={"url_base": None},
        )
        assert settings.url_base is None

    def test_create_with_extra_fields_str_conversion(self) -> None:
        """Test create with extra fields converts to str when default is str."""
        factory = SettingsFactory(
            CustomDownloadClientSettings, {"url_base": ("url_base", "/api")}
        )
        # Pass int value, should be converted to str because default_value is str
        settings = factory.create(
            host="localhost",
            port=8080,
            username=None,
            password=None,
            use_ssl=False,
            timeout_seconds=30,
            category=None,
            download_path=None,
            additional_settings={"url_base": 12345},
        )
        assert settings.url_base == "12345"  # Converted to str

    def test_create_with_extra_fields_no_str_conversion(self) -> None:
        """Test create with extra fields doesn't convert when default is not str."""

        # Create a custom settings class with int field
        class IntSettings(DownloadClientSettings):
            max_connections: int | None = Field(default=None)

        factory = SettingsFactory(
            IntSettings, {"max_connections": ("max_connections", 10)}
        )
        settings = factory.create(
            host="localhost",
            port=8080,
            username=None,
            password=None,
            use_ssl=False,
            timeout_seconds=30,
            category=None,
            download_path=None,
            additional_settings={"max_connections": 20},
        )
        assert settings.max_connections == 20  # Not converted to str

    def test_create_with_multiple_extra_fields(self) -> None:
        """Test create with multiple extra fields."""

        class MultiSettings(DownloadClientSettings):
            url_base: str | None = Field(default=None)
            max_connections: int | None = Field(default=None)

        factory = SettingsFactory(
            MultiSettings,
            {
                "url_base": ("url_base", "/api"),
                "max_connections": ("max_connections", 10),
            },
        )
        settings = factory.create(
            host="localhost",
            port=8080,
            username=None,
            password=None,
            use_ssl=False,
            timeout_seconds=30,
            category=None,
            download_path=None,
            additional_settings={"url_base": "/custom", "max_connections": 20},
        )
        assert settings.url_base == "/custom"
        assert settings.max_connections == 20

    def test_create_with_extra_fields_none_additional_settings(self) -> None:
        """Test create with extra fields when additional_settings is None."""
        factory = SettingsFactory(
            CustomDownloadClientSettings, {"url_base": ("url_base", "/api")}
        )
        settings = factory.create(
            host="localhost",
            port=8080,
            username=None,
            password=None,
            use_ssl=False,
            timeout_seconds=30,
            category=None,
            download_path=None,
            additional_settings=None,
        )
        assert settings.url_base == "/api"  # Uses default


# ============================================================================
# IndexerSettingsFactory Tests
# ============================================================================


class TestIndexerSettingsFactoryInit:
    """Test IndexerSettingsFactory initialization."""

    def test_init_without_extra_fields(self) -> None:
        """Test IndexerSettingsFactory initialization without extra fields."""
        factory = IndexerSettingsFactory(IndexerSettings)
        assert factory.settings_class == IndexerSettings
        assert factory.extra_fields == {}

    def test_init_with_extra_fields(self) -> None:
        """Test IndexerSettingsFactory initialization with extra fields."""
        extra_fields = {"api_path": ("api_path", "/api")}
        factory = IndexerSettingsFactory(CustomIndexerSettings, extra_fields)
        assert factory.settings_class == CustomIndexerSettings
        assert factory.extra_fields == extra_fields

    def test_init_with_none_extra_fields(self) -> None:
        """Test IndexerSettingsFactory initialization with None extra fields."""
        factory = IndexerSettingsFactory(IndexerSettings, None)
        assert factory.settings_class == IndexerSettings
        assert factory.extra_fields == {}


class TestIndexerSettingsFactoryCreate:
    """Test IndexerSettingsFactory.create method."""

    def test_create_basic(self) -> None:
        """Test create with basic fields only."""
        factory = IndexerSettingsFactory(IndexerSettings)
        settings = factory.create(
            base_url="https://indexer.example.com",
            api_key="test-key",
            timeout_seconds=30,
            retry_count=3,
            categories=[1000, 2000],
        )
        assert isinstance(settings, IndexerSettings)
        assert settings.base_url == "https://indexer.example.com"
        assert settings.api_key == "test-key"
        assert settings.timeout_seconds == 30
        assert settings.retry_count == 3
        assert settings.categories == [1000, 2000]

    def test_create_with_none_values(self) -> None:
        """Test create with None values for optional fields."""
        factory = IndexerSettingsFactory(IndexerSettings)
        settings = factory.create(
            base_url="https://indexer.example.com",
            api_key=None,
            timeout_seconds=30,
            retry_count=3,
            categories=None,
        )
        assert settings.api_key is None
        assert settings.categories is None

    def test_create_with_extra_fields_no_additional_settings(self) -> None:
        """Test create with extra fields but no additional_settings."""
        factory = IndexerSettingsFactory(
            CustomIndexerSettings, {"api_path": ("api_path", "/api")}
        )
        settings = factory.create(
            base_url="https://indexer.example.com",
            api_key="test-key",
            timeout_seconds=30,
            retry_count=3,
            categories=None,
        )
        assert settings.api_path == "/api"  # Uses default

    def test_create_with_extra_fields_with_additional_settings(self) -> None:
        """Test create with extra fields and additional_settings."""
        factory = IndexerSettingsFactory(
            CustomIndexerSettings, {"api_path": ("api_path", "/api")}
        )
        settings = factory.create(
            base_url="https://indexer.example.com",
            api_key="test-key",
            timeout_seconds=30,
            retry_count=3,
            categories=None,
            additional_settings={"api_path": "/custom"},
        )
        assert settings.api_path == "/custom"  # Uses value from additional_settings

    def test_create_with_extra_fields_missing_in_additional_settings(
        self,
    ) -> None:
        """Test create with extra fields but key missing in additional_settings."""
        factory = IndexerSettingsFactory(
            CustomIndexerSettings, {"api_path": ("api_path", "/api")}
        )
        settings = factory.create(
            base_url="https://indexer.example.com",
            api_key="test-key",
            timeout_seconds=30,
            retry_count=3,
            categories=None,
            additional_settings={"other_field": "value"},
        )
        assert settings.api_path == "/api"  # Uses default

    def test_create_with_extra_fields_none_value(self) -> None:
        """Test create with extra fields when value is None."""
        factory = IndexerSettingsFactory(
            CustomIndexerSettings, {"api_path": ("api_path", None)}
        )
        settings = factory.create(
            base_url="https://indexer.example.com",
            api_key="test-key",
            timeout_seconds=30,
            retry_count=3,
            categories=None,
            additional_settings={"api_path": None},
        )
        assert settings.api_path is None

    def test_create_with_extra_fields_str_conversion(self) -> None:
        """Test create with extra fields converts to str when default is str."""
        factory = IndexerSettingsFactory(
            CustomIndexerSettings, {"api_path": ("api_path", "/api")}
        )
        # Pass int value, should be converted to str because default_value is str
        settings = factory.create(
            base_url="https://indexer.example.com",
            api_key="test-key",
            timeout_seconds=30,
            retry_count=3,
            categories=None,
            additional_settings={"api_path": 12345},
        )
        assert settings.api_path == "12345"  # Converted to str

    def test_create_with_extra_fields_no_str_conversion(self) -> None:
        """Test create with extra fields doesn't convert when default is not str."""

        # Create a custom settings class with int field
        class IntSettings(IndexerSettings):
            max_results: int | None = Field(default=None)

        factory = IndexerSettingsFactory(
            IntSettings, {"max_results": ("max_results", 100)}
        )
        settings = factory.create(
            base_url="https://indexer.example.com",
            api_key="test-key",
            timeout_seconds=30,
            retry_count=3,
            categories=None,
            additional_settings={"max_results": 200},
        )
        assert settings.max_results == 200  # Not converted to str

    def test_create_with_multiple_extra_fields(self) -> None:
        """Test create with multiple extra fields."""

        class MultiSettings(IndexerSettings):
            api_path: str | None = Field(default=None)
            max_results: int | None = Field(default=None)

        factory = IndexerSettingsFactory(
            MultiSettings,
            {
                "api_path": ("api_path", "/api"),
                "max_results": ("max_results", 100),
            },
        )
        settings = factory.create(
            base_url="https://indexer.example.com",
            api_key="test-key",
            timeout_seconds=30,
            retry_count=3,
            categories=None,
            additional_settings={"api_path": "/custom", "max_results": 200},
        )
        assert settings.api_path == "/custom"
        assert settings.max_results == 200

    def test_create_with_extra_fields_none_additional_settings(self) -> None:
        """Test create with extra fields when additional_settings is None."""
        factory = IndexerSettingsFactory(
            CustomIndexerSettings, {"api_path": ("api_path", "/api")}
        )
        settings = factory.create(
            base_url="https://indexer.example.com",
            api_key="test-key",
            timeout_seconds=30,
            retry_count=3,
            categories=None,
            additional_settings=None,
        )
        assert settings.api_path == "/api"  # Uses default

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

"""System configuration models for Fundamental.

These models store system-level configuration settings that apply to the entire
application, as opposed to user-specific settings. Each model represents a
singleton configuration (only one record should exist per table).
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, SQLModel


class LogLevel(StrEnum):
    """Application log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EmailServerType(StrEnum):
    """Email server type enumeration."""

    SMTP = "smtp"
    GMAIL = "gmail"


class EmailServerConfig(SQLModel, table=True):
    """Email server configuration for sending e-books to devices.

    Attributes
    ----------
    id : int | None
        Primary key identifier. Only one record should exist (singleton).
    server_type : EmailServerType
        Email server type: SMTP or Gmail (default: SMTP).
    smtp_host : str | None
        SMTP server hostname (required for SMTP type).
    smtp_port : int | None
        SMTP server port (default: 587 for TLS, 465 for SSL).
    smtp_username : str | None
        SMTP authentication username.
    smtp_password : str | None
        SMTP authentication password (should be encrypted at service layer).
    smtp_use_tls : bool
        Whether to use TLS encryption (default: True).
    smtp_use_ssl : bool
        Whether to use SSL encryption (default: False).
    smtp_from_email : str | None
        Email address to send from.
    smtp_from_name : str | None
        Display name for sender.
    max_email_size_mb : int
        Maximum email size in MB (default: 25).
    gmail_token : dict[str, object] | None
        Gmail OAuth token data (JSON, required for Gmail type).
    enabled : bool
        Whether email server is enabled (default: False).
    created_at : datetime
        Configuration creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "email_server_config"

    id: int | None = Field(default=None, primary_key=True)
    server_type: EmailServerType = Field(
        default=EmailServerType.SMTP,
        sa_column=Column(SQLEnum(EmailServerType, native_enum=False)),
    )
    smtp_host: str | None = Field(default=None, max_length=255)
    smtp_port: int | None = Field(default=587)
    smtp_username: str | None = Field(default=None, max_length=255)
    smtp_password: str | None = Field(default=None, max_length=500)
    smtp_use_tls: bool = Field(default=True)
    smtp_use_ssl: bool = Field(default=False)
    smtp_from_email: str | None = Field(default=None, max_length=255)
    smtp_from_name: str | None = Field(default=None, max_length=255)
    max_email_size_mb: int = Field(default=25)
    gmail_token: dict[str, object] | None = Field(default=None, sa_column=Column(JSON))
    enabled: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class Library(SQLModel, table=True):
    """Calibre library configuration.

    Supports multiple libraries, with one active library at a time.
    Each library points to a separate Calibre metadata.db file.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    name : str
        User-friendly library name.
    calibre_db_path : str
        Path to Calibre database directory (contains metadata.db).
    calibre_db_file : str
        Calibre database filename (default: 'metadata.db').
    library_root : str | None
        Optional root directory where Calibre stores book files. If provided,
        file paths are resolved under this directory instead of deriving from
        ``calibre_db_path``. This is useful when the database directory and
        the books directory are not the same parent (e.g., split mounts).
    calibre_uuid : str | None
        Calibre library UUID (auto-detected from database).
    use_split_library : bool
        Whether to use split library mode (default: False).
    split_library_dir : str | None
        Directory for split library mode.
    auto_reconnect : bool
        Whether to automatically reconnect to database on errors (default: True).
    is_active : bool
        Whether this is the currently active library (only one can be active).
    created_at : datetime
        Library creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "libraries"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    calibre_db_path: str = Field(max_length=1000)
    calibre_db_file: str = Field(default="metadata.db", max_length=255)
    library_root: str | None = Field(default=None, max_length=1000)
    calibre_uuid: str | None = Field(default=None, max_length=36)
    use_split_library: bool = Field(default=False)
    split_library_dir: str | None = Field(default=None, max_length=1000)
    auto_reconnect: bool = Field(default=True)
    is_active: bool = Field(default=False, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class BasicConfig(SQLModel, table=True):
    """Basic system configuration settings.

    Attributes
    ----------
    id : int | None
        Primary key identifier. Only one record should exist (singleton).
    app_title : str
        Application title displayed in UI (default: 'Fundamental').
    server_port : int
        HTTP server port (default: 8000).
    external_port : int | None
        External-facing port (for reverse proxy, default: None uses server_port).
    ssl_cert_file : str | None
        Path to SSL certificate file.
    ssl_key_file : str | None
        Path to SSL private key file.
    trusted_hosts : str | None
        Comma-separated list of trusted hostnames for reverse proxy.
    log_level : LogLevel
        Application log level (default: INFO).
    log_file : str | None
        Path to application log file (default: None uses stdout).
    enable_access_log : bool
        Whether to enable access logging (default: False).
    access_log_file : str | None
        Path to access log file.
    max_upload_size_mb : int
        Maximum file upload size in MB (default: 100).
    allow_anonymous_browsing : bool
        Whether to allow anonymous users to browse library (default: False).
    allow_public_registration : bool
        Whether to allow public user registration (default: False).
    require_invite_for_registration : bool
        Whether registration requires an invite token (default: True).
    require_email_for_registration : bool
        Whether registration requires email verification (default: False).
    allow_remote_login : bool
        Whether to allow remote login (default: False).
    allow_file_uploads : bool
        Whether to allow file uploads (default: False).
    session_timeout_minutes : int
        User session timeout in minutes (default: 60).
    default_language : str
        Default language code (default: 'all').
    default_locale : str
        Default locale code (default: 'en').
    created_at : datetime
        Configuration creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "basic_config"

    id: int | None = Field(default=None, primary_key=True)
    app_title: str = Field(default="Fundamental", max_length=255)
    server_port: int = Field(default=8000)
    external_port: int | None = Field(default=None)
    ssl_cert_file: str | None = Field(default=None, max_length=1000)
    ssl_key_file: str | None = Field(default=None, max_length=1000)
    trusted_hosts: str | None = Field(default=None, max_length=500)
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        sa_column=Column(SQLEnum(LogLevel, native_enum=False)),
    )
    log_file: str | None = Field(default=None, max_length=1000)
    enable_access_log: bool = Field(default=False)
    access_log_file: str | None = Field(default=None, max_length=1000)
    max_upload_size_mb: int = Field(default=100)
    allow_anonymous_browsing: bool = Field(default=False)
    allow_public_registration: bool = Field(default=False)
    require_invite_for_registration: bool = Field(default=True)
    require_email_for_registration: bool = Field(default=False)
    allow_remote_login: bool = Field(default=False)
    allow_file_uploads: bool = Field(default=False)
    session_timeout_minutes: int = Field(default=60)
    default_language: str = Field(default="all", max_length=10)
    default_locale: str = Field(default="en", max_length=10)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class UIConfig(SQLModel, table=True):
    """UI configuration settings.

    Attributes
    ----------
    id : int | None
        Primary key identifier. Only one record should exist (singleton).
    books_per_page : int
        Number of books to display per page (default: 20).
    random_books_count : int
        Number of random books to display (default: 4).
    authors_max_display : int
        Maximum number of authors to display (0 = unlimited, default: 0).
    default_view_mode : str
        Default view mode: 'grid' or 'list' (default: 'grid').
    theme : str
        UI theme name (default: 'dark').
    show_thumbnails : bool
        Whether to show book thumbnails (default: True).
    thumbnail_size : int
        Thumbnail size in pixels (default: 200).
    enable_advanced_search : bool
        Whether to enable advanced search features (default: True).
    read_column_id : int | None
        Custom column ID to use for "read" status (0 = disabled, default: None).
    title_sort_regex : str | None
        Regex pattern for title sorting (ignores articles like "The", "A").
    columns_to_ignore : str | None
        Comma-separated list of column IDs to hide in UI.
    created_at : datetime
        Configuration creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "ui_config"

    id: int | None = Field(default=None, primary_key=True)
    books_per_page: int = Field(default=20)
    random_books_count: int = Field(default=4)
    authors_max_display: int = Field(default=0)
    default_view_mode: str = Field(default="grid", max_length=20)
    theme: str = Field(default="dark", max_length=50)
    show_thumbnails: bool = Field(default=True)
    thumbnail_size: int = Field(default=200)
    enable_advanced_search: bool = Field(default=True)
    read_column_id: int | None = Field(default=None)
    title_sort_regex: str | None = Field(default=None, max_length=500)
    columns_to_ignore: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class ScheduledTasksConfig(SQLModel, table=True):
    """Scheduled tasks configuration.

    Attributes
    ----------
    id : int | None
        Primary key identifier. Only one record should exist (singleton).
    start_time_hour : int
        Hour of day to start scheduled tasks (0-23, default: 4).
    duration_hours : int
        Maximum duration for scheduled tasks in hours (default: 10).
    generate_book_covers : bool
        Whether to generate book cover thumbnails (default: False).
    generate_series_covers : bool
        Whether to generate series cover thumbnails (default: False).
    reconnect_database : bool
        Whether to reconnect to Calibre database (default: False).
    metadata_backup : bool
        Whether to backup metadata (default: False).
    epub_fixer_daily_scan : bool
        Whether to enable daily EPUB fixer scan (default: False).
    epub_fixer_auto_fix_on_ingest : bool
        Whether to automatically fix EPUBs on book upload (default: False).
    created_at : datetime
        Configuration creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "scheduled_tasks_config"

    id: int | None = Field(default=None, primary_key=True)
    start_time_hour: int = Field(default=4)
    duration_hours: int = Field(default=10)
    generate_book_covers: bool = Field(default=False)
    generate_series_covers: bool = Field(default=False)
    reconnect_database: bool = Field(default=False)
    metadata_backup: bool = Field(default=False)
    epub_fixer_daily_scan: bool = Field(default=False)
    epub_fixer_auto_fix_on_ingest: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class SecurityConfig(SQLModel, table=True):
    """Security and authentication configuration.

    Attributes
    ----------
    id : int | None
        Primary key identifier. Only one record should exist (singleton).
    enable_password_policy : bool
        Whether to enforce password policy (default: True).
    password_min_length : int
        Minimum password length (default: 8).
    password_require_number : bool
        Require at least one number (default: True).
    password_require_lowercase : bool
        Require at least one lowercase letter (default: True).
    password_require_uppercase : bool
        Require at least one uppercase letter (default: True).
    password_require_special : bool
        Require at least one special character (default: True).
    session_type : int
        Session type: 1=permanent, 2=timeout (default: 1).
    enable_rate_limiting : bool
        Whether to enable rate limiting (default: True).
    rate_limiter_uri : str | None
        Rate limiter URI/endpoint.
    rate_limiter_options : str | None
        Rate limiter configuration options (JSON string).
    enable_reverse_proxy_login : bool
        Whether to allow reverse proxy header login (default: False).
    reverse_proxy_login_header : str | None
        Header name for reverse proxy authentication.
    check_file_extensions : bool
        Whether to validate file extensions on upload (default: True).
    created_at : datetime
        Configuration creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "security_config"

    id: int | None = Field(default=None, primary_key=True)
    enable_password_policy: bool = Field(default=True)
    password_min_length: int = Field(default=8)
    password_require_number: bool = Field(default=True)
    password_require_lowercase: bool = Field(default=True)
    password_require_uppercase: bool = Field(default=True)
    password_require_special: bool = Field(default=True)
    session_type: int = Field(default=1)
    enable_rate_limiting: bool = Field(default=True)
    rate_limiter_uri: str | None = Field(default=None, max_length=500)
    rate_limiter_options: str | None = Field(default=None, max_length=1000)
    enable_reverse_proxy_login: bool = Field(default=False)
    reverse_proxy_login_header: str | None = Field(default=None, max_length=255)
    check_file_extensions: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class ContentRestrictionsConfig(SQLModel, table=True):
    """Content access restrictions configuration.

    Attributes
    ----------
    id : int | None
        Primary key identifier. Only one record should exist (singleton).
    denied_tags : str | None
        Comma-separated list of denied tags (users cannot access books with these).
    allowed_tags : str | None
        Comma-separated list of allowed tags (users can only access books with these).
    restricted_column_id : int | None
        Custom column ID to use for content restrictions (0 = disabled).
    denied_column_values : str | None
        Comma-separated list of denied column values.
    allowed_column_values : str | None
        Comma-separated list of allowed column values.
    created_at : datetime
        Configuration creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "content_restrictions_config"

    id: int | None = Field(default=None, primary_key=True)
    denied_tags: str | None = Field(default=None, max_length=1000)
    allowed_tags: str | None = Field(default=None, max_length=1000)
    restricted_column_id: int | None = Field(default=None)
    denied_column_values: str | None = Field(default=None, max_length=1000)
    allowed_column_values: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class FileHandlingConfig(SQLModel, table=True):
    """File handling and conversion configuration.

    Attributes
    ----------
    id : int | None
        Primary key identifier. Only one record should exist (singleton).
    calibre_binaries_dir : str | None
        Directory containing Calibre binaries.
    converter_path : str | None
        Path to ebook-convert binary.
    kepubify_path : str | None
        Path to kepubify binary.
    unrar_path : str | None
        Path to unrar binary.
    allowed_upload_formats : str
        Comma-separated list of allowed upload formats (default: common formats).
    support_unicode_filenames : bool
        Whether to support Unicode characters in filenames (default: False).
    embed_metadata : bool
        Whether to embed metadata in converted files (default: True).
    created_at : datetime
        Configuration creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "file_handling_config"

    id: int | None = Field(default=None, primary_key=True)
    calibre_binaries_dir: str | None = Field(default=None, max_length=1000)
    converter_path: str | None = Field(default=None, max_length=1000)
    kepubify_path: str | None = Field(default=None, max_length=1000)
    unrar_path: str | None = Field(default=None, max_length=1000)
    allowed_upload_formats: str = Field(
        default="epub,mobi,azw,azw3,pdf,txt,rtf,fb2",
        max_length=500,
    )
    support_unicode_filenames: bool = Field(default=False)
    embed_metadata: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class EPUBFixerConfig(SQLModel, table=True):
    """EPUB fixer configuration.

    Attributes
    ----------
    id : int | None
        Primary key identifier. Only one record should exist (singleton).
    enabled : bool
        Master enable/disable flag (default: False).
    backup_enabled : bool
        Whether backups are enabled (default: True).
    backup_directory : str
        Directory for storing backups (default: '/config/processed_books/fixed_originals').
    default_language : str
        Default language for fixes (default: 'en').
    skip_already_fixed : bool
        Skip EPUBs that were already fixed (default: True).
    skip_failed : bool
        Skip EPUBs that previously failed (default: True).
    created_at : datetime
        Configuration creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "epub_fixer_config"

    id: int | None = Field(default=None, primary_key=True)
    enabled: bool = Field(default=False)
    backup_enabled: bool = Field(default=True)
    backup_directory: str = Field(
        default="/config/processed_books/fixed_originals", max_length=1000
    )
    default_language: str = Field(default="en", max_length=10)
    skip_already_fixed: bool = Field(default=True)
    skip_failed: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class LDAPConfig(SQLModel, table=True):
    """LDAP authentication configuration.

    Attributes
    ----------
    id : int | None
        Primary key identifier. Only one record should exist (singleton).
    enabled : bool
        Whether LDAP authentication is enabled (default: False).
    provider_url : str
        LDAP provider URL (default: 'example.org').
    port : int
        LDAP port (default: 389).
    use_ssl : bool
        Whether to use SSL (default: False).
    use_tls : bool
        Whether to use TLS (default: False).
    bind_dn : str | None
        LDAP bind DN for service account.
    bind_password : str | None
        LDAP bind password (should be encrypted at service layer).
    base_dn : str
        Base DN for user search (default: 'dc=example,dc=org').
    user_object_filter : str
        User object filter pattern (default: 'uid=%s').
    group_object_filter : str | None
        Group object filter pattern.
    group_members_field : str
        Field name for group members (default: 'memberUid').
    group_name : str
        LDAP group name for access (default: 'calibreweb').
    ca_cert_path : str | None
        Path to CA certificate file.
    client_cert_path : str | None
        Path to client certificate file.
    client_key_path : str | None
        Path to client private key file.
    is_openldap : bool
        Whether using OpenLDAP (default: True).
    created_at : datetime
        Configuration creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "ldap_config"

    id: int | None = Field(default=None, primary_key=True)
    enabled: bool = Field(default=False)
    provider_url: str = Field(default="example.org", max_length=255)
    port: int = Field(default=389)
    use_ssl: bool = Field(default=False)
    use_tls: bool = Field(default=False)
    bind_dn: str | None = Field(default=None, max_length=500)
    bind_password: str | None = Field(default=None, max_length=500)
    base_dn: str = Field(default="dc=example,dc=org", max_length=500)
    user_object_filter: str = Field(default="uid=%s", max_length=255)
    group_object_filter: str | None = Field(default=None, max_length=500)
    group_members_field: str = Field(default="memberUid", max_length=100)
    group_name: str = Field(default="calibreweb", max_length=255)
    ca_cert_path: str | None = Field(default=None, max_length=1000)
    client_cert_path: str | None = Field(default=None, max_length=1000)
    client_key_path: str | None = Field(default=None, max_length=1000)
    is_openldap: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class IntegrationConfig(SQLModel, table=True):
    """Third-party integration configuration.

    Attributes
    ----------
    id : int | None
        Primary key identifier. Only one record should exist (singleton).
    google_drive_enabled : bool
        Whether Google Drive integration is enabled (default: False).
    google_drive_folder_id : str | None
        Google Drive folder ID.
    google_drive_watch_token : dict[str, object] | None
        Google Drive watch token data (JSON).
    goodreads_enabled : bool
        Whether Goodreads integration is enabled (default: False).
    goodreads_api_key : str | None
        Goodreads API key.
    kobo_sync_enabled : bool
        Whether Kobo sync is enabled (default: False).
    kobo_proxy_enabled : bool
        Whether Kobo proxy is enabled (default: False).
    created_at : datetime
        Configuration creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "integration_config"

    id: int | None = Field(default=None, primary_key=True)
    google_drive_enabled: bool = Field(default=False)
    google_drive_folder_id: str | None = Field(default=None, max_length=255)
    google_drive_watch_token: dict[str, object] | None = Field(
        default=None, sa_column=Column(JSON)
    )
    goodreads_enabled: bool = Field(default=False)
    goodreads_api_key: str | None = Field(default=None, max_length=255)
    kobo_sync_enabled: bool = Field(default=False)
    kobo_proxy_enabled: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class LibraryScanProviderConfig(SQLModel, table=True):
    """Library scan provider configuration settings.

    Stores provider-specific settings for external data sources used during
    library scans. Each provider (e.g., OpenLibrary) can have its own configuration
    for rate limiting, data freshness, and resource limits.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    provider_name : str
        Provider name (e.g., 'openlibrary'). Must be unique.
    rate_limit_delay_seconds : float
        Delay between API requests in seconds (default: 0.5).
        Prevents overwhelming the provider's API.
    max_requests_per_minute : int | None
        Maximum number of requests per minute (None = no limit, default: None).
        Additional throttling beyond rate_limit_delay_seconds.
    max_requests_per_hour : int | None
        Maximum number of requests per hour (None = no limit, default: None).
        Long-term throttling to respect provider limits.
    stale_data_max_age_days : int | None
        Maximum age of cached data in days before considering it stale
        (None = always refresh, default: 30).
        Authors with last_synced_at older than this will be re-queried.
    stale_data_refresh_interval_days : int | None
        Minimum interval between refreshes in days (None = no minimum, default: 7).
        Prevents excessive refreshes even if data is older than max_age.
    max_works_per_author : int | None
        Maximum number of works to fetch per author (None = no limit, default: 1000).
        Prevents excessive pagination for prolific authors.
    enabled : bool
        Whether this provider is enabled for library scans (default: True).
    created_at : datetime
        Configuration creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "library_scan_provider_config"

    id: int | None = Field(default=None, primary_key=True)
    provider_name: str = Field(unique=True, index=True, max_length=100)
    rate_limit_delay_seconds: float = Field(default=0.5, ge=0.0)
    max_requests_per_minute: int | None = Field(default=None, ge=1)
    max_requests_per_hour: int | None = Field(default=None, ge=1)
    stale_data_max_age_days: int | None = Field(default=30, ge=0)
    stale_data_refresh_interval_days: int | None = Field(default=7, ge=0)
    max_works_per_author: int | None = Field(default=1000, ge=1)
    enabled: bool = Field(default=True, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class OpenLibraryDumpConfig(SQLModel, table=True):
    """OpenLibrary data dump configuration settings.

    Manages configuration for downloading and processing OpenLibrary data dumps.
    Controls staleness thresholds, automation, and default processing options.

    Attributes
    ----------
    id : int | None
        Primary key identifier. Only one record should exist (singleton).
    authors_url : str | None
        URL for authors dump file (default: latest OpenLibrary URL).
    works_url : str | None
        URL for works dump file (default: latest OpenLibrary URL).
    editions_url : str | None
        URL for editions dump file (default: latest OpenLibrary URL).
    default_process_authors : bool
        Whether to process authors by default (default: True).
    default_process_works : bool
        Whether to process works by default (default: True).
    default_process_editions : bool
        Whether to process editions by default (default: False).
    staleness_threshold_days : int
        Number of days before data is considered stale (default: 30).
        When data is stale, the "Process files" button is enabled.
    enable_auto_download : bool
        Whether to automatically download dumps when stale (default: False).
    enable_auto_process : bool
        Whether to automatically process dumps after download (default: False).
    auto_check_interval_hours : int
        How often to check for staleness in hours (default: 24).
        Only used when auto-download or auto-process is enabled.
    created_at : datetime
        Configuration creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "openlibrary_dump_config"

    id: int | None = Field(default=None, primary_key=True)
    authors_url: str | None = Field(
        default=None,
        max_length=1000,
        description="URL for OpenLibrary authors dump",
    )
    works_url: str | None = Field(
        default=None,
        max_length=1000,
        description="URL for OpenLibrary works dump",
    )
    editions_url: str | None = Field(
        default=None,
        max_length=1000,
        description="URL for OpenLibrary editions dump",
    )
    default_process_authors: bool = Field(
        default=True,
        description="Process authors dump by default",
    )
    default_process_works: bool = Field(
        default=True,
        description="Process works dump by default",
    )
    default_process_editions: bool = Field(
        default=False,
        description="Process editions dump by default",
    )
    staleness_threshold_days: int = Field(
        default=30,
        ge=1,
        description="Days before data is considered stale",
    )
    enable_auto_download: bool = Field(
        default=False,
        description="Automatically download dumps when stale",
    )
    enable_auto_process: bool = Field(
        default=False,
        description="Automatically process dumps after download",
    )
    auto_check_interval_hours: int = Field(
        default=24,
        ge=1,
        le=168,  # Max 1 week
        description="Hours between automatic staleness checks",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class OpenLibraryDumpState(SQLModel, table=True):
    """OpenLibrary dump state tracking.

    Tracks when dump files were last downloaded and when they were last ingested.
    These are tracked separately because:
    - A dump may be downloaded but not yet ingested
    - A dump may need re-downloading if it's stale, even if recently ingested
    - Download staleness determines when to fetch new dumps
    - Ingestion staleness determines when to process existing dumps

    Staleness checks:
    - Download staleness: Compare `last_downloaded_at` to `staleness_threshold_days`
      from OpenLibraryDumpConfig. If None or older than threshold, download is stale.
    - Ingestion staleness: Compare `last_processed_at` to `staleness_threshold_days`.
      If None or older than threshold, ingestion is stale and "Process files" is enabled.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    dump_type : str
        Type of dump: 'authors', 'works', or 'editions'. Unique per type.
    last_downloaded_at : datetime | None
        Timestamp when dump was last successfully downloaded.
        Used to determine if a new download is needed.
        Updated by download tasks upon successful completion.
    last_processed_at : datetime | None
        Timestamp when dump was last successfully processed/ingested into database.
        Used to determine if processing is needed (enables "Process files" button).
        Updated by ingest tasks upon successful completion.
    file_path : str | None
        Path to the downloaded dump file.
        Set when download completes, cleared if file is deleted.
    file_size_bytes : int | None
        Size of the downloaded file in bytes.
        Used for verification and progress tracking.
    created_at : datetime
        Record creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "openlibrary_dump_states"

    id: int | None = Field(default=None, primary_key=True)
    dump_type: str = Field(
        max_length=50,
        unique=True,
        index=True,
        description="Type of dump: authors, works, or editions",
    )
    last_downloaded_at: datetime | None = Field(
        default=None,
        index=True,
        description="When dump was last downloaded (for download staleness checks)",
    )
    last_processed_at: datetime | None = Field(
        default=None,
        index=True,
        description="When dump was last ingested/processed (for ingestion staleness checks)",
    )
    file_path: str | None = Field(
        default=None,
        max_length=1000,
        description="Path to downloaded dump file",
    )
    file_size_bytes: int | None = Field(
        default=None,
        description="Size of downloaded file in bytes",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

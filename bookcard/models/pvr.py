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

"""PVR (Personal Video Recorder) database models for book tracking and downloading.

This module provides models for tracking books to download, managing indexers
(torrent/usenet sources), download clients, and monitoring download progress.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column, ForeignKey, Index, Integer, Text
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, Relationship, SQLModel

from bookcard.models.config import Library


class IndexerProtocol(StrEnum):
    """Indexer protocol enumeration.

    Attributes
    ----------
    TORRENT : str
        Torrent-based indexer (BitTorrent).
    USENET : str
        Usenet-based indexer (NNTP).
    """

    TORRENT = "torrent"
    USENET = "usenet"


class IndexerType(StrEnum):
    """Indexer type enumeration.

    Attributes
    ----------
    TORZNAB : str
        Torznab API indexer (torrent-based, generic API).
    NEWZNAB : str
        Newznab API indexer (usenet-based, generic API).
    TORRENT_RSS : str
        Generic torrent RSS feed.
    USENET_RSS : str
        Generic usenet RSS feed.
    CUSTOM : str
        Custom indexer implementation with specific API (e.g., BroadcastheNet,
        FileList, HDBits, IPTorrents, Nyaa, TorrentLeech).
    """

    TORZNAB = "torznab"
    NEWZNAB = "newznab"
    TORRENT_RSS = "torrent_rss"
    USENET_RSS = "usenet_rss"
    CUSTOM = "custom"


class DownloadClientType(StrEnum):
    """Download client type enumeration.

    Attributes
    ----------
    QBITTORRENT : str
        qBittorrent client (torrent).
    TRANSMISSION : str
        Transmission client (torrent).
    DELUGE : str
        Deluge client (torrent).
    RTORRENT : str
        rTorrent client (torrent).
    UTORRENT : str
        uTorrent client (torrent).
    VUZE : str
        Vuze client (torrent).
    ARIA2 : str
        Aria2 client (torrent).
    FLOOD : str
        Flood client (torrent).
    HADOUKEN : str
        Hadouken client (torrent).
    FREEBOX_DOWNLOAD : str
        Freebox Download client (torrent).
    DOWNLOAD_STATION : str
        Synology Download Station (supports both torrent and usenet).
    SABNZBD : str
        SABnzbd client (usenet).
    NZBGET : str
        NZBGet client (usenet).
    NZBVORTEX : str
        NZBVortex client (usenet).
    PNEUMATIC : str
        Pneumatic client (usenet).
    TORRENT_BLACKHOLE : str
        Torrent blackhole (writes .torrent files to directory).
    USENET_BLACKHOLE : str
        Usenet blackhole (writes .nzb files to directory).
    """

    # Torrent clients
    QBITTORRENT = "qbittorrent"
    TRANSMISSION = "transmission"
    DELUGE = "deluge"
    RTORRENT = "rtorrent"
    UTORRENT = "utorrent"
    VUZE = "vuze"
    ARIA2 = "aria2"
    FLOOD = "flood"
    HADOUKEN = "hadouken"
    FREEBOX_DOWNLOAD = "freebox_download"
    # Universal clients
    DOWNLOAD_STATION = "download_station"
    # Usenet clients
    SABNZBD = "sabnzbd"
    NZBGET = "nzbget"
    NZBVORTEX = "nzbvortex"
    PNEUMATIC = "pneumatic"
    # Blackhole clients (file-based, no API)
    TORRENT_BLACKHOLE = "torrent_blackhole"
    USENET_BLACKHOLE = "usenet_blackhole"


class ProwlarrConfig(SQLModel, table=True):
    """Prowlarr configuration settings.

    Singleton configuration for Prowlarr integration.
    Prowlarr is an indexer manager/proxy built on the popular *arr stack
    to integrate with various PVR apps.

    Attributes
    ----------
    id : int | None
        Primary key identifier. Only one record should exist (singleton).
    url : str
        Prowlarr server URL (e.g., http://localhost:9696).
    api_key : str | None
        Prowlarr API key.
    enabled : bool
        Whether Prowlarr integration is enabled (default: False).
    sync_categories : list[str] | None
        JSON array of Prowlarr category names to sync (e.g., ["Audio", "Books"]).
    sync_app_profiles : list[int] | None
        JSON array of Prowlarr app profile IDs to sync.
    sync_interval_minutes : int
        Interval in minutes for automatic sync (default: 60).
    created_at : datetime
        Configuration creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "prowlarr_config"

    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(default="http://localhost:9696", max_length=255)
    api_key: str | None = Field(default=None, max_length=500)
    enabled: bool = Field(default=False, index=True)
    sync_categories: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    sync_app_profiles: list[int] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    sync_interval_minutes: int = Field(default=60)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class TrackedBookStatus(StrEnum):
    """Tracked book status enumeration.

    Attributes
    ----------
    WANTED : str
        Book is wanted but not yet searched.
    SEARCHING : str
        Currently searching indexers for the book.
    DOWNLOADING : str
        Book is being downloaded.
    PAUSED : str
        Download is paused.
    STALLED : str
        Download is stalled (no peers/seeds).
    SEEDING : str
        Download completed and is seeding.
    COMPLETED : str
        Book download completed and imported.
    FAILED : str
        Download or import failed.
    IGNORED : str
        Book tracking is ignored (user disabled).
    """

    WANTED = "wanted"
    SEARCHING = "searching"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    STALLED = "stalled"
    SEEDING = "seeding"
    COMPLETED = "completed"
    FAILED = "failed"
    IGNORED = "ignored"


class MonitorMode(StrEnum):
    """Monitor mode for tracked books.

    Attributes
    ----------
    BOOK_ONLY : str
        Monitor only this specific book.
    SERIES : str
        Monitor the series this book belongs to.
    AUTHOR : str
        Monitor all books by this author.
    """

    BOOK_ONLY = "book_only"
    SERIES = "series"
    AUTHOR = "author"


class IndexerStatus(StrEnum):
    """Indexer status enumeration.

    Attributes
    ----------
    HEALTHY : str
        Indexer is healthy and responding.
    DEGRADED : str
        Indexer is responding but with errors.
    UNHEALTHY : str
        Indexer is not responding or has critical errors.
    DISABLED : str
        Indexer is disabled by user.
    UNKNOWN : str
        Indexer status is unknown.
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


class DownloadClientStatus(StrEnum):
    """Download client status enumeration.

    Attributes
    ----------
    HEALTHY : str
        Download client is healthy and responding.
    DEGRADED : str
        Download client is responding but with errors.
    UNHEALTHY : str
        Download client is not responding or has critical errors.
    DISABLED : str
        Download client is disabled by user.
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"


class DownloadItemStatus(StrEnum):
    """Download item status enumeration.

    Attributes
    ----------
    QUEUED : str
        Download is queued in the client.
    DOWNLOADING : str
        Download is in progress.
    PAUSED : str
        Download is paused.
    STALLED : str
        Download is stalled.
    SEEDING : str
        Download is seeding.
    COMPLETED : str
        Download completed successfully.
    FAILED : str
        Download failed.
    REMOVED : str
        Download was removed from client.
    """

    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    STALLED = "stalled"
    SEEDING = "seeding"
    COMPLETED = "completed"
    FAILED = "failed"
    REMOVED = "removed"


class RejectionType(StrEnum):
    """Type of rejection for download decisions.

    Attributes
    ----------
    PERMANENT : str
        Permanent rejection - release will never be accepted.
    TEMPORARY : str
        Temporary rejection - release may be accepted later.
    """

    PERMANENT = "permanent"
    TEMPORARY = "temporary"


class DownloadRejectionReason(StrEnum):
    """Reasons for rejecting a download.

    Attributes
    ----------
    UNKNOWN : str
        Unknown reason.
    WRONG_FORMAT : str
        Release format is not in preferred formats.
    LOW_QUALITY : str
        Release quality is below minimum threshold.
    BELOW_MINIMUM_SIZE : str
        Release size is below minimum required size.
    ABOVE_MAXIMUM_SIZE : str
        Release size exceeds maximum allowed size.
    INSUFFICIENT_SEEDERS : str
        Torrent has insufficient seeders.
    TOO_OLD : str
        Release is too old (exceeds maximum age).
    TOO_NEW : str
        Release is too new (below minimum age delay).
    EXCLUDED_KEYWORD : str
        Release contains excluded keywords.
    MISSING_REQUIRED_KEYWORD : str
        Release is missing required keywords.
    INDEXER_DISABLED : str
        Indexer is disabled.
    BLOCKLISTED : str
        Release is blocklisted.
    ALREADY_DOWNLOADED : str
        Release has already been downloaded.
    INVALID_URL : str
        Download URL is invalid or missing.
    MISSING_METADATA : str
        Release is missing required metadata (title, author, etc.).
    """

    UNKNOWN = "unknown"
    WRONG_FORMAT = "wrong_format"
    LOW_QUALITY = "low_quality"
    BELOW_MINIMUM_SIZE = "below_minimum_size"
    ABOVE_MAXIMUM_SIZE = "above_maximum_size"
    INSUFFICIENT_SEEDERS = "insufficient_seeders"
    TOO_OLD = "too_old"
    TOO_NEW = "too_new"
    EXCLUDED_KEYWORD = "excluded_keyword"
    MISSING_REQUIRED_KEYWORD = "missing_required_keyword"
    INDEXER_DISABLED = "indexer_disabled"
    BLOCKLISTED = "blocklisted"
    ALREADY_DOWNLOADED = "already_downloaded"
    INVALID_URL = "invalid_url"
    MISSING_METADATA = "missing_metadata"


class TrackedBookFile(SQLModel, table=True):
    """File associated with a tracked book.

    Tracks files that were downloaded/imported for a tracked book,
    including main book files, extra formats, covers, and other artifacts.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    tracked_book_id : int
        Foreign key to tracked book.
    path : str
        Absolute path to the file.
    filename : str
        Name of the file.
    size_bytes : int
        Size of the file in bytes.
    file_type : str
        Type of file (e.g., 'main', 'format', 'cover', 'playlist', 'artifact').
    created_at : datetime
        Timestamp when file was recorded.
    """

    __tablename__ = "tracked_book_files"

    id: int | None = Field(default=None, primary_key=True)
    tracked_book_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("tracked_books.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    path: str = Field(max_length=2000)
    filename: str = Field(max_length=500)
    size_bytes: int = Field(default=0)
    file_type: str = Field(default="artifact", max_length=50)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )

    # Relationships
    tracked_book: "TrackedBook" = Relationship(back_populates="files")


class TrackedBook(SQLModel, table=True):
    """Tracked book model for books to be downloaded.

    Tracks books that users want to download, linking to metadata search
    results and managing the download lifecycle from search to import.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    title : str
        Book title to track.
    author : str
        Author name to track.
    isbn : str | None
        Optional ISBN for more precise matching.
    library_id : int | None
        Foreign key to target library for import (None uses active library).
    metadata_source_id : str | None
        Source ID of the metadata provider (e.g., 'google', 'openlibrary').
    metadata_external_id : str | None
        External ID from the metadata provider.
    status : TrackedBookStatus
        Current tracking status.
    auto_search_enabled : bool
        Whether to automatically search for this book (default True).
    auto_download_enabled : bool
        Whether to automatically download when found (default False).
    preferred_formats : list[str] | None
        JSON array of preferred formats (e.g., ['epub', 'pdf']).
    last_searched_at : datetime | None
        Timestamp of last search attempt.
    last_downloaded_at : datetime | None
        Timestamp of last successful download.
    matched_book_id : int | None
        Calibre book ID if exact match found in library (no FK constraint).
    matched_library_id : int | None
        Library ID where match was found.
    error_message : str | None
        Error message if tracking/download failed.
    created_at : datetime
        Timestamp when book was added to tracking.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "tracked_books"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=500, index=True)
    author: str = Field(max_length=500, index=True)
    isbn: str | None = Field(default=None, max_length=20, index=True)
    library_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("libraries.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )
    metadata_source_id: str | None = Field(default=None, max_length=100)
    metadata_external_id: str | None = Field(default=None, max_length=255)
    cover_url: str | None = Field(default=None, max_length=2000)
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    publisher: str | None = Field(default=None, max_length=500)
    published_date: str | None = Field(default=None, max_length=50)
    series_name: str | None = Field(default=None, max_length=500, index=True)
    series_index: float | None = Field(default=None)
    rating: float | None = Field(default=None)
    tags: list[str] | None = Field(default=None, sa_column=Column(JSON, nullable=True))  # type: ignore[call-overload]
    status: TrackedBookStatus = Field(
        default=TrackedBookStatus.WANTED,
        sa_column=Column(
            SQLEnum(TrackedBookStatus, native_enum=False), nullable=False, index=True
        ),  # type: ignore[call-overload]
    )
    monitor_mode: MonitorMode = Field(
        default=MonitorMode.BOOK_ONLY,
        sa_column=Column(
            SQLEnum(MonitorMode, native_enum=False),
            nullable=False,
            default=MonitorMode.BOOK_ONLY,
        ),  # type: ignore[call-overload]
    )
    auto_search_enabled: bool = Field(default=True, index=True)
    auto_download_enabled: bool = Field(default=False)
    preferred_formats: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
        description="Preferred file formats for this book (e.g., ['epub', 'pdf'])",
    )
    exclude_keywords: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
        description="Keywords to exclude from release title/description for this book",
    )
    require_keywords: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
        description="Keywords that must appear in release title/description for this book",
    )
    require_title_match: bool = Field(
        default=True,
        description="Whether title must match search criteria for this book",
    )
    require_author_match: bool = Field(
        default=True,
        description="Whether author must match search criteria for this book",
    )
    require_isbn_match: bool = Field(
        default=False, description="Whether ISBN must match if provided for this book"
    )
    last_searched_at: datetime | None = Field(default=None, index=True)
    last_downloaded_at: datetime | None = Field(default=None)
    matched_book_id: int | None = Field(default=None, index=True)
    matched_library_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("libraries.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )
    error_message: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Relationships
    library: Library | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[TrackedBook.library_id]"}
    )
    matched_library: Library | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[TrackedBook.matched_library_id]"}
    )
    download_items: list["DownloadItem"] = Relationship(
        back_populates="tracked_book",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    files: list["TrackedBookFile"] = Relationship(
        back_populates="tracked_book",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    __table_args__ = (
        Index("idx_tracked_books_title_author", "title", "author"),
        Index("idx_tracked_books_status_created", "status", "created_at"),
        Index("idx_tracked_books_auto_search", "auto_search_enabled", "status"),
    )


class IndexerDefinition(SQLModel, table=True):
    """Indexer definition model for indexer configuration.

    Stores configuration for indexers (torrent/usenet sources) that can
    be searched for books. Supports multiple indexer types and protocols.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    name : str
        User-friendly name for the indexer.
    indexer_type : IndexerType
        Type of indexer (Torznab, Newznab, RSS, etc.).
    protocol : IndexerProtocol
        Protocol used (Torrent or Usenet).
    base_url : str
        Base URL of the indexer API.
    api_key : str | None
        API key for authentication (encrypted in production).
    enabled : bool
        Whether this indexer is enabled (default True).
    priority : int
        Priority for search order (lower = higher priority, default 0).
    timeout_seconds : int
        Request timeout in seconds (default 30).
    retry_count : int
        Number of retries on failure (default 3).
    categories : list[int] | None
        JSON array of category IDs to search (None = all categories).
    additional_settings : dict | None
        JSON object for indexer-specific settings.
    status : IndexerStatus
        Current health status of the indexer.
    last_checked_at : datetime | None
        Timestamp of last health check.
    last_successful_query_at : datetime | None
        Timestamp of last successful query.
    error_count : int
        Number of consecutive errors (default 0).
    error_message : str | None
        Last error message if status is unhealthy.
    created_at : datetime
        Timestamp when indexer was added.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "indexer_definitions"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    indexer_type: IndexerType = Field(
        sa_column=Column(
            SQLEnum(IndexerType, native_enum=False), nullable=False, index=True
        ),  # type: ignore[call-overload]
    )
    protocol: IndexerProtocol = Field(
        sa_column=Column(
            SQLEnum(IndexerProtocol, native_enum=False), nullable=False, index=True
        ),  # type: ignore[call-overload]
    )
    base_url: str = Field(max_length=1000)
    api_key: str | None = Field(default=None, max_length=500)
    enabled: bool = Field(default=True, index=True)
    priority: int = Field(default=0, index=True)
    timeout_seconds: int = Field(default=30)
    retry_count: int = Field(default=3)
    categories: list[int] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    additional_settings: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    status: IndexerStatus = Field(
        default=IndexerStatus.UNHEALTHY,
        sa_column=Column(
            SQLEnum(IndexerStatus, native_enum=False), nullable=False, index=True
        ),  # type: ignore[call-overload]
    )
    last_checked_at: datetime | None = Field(default=None)
    last_successful_query_at: datetime | None = Field(default=None, index=True)
    error_count: int = Field(default=0)
    error_message: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    __table_args__ = (
        Index("idx_indexers_enabled_priority", "enabled", "priority"),
        Index("idx_indexers_status_checked", "status", "last_checked_at"),
    )


class DownloadClientDefinition(SQLModel, table=True):
    """Download client definition model for download client configuration.

    Stores configuration for download clients (qBittorrent, Transmission, etc.)
    that handle actual downloads of torrents or usenet files.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    name : str
        User-friendly name for the download client.
    client_type : DownloadClientType
        Type of download client.
    host : str
        Hostname or IP address of the client.
    port : int
        Port number for the client API.
    username : str | None
        Username for authentication.
    password : str | None
        Password for authentication (encrypted in production).
    use_ssl : bool
        Whether to use SSL/TLS (default False).
    enabled : bool
        Whether this client is enabled (default True).
    priority : int
        Priority for download assignment (lower = higher priority, default 0).
    timeout_seconds : int
        Request timeout in seconds (default 30).
    category : str | None
        Category/tag to assign to downloads (e.g., 'bookcard').
    download_path : str | None
        Path where client should save downloads.
    additional_settings : dict | None
        JSON object for client-specific settings.
    status : DownloadClientStatus
        Current health status of the client.
    last_checked_at : datetime | None
        Timestamp of last health check.
    last_successful_connection_at : datetime | None
        Timestamp of last successful connection.
    error_count : int
        Number of consecutive errors (default 0).
    error_message : str | None
        Last error message if status is unhealthy.
    created_at : datetime
        Timestamp when client was added.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "download_client_definitions"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    client_type: DownloadClientType = Field(
        sa_column=Column(
            SQLEnum(DownloadClientType, native_enum=False), nullable=False, index=True
        ),  # type: ignore[call-overload]
    )
    host: str = Field(max_length=255)
    port: int = Field(default=8080)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=500)
    use_ssl: bool = Field(default=False)
    enabled: bool = Field(default=True, index=True)
    priority: int = Field(default=0, index=True)
    timeout_seconds: int = Field(default=30)
    category: str | None = Field(default=None, max_length=100)
    download_path: str | None = Field(default=None, max_length=1000)
    additional_settings: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    status: DownloadClientStatus = Field(
        default=DownloadClientStatus.UNHEALTHY,
        sa_column=Column(
            SQLEnum(DownloadClientStatus, native_enum=False),
            nullable=False,
            index=True,
        ),  # type: ignore[call-overload]
    )
    last_checked_at: datetime | None = Field(default=None)
    last_successful_connection_at: datetime | None = Field(default=None, index=True)
    error_count: int = Field(default=0)
    error_message: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Relationships
    download_items: list["DownloadItem"] = Relationship(back_populates="client")

    __table_args__ = (
        Index("idx_download_clients_enabled_priority", "enabled", "priority"),
        Index("idx_download_clients_status_checked", "status", "last_checked_at"),
    )


class DownloadItem(SQLModel, table=True):
    """Download item model for tracking active downloads.

    Tracks individual downloads from indexers, linking them to tracked books
    and download clients, and monitoring progress until completion.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    tracked_book_id : int
        Foreign key to tracked book.
    download_client_id : int
        Foreign key to download client handling this download.
    indexer_id : int | None
        Foreign key to indexer that provided this release.
    client_item_id : str
        Unique identifier for the item in the download client.
    title : str
        Title of the release being downloaded.
    download_url : str
        URL or magnet link for the download.
    file_path : str | None
        Path to downloaded file(s) when complete.
    status : DownloadItemStatus
        Current download status.
    progress : float
        Download progress (0.0 to 1.0).
    size_bytes : int | None
        Total size of download in bytes.
    downloaded_bytes : int | None
        Bytes downloaded so far.
    download_speed_bytes_per_sec : float | None
        Current download speed.
    eta_seconds : int | None
        Estimated time to completion in seconds.
    quality : str | None
        Quality/format of the release (e.g., 'epub', 'pdf').
    release_info : dict[str, Any] | None
        JSON object with additional release metadata from indexer.
    error_message : str | None
        Error message if download failed.
    started_at : datetime
        Timestamp when download was initiated.
    completed_at : datetime | None
        Timestamp when download completed.
    created_at : datetime
        Timestamp when download item was created.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "download_items"

    id: int | None = Field(default=None, primary_key=True)
    tracked_book_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("tracked_books.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    download_client_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("download_client_definitions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    indexer_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("indexer_definitions.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )
    client_item_id: str = Field(max_length=255, index=True)
    guid: str | None = Field(
        default=None,
        max_length=255,
        index=True,
        description="Unique identifier from indexer",
    )
    title: str = Field(max_length=500, index=True)
    download_url: str = Field(max_length=2000)
    file_path: str | None = Field(default=None, max_length=2000)
    status: DownloadItemStatus = Field(
        default=DownloadItemStatus.QUEUED,
        sa_column=Column(
            SQLEnum(DownloadItemStatus, native_enum=False), nullable=False, index=True
        ),  # type: ignore[call-overload]
    )
    progress: float = Field(default=0.0, ge=0.0, le=1.0, index=True)
    size_bytes: int | None = Field(default=None)
    downloaded_bytes: int | None = Field(default=None)
    download_speed_bytes_per_sec: float | None = Field(default=None)
    eta_seconds: int | None = Field(default=None)
    quality: str | None = Field(default=None, max_length=50, index=True)
    release_info: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    error_message: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    completed_at: datetime | None = Field(default=None, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Relationships
    tracked_book: TrackedBook = Relationship(back_populates="download_items")
    client: DownloadClientDefinition = Relationship(back_populates="download_items")
    indexer: IndexerDefinition | None = Relationship()

    __table_args__ = (
        Index("idx_download_items_tracked_book_status", "tracked_book_id", "status"),
        Index("idx_download_items_status_created", "status", "created_at"),
        Index(
            "idx_download_items_client_item_id", "download_client_id", "client_item_id"
        ),
    )


class DownloadDecisionDefaults(SQLModel, table=True):
    """System-wide default preferences for download decisions.

    Stores global defaults that apply to all tracked books unless overridden
    by per-book preferences in TrackedBook.

    Attributes
    ----------
    id : int | None
        Primary key identifier. Only one record should exist (singleton).
    preferred_formats : list[str] | None
        Default preferred file formats (e.g., ['epub', 'pdf', 'mobi']).
    min_size_bytes : int | None
        Default minimum file size in bytes.
    max_size_bytes : int | None
        Default maximum file size in bytes.
    min_seeders : int | None
        Default minimum number of seeders for torrents.
    min_leechers : int | None
        Default minimum number of leechers for torrents.
    max_age_days : int | None
        Default maximum age in days for releases.
    min_age_days : int | None
        Default minimum age in days (delay) for releases.
    exclude_keywords : list[str] | None
        Default keywords to exclude from release title/description.
    require_keywords : list[str] | None
        Default keywords that must appear in release title/description.
    require_title_match : bool
        Default whether title must match search criteria.
    require_author_match : bool
        Default whether author must match search criteria.
    require_isbn_match : bool
        Default whether ISBN must match if provided.
    created_at : datetime
        Timestamp when defaults were created.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "download_decision_defaults"

    id: int | None = Field(default=None, primary_key=True)
    preferred_formats: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    min_size_bytes: int | None = Field(default=None)
    max_size_bytes: int | None = Field(default=None)
    min_seeders: int | None = Field(default=None)
    min_leechers: int | None = Field(default=None)
    max_age_days: int | None = Field(default=None)
    min_age_days: int | None = Field(default=None)
    exclude_keywords: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    require_keywords: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),  # type: ignore[call-overload]
    )
    require_title_match: bool = Field(default=True)
    require_author_match: bool = Field(default=True)
    require_isbn_match: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class DownloadBlocklist(SQLModel, table=True):
    """Blocklist for download URLs.

    Tracks download URLs that should be rejected, such as:
    - URLs that have already been downloaded
    - URLs that were manually rejected
    - URLs that failed to download multiple times

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    download_url : str
        Blocklisted download URL (unique).
    reason : str | None
        Reason for blocklisting (e.g., 'already_downloaded', 'manual_reject').
    tracked_book_id : int | None
        Foreign key to tracked book if blocklist is book-specific.
    indexer_id : int | None
        Foreign key to indexer that provided this release.
    created_at : datetime
        Timestamp when URL was blocklisted.
    """

    __tablename__ = "download_blocklist"

    id: int | None = Field(default=None, primary_key=True)
    download_url: str = Field(max_length=2000, unique=True, index=True)
    reason: str | None = Field(default=None, max_length=255)
    tracked_book_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("tracked_books.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )
    indexer_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("indexer_definitions.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )

    # Relationships
    tracked_book: TrackedBook | None = Relationship()
    indexer: IndexerDefinition | None = Relationship()

    __table_args__ = (
        Index("idx_blocklist_tracked_book", "tracked_book_id"),
        Index("idx_blocklist_indexer", "indexer_id"),
        Index("idx_blocklist_created", "created_at"),
    )


class DownloadQueue(SQLModel):
    """
    Represents the queue of active downloads.

    Attributes
    ----------
    items : list[DownloadItem]
        List of active download items.
    total_count : int
        Total number of items in queue.
    """

    items: list[DownloadItem]
    total_count: int


class DownloadHistory(SQLModel):
    """
    Represents the history of completed/failed downloads.

    Attributes
    ----------
    items : list[DownloadItem]
        List of historical download items.
    total_count : int
        Total number of items in history.
    """

    items: list[DownloadItem]
    total_count: int

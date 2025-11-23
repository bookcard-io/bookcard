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

"""API schemas organized by domain.

This package contains Pydantic models for API request/response validation,
organized by domain to follow Single Responsibility Principle.

Modules:
    auth: User authentication and authorization schemas
    books: Book management and search schemas
    libraries: Library management schemas
    metadata: Metadata search schemas and events
"""

from __future__ import annotations

# Re-export all schemas for backward compatibility
from fundamental.api.schemas.auth import (
    AdminUserCreate,
    AdminUserUpdate,
    EmailServerConfigRead,
    EmailServerConfigUpdate,
    EReaderDeviceCreate,
    EReaderDeviceRead,
    EReaderDeviceUpdate,
    InviteValidationResponse,
    LoginRequest,
    LoginResponse,
    OpenLibraryDumpConfigRead,
    OpenLibraryDumpConfigUpdate,
    PasswordChangeRequest,
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
    ProfilePictureUpdateRequest,
    ProfileRead,
    ProfileUpdate,
    RoleCreate,
    RolePermissionGrant,
    RolePermissionRead,
    RolePermissionUpdate,
    RoleRead,
    RoleUpdate,
    SettingRead,
    SettingsRead,
    SettingUpdate,
    TokenResponse,
    UserCreate,
    UserRead,
    UserRoleAssign,
)
from fundamental.api.schemas.books import (
    BookBatchUploadResponse,
    BookDeleteRequest,
    BookFilterRequest,
    BookListResponse,
    BookRead,
    BookSendRequest,
    BookUpdate,
    BookUploadResponse,
    CoverFromUrlRequest,
    CoverFromUrlResponse,
    FilterSuggestionsResponse,
    SearchSuggestionItem,
    SearchSuggestionsResponse,
)
from fundamental.api.schemas.libraries import (
    LibraryCreate,
    LibraryRead,
    LibraryStats,
    LibraryUpdate,
)
from fundamental.api.schemas.metadata import (
    MetadataProviderCompletedEvent,
    MetadataProviderFailedEvent,
    MetadataProviderProgressEvent,
    MetadataProvidersResponse,
    MetadataProviderStartedEvent,
    MetadataSearchCompletedEvent,
    MetadataSearchEvent,
    MetadataSearchProgressEvent,
    MetadataSearchRequest,
    MetadataSearchResponse,
    MetadataSearchStartedEvent,
)
from fundamental.api.schemas.reading import (
    ReadingHistoryResponse,
    ReadingProgressCreate,
    ReadingProgressRead,
    ReadingSessionCreate,
    ReadingSessionEnd,
    ReadingSessionRead,
    ReadingSessionsListResponse,
    ReadStatusRead,
    ReadStatusUpdate,
    RecentReadsResponse,
)
from fundamental.api.schemas.shelves import (
    BookShelfLinkRead,
    ShelfCreate,
    ShelfListResponse,
    ShelfRead,
    ShelfReorderRequest,
    ShelfUpdate,
)
from fundamental.api.schemas.tasks import (
    TaskCancelResponse,
    TaskListResponse,
    TaskRead,
    TaskStatisticsRead,
    TaskTypesResponse,
)

__all__ = [
    # Auth schemas
    "AdminUserCreate",
    "AdminUserUpdate",
    # Book schemas
    "BookBatchUploadResponse",
    "BookDeleteRequest",
    "BookFilterRequest",
    "BookListResponse",
    "BookRead",
    "BookSendRequest",
    # Shelf schemas
    "BookShelfLinkRead",
    "BookUpdate",
    "BookUploadResponse",
    "CoverFromUrlRequest",
    "CoverFromUrlResponse",
    "EReaderDeviceCreate",
    "EReaderDeviceRead",
    "EReaderDeviceUpdate",
    "EmailServerConfigRead",
    "EmailServerConfigUpdate",
    "FilterSuggestionsResponse",
    "InviteValidationResponse",
    # Library schemas
    "LibraryCreate",
    "LibraryRead",
    "LibraryStats",
    "LibraryUpdate",
    "LoginRequest",
    "LoginResponse",
    # Metadata schemas
    "MetadataProviderCompletedEvent",
    "MetadataProviderFailedEvent",
    "MetadataProviderProgressEvent",
    "MetadataProviderStartedEvent",
    "MetadataProvidersResponse",
    "MetadataSearchCompletedEvent",
    "MetadataSearchEvent",
    "MetadataSearchProgressEvent",
    "MetadataSearchRequest",
    "MetadataSearchResponse",
    "MetadataSearchStartedEvent",
    "OpenLibraryDumpConfigRead",
    "OpenLibraryDumpConfigUpdate",
    "PasswordChangeRequest",
    "PermissionCreate",
    "PermissionRead",
    "PermissionUpdate",
    "ProfilePictureUpdateRequest",
    "ProfileRead",
    "ProfileUpdate",
    "ReadStatusRead",
    "ReadStatusUpdate",
    "ReadingHistoryResponse",
    "ReadingProgressCreate",
    "ReadingProgressRead",
    "ReadingSessionCreate",
    "ReadingSessionEnd",
    "ReadingSessionRead",
    "ReadingSessionsListResponse",
    "RecentReadsResponse",
    "RoleCreate",
    "RolePermissionGrant",
    "RolePermissionRead",
    "RolePermissionUpdate",
    "RoleRead",
    "RoleUpdate",
    "SearchSuggestionItem",
    "SearchSuggestionsResponse",
    "SettingRead",
    "SettingUpdate",
    "SettingsRead",
    "ShelfCreate",
    "ShelfListResponse",
    "ShelfRead",
    "ShelfReorderRequest",
    "ShelfUpdate",
    "TaskCancelResponse",
    "TaskListResponse",
    "TaskRead",
    "TaskStatisticsRead",
    "TaskTypesResponse",
    "TokenResponse",
    "UserCreate",
    "UserRead",
    "UserRoleAssign",
]

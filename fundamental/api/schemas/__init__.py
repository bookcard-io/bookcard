# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
    EReaderDeviceCreate,
    EReaderDeviceRead,
    EReaderDeviceUpdate,
    InviteValidationResponse,
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    PermissionRead,
    ProfilePictureUpdateRequest,
    ProfileRead,
    RoleCreate,
    RolePermissionGrant,
    RoleRead,
    TokenResponse,
    UserCreate,
    UserRead,
    UserRoleAssign,
)
from fundamental.api.schemas.books import (
    BookFilterRequest,
    BookListResponse,
    BookRead,
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

__all__ = [
    # Auth schemas
    "AdminUserCreate",
    "AdminUserUpdate",
    # Book schemas
    "BookFilterRequest",
    "BookListResponse",
    "BookRead",
    "BookUpdate",
    "BookUploadResponse",
    "CoverFromUrlRequest",
    "CoverFromUrlResponse",
    "EReaderDeviceCreate",
    "EReaderDeviceRead",
    "EReaderDeviceUpdate",
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
    "PasswordChangeRequest",
    "PermissionRead",
    "ProfilePictureUpdateRequest",
    "ProfileRead",
    "RoleCreate",
    "RolePermissionGrant",
    "RoleRead",
    "SearchSuggestionItem",
    "SearchSuggestionsResponse",
    "TokenResponse",
    "UserCreate",
    "UserRead",
    "UserRoleAssign",
]

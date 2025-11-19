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

"""Database models for Fundamental."""

from fundamental.models.auth import (
    EBookFormat,
    EReaderDevice,
    Permission,
    RefreshToken,
    Role,
    RolePermission,
    User,
    UserRole,
    UserSetting,
)
from fundamental.models.author_metadata import (
    AuthorAlternateName,
    AuthorLink,
    AuthorMapping,
    AuthorMetadata,
    AuthorPhoto,
    AuthorRemoteId,
    AuthorSimilarity,
    AuthorWork,
    WorkSubject,
)
from fundamental.models.config import (
    BasicConfig,
    ContentRestrictionsConfig,
    EmailServerConfig,
    EmailServerType,
    FileHandlingConfig,
    IntegrationConfig,
    LDAPConfig,
    Library,
    LogLevel,
    ScheduledTasksConfig,
    SecurityConfig,
    UIConfig,
)
from fundamental.models.core import (
    Author,
    Book,
    BookAuthorLink,
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
    Comment,
    Identifier,
    Language,
    Publisher,
    Rating,
    Series,
    Tag,
)
from fundamental.models.library_scanning import LibraryScanState
from fundamental.models.media import ConversionOptions, Data
from fundamental.models.reading import (
    Annotation,
    AnnotationDirtied,
    LastReadPosition,
)
from fundamental.models.shelves import (
    BookShelfLink,
    Shelf,
    ShelfArchive,
)
from fundamental.models.system import (
    BookPluginData,
    CustomColumn,
    Feed,
    LibraryId,
    MetadataDirtied,
    Preference,
)
from fundamental.models.tasks import (
    Task,
    TaskStatistics,
    TaskStatus,
    TaskType,
)

__all__ = [
    "Annotation",
    "AnnotationDirtied",
    "Author",
    "AuthorAlternateName",
    "AuthorLink",
    "AuthorMapping",
    "AuthorMetadata",
    "AuthorPhoto",
    "AuthorRemoteId",
    "AuthorSimilarity",
    "AuthorWork",
    "BasicConfig",
    "Book",
    "BookAuthorLink",
    "BookLanguageLink",
    "BookPluginData",
    "BookPublisherLink",
    "BookRatingLink",
    "BookSeriesLink",
    "BookShelfLink",
    "BookTagLink",
    "Comment",
    "ContentRestrictionsConfig",
    "ConversionOptions",
    "CustomColumn",
    "Data",
    "EBookFormat",
    "EReaderDevice",
    "EmailServerConfig",
    "EmailServerType",
    "Feed",
    "FileHandlingConfig",
    "Identifier",
    "IntegrationConfig",
    "LDAPConfig",
    "Language",
    "LastReadPosition",
    "Library",
    "LibraryId",
    "LibraryScanState",
    "LogLevel",
    "MetadataDirtied",
    "Permission",
    "Preference",
    "Publisher",
    "Rating",
    "RefreshToken",
    "Role",
    "RolePermission",
    "ScheduledTasksConfig",
    "SecurityConfig",
    "Series",
    "Shelf",
    "ShelfArchive",
    "Tag",
    "Task",
    "TaskStatistics",
    "TaskStatus",
    "TaskType",
    "UIConfig",
    "User",
    "UserRole",
    "UserSetting",
    "WorkSubject",
]

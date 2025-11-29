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
    EPUBFixerConfig,
    FileHandlingConfig,
    IntegrationConfig,
    LDAPConfig,
    Library,
    LogLevel,
    ScheduledTasksConfig,
    SecurityConfig,
    UIConfig,
)
from fundamental.models.conversion import (
    BookConversion,
    ConversionMethod,
    ConversionStatus,
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
from fundamental.models.epub_fixer import (
    EPUBFix,
    EPUBFixRun,
    EPUBFixType,
)
from fundamental.models.ingest import (
    IngestAudit,
    IngestConfig,
    IngestHistory,
    IngestRetry,
    IngestStatus,
)
from fundamental.models.library_scanning import LibraryScanState
from fundamental.models.media import ConversionOptions, Data
from fundamental.models.metadata_enforcement import (
    EnforcementStatus,
    MetadataEnforcementOperation,
)
from fundamental.models.openlibrary import (
    OpenLibraryAuthor,
    OpenLibraryAuthorWork,
    OpenLibraryEdition,
    OpenLibraryEditionIsbn,
    OpenLibraryWork,
)
from fundamental.models.reading import (
    Annotation,
    AnnotationDirtied,
    ReadingProgress,
    ReadingSession,
    ReadStatus,
    ReadStatusEnum,
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
    "BookConversion",
    "BookLanguageLink",
    "BookPluginData",
    "BookPublisherLink",
    "BookRatingLink",
    "BookSeriesLink",
    "BookShelfLink",
    "BookTagLink",
    "Comment",
    "ContentRestrictionsConfig",
    "ConversionMethod",
    "ConversionOptions",
    "ConversionStatus",
    "CustomColumn",
    "Data",
    "EBookFormat",
    "EPUBFix",
    "EPUBFixRun",
    "EPUBFixType",
    "EPUBFixerConfig",
    "EReaderDevice",
    "EmailServerConfig",
    "EmailServerType",
    "EnforcementStatus",
    "Feed",
    "FileHandlingConfig",
    "Identifier",
    "IngestAudit",
    "IngestConfig",
    "IngestHistory",
    "IngestRetry",
    "IngestStatus",
    "IntegrationConfig",
    "LDAPConfig",
    "Language",
    "Library",
    "LibraryId",
    "LibraryScanState",
    "LogLevel",
    "MetadataDirtied",
    "MetadataEnforcementOperation",
    "OpenLibraryAuthor",
    "OpenLibraryAuthorWork",
    "OpenLibraryEdition",
    "OpenLibraryEditionIsbn",
    "OpenLibraryWork",
    "Permission",
    "Preference",
    "Publisher",
    "Rating",
    "ReadStatus",
    "ReadStatusEnum",
    "ReadingProgress",
    "ReadingSession",
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

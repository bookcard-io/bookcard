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

"""PVR Import helper modules."""

from bookcard.services.pvr.importing.book_matching import BookMatchingService
from bookcard.services.pvr.importing.file_preparation import FilePreparationService
from bookcard.services.pvr.importing.file_selection import (
    FileSelectionStrategy,
    PreferenceBasedSelector,
)
from bookcard.services.pvr.importing.models import (
    BookMetadata,
    FileType,
    MatchScore,
    MatchScoreThresholds,
)
from bookcard.services.pvr.importing.path_mapping import PathMappingService
from bookcard.services.pvr.importing.protocols import (
    BookServiceFactory,
    BookServiceProtocol,
    FileDiscoveryProtocol,
    IngestServiceProtocol,
    MetricsRecorder,
    SessionFactory,
    TrackedBookServiceProtocol,
)
from bookcard.services.pvr.importing.results import (
    ImportBatchResult,
    ImportResult,
    ImportStatus,
)

__all__ = [
    "BookMatchingService",
    "BookMetadata",
    "BookServiceFactory",
    "BookServiceProtocol",
    "FileDiscoveryProtocol",
    "FilePreparationService",
    "FileSelectionStrategy",
    "FileType",
    "ImportBatchResult",
    "ImportResult",
    "ImportStatus",
    "IngestServiceProtocol",
    "MatchScore",
    "MatchScoreThresholds",
    "MetricsRecorder",
    "PathMappingService",
    "PreferenceBasedSelector",
    "SessionFactory",
    "TrackedBookServiceProtocol",
]

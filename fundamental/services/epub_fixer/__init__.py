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

"""EPUB fixer service module.

Provides SOLID-compliant EPUB fixing functionality with full audit trail.
"""

from fundamental.services.epub_fixer.config import EPUBFixerSettings
from fundamental.services.epub_fixer.core import (
    EPUBContents,
    EPUBReader,
    EPUBWriter,
    FixResult,
)
from fundamental.services.epub_fixer.core.fixes import (
    BodyIdLinkFix,
    EncodingFix,
    EPUBFix,
    LanguageFix,
    StrayImageFix,
)
from fundamental.services.epub_fixer.orchestrator import EPUBFixerOrchestrator
from fundamental.services.epub_fixer.services import (
    BackupService,
    EPUBScanner,
    FixResultRecorder,
    IBackupService,
    LibraryLocator,
    NullBackupService,
)
from fundamental.services.epub_fixer.utils import FileTypes, OPFLocator

__all__ = [
    "BackupService",
    "BodyIdLinkFix",
    "EPUBContents",
    "EPUBFix",
    "EPUBFixerOrchestrator",
    "EPUBFixerSettings",
    "EPUBReader",
    "EPUBScanner",
    "EPUBWriter",
    "EncodingFix",
    "FileTypes",
    "FixResult",
    "FixResultRecorder",
    "IBackupService",
    "LanguageFix",
    "LibraryLocator",
    "NullBackupService",
    "OPFLocator",
    "StrayImageFix",
]

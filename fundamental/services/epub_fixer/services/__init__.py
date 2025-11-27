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

"""Service layer for EPUB fixer.

Separates concerns: backup, library location, persistence, scanning.
"""

from fundamental.services.epub_fixer.services.backup import (
    BackupService,
    IBackupService,
    NullBackupService,
)
from fundamental.services.epub_fixer.services.library import LibraryLocator
from fundamental.services.epub_fixer.services.persistence import FixResultRecorder
from fundamental.services.epub_fixer.services.scanner import EPUBScanner

__all__ = [
    "BackupService",
    "EPUBScanner",
    "FixResultRecorder",
    "IBackupService",
    "LibraryLocator",
    "NullBackupService",
]

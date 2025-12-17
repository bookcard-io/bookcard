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

"""Tests for EPUB fixer module __init__.py imports."""


def test_epub_fixer_init_imports() -> None:
    """Test that all exports from __init__.py can be imported."""
    from bookcard.services.epub_fixer import (
        BackupService,
        BodyIdLinkFix,
        EncodingFix,
        EPUBContents,
        EPUBFix,
        EPUBFixerOrchestrator,
        EPUBFixerSettings,
        EPUBReader,
        EPUBScanner,
        EPUBWriter,
        FileTypes,
        FixResult,
        FixResultRecorder,
        IBackupService,
        LanguageFix,
        LibraryLocator,
        NullBackupService,
        OPFLocator,
        StrayImageFix,
    )

    # Verify all imports are available
    assert BackupService is not None
    assert BodyIdLinkFix is not None
    assert EPUBContents is not None
    assert EPUBFix is not None
    assert EPUBFixerOrchestrator is not None
    assert EPUBFixerSettings is not None
    assert EPUBReader is not None
    assert EPUBScanner is not None
    assert EPUBWriter is not None
    assert EncodingFix is not None
    assert FileTypes is not None
    assert FixResult is not None
    assert FixResultRecorder is not None
    assert IBackupService is not None
    assert LanguageFix is not None
    assert LibraryLocator is not None
    assert NullBackupService is not None
    assert OPFLocator is not None
    assert StrayImageFix is not None


def test_core_init_imports() -> None:
    """Test that all exports from core/__init__.py can be imported."""
    from bookcard.services.epub_fixer.core import (
        EPUBContents,
        EPUBReader,
        EPUBWriter,
        FixResult,
    )

    assert EPUBContents is not None
    assert EPUBReader is not None
    assert EPUBWriter is not None
    assert FixResult is not None


def test_fixes_init_imports() -> None:
    """Test that all exports from fixes/__init__.py can be imported."""
    from bookcard.services.epub_fixer.core.fixes import (
        BodyIdLinkFix,
        EncodingFix,
        EPUBFix,
        LanguageFix,
        StrayImageFix,
    )

    assert BodyIdLinkFix is not None
    assert EPUBFix is not None
    assert EncodingFix is not None
    assert LanguageFix is not None
    assert StrayImageFix is not None


def test_services_init_imports() -> None:
    """Test that all exports from services/__init__.py can be imported."""
    from bookcard.services.epub_fixer.services import (
        BackupService,
        EPUBScanner,
        FixResultRecorder,
        IBackupService,
        LibraryLocator,
        NullBackupService,
    )

    assert BackupService is not None
    assert EPUBScanner is not None
    assert FixResultRecorder is not None
    assert IBackupService is not None
    assert LibraryLocator is not None
    assert NullBackupService is not None


def test_utils_init_imports() -> None:
    """Test that all exports from utils/__init__.py can be imported."""
    from bookcard.services.epub_fixer.utils import FileTypes, OPFLocator

    assert FileTypes is not None
    assert OPFLocator is not None

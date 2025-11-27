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

"""Tests for persistence service."""

from unittest.mock import MagicMock

from fundamental.models.epub_fixer import EPUBFix, EPUBFixType
from fundamental.services.epub_fixer.core.epub import FixResult
from fundamental.services.epub_fixer.services.persistence import FixResultRecorder
from fundamental.services.epub_fixer_service import EPUBFixerService
from tests.conftest import DummySession


def test_fix_result_recorder_init() -> None:
    """Test FixResultRecorder initialization."""
    session = DummySession()
    fixer_service = EPUBFixerService(session)  # type: ignore[arg-type]
    recorder = FixResultRecorder(fixer_service)

    assert recorder._fixer_service == fixer_service


def test_fix_result_recorder_record_fix() -> None:
    """Test FixResultRecorder records single fix."""
    session = DummySession()
    fixer_service = EPUBFixerService(session)  # type: ignore[arg-type]
    recorder = FixResultRecorder(fixer_service)

    # Mock the record_fix method
    mock_fix = EPUBFix(
        id=1,
        run_id=1,
        fix_type=EPUBFixType.ENCODING,
        fix_description="Test fix",
    )
    fixer_service.record_fix = MagicMock(return_value=mock_fix)  # type: ignore[method-assign]

    fix_result = FixResult(
        fix_type=EPUBFixType.ENCODING,
        description="Test fix",
        file_name="test.html",
    )

    result = recorder.record_fix(
        run_id=1,
        book_id=1,
        book_title="Test Book",
        file_path="/path/to/test.epub",
        fix_result=fix_result,
        original_file_path="/path/to/backup.epub",
        backup_created=True,
    )

    assert result == mock_fix
    fixer_service.record_fix.assert_called_once_with(  # type: ignore[attr-defined]
        run_id=1,
        book_id=1,
        book_title="Test Book",
        file_path="/path/to/test.epub",
        fix_type=EPUBFixType.ENCODING,
        fix_description="Test fix",
        file_name="test.html",
        original_value=None,
        fixed_value=None,
        original_file_path="/path/to/backup.epub",
        backup_created=True,
    )


def test_fix_result_recorder_record_fixes() -> None:
    """Test FixResultRecorder records multiple fixes."""
    session = DummySession()
    fixer_service = EPUBFixerService(session)  # type: ignore[arg-type]
    recorder = FixResultRecorder(fixer_service)

    # Mock the record_fix method
    mock_fixes = [
        EPUBFix(
            id=1,
            run_id=1,
            fix_type=EPUBFixType.ENCODING,
            fix_description="Fix 1",
        ),
        EPUBFix(
            id=2,
            run_id=1,
            fix_type=EPUBFixType.LANGUAGE_TAG,
            fix_description="Fix 2",
        ),
    ]
    fixer_service.record_fix = MagicMock(side_effect=mock_fixes)  # type: ignore[method-assign]

    fix_results = [
        FixResult(
            fix_type=EPUBFixType.ENCODING,
            description="Fix 1",
            file_name="test1.html",
        ),
        FixResult(
            fix_type=EPUBFixType.LANGUAGE_TAG,
            description="Fix 2",
            file_name="test2.html",
        ),
    ]

    results = recorder.record_fixes(
        run_id=1,
        book_id=1,
        book_title="Test Book",
        file_path="/path/to/test.epub",
        fix_results=fix_results,
    )

    assert len(results) == 2
    assert results[0] == mock_fixes[0]
    assert results[1] == mock_fixes[1]
    assert fixer_service.record_fix.call_count == 2  # type: ignore[attr-defined]

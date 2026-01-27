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

"""Tests for MetadataDbBackupTask."""

from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlmodel import Session

from bookcard.models.config import Library
from bookcard.models.tasks import TaskType
from bookcard.services.tasks.metadata_db_backup_task import MetadataDbBackupTask


@pytest.fixture
def mock_update_progress() -> MagicMock:
    """Mock update_progress callback."""
    return MagicMock()


@pytest.fixture
def backup_task(session: Session) -> MetadataDbBackupTask:
    """Create a MetadataDbBackupTask instance."""
    return MetadataDbBackupTask(
        task_id=1,
        user_id=1,
        metadata={"task_type": TaskType.METADATA_BACKUP},
    )


def test_backup_single_library(
    session: Session,
    backup_task: MetadataDbBackupTask,
    tmp_path: Path,
    mock_update_progress: MagicMock,
) -> None:
    """Test backing up a single library."""
    # Setup library with DB file
    lib_dir = tmp_path / "library1"
    lib_dir.mkdir()
    db_file = lib_dir / "metadata.db"
    db_file.write_text("dummy content")

    library = Library(
        name="Test Lib",
        calibre_db_path=str(lib_dir),
        calibre_db_file="metadata.db",
    )
    session.add(library)
    session.commit()

    # Configure exec result for library_repo.list()
    session.add_exec_result([library])  # type: ignore[attr-defined]

    # Run task
    backup_task.update_progress = mock_update_progress  # type: ignore[method-assign]
    backup_task.run({"session": session})

    # Verify backup created
    backups = list(lib_dir.glob("metadata.*.db.bk"))
    assert len(backups) == 1
    assert backups[0].read_text() == "dummy content"

    # Verify progress update
    mock_update_progress.assert_called_with(1.0)


def test_backup_rotation(
    session: Session,
    backup_task: MetadataDbBackupTask,
    tmp_path: Path,
    mock_update_progress: MagicMock,
) -> None:
    """Test that old backups are rotated."""
    # Setup library
    lib_dir = tmp_path / "library_rotation"
    lib_dir.mkdir()
    db_file = lib_dir / "metadata.db"
    db_file.write_text("current content")

    library = Library(
        name="Rotation Lib",
        calibre_db_path=str(lib_dir),
        calibre_db_file="metadata.db",
    )
    session.add(library)
    session.commit()

    # Configure exec result for library_repo.list()
    session.add_exec_result([library])  # type: ignore[attr-defined]

    # Create 105 fake old backups
    for i in range(105):
        # Use different timestamps
        ts = 1000000000 + i
        bk_file = lib_dir / f"metadata.{ts}.db.bk"
        bk_file.write_text(f"backup {i}")

    # Run task
    backup_task.update_progress = mock_update_progress  # type: ignore[method-assign]
    backup_task.run({"session": session})

    # Verify rotation
    # Should have 100 backups now (including the new one)
    # Wait, the logic is: create new backup, then rotate.
    # So if we had 105, we add 1 -> 106.
    # Then we keep top 100.
    # So we should have 100 files left.

    backups = list(lib_dir.glob("metadata.*.db.bk"))
    assert len(backups) == 100

    # The newest backup should be present (the one we just created)
    # It will have a much larger timestamp than our fake ones
    # We can check content of the newest file
    backups.sort(
        key=lambda p: p.stat().st_mtime
    )  # Modification time might be same if created fast
    # Better sort by filename timestamp if possible, but regex extraction is needed.
    # Let's just check that one file has "current content"

    has_current = any(b.read_text() == "current content" for b in backups)
    assert has_current


def test_missing_db_file(
    session: Session,
    backup_task: MetadataDbBackupTask,
    tmp_path: Path,
    mock_update_progress: MagicMock,
) -> None:
    """Test handling of missing DB file."""
    # Setup library pointing to non-existent file
    lib_dir = tmp_path / "empty_lib"
    lib_dir.mkdir()

    library = Library(
        name="Empty Lib",
        calibre_db_path=str(lib_dir),
        calibre_db_file="metadata.db",
    )
    session.add(library)
    session.commit()

    # Configure exec result for library_repo.list()
    session.add_exec_result([library])  # type: ignore[attr-defined]

    # Run task - should not raise exception
    backup_task.update_progress = mock_update_progress  # type: ignore[method-assign]
    backup_task.run({"session": session})

    # Verify no backups created
    backups = list(lib_dir.glob("*.bk"))
    assert len(backups) == 0

    # Progress still updated
    mock_update_progress.assert_called_with(1.0)


def test_custom_db_filename(
    session: Session,
    backup_task: MetadataDbBackupTask,
    tmp_path: Path,
    mock_update_progress: MagicMock,
) -> None:
    """Test backup with custom DB filename."""
    lib_dir = tmp_path / "custom_lib"
    lib_dir.mkdir()
    db_file = lib_dir / "my_books.sqlite"
    db_file.write_text("custom content")

    library = Library(
        name="Custom Lib",
        calibre_db_path=str(lib_dir),
        calibre_db_file="my_books.sqlite",
    )
    session.add(library)
    session.commit()

    # Configure exec result for library_repo.list()
    session.add_exec_result([library])  # type: ignore[attr-defined]

    backup_task.update_progress = mock_update_progress  # type: ignore[method-assign]
    backup_task.run({"session": session})

    # Check for backup: my_books.{ts}.sqlite.bk
    backups = list(lib_dir.glob("my_books.*.sqlite.bk"))
    assert len(backups) == 1
    assert backups[0].read_text() == "custom content"


def test_no_libraries_returns_without_progress_update(
    session: Session,
    backup_task: MetadataDbBackupTask,
    mock_update_progress: MagicMock,
) -> None:
    """Task returns early when no libraries are configured."""
    session.add_exec_result([])  # type: ignore[attr-defined]

    backup_task.update_progress = mock_update_progress  # type: ignore[method-assign]
    backup_task.run({"session": session})

    mock_update_progress.assert_not_called()


def test_run_raises_when_any_library_fails(
    session: Session,
    backup_task: MetadataDbBackupTask,
    mock_update_progress: MagicMock,
) -> None:
    """Task raises if any library backup fails."""
    library = Library(
        id=1,
        name="Fail Lib",
        calibre_db_path="/does/not/matter",
        calibre_db_file="metadata.db",
    )
    session.add_exec_result([library])  # type: ignore[attr-defined]

    def boom(_: object) -> None:
        raise RuntimeError("boom")

    backup_task._backup_library = boom  # type: ignore[method-assign]
    backup_task.update_progress = mock_update_progress  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="Backup failed for 1 libraries"):
        backup_task.run({"session": session})

    mock_update_progress.assert_called_once_with(1.0)


def test_backup_library_no_path_configured_does_nothing(
    backup_task: MetadataDbBackupTask, tmp_path: Path
) -> None:
    """Backup is skipped when calibre_db_path is empty."""
    library = SimpleNamespace(
        id=1,
        name="No Path",
        calibre_db_path="",
        calibre_db_file="metadata.db",
    )
    backup_task._backup_library(library)  # type: ignore[arg-type]
    assert list(tmp_path.glob("**/*.bk")) == []


def test_rotate_backups_handles_listing_error(
    backup_task: MetadataDbBackupTask, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rotation returns early on directory listing errors."""
    db_path = tmp_path / "metadata.db"
    db_path.write_text("x")
    parent_dir = db_path.parent

    original_iterdir = Path.iterdir

    def fake_iterdir(self: Path) -> Iterator[Path]:
        if self == parent_dir:
            raise OSError("cannot list")
        return original_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", fake_iterdir)

    backup_task._rotate_backups(db_path)  # should not raise


def test_rotate_backups_suppresses_unlink_oserror_and_skips_non_files(
    backup_task: MetadataDbBackupTask, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rotation ignores unlink errors and ignores non-file entries."""
    # Use a stem containing '.' to exercise regex escaping.
    db_path = tmp_path / "meta.data.db"
    db_path.write_text("db")

    # A directory matching the pattern should be ignored (not is_file()).
    (tmp_path / "meta.data.1.db.bk").mkdir()

    bk_keep = tmp_path / "meta.data.300.db.bk"
    bk_remove_1 = tmp_path / "meta.data.200.db.bk"
    bk_remove_2 = tmp_path / "meta.data.100.db.bk"
    for p in [bk_keep, bk_remove_1, bk_remove_2]:
        p.write_text(p.name)

    original_unlink = Path.unlink

    def fake_unlink(self: Path, missing_ok: bool = False) -> None:
        if self == bk_remove_2:
            raise OSError("permission denied")
        return original_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", fake_unlink)

    backup_task._rotate_backups(db_path, max_backups=1)

    assert bk_keep.exists()
    assert bk_remove_1.exists() is False
    # unlink failure should be suppressed
    assert bk_remove_2.exists()

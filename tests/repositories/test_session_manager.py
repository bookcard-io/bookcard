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

from __future__ import annotations

from pathlib import Path  # noqa: TC003

from sqlalchemy import text

from bookcard.repositories.session_manager import CalibreSessionManager


def test_calibre_session_manager_sets_sqlite_pragmas(tmp_path: Path) -> None:
    """Ensure Calibre engine config applies SQLite pragmas for concurrency."""
    db_file = tmp_path / "metadata.db"
    db_file.touch()

    manager = CalibreSessionManager(str(tmp_path), "metadata.db")
    engine = manager._get_engine()

    with engine.connect() as conn:
        journal_mode = conn.execute(text("PRAGMA journal_mode")).fetchone()
        assert journal_mode is not None
        assert journal_mode[0].lower() == "wal"

        busy_timeout = conn.execute(text("PRAGMA busy_timeout")).fetchone()
        assert busy_timeout is not None
        assert busy_timeout[0] == 30000

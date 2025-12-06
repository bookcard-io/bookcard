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
from types import SimpleNamespace

import pytest
from sqlalchemy import text

import fundamental.database as db


def test_create_db_engine_passes_config(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_create_engine(
        url: str, echo: bool, future: bool, **kwargs: object
    ) -> object:
        captured["url"] = url
        captured["echo"] = echo
        captured["future"] = future
        captured["kwargs"] = kwargs
        # Return a mock engine that behaves like an SQLAlchemy engine
        return SimpleNamespace()

    monkeypatch.setattr(db, "create_engine", fake_create_engine)

    # Mock sqlalchemy.event.listens_for to avoid InvalidRequestError
    # Since create_db_engine uses @event.listens_for(engine, "connect")
    # we need the engine to be a valid target or mock the event system.
    # Easier to mock event.listens_for

    class MockEvent:
        def listens_for(self, target: object, identifier: str) -> object:
            def decorator(fn: object) -> object:
                return fn

            return decorator

    monkeypatch.setattr(db, "event", MockEvent())

    cfg = SimpleNamespace(database_url="sqlite://", echo_sql=True)
    engine = db.create_db_engine(cfg)  # type: ignore[arg-type]

    # Verify arguments passed to create_engine
    assert captured["url"] == "sqlite://"
    assert captured["echo"] is True
    assert captured["future"] is True
    assert engine is not None


def test_create_all_tables_calls_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"ok": False}

    class FakeMeta:
        def create_all(self, engine: object) -> None:
            called["ok"] = True

    fake_sqlmodel = SimpleNamespace(metadata=FakeMeta())
    monkeypatch.setattr(db, "SQLModel", fake_sqlmodel)
    db.create_all_tables(object())  # type: ignore[arg-type]
    assert called["ok"] is True


class DummySession:
    def __init__(self, engine: object) -> None:
        self.committed = False
        self.rolled = False
        self.closed = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled = True

    def close(self) -> None:
        self.closed = True


def test_get_session_commit_and_close(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db, "Session", DummySession)
    with db.get_session(object()) as session:
        assert isinstance(session, DummySession)
    assert session.committed is True
    assert session.closed is True
    assert session.rolled is False


def test_get_session_rollback_on_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db, "Session", DummySession)
    with pytest.raises(RuntimeError), db.get_session(object()) as session:
        raise RuntimeError("boom")
    assert session.rolled is True
    assert session.closed is True


class DummySessionWithLockError:
    """Session that raises OperationalError with 'database is locked' message."""

    def __init__(self, engine: object) -> None:
        self.committed = False
        self.rolled = False
        self.closed = False
        self.commit_count = 0

    def commit(self) -> None:
        """Raise OperationalError on first two commits, succeed on third."""
        self.commit_count += 1
        if self.commit_count < 3:
            from sqlalchemy.exc import OperationalError

            raise OperationalError("database is locked", None, RuntimeError("Locked"))

        self.committed = True

    def rollback(self) -> None:
        self.rolled = True

    def close(self) -> None:
        self.closed = True


def test_get_session_retry_on_lock_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that get_session retries on database lock errors (covers lines 130-141)."""
    monkeypatch.setattr(db, "Session", DummySessionWithLockError)
    with db.get_session(object()) as session:
        assert isinstance(session, DummySessionWithLockError)
    # Should have retried and eventually succeeded
    assert session.committed is True
    assert session.commit_count == 3
    assert session.closed is True
    assert session.rolled is False


class DummySessionWithMaxRetries:
    """Session that always raises OperationalError with 'database is locked'."""

    def __init__(self, engine: object) -> None:
        self.committed = False
        self.rolled = False
        self.closed = False
        self.commit_count = 0

    def commit(self) -> None:
        """Always raise OperationalError."""
        self.commit_count += 1
        from sqlalchemy.exc import OperationalError

        raise OperationalError("database is locked", None, RuntimeError("Locked"))

    def rollback(self) -> None:
        self.rolled = True

    def close(self) -> None:
        self.closed = True


def test_get_session_max_retries_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that get_session raises after max retries (covers lines 130-141)."""
    monkeypatch.setattr(db, "Session", DummySessionWithMaxRetries)
    from sqlalchemy.exc import OperationalError

    with (
        pytest.raises(OperationalError),
        db.get_session(object(), max_retries=2) as session,
    ):
        pass
    # Should have tried max_retries times
    assert session.commit_count == 2
    assert session.closed is True


class DummySessionWithOtherError:
    """Session that raises OperationalError without 'database is locked'."""

    def __init__(self, engine: object) -> None:
        self.committed = False
        self.rolled = False
        self.closed = False

    def commit(self) -> None:
        """Raise OperationalError with different message."""
        from sqlalchemy.exc import OperationalError

        raise OperationalError("connection lost", None, RuntimeError("Connection lost"))

    def rollback(self) -> None:
        self.rolled = True

    def close(self) -> None:
        self.closed = True


def test_get_session_no_retry_on_other_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that get_session does not retry on non-lock errors (covers lines 130-141)."""
    monkeypatch.setattr(db, "Session", DummySessionWithOtherError)
    from sqlalchemy.exc import OperationalError

    with pytest.raises(OperationalError), db.get_session(object()) as session:
        pass
    assert session.rolled is True
    assert session.closed is True


def test_create_db_engine_sqlite_pragma_setup(tmp_path: Path) -> None:
    """Test SQLite pragma setup on connection (covers lines 79-84)."""
    # Use a temporary file-based database
    db_file = tmp_path / "test_pragma.db"
    cfg = SimpleNamespace(database_url=f"sqlite:///{db_file}", echo_sql=False)
    engine = db.create_db_engine(cfg)  # type: ignore[arg-type]

    # Connect to trigger the event listener
    with engine.connect() as conn:
        # Execute raw SQL to check pragma values
        result = conn.execute(text("PRAGMA journal_mode")).fetchone()
        assert result is not None
        assert result[0].lower() == "wal"  # SQLite returns lowercase

        result = conn.execute(text("PRAGMA busy_timeout")).fetchone()
        assert result is not None
        assert result[0] == 30000

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

from types import SimpleNamespace

import pytest

import fundamental.database as db


def test_create_db_engine_passes_config(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_create_engine(url: str, echo: bool, future: bool) -> object:
        captured["url"] = url
        captured["echo"] = echo
        captured["future"] = future
        return object()

    monkeypatch.setattr(db, "create_engine", fake_create_engine)
    cfg = SimpleNamespace(database_url="sqlite://", echo_sql=True)
    engine = db.create_db_engine(cfg)  # type: ignore[arg-type]
    assert captured == {"url": "sqlite://", "echo": True, "future": True}
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

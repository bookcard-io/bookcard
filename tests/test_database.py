# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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

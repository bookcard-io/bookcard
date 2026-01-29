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

"""Tests for demo-mode write-lock middleware."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from bookcard.api.middleware.auth_middleware import AuthMiddleware
from bookcard.api.middleware.demo_mode_middleware import DemoModeWriteLockMiddleware
from bookcard.config import AppConfig
from bookcard.services.security import JWTManager
from tests.conftest import TEST_ENCRYPTION_KEY


@pytest.fixture
def demo_config() -> AppConfig:
    return AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
        alembic_enabled=False,
        demo_mode=True,
    )


@pytest.fixture
def non_demo_config() -> AppConfig:
    return AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
        alembic_enabled=False,
        demo_mode=False,
    )


@pytest.fixture
def demo_state() -> dict[str, int]:
    return {
        "mutations": 0,
        "settings_put": 0,
        "profile_patch": 0,
        "password_put": 0,
        "reading_progress_put": 0,
        "reading_sessions_post": 0,
        "reading_sessions_put": 0,
        "reading_status_put": 0,
        "profile_picture_post": 0,
        "kobo_sync_get": 0,
        "oidc_callback_get": 0,
    }


def _attach_middleware(app: FastAPI) -> None:
    # Mirror production order (auth runs first, see middleware_config.py note).
    app.add_middleware(DemoModeWriteLockMiddleware)  # type: ignore[invalid-argument-type]
    app.add_middleware(AuthMiddleware)  # type: ignore[invalid-argument-type]


def _register_base_routes(app: FastAPI, state: dict[str, int]) -> None:
    @app.post("/mutate")
    def mutate() -> dict[str, bool]:
        state["mutations"] += 1
        return {"ok": True}

    @app.get("/mutate")
    def read_only() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/auth/login")
    def login() -> dict[str, bool]:
        # Should remain available in demo mode so users can obtain tokens.
        return {"ok": True}


def _register_demo_allowed_write_routes(app: FastAPI, state: dict[str, int]) -> None:
    @app.put("/auth/settings/theme")
    def save_setting() -> dict[str, bool]:
        state["settings_put"] += 1
        return {"ok": True}

    @app.patch("/auth/profile")
    def update_profile() -> dict[str, bool]:
        state["profile_patch"] += 1
        return {"ok": True}

    @app.put("/auth/password")
    def change_password() -> dict[str, bool]:
        state["password_put"] += 1
        return {"ok": True}

    @app.put("/reading/progress")
    def update_progress() -> dict[str, bool]:
        state["reading_progress_put"] += 1
        return {"ok": True}

    @app.post("/reading/sessions")
    def start_session() -> dict[str, bool]:
        state["reading_sessions_post"] += 1
        return {"ok": True}

    @app.put("/reading/sessions/1")
    def end_session() -> dict[str, bool]:
        state["reading_sessions_put"] += 1
        return {"ok": True}

    @app.put("/reading/status/1")
    def update_status() -> dict[str, bool]:
        state["reading_status_put"] += 1
        return {"ok": True}


def _register_demo_blocked_routes(app: FastAPI, state: dict[str, int]) -> None:
    @app.post("/auth/profile-picture")
    def upload_profile_picture() -> dict[str, bool]:
        state["profile_picture_post"] += 1
        return {"ok": True}

    @app.get("/kobo/v1/library/sync")
    def kobo_sync() -> dict[str, bool]:
        state["kobo_sync_get"] += 1
        return {"ok": True}

    @app.get("/auth/oidc/callback")
    def oidc_callback_get() -> dict[str, bool]:
        state["oidc_callback_get"] += 1
        return {"ok": True}


def _make_demo_app(config: AppConfig, state: dict[str, int]) -> FastAPI:
    app = FastAPI()
    app.state.config = config

    _attach_middleware(app)
    _register_base_routes(app, state)
    _register_demo_allowed_write_routes(app, state)
    _register_demo_blocked_routes(app, state)

    app.state._test_state = state
    return app


@pytest.fixture
def demo_app(demo_config: AppConfig, demo_state: dict[str, int]) -> FastAPI:
    return _make_demo_app(config=demo_config, state=demo_state)


@pytest.fixture
def non_demo_app(non_demo_config: AppConfig, demo_state: dict[str, int]) -> FastAPI:
    return _make_demo_app(config=non_demo_config, state=demo_state)


def _make_token(*, is_admin: bool) -> str:
    cfg = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        demo_mode=True,
    )
    jwt_mgr = JWTManager(cfg)
    return jwt_mgr.create_access_token("1", extra_claims={"is_admin": is_admin})


def test_demo_mode_blocks_write_for_non_admin(demo_app: FastAPI) -> None:
    app = demo_app
    client = TestClient(app)

    token = _make_token(is_admin=False)
    resp = client.post("/mutate", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 403
    assert resp.json()["detail"] == "demo_mode_read_only"
    assert app.state._test_state["mutations"] == 0


def test_demo_mode_allows_db_only_writes_for_non_admin(demo_app: FastAPI) -> None:
    app = demo_app
    client = TestClient(app)

    token = _make_token(is_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.put("/auth/settings/theme", headers=headers)
    assert resp.status_code == 200
    assert app.state._test_state["settings_put"] == 1

    resp = client.patch("/auth/profile", headers=headers)
    assert resp.status_code == 200
    assert app.state._test_state["profile_patch"] == 1

    resp = client.put("/auth/password", headers=headers)
    assert resp.status_code == 200
    assert app.state._test_state["password_put"] == 1

    resp = client.put("/reading/progress", headers=headers)
    assert resp.status_code == 200
    assert app.state._test_state["reading_progress_put"] == 1

    resp = client.post("/reading/sessions", headers=headers)
    assert resp.status_code == 200
    assert app.state._test_state["reading_sessions_post"] == 1

    resp = client.put("/reading/sessions/1", headers=headers)
    assert resp.status_code == 200
    assert app.state._test_state["reading_sessions_put"] == 1

    resp = client.put("/reading/status/1", headers=headers)
    assert resp.status_code == 200
    assert app.state._test_state["reading_status_put"] == 1


def test_demo_mode_blocks_filesystem_like_writes_for_non_admin(
    demo_app: FastAPI,
) -> None:
    app = demo_app
    client = TestClient(app)

    token = _make_token(is_admin=False)
    resp = client.post(
        "/auth/profile-picture", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "demo_mode_read_only"
    assert app.state._test_state["profile_picture_post"] == 0


def test_demo_mode_blocks_stateful_get_for_non_admin(demo_app: FastAPI) -> None:
    app = demo_app
    client = TestClient(app)

    token = _make_token(is_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/kobo/v1/library/sync", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "demo_mode_read_only"
    assert app.state._test_state["kobo_sync_get"] == 0

    resp = client.get("/auth/oidc/callback", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "demo_mode_read_only"
    assert app.state._test_state["oidc_callback_get"] == 0


def test_demo_mode_allows_write_for_admin(demo_app: FastAPI) -> None:
    app = demo_app
    client = TestClient(app)

    token = _make_token(is_admin=True)
    resp = client.post("/mutate", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert app.state._test_state["mutations"] == 1


def test_demo_mode_allows_safe_methods(demo_app: FastAPI) -> None:
    app = demo_app
    client = TestClient(app)

    resp = client.get("/mutate")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_demo_mode_allows_login_endpoint_without_token(demo_app: FastAPI) -> None:
    app = demo_app
    client = TestClient(app)

    resp = client.post("/auth/login")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_non_demo_mode_does_not_block_writes(non_demo_app: FastAPI) -> None:
    app = non_demo_app
    client = TestClient(app)

    resp = client.post("/mutate")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert app.state._test_state["mutations"] == 1

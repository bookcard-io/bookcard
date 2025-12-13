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

"""Tests for KeycloakAuthService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fundamental.config import AppConfig
from fundamental.services.keycloak_auth_service import (
    KeycloakAuthService,
    KeycloakTokenValidationError,
)
from tests.conftest import TEST_ENCRYPTION_KEY


def _cfg() -> AppConfig:
    return AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        keycloak_enabled=True,
        keycloak_client_id="fundamental-client",
        keycloak_issuer="http://keycloak:8080/realms/fundamental",
    )


def test_validate_access_token_happy_path() -> None:
    """Valid token should return claims when aud/azp matches client."""
    service = KeycloakAuthService(_cfg(), http_client=MagicMock())

    with (
        patch.object(service, "_get_jwks", return_value={"keys": [{"kid": "k1"}]}),
        patch(
            "fundamental.services.keycloak_auth_service.jwt.get_unverified_header",
            return_value={"kid": "k1"},
        ),
        patch(
            "fundamental.services.keycloak_auth_service.RSAAlgorithm.from_jwk",
            return_value="pub",
        ),
        patch(
            "fundamental.services.keycloak_auth_service.jwt.decode",
            return_value={"sub": "s", "aud": "fundamental-client"},
        ),
    ):
        claims = service.validate_access_token(token="t")
        assert claims["sub"] == "s"


def test_validate_access_token_audience_mismatch_raises() -> None:
    """Mismatched aud/azp should raise KeycloakTokenValidationError."""
    service = KeycloakAuthService(_cfg(), http_client=MagicMock())

    with (
        patch.object(service, "_get_jwks", return_value={"keys": [{"kid": "k1"}]}),
        patch(
            "fundamental.services.keycloak_auth_service.jwt.get_unverified_header",
            return_value={"kid": "k1"},
        ),
        patch(
            "fundamental.services.keycloak_auth_service.RSAAlgorithm.from_jwk",
            return_value="pub",
        ),
        patch(
            "fundamental.services.keycloak_auth_service.jwt.decode",
            return_value={"sub": "s", "aud": "some-other-client"},
        ),
        pytest.raises(KeycloakTokenValidationError),
    ):
        service.validate_access_token(token="t")

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

"""Generic OIDC client and token validator.

This module encapsulates all OpenID Connect interactions:
- Discovery document resolution
- Authorization URL construction
- Authorization-code token exchange
- UserInfo retrieval
- JWT validation using JWKS

Supports any OIDC-compliant provider.

The web/API layer should treat this as a pure integration component (SRP),
keeping HTTP endpoints thin and policy decisions elsewhere (SOC).
"""

from __future__ import annotations

import json
import secrets
import time
from dataclasses import dataclass
from threading import Lock
from typing import Final
from urllib.parse import urlencode

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm  # type: ignore[attr-defined]

from bookcard.config import AppConfig  # noqa: TC001


class OIDCAuthError(Exception):
    """Raised when OIDC authentication operations fail."""


class OIDCConfigurationError(OIDCAuthError):
    """Raised when OIDC configuration is incomplete or invalid."""


class OIDCError(OIDCAuthError):
    """Raised when the OIDC provider returns an OAuth/OIDC error response."""


class OIDCTokenValidationError(OIDCAuthError):
    """Raised when an OIDC JWT cannot be validated."""


@dataclass(frozen=True, slots=True)
class OIDCTokenSet:
    """Token response from OIDC token endpoint."""

    access_token: str
    expires_in: int | None = None
    refresh_token: str | None = None
    refresh_expires_in: int | None = None
    token_type: str | None = None
    id_token: str | None = None
    scope: str | None = None


class OIDCAuthService:
    """Generic OIDC integration service.

    Supports any OIDC-compliant provider.

    Parameters
    ----------
    config : AppConfig
        Application configuration containing OIDC settings.
    http_client : httpx.Client | None
        Optional injected HTTP client. If not provided, an internal client is used.
        This supports IOC/testing without coupling call sites to httpx.
    """

    _DISCOVERY_PATH: Final[str] = ".well-known/openid-configuration"
    _STATE_AUD: Final[str] = "bookcard:oidc_state"

    def __init__(
        self, config: AppConfig, http_client: httpx.Client | None = None
    ) -> None:
        self._cfg = config
        self._http = http_client or httpx.Client(timeout=10.0)

        self._lock = Lock()
        self._discovery_cache: dict[str, object] | None = None
        self._discovery_cache_expires_at: float = 0.0
        self._jwks_cache: dict[str, object] | None = None
        self._jwks_cache_expires_at: float = 0.0

    def build_authorization_url(
        self,
        *,
        redirect_uri: str,
        next_path: str | None = None,
        state_ttl_seconds: int = 600,
    ) -> str:
        """Build an OIDC authorization URL for the code flow.

        Parameters
        ----------
        redirect_uri : str
            Redirect URI registered in the OIDC provider for the client.
        next_path : str | None
            Optional post-login navigation hint preserved in the signed state.
        state_ttl_seconds : int
            State token TTL in seconds.

        Returns
        -------
        str
            Fully-qualified authorization URL.
        """
        discovery = self._get_discovery()
        authorization_endpoint = discovery.get("authorization_endpoint")
        if not isinstance(authorization_endpoint, str) or not authorization_endpoint:
            msg = "OIDC discovery missing authorization_endpoint"
            raise OIDCConfigurationError(msg)

        state = self._encode_state(
            redirect_uri=redirect_uri,
            next_path=next_path,
            ttl_seconds=state_ttl_seconds,
        )
        nonce = secrets.token_urlsafe(24)
        params = {
            "client_id": self._cfg.oidc_client_id,
            "response_type": "code",
            "scope": self._cfg.oidc_scopes,
            "redirect_uri": redirect_uri,
            "state": state,
            "nonce": nonce,
        }
        return f"{authorization_endpoint}?{urlencode(params)}"

    def exchange_code_for_token(self, *, code: str, redirect_uri: str) -> OIDCTokenSet:
        """Exchange authorization code for tokens at the token endpoint.

        Parameters
        ----------
        code : str
            Authorization code from OIDC provider callback.
        redirect_uri : str
            Redirect URI used in the initial authorization request.

        Returns
        -------
        OIDCTokenSet
            Parsed token set.
        """
        discovery = self._get_discovery()
        token_endpoint = discovery.get("token_endpoint")
        if not isinstance(token_endpoint, str) or not token_endpoint:
            msg = "OIDC discovery missing token_endpoint"
            raise OIDCConfigurationError(msg)

        data: dict[str, str] = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self._cfg.oidc_client_id,
        }
        # Confidential clients must present a secret; public clients may omit.
        if self._cfg.oidc_client_secret:
            data["client_secret"] = self._cfg.oidc_client_secret

        try:
            resp = self._http.post(
                token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.TimeoutException as err:
            msg = "oidc_token_timeout"
            raise OIDCError(msg) from err
        except httpx.HTTPError as err:
            msg = "oidc_token_http_error"
            raise OIDCError(msg) from err

        payload = self._parse_json_response(resp, error_prefix="oidc_token")
        if resp.status_code >= 400:
            # OIDC providers usually return error + error_description for OAuth failures.
            error = None
            if isinstance(payload, dict):
                payload_dict = {str(k): v for k, v in payload.items()}
                error = payload_dict.get("error")
            msg = (
                f"oidc_token_exchange_failed:{error}"
                if isinstance(error, str) and error
                else "oidc_token_exchange_failed"
            )
            raise OIDCError(msg)

        if not isinstance(payload, dict) or "access_token" not in payload:
            msg = "oidc_token_response_invalid"
            raise OIDCError(msg)

        payload_dict: dict[str, object] = {str(k): v for k, v in payload.items()}

        expires_in_val = payload_dict.get("expires_in")
        refresh_token_val = payload_dict.get("refresh_token")
        refresh_expires_in_val = payload_dict.get("refresh_expires_in")
        token_type_val = payload_dict.get("token_type")
        id_token_val = payload_dict.get("id_token")
        scope_val = payload_dict.get("scope")

        return OIDCTokenSet(
            access_token=str(payload_dict["access_token"]),
            expires_in=int(expires_in_val) if isinstance(expires_in_val, int) else None,
            refresh_token=(
                str(refresh_token_val) if isinstance(refresh_token_val, str) else None
            ),
            refresh_expires_in=(
                int(refresh_expires_in_val)
                if isinstance(refresh_expires_in_val, int)
                else None
            ),
            token_type=str(token_type_val) if isinstance(token_type_val, str) else None,
            id_token=str(id_token_val) if isinstance(id_token_val, str) else None,
            scope=str(scope_val) if isinstance(scope_val, str) else None,
        )

    def fetch_userinfo(self, *, access_token: str) -> dict[str, object]:
        """Fetch OIDC userinfo for the bearer access token.

        Parameters
        ----------
        access_token : str
            OAuth2 access token.

        Returns
        -------
        dict[str, object]
            Userinfo payload from the OIDC provider.
        """
        discovery = self._get_discovery()
        userinfo_endpoint = discovery.get("userinfo_endpoint")
        if not isinstance(userinfo_endpoint, str) or not userinfo_endpoint:
            msg = "OIDC discovery missing userinfo_endpoint"
            raise OIDCConfigurationError(msg)

        try:
            resp = self._http.get(
                userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.TimeoutException as err:
            msg = "oidc_userinfo_timeout"
            raise OIDCError(msg) from err
        except httpx.HTTPError as err:
            msg = "oidc_userinfo_http_error"
            raise OIDCError(msg) from err

        payload = self._parse_json_response(resp, error_prefix="oidc_userinfo")
        if resp.status_code >= 400:
            msg = "oidc_userinfo_failed"
            raise OIDCError(msg)
        if not isinstance(payload, dict):
            msg = "oidc_userinfo_invalid"
            raise OIDCError(msg)
        return {str(k): v for k, v in payload.items()}

    def validate_access_token(self, *, token: str) -> dict[str, object]:
        """Validate an OIDC JWT access token using JWKS.

        Parameters
        ----------
        token : str
            JWT access token from the OIDC provider.

        Returns
        -------
        dict[str, object]
            Validated JWT claims.
        """
        jwks = self._get_jwks()
        keys_raw = jwks.get("keys") if isinstance(jwks, dict) else None
        if not isinstance(keys_raw, list) or not keys_raw:
            msg = "oidc_jwks_invalid"
            raise OIDCTokenValidationError(msg)
        keys: list[object] = list(keys_raw)

        kid = self._extract_kid_from_jwt_header(token)
        if not isinstance(kid, str) or not kid:
            msg = "oidc_token_missing_kid"
            raise OIDCTokenValidationError(msg)

        jwk = self._select_jwk_for_kid(keys, kid)
        if jwk is None:
            msg = "oidc_token_unknown_kid"
            raise OIDCTokenValidationError(msg)

        try:
            public_key = RSAAlgorithm.from_jwk(json.dumps(jwk))
        except (ValueError, TypeError) as err:
            msg = "oidc_jwk_parse_failed"
            raise OIDCTokenValidationError(msg) from err

        issuer = self._cfg.oidc_issuer
        options = {"verify_aud": False}
        try:
            claims = jwt.decode(
                token,
                key=public_key,
                algorithms=["RS256"],
                issuer=issuer if issuer else None,
                options=options,
            )
        except jwt.ExpiredSignatureError as err:
            msg = "oidc_token_expired"
            raise OIDCTokenValidationError(msg) from err
        except jwt.InvalidIssuerError as err:
            msg = "oidc_token_invalid_issuer"
            raise OIDCTokenValidationError(msg) from err
        except jwt.InvalidTokenError as err:
            msg = "oidc_token_invalid"
            raise OIDCTokenValidationError(msg) from err

        if not isinstance(claims, dict):
            msg = "oidc_token_invalid"
            raise OIDCTokenValidationError(msg)

        claims_dict: dict[str, object] = {str(k): v for k, v in claims.items()}
        self._enforce_client_audience_or_azp(claims_dict)
        return claims_dict

    @staticmethod
    def _extract_kid_from_jwt_header(token: str) -> str | None:
        """Extract `kid` from JWT header without verifying the signature."""
        try:
            header_raw = jwt.get_unverified_header(token)
        except jwt.DecodeError:
            return None
        if not isinstance(header_raw, dict):
            return None
        header: dict[str, object] = {str(k): v for k, v in header_raw.items()}
        kid = header.get("kid")
        return kid if isinstance(kid, str) else None

    @staticmethod
    def _select_jwk_for_kid(keys: list[object], kid: str) -> dict[str, object] | None:
        """Select a JWK from JWKS matching the given `kid`."""
        for key_obj in keys:
            if not isinstance(key_obj, dict):
                continue
            key_dict: dict[str, object] = {str(k): v for k, v in key_obj.items()}
            if key_dict.get("kid") == kid:
                return key_dict
        return None

    def decode_state(self, *, state: str) -> dict[str, object]:
        """Decode and validate the signed OIDC state token.

        Parameters
        ----------
        state : str
            Signed state string produced by :meth:`build_authorization_url`.

        Returns
        -------
        dict[str, object]
            Decoded state payload.
        """
        try:
            payload = jwt.decode(
                state,
                self._cfg.jwt_secret,
                algorithms=[self._cfg.jwt_algorithm],
                audience=self._STATE_AUD,
            )
        except jwt.ExpiredSignatureError as err:
            msg = "oidc_state_expired"
            raise OIDCError(msg) from err
        except jwt.InvalidTokenError as err:
            msg = "oidc_state_invalid"
            raise OIDCError(msg) from err

        if not isinstance(payload, dict):
            msg = "oidc_state_invalid"
            raise OIDCError(msg)
        return {str(k): v for k, v in payload.items()}

    def _encode_state(
        self, *, redirect_uri: str, next_path: str | None, ttl_seconds: int
    ) -> str:
        now = int(time.time())
        payload: dict[str, object] = {
            "aud": self._STATE_AUD,
            "iat": now,
            "exp": now + ttl_seconds,
            "redirect_uri": redirect_uri,
        }
        if next_path:
            payload["next"] = next_path
        return jwt.encode(
            payload, self._cfg.jwt_secret, algorithm=self._cfg.jwt_algorithm
        )

    def _get_discovery(self) -> dict[str, object]:
        if not self._cfg.oidc_enabled:
            msg = "oidc_disabled"
            raise OIDCConfigurationError(msg)
        if not self._cfg.oidc_issuer:
            msg = "oidc_issuer_missing"
            raise OIDCConfigurationError(msg)

        now = time.time()
        with self._lock:
            if (
                self._discovery_cache is not None
                and now < self._discovery_cache_expires_at
            ):
                return self._discovery_cache

        url = f"{self._cfg.oidc_issuer.rstrip('/')}/{self._DISCOVERY_PATH}"
        try:
            resp = self._http.get(url)
        except httpx.TimeoutException as err:
            msg = "oidc_discovery_timeout"
            raise OIDCError(msg) from err
        except httpx.HTTPError as err:
            msg = "oidc_discovery_http_error"
            raise OIDCError(msg) from err

        payload = self._parse_json_response(resp, error_prefix="oidc_discovery")
        if resp.status_code >= 400:
            msg = "oidc_discovery_failed"
            raise OIDCError(msg)
        if not isinstance(payload, dict):
            msg = "oidc_discovery_invalid"
            raise OIDCError(msg)

        payload_dict: dict[str, object] = {str(k): v for k, v in payload.items()}
        with self._lock:
            self._discovery_cache = payload_dict
            self._discovery_cache_expires_at = time.time() + 3600.0
        return payload_dict

    def _get_jwks(self) -> dict[str, object]:
        discovery = self._get_discovery()
        jwks_uri = discovery.get("jwks_uri")
        if not isinstance(jwks_uri, str) or not jwks_uri:
            msg = "OIDC discovery missing jwks_uri"
            raise OIDCConfigurationError(msg)

        now = time.time()
        with self._lock:
            if self._jwks_cache is not None and now < self._jwks_cache_expires_at:
                return self._jwks_cache

        try:
            resp = self._http.get(jwks_uri)
        except httpx.TimeoutException as err:
            msg = "oidc_jwks_timeout"
            raise OIDCError(msg) from err
        except httpx.HTTPError as err:
            msg = "oidc_jwks_http_error"
            raise OIDCError(msg) from err

        payload = self._parse_json_response(resp, error_prefix="oidc_jwks")
        if resp.status_code >= 400:
            msg = "oidc_jwks_failed"
            raise OIDCError(msg)
        if not isinstance(payload, dict):
            msg = "oidc_jwks_invalid"
            raise OIDCError(msg)

        payload_dict: dict[str, object] = {str(k): v for k, v in payload.items()}
        with self._lock:
            self._jwks_cache = payload_dict
            self._jwks_cache_expires_at = time.time() + 3600.0
        return payload_dict

    @staticmethod
    def _parse_json_response(resp: httpx.Response, *, error_prefix: str) -> object:
        try:
            return resp.json()
        except json.JSONDecodeError as err:
            msg = f"{error_prefix}_non_json"
            raise OIDCError(msg) from err

    def _enforce_client_audience_or_azp(self, claims: dict[str, object]) -> None:
        client_id = self._cfg.oidc_client_id
        if not client_id:
            # Shouldn't happen when OIDC is enabled, but keep validator robust.
            return

        aud = claims.get("aud")
        azp = claims.get("azp")

        aud_ok = False
        if isinstance(aud, str):
            aud_ok = aud == client_id
        elif isinstance(aud, list):
            aud_ok = client_id in aud

        azp_ok = isinstance(azp, str) and azp == client_id

        if not (aud_ok or azp_ok):
            msg = "oidc_token_audience_mismatch"
            raise OIDCTokenValidationError(msg)

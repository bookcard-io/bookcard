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

"""Kobo device authentication service.

Handles device authentication token generation and proxy logic.
"""

from __future__ import annotations

import base64
import json
import os
from contextlib import suppress
from typing import TYPE_CHECKING

import httpx

from bookcard.api.schemas.kobo import KoboAuthTokenResponse

if TYPE_CHECKING:
    from fastapi import Request
    from sqlmodel import Session

    from bookcard.services.kobo.store_proxy_service import KoboStoreProxyService


class KoboDeviceAuthService:
    """Service for handling Kobo device authentication.

    Generates device authentication tokens and handles proxy logic for
    forwarding requests to Kobo Store when enabled.

    Parameters
    ----------
    session : Session
        Database session.
    proxy_service : KoboStoreProxyService
        Store proxy service.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        proxy_service: KoboStoreProxyService,
    ) -> None:
        self._session = session
        self._proxy_service = proxy_service

    async def authenticate_device(
        self, request: Request, user_key: str
    ) -> KoboAuthTokenResponse:
        """Authenticate a Kobo device.

        Parameters
        ----------
        request : Request
            FastAPI request.
        user_key : str
            User key from request body.

        Returns
        -------
        KoboAuthTokenResponse
            Authentication token response.

        Raises
        ------
        HTTPException
            If proxy fails and local auth is not available.
        """
        # Try proxy first if enabled
        if self._proxy_service.should_proxy():
            with suppress(
                httpx.HTTPError, json.JSONDecodeError, AttributeError, KeyError
            ):
                return await self._proxy_authentication(request)

        # Local authentication
        return self._generate_local_tokens(user_key)

    async def _proxy_authentication(self, request: Request) -> KoboAuthTokenResponse:
        """Proxy authentication request to Kobo Store.

        Parameters
        ----------
        request : Request
            FastAPI request.

        Returns
        -------
        KoboAuthTokenResponse
            Response from Kobo Store.

        Raises
        ------
        httpx.HTTPError
            If proxy request fails.
        json.JSONDecodeError
            If response JSON is invalid.
        """
        auth_token = request.path_params.get("auth_token", "")
        path = request.url.path.replace(f"/kobo/{auth_token}", "")
        response = await self._proxy_service.proxy_request(
            path=path,
            method=request.method,
            headers=dict(request.headers),
            data=await request.body(),
        )
        response_data = response.json()
        return KoboAuthTokenResponse(**response_data)

    def _generate_local_tokens(self, user_key: str) -> KoboAuthTokenResponse:
        """Generate local authentication tokens.

        Parameters
        ----------
        user_key : str
            User key from request.

        Returns
        -------
        KoboAuthTokenResponse
            Generated token response.
        """
        access_token = base64.b64encode(os.urandom(24)).decode("utf-8")
        refresh_token = base64.b64encode(os.urandom(24)).decode("utf-8")

        return KoboAuthTokenResponse(
            AccessToken=access_token,
            RefreshToken=refresh_token,
            TokenType="Bearer",
            TrackingId=str(os.urandom(16).hex()),
            UserKey=user_key,
        )

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

"""Tests for PVR search routes."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException, status

import bookcard.api.routes.pvr_search as pvr_search_routes
from bookcard.api.schemas.pvr_search import (
    PVRDownloadRequest,
    PVRDownloadResponse,
    PVRSearchRequest,
    PVRSearchResponse,
    PVRSearchResultsResponse,
)
from bookcard.models.auth import User

# Rebuild Pydantic models to resolve forward references
PVRSearchResponse.model_rebuild()
PVRSearchResultsResponse.model_rebuild()
PVRDownloadResponse.model_rebuild()

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def user() -> User:
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
        is_admin=False,
    )


@pytest.fixture
def valid_fernet_key() -> str:
    return Fernet.generate_key().decode()


class TestGetTrackedBookSearchService:
    def test_get_tracked_book_search_service(
        self, session: DummySession, valid_fernet_key: str
    ) -> None:
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        service = pvr_search_routes._get_tracked_book_search_service(session, request)
        assert service is not None
        assert hasattr(service, "_tracked_book_service")
        assert hasattr(service, "_indexer_search_service")
        assert hasattr(service, "_download_service")


class TestSearchTrackedBook:
    def test_search_tracked_book_delegation(
        self,
        session: DummySession,
        user: User,
        valid_fernet_key: str,
    ) -> None:
        request_data = PVRSearchRequest(tracked_book_id=1)
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with patch(
            "bookcard.api.routes.pvr_search._get_tracked_book_search_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_response = PVRSearchResponse(
                tracked_book_id=1,
                search_initiated=True,
                message="Search initiated",
            )
            mock_service.search_tracked_book.return_value = mock_response
            mock_get_service.return_value = mock_service

            # Mock permission helper
            with patch(
                "bookcard.api.routes.pvr_search.BookPermissionHelper"
            ) as mock_helper_cls:
                mock_helper = MagicMock()
                mock_helper_cls.return_value = mock_helper

                result = pvr_search_routes.search_tracked_book(
                    request=request_data,
                    session=session,
                    current_user=user,
                    permission_helper=mock_helper,
                    fastapi_request=request,
                )

                assert result == mock_response
                mock_service.search_tracked_book.assert_called_once_with(
                    tracked_book_id=1,
                    max_results_per_indexer=100,
                    indexer_ids=None,
                )
                mock_helper.check_read_permission.assert_called_once_with(user)

    def test_search_tracked_book_not_found(
        self,
        session: DummySession,
        user: User,
        valid_fernet_key: str,
    ) -> None:
        request_data = PVRSearchRequest(tracked_book_id=1)
        request = MagicMock()

        with patch(
            "bookcard.api.routes.pvr_search._get_tracked_book_search_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.search_tracked_book.side_effect = ValueError(
                "Tracked book 1 not found"
            )
            mock_get_service.return_value = mock_service

            with patch(
                "bookcard.api.routes.pvr_search.BookPermissionHelper"
            ) as mock_helper_cls:
                with pytest.raises(HTTPException) as exc_info:
                    pvr_search_routes.search_tracked_book(
                        request=request_data,
                        session=session,
                        current_user=user,
                        permission_helper=mock_helper_cls.return_value,
                        fastapi_request=request,
                    )

                assert isinstance(exc_info.value, HTTPException)
                assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestGetSearchResults:
    def test_get_search_results_delegation(
        self,
        session: DummySession,
        user: User,
        valid_fernet_key: str,
    ) -> None:
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with patch(
            "bookcard.api.routes.pvr_search._get_tracked_book_search_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_response = PVRSearchResultsResponse(
                tracked_book_id=1,
                results=[],
                total=0,
            )
            mock_service.get_search_results.return_value = mock_response
            mock_get_service.return_value = mock_service

            with patch(
                "bookcard.api.routes.pvr_search.BookPermissionHelper"
            ) as mock_helper_cls:
                result = pvr_search_routes.get_search_results(
                    tracked_book_id=1,
                    session=session,
                    current_user=user,
                    permission_helper=mock_helper_cls.return_value,
                    fastapi_request=request,
                )

                assert result == mock_response
                mock_service.get_search_results.assert_called_once_with(1)

    def test_get_search_results_not_found(
        self,
        session: DummySession,
        user: User,
    ) -> None:
        request = MagicMock()

        with patch(
            "bookcard.api.routes.pvr_search._get_tracked_book_search_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_search_results.side_effect = ValueError(
                "No search results available"
            )
            mock_get_service.return_value = mock_service

            with patch(
                "bookcard.api.routes.pvr_search.BookPermissionHelper"
            ) as mock_helper_cls:
                with pytest.raises(HTTPException) as exc_info:
                    pvr_search_routes.get_search_results(
                        tracked_book_id=1,
                        session=session,
                        current_user=user,
                        permission_helper=mock_helper_cls.return_value,
                        fastapi_request=request,
                    )

                assert isinstance(exc_info.value, HTTPException)
                assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestTriggerDownload:
    def test_trigger_download_delegation(
        self,
        session: DummySession,
        user: User,
        valid_fernet_key: str,
    ) -> None:
        request_data = PVRDownloadRequest(release_index=0)
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with patch(
            "bookcard.api.routes.pvr_search._get_tracked_book_search_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_response = PVRDownloadResponse(
                tracked_book_id=1,
                download_item_id=1,
                release_title="Test",
                message="Download initiated",
            )
            mock_service.trigger_download.return_value = mock_response
            mock_get_service.return_value = mock_service

            with patch(
                "bookcard.api.routes.pvr_search.PermissionService"
            ) as mock_perm_cls:
                result = pvr_search_routes.trigger_download(
                    tracked_book_id=1,
                    request=request_data,
                    session=session,
                    current_user=user,
                    fastapi_request=request,
                )

                assert result == mock_response
                mock_service.trigger_download.assert_called_once()
                mock_perm_cls.return_value.check_permission.assert_called_once()

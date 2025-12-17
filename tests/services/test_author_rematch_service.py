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

"""Tests for AuthorRematchService to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.author_metadata import AuthorMapping
from bookcard.models.config import Library
from bookcard.models.core import Author
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.author_rematch_service import AuthorRematchService
from bookcard.services.author_service import AuthorService
from bookcard.services.config_service import LibraryService
from bookcard.services.library_scanning.pipeline.link_components import (
    AuthorMappingRepository,
)
from bookcard.services.library_scanning.workers.progress import JobProgressTracker
from bookcard.services.messaging.base import MessageBroker
from bookcard.services.messaging.redis_broker import RedisBroker

if TYPE_CHECKING:
    from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_author_service() -> MagicMock:
    """Create a mock author service."""
    return MagicMock(spec=AuthorService)


@pytest.fixture
def mock_library_repo() -> MagicMock:
    """Create a mock library repository."""
    return MagicMock(spec=LibraryRepository)


@pytest.fixture
def mock_library_service() -> MagicMock:
    """Create a mock library service."""
    return MagicMock(spec=LibraryService)


@pytest.fixture
def mock_message_broker() -> MagicMock:
    """Create a mock message broker."""
    return MagicMock(spec=RedisBroker)


@pytest.fixture
def active_library() -> Library:
    """Create an active library."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )


@pytest.fixture
def author_mapping() -> AuthorMapping:
    """Create sample author mapping."""
    return AuthorMapping(
        id=1,
        calibre_author_id=10,
        author_metadata_id=1,
        library_id=1,
        is_verified=False,
    )


@pytest.fixture
def calibre_author() -> Author:
    """Create sample Calibre author."""
    return Author(id=10, name="Test Author", sort="Author, Test")


@pytest.fixture
def rematch_service(
    session: DummySession,
    mock_author_service: MagicMock,
    mock_library_repo: MagicMock | None,
    mock_library_service: MagicMock | None,
    mock_message_broker: MagicMock | None,
) -> AuthorRematchService:
    """Create AuthorRematchService instance."""
    return AuthorRematchService(
        session=session,  # type: ignore[arg-type]
        author_service=mock_author_service,
        library_repo=mock_library_repo,
        library_service=mock_library_service,
        message_broker=mock_message_broker,
    )


@pytest.fixture
def rematch_service_no_deps(
    session: DummySession,
    mock_author_service: MagicMock,
) -> AuthorRematchService:
    """Create AuthorRematchService without optional dependencies."""
    return AuthorRematchService(
        session=session,  # type: ignore[arg-type]
        author_service=mock_author_service,
    )


# ============================================================================
# Initialization Tests
# ============================================================================


class TestAuthorRematchServiceInit:
    """Test AuthorRematchService initialization."""

    def test_init_with_all_dependencies(
        self,
        session: DummySession,
        mock_author_service: MagicMock,
        mock_library_repo: MagicMock,
        mock_library_service: MagicMock,
        mock_message_broker: MagicMock,
    ) -> None:
        """Test __init__ with all dependencies provided."""
        service = AuthorRematchService(
            session=session,  # type: ignore[arg-type]
            author_service=mock_author_service,
            library_repo=mock_library_repo,
            library_service=mock_library_service,
            message_broker=mock_message_broker,
        )

        assert service._session == session
        assert service._author_service == mock_author_service
        assert service._library_repo == mock_library_repo
        assert service._library_service == mock_library_service
        assert service._message_broker == mock_message_broker

    def test_init_without_optional_dependencies(
        self,
        session: DummySession,
        mock_author_service: MagicMock,
    ) -> None:
        """Test __init__ creates dependencies when not provided."""
        service = AuthorRematchService(
            session=session,  # type: ignore[arg-type]
            author_service=mock_author_service,
        )

        assert service._session == session
        assert service._author_service == mock_author_service
        assert isinstance(service._library_repo, LibraryRepository)
        assert isinstance(service._library_service, LibraryService)
        assert service._message_broker is None


# ============================================================================
# _raise_no_active_library_error Tests
# ============================================================================


class TestRaiseNoActiveLibraryError:
    """Test _raise_no_active_library_error method."""

    def test_raise_no_active_library_error(
        self,
        rematch_service: AuthorRematchService,
    ) -> None:
        """Test _raise_no_active_library_error raises ValueError."""
        with pytest.raises(ValueError, match="No active library found"):
            rematch_service._raise_no_active_library_error()


# ============================================================================
# normalize_openlibrary_key Tests
# ============================================================================


class TestNormalizeOpenlibraryKey:
    """Test normalize_openlibrary_key method."""

    @pytest.mark.parametrize(
        ("input_key", "expected"),
        [
            ("OL123A", "/authors/OL123A"),
            ("/authors/OL123A", "/authors/OL123A"),
            ("authors/OL123A", "/authors/OL123A"),
            ("/authors/authors/OL123A", "/authors/authors/OL123A"),
            ("  OL123A  ", "/authors/OL123A"),
            ("/authors/", "/authors/"),
        ],
    )
    def test_normalize_openlibrary_key(
        self,
        input_key: str,
        expected: str,
        rematch_service: AuthorRematchService,
    ) -> None:
        """Test normalize_openlibrary_key with various formats."""
        result = rematch_service.normalize_openlibrary_key(input_key)

        assert result == expected


# ============================================================================
# determine_openlibrary_key Tests
# ============================================================================


class TestDetermineOpenlibraryKey:
    """Test determine_openlibrary_key method."""

    def test_determine_openlibrary_key_with_provided_olid(
        self,
        rematch_service: AuthorRematchService,
    ) -> None:
        """Test determine_openlibrary_key with provided OLID."""
        provided_olid = "OL123A"
        author_data: dict[str, object] = {}

        result = rematch_service.determine_openlibrary_key(provided_olid, author_data)

        assert result == "/authors/OL123A"

    def test_determine_openlibrary_key_with_provided_olid_whitespace(
        self,
        rematch_service: AuthorRematchService,
    ) -> None:
        """Test determine_openlibrary_key with provided OLID with whitespace."""
        provided_olid = "  OL123A  "
        author_data: dict[str, object] = {}

        result = rematch_service.determine_openlibrary_key(provided_olid, author_data)

        assert result == "/authors/OL123A"

    def test_determine_openlibrary_key_with_existing_key(
        self,
        rematch_service: AuthorRematchService,
    ) -> None:
        """Test determine_openlibrary_key with existing key in author_data."""
        provided_olid = None
        author_data: dict[str, object] = {"key": "OL123A"}

        result = rematch_service.determine_openlibrary_key(provided_olid, author_data)

        assert result == "OL123A"

    def test_determine_openlibrary_key_with_placeholder_key(
        self,
        rematch_service: AuthorRematchService,
    ) -> None:
        """Test determine_openlibrary_key raises error with placeholder key."""
        provided_olid = None
        author_data: dict[str, object] = {"key": "calibre-123"}

        with pytest.raises(
            ValueError,
            match="Author does not have an OpenLibrary key",
        ):
            rematch_service.determine_openlibrary_key(provided_olid, author_data)

    def test_determine_openlibrary_key_no_key_no_olid(
        self,
        rematch_service: AuthorRematchService,
    ) -> None:
        """Test determine_openlibrary_key raises error with no key."""
        provided_olid = None
        author_data: dict[str, object] = {}

        with pytest.raises(
            ValueError,
            match="Author does not have an OpenLibrary key and no OLID was provided",
        ):
            rematch_service.determine_openlibrary_key(provided_olid, author_data)

    def test_determine_openlibrary_key_empty_olid_string(
        self,
        rematch_service: AuthorRematchService,
    ) -> None:
        """Test determine_openlibrary_key with empty OLID string."""
        provided_olid = "   "
        author_data: dict[str, object] = {"key": "OL123A"}

        result = rematch_service.determine_openlibrary_key(provided_olid, author_data)

        assert result == "OL123A"

    def test_determine_openlibrary_key_placeholder_key_not_string(
        self,
        rematch_service: AuthorRematchService,
    ) -> None:
        """Test determine_openlibrary_key with non-string placeholder key."""
        provided_olid = None
        author_data: dict[str, object] = {"key": 123}

        # Should not raise error for placeholder check since key is not a string
        # It will be converted to string and used
        result = rematch_service.determine_openlibrary_key(provided_olid, author_data)

        assert result == "123"


# ============================================================================
# _resolve_via_metadata_id Tests
# ============================================================================


class TestResolveViaMetadataId:
    """Test _resolve_via_metadata_id method."""

    def test_resolve_via_metadata_id_success(
        self,
        rematch_service: AuthorRematchService,
        session: DummySession,
        author_mapping: AuthorMapping,
    ) -> None:
        """Test _resolve_via_metadata_id with found mapping."""
        author_metadata_id = 1

        session.set_exec_result([author_mapping])

        result = rematch_service._resolve_via_metadata_id(author_metadata_id)

        assert result == (1, 10, 1)

    def test_resolve_via_metadata_id_not_found(
        self,
        rematch_service: AuthorRematchService,
        session: DummySession,
    ) -> None:
        """Test _resolve_via_metadata_id raises error when mapping not found."""
        author_metadata_id = 999

        session.set_exec_result([])

        with pytest.raises(ValueError, match="Author mapping not found"):
            rematch_service._resolve_via_metadata_id(author_metadata_id)


# ============================================================================
# _resolve_via_calibre_prefix Tests
# ============================================================================


class TestResolveViaCalibrePrefix:
    """Test _resolve_via_calibre_prefix method."""

    def test_resolve_via_calibre_prefix_with_mapping(
        self,
        rematch_service: AuthorRematchService,
        session: DummySession,
        active_library: Library,
        author_mapping: AuthorMapping,
    ) -> None:
        """Test _resolve_via_calibre_prefix with existing mapping."""
        author_id = "calibre-10"
        rematch_service._library_service.get_active_library.return_value = (  # type: ignore[assignment]
            active_library
        )

        with patch(
            "bookcard.services.author_rematch_service.AuthorMappingRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock(spec=AuthorMappingRepository)
            mock_repo_class.return_value = mock_repo
            mock_repo.find_by_calibre_author_id_and_library.return_value = (
                author_mapping
            )

            result = rematch_service._resolve_via_calibre_prefix(author_id)

            assert result == (1, 10, 1)

    def test_resolve_via_calibre_prefix_without_mapping(
        self,
        rematch_service: AuthorRematchService,
        session: DummySession,
        active_library: Library,
    ) -> None:
        """Test _resolve_via_calibre_prefix without existing mapping."""
        author_id = "calibre-10"
        rematch_service._library_service.get_active_library.return_value = (  # type: ignore[assignment]
            active_library
        )

        with patch(
            "bookcard.services.author_rematch_service.AuthorMappingRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock(spec=AuthorMappingRepository)
            mock_repo_class.return_value = mock_repo
            mock_repo.find_by_calibre_author_id_and_library.return_value = None

            result = rematch_service._resolve_via_calibre_prefix(author_id)

            assert result == (1, 10, None)

    def test_resolve_via_calibre_prefix_no_active_library(
        self,
        rematch_service: AuthorRematchService,
    ) -> None:
        """Test _resolve_via_calibre_prefix raises error when no active library."""
        author_id = "calibre-10"
        rematch_service._library_service.get_active_library.return_value = None  # type: ignore[assignment]

        with pytest.raises(ValueError, match="No active library found"):
            rematch_service._resolve_via_calibre_prefix(author_id)

    def test_resolve_via_calibre_prefix_library_no_id(
        self,
        rematch_service: AuthorRematchService,
        active_library: Library,
    ) -> None:
        """Test _resolve_via_calibre_prefix raises error when library has no ID."""
        author_id = "calibre-10"
        active_library.id = None
        rematch_service._library_service.get_active_library.return_value = (  # type: ignore[assignment]
            active_library
        )

        with pytest.raises(ValueError, match="No active library found"):
            rematch_service._resolve_via_calibre_prefix(author_id)

    def test_resolve_via_calibre_prefix_invalid_format(
        self,
        rematch_service: AuthorRematchService,
    ) -> None:
        """Test _resolve_via_calibre_prefix raises error with invalid format."""
        author_id = "calibre-invalid"

        with pytest.raises(ValueError, match="Invalid author ID format"):
            rematch_service._resolve_via_calibre_prefix(author_id)


# ============================================================================
# resolve_library_and_author_ids Tests
# ============================================================================


class TestResolveLibraryAndAuthorIds:
    """Test resolve_library_and_author_ids method."""

    def test_resolve_library_and_author_ids_via_metadata_id(
        self,
        rematch_service: AuthorRematchService,
        session: DummySession,
        author_mapping: AuthorMapping,
    ) -> None:
        """Test resolve_library_and_author_ids via metadata ID."""
        author_id = "1"
        author_data: dict[str, object] = {"id": 1}

        session.set_exec_result([author_mapping])

        result = rematch_service.resolve_library_and_author_ids(author_id, author_data)

        assert result == (1, 10, 1)

    def test_resolve_library_and_author_ids_via_calibre_prefix(
        self,
        rematch_service: AuthorRematchService,
        session: DummySession,
        active_library: Library,
        author_mapping: AuthorMapping,
    ) -> None:
        """Test resolve_library_and_author_ids via calibre- prefix."""
        author_id = "calibre-10"
        author_data: dict[str, object] = {}

        rematch_service._library_service.get_active_library.return_value = (  # type: ignore[assignment]
            active_library
        )

        with patch(
            "bookcard.services.author_rematch_service.AuthorMappingRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock(spec=AuthorMappingRepository)
            mock_repo_class.return_value = mock_repo
            mock_repo.find_by_calibre_author_id_and_library.return_value = (
                author_mapping
            )

            result = rematch_service.resolve_library_and_author_ids(
                author_id, author_data
            )

            assert result == (1, 10, 1)

    def test_resolve_library_and_author_ids_metadata_id_not_int(
        self,
        rematch_service: AuthorRematchService,
        session: DummySession,
        active_library: Library,
        author_mapping: AuthorMapping,
    ) -> None:
        """Test resolve_library_and_author_ids with non-int metadata ID."""
        author_id = "calibre-10"
        author_data: dict[str, object] = {"id": "not-an-int"}

        rematch_service._library_service.get_active_library.return_value = (  # type: ignore[assignment]
            active_library
        )

        with patch(
            "bookcard.services.author_rematch_service.AuthorMappingRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock(spec=AuthorMappingRepository)
            mock_repo_class.return_value = mock_repo
            mock_repo.find_by_calibre_author_id_and_library.return_value = (
                author_mapping
            )

            result = rematch_service.resolve_library_and_author_ids(
                author_id, author_data
            )

            assert result == (1, 10, 1)

    def test_resolve_library_and_author_ids_no_metadata_id_no_calibre(
        self,
        rematch_service: AuthorRematchService,
    ) -> None:
        """Test resolve_library_and_author_ids raises error with no valid ID."""
        author_id = "invalid-format"
        author_data: dict[str, object] = {}

        with pytest.raises(ValueError, match="Author metadata ID not found"):
            rematch_service.resolve_library_and_author_ids(author_id, author_data)


# ============================================================================
# get_calibre_author_dict Tests
# ============================================================================


class TestGetCalibreAuthorDict:
    """Test get_calibre_author_dict method."""

    def test_get_calibre_author_dict_success(
        self,
        rematch_service: AuthorRematchService,
        mock_library_repo: MagicMock,
        active_library: Library,
        calibre_author: Author,
    ) -> None:
        """Test get_calibre_author_dict with found author."""
        library_id = 1
        calibre_author_id = 10

        mock_library_repo.get.return_value = active_library
        rematch_service._library_repo = mock_library_repo

        with patch(
            "bookcard.services.author_rematch_service.CalibreBookRepository"
        ) as mock_repo_class:
            mock_calibre_repo = MagicMock()
            mock_calibre_session = MagicMock()
            mock_calibre_session.__enter__.return_value = mock_calibre_session
            mock_calibre_session.__exit__.return_value = None
            mock_calibre_session.exec.return_value.first.return_value = calibre_author
            mock_calibre_repo.get_session.return_value = mock_calibre_session
            mock_repo_class.return_value = mock_calibre_repo

            result = rematch_service.get_calibre_author_dict(
                library_id, calibre_author_id
            )

            assert isinstance(result, dict)
            assert result["id"] == 10
            assert result["name"] == "Test Author"

    def test_get_calibre_author_dict_library_not_found(
        self,
        rematch_service: AuthorRematchService,
        mock_library_repo: MagicMock,
    ) -> None:
        """Test get_calibre_author_dict raises error when library not found."""
        library_id = 999
        calibre_author_id = 10

        mock_library_repo.get.return_value = None
        rematch_service._library_repo = mock_library_repo

        with pytest.raises(
            ValueError, match="Library or Calibre database path not found"
        ):
            rematch_service.get_calibre_author_dict(library_id, calibre_author_id)

    def test_get_calibre_author_dict_no_db_path(
        self,
        rematch_service: AuthorRematchService,
        mock_library_repo: MagicMock,
        active_library: Library,
    ) -> None:
        """Test get_calibre_author_dict raises error when library has no db path."""
        library_id = 1
        calibre_author_id = 10

        active_library.calibre_db_path = None
        mock_library_repo.get.return_value = active_library
        rematch_service._library_repo = mock_library_repo

        with pytest.raises(
            ValueError, match="Library or Calibre database path not found"
        ):
            rematch_service.get_calibre_author_dict(library_id, calibre_author_id)

    def test_get_calibre_author_dict_author_not_found(
        self,
        rematch_service: AuthorRematchService,
        mock_library_repo: MagicMock,
        active_library: Library,
    ) -> None:
        """Test get_calibre_author_dict raises error when author not found."""
        library_id = 1
        calibre_author_id = 999

        mock_library_repo.get.return_value = active_library
        rematch_service._library_repo = mock_library_repo

        with patch(
            "bookcard.services.author_rematch_service.CalibreBookRepository"
        ) as mock_repo_class:
            mock_calibre_repo = MagicMock()
            mock_calibre_session = MagicMock()
            mock_calibre_session.__enter__.return_value = mock_calibre_session
            mock_calibre_session.__exit__.return_value = None
            mock_calibre_session.exec.return_value.first.return_value = None
            mock_calibre_repo.get_session.return_value = mock_calibre_session
            mock_repo_class.return_value = mock_calibre_repo

            with pytest.raises(ValueError, match="Calibre author not found"):
                rematch_service.get_calibre_author_dict(library_id, calibre_author_id)

    def test_get_calibre_author_dict_custom_db_file(
        self,
        rematch_service: AuthorRematchService,
        mock_library_repo: MagicMock,
        active_library: Library,
        calibre_author: Author,
    ) -> None:
        """Test get_calibre_author_dict with custom database file."""
        library_id = 1
        calibre_author_id = 10
        active_library.calibre_db_file = "custom.db"

        mock_library_repo.get.return_value = active_library
        rematch_service._library_repo = mock_library_repo

        with patch(
            "bookcard.services.author_rematch_service.CalibreBookRepository"
        ) as mock_repo_class:
            mock_calibre_repo = MagicMock()
            mock_calibre_session = MagicMock()
            mock_calibre_session.__enter__.return_value = mock_calibre_session
            mock_calibre_session.__exit__.return_value = None
            mock_calibre_session.exec.return_value.first.return_value = calibre_author
            mock_calibre_repo.get_session.return_value = mock_calibre_session
            mock_repo_class.return_value = mock_calibre_repo

            result = rematch_service.get_calibre_author_dict(
                library_id, calibre_author_id
            )

            assert isinstance(result, dict)
            mock_repo_class.assert_called_once_with("/path/to/library", "custom.db")


# ============================================================================
# enqueue_rematch_job Tests
# ============================================================================


class TestEnqueueRematchJob:
    """Test enqueue_rematch_job method."""

    def test_enqueue_rematch_job_with_metadata_id(
        self,
        rematch_service: AuthorRematchService,
        mock_message_broker: MagicMock,
    ) -> None:
        """Test enqueue_rematch_job with author metadata ID."""
        library_id = 1
        author_dict: dict[str, object] = {"id": 10, "name": "Test Author"}
        openlibrary_key = "/authors/OL123A"
        author_metadata_id = 1

        rematch_service._message_broker = mock_message_broker
        mock_message_broker.__class__ = RedisBroker

        with patch(
            "bookcard.services.author_rematch_service.JobProgressTracker"
        ) as mock_tracker_class:
            mock_tracker = MagicMock(spec=JobProgressTracker)
            mock_tracker_class.return_value = mock_tracker

            rematch_service.enqueue_rematch_job(
                library_id, author_dict, openlibrary_key, author_metadata_id
            )

            mock_tracker.initialize_job.assert_called_once_with(library_id, 1, None)
            mock_message_broker.publish.assert_called_once()
            call_args = mock_message_broker.publish.call_args
            assert call_args[0][0] == "match_queue"
            message = call_args[0][1]
            assert message["library_id"] == library_id
            assert message["author"] == author_dict
            assert message["openlibrary_key"] == openlibrary_key
            assert message["target_author_metadata_id"] == author_metadata_id

    def test_enqueue_rematch_job_without_metadata_id(
        self,
        rematch_service: AuthorRematchService,
        mock_message_broker: MagicMock,
    ) -> None:
        """Test enqueue_rematch_job without author metadata ID."""
        library_id = 1
        author_dict: dict[str, object] = {"id": 10, "name": "Test Author"}
        openlibrary_key = "/authors/OL123A"
        author_metadata_id = None

        rematch_service._message_broker = mock_message_broker
        mock_message_broker.__class__ = RedisBroker

        with patch(
            "bookcard.services.author_rematch_service.JobProgressTracker"
        ) as mock_tracker_class:
            mock_tracker = MagicMock(spec=JobProgressTracker)
            mock_tracker_class.return_value = mock_tracker

            rematch_service.enqueue_rematch_job(
                library_id, author_dict, openlibrary_key, author_metadata_id
            )

            call_args = mock_message_broker.publish.call_args
            message = call_args[0][1]
            assert "target_author_metadata_id" not in message

    def test_enqueue_rematch_job_no_broker(
        self,
        rematch_service: AuthorRematchService,
    ) -> None:
        """Test enqueue_rematch_job raises error when no broker."""
        library_id = 1
        author_dict: dict[str, object] = {"id": 10, "name": "Test Author"}
        openlibrary_key = "/authors/OL123A"
        author_metadata_id = None

        rematch_service._message_broker = None

        with pytest.raises(TypeError, match="Message broker not available"):
            rematch_service.enqueue_rematch_job(
                library_id, author_dict, openlibrary_key, author_metadata_id
            )

    def test_enqueue_rematch_job_wrong_broker_type(
        self,
        rematch_service: AuthorRematchService,
    ) -> None:
        """Test enqueue_rematch_job raises error with wrong broker type."""
        library_id = 1
        author_dict: dict[str, object] = {"id": 10, "name": "Test Author"}
        openlibrary_key = "/authors/OL123A"
        author_metadata_id = None

        wrong_broker = MagicMock(spec=MessageBroker)
        rematch_service._message_broker = wrong_broker

        with pytest.raises(TypeError, match="Message broker not available"):
            rematch_service.enqueue_rematch_job(
                library_id, author_dict, openlibrary_key, author_metadata_id
            )

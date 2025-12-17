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

"""Tests for AuthorDictBuilder to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from bookcard.models.author_metadata import (
    AuthorAlternateName,
    AuthorLink,
    AuthorMapping,
    AuthorMetadata,
    AuthorPhoto,
    AuthorRemoteId,
    AuthorUserMetadata,
    AuthorUserPhoto,
    AuthorWork,
    WorkSubject,
)
from bookcard.services.author.dict_builder import AuthorDictBuilder

if TYPE_CHECKING:
    from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def dict_builder(session: DummySession) -> AuthorDictBuilder:
    """Create AuthorDictBuilder instance."""
    return AuthorDictBuilder(session)  # type: ignore[arg-type]


@pytest.fixture
def author_metadata() -> AuthorMetadata:
    """Create sample author metadata."""
    return AuthorMetadata(
        id=1,
        openlibrary_key="OL123A",
        name="Test Author",
    )


@pytest.fixture
def author_metadata_unmatched() -> AuthorMetadata:
    """Create unmatched author metadata without OpenLibrary key."""
    return AuthorMetadata(
        id=1,
        openlibrary_key=None,
        name="Unmatched Author",
    )


@pytest.fixture
def author_metadata_transient() -> AuthorMetadata:
    """Create transient unmatched author metadata."""
    author = AuthorMetadata(
        id=None,
        openlibrary_key=None,
        name="Transient Author",
    )
    # Set _calibre_id attribute to simulate transient unmatched author
    author._calibre_id = 42
    return author


# ============================================================================
# build Tests - Unmatched Transient
# ============================================================================


class TestBuildUnmatchedTransient:
    """Test build method for transient unmatched authors."""

    def test_build_unmatched_transient(
        self,
        dict_builder: AuthorDictBuilder,
        author_metadata_transient: AuthorMetadata,
    ) -> None:
        """Test build for transient unmatched author (id is None, calibre_id exists)."""
        result = dict_builder.build(author_metadata_transient)

        assert result["name"] == "Transient Author"
        assert result["key"] == "calibre-42"
        assert result["calibre_id"] == 42
        assert result["is_unmatched"] is True
        assert result["location"] == "Local Library (Unmatched)"


# ============================================================================
# build Tests - Unmatched Persisted
# ============================================================================


class TestBuildUnmatchedPersisted:
    """Test build method for persisted unmatched authors."""

    def test_build_unmatched_persisted_no_mappings(
        self,
        dict_builder: AuthorDictBuilder,
        session: DummySession,
        author_metadata_unmatched: AuthorMetadata,
    ) -> None:
        """Test build for persisted unmatched author without mappings."""
        session.set_exec_result([])  # type: ignore[attr-defined]
        author_metadata_unmatched.remote_ids = []
        author_metadata_unmatched.photos = []
        author_metadata_unmatched.alternate_names = []
        author_metadata_unmatched.links = []
        author_metadata_unmatched.works = []

        result = dict_builder.build(author_metadata_unmatched)

        assert result["name"] == "Unmatched Author"
        assert result["key"] == "local-1"
        assert result["calibre_id"] is None
        assert result["is_unmatched"] is True

    def test_build_unmatched_persisted_with_mappings(
        self,
        dict_builder: AuthorDictBuilder,
        session: DummySession,
        author_metadata_unmatched: AuthorMetadata,
    ) -> None:
        """Test build for persisted unmatched author with mappings."""
        mapping = AuthorMapping(
            id=1,
            author_metadata_id=1,
            calibre_author_id=42,
            library_id=1,
        )
        session.set_exec_result([mapping])  # type: ignore[attr-defined]
        author_metadata_unmatched.remote_ids = []
        author_metadata_unmatched.photos = []
        author_metadata_unmatched.alternate_names = []
        author_metadata_unmatched.links = []
        author_metadata_unmatched.works = []

        result = dict_builder.build(author_metadata_unmatched)

        assert result["name"] == "Unmatched Author"
        assert result["key"] == "calibre-42"
        assert result["calibre_id"] == 42
        assert result["is_unmatched"] is True

    def test_build_unmatched_persisted_loads_relationships(
        self,
        dict_builder: AuthorDictBuilder,
        session: DummySession,
        author_metadata_unmatched: AuthorMetadata,
    ) -> None:
        """Test build for persisted unmatched author loads relationships."""
        mapping = AuthorMapping(
            id=1,
            author_metadata_id=1,
            calibre_author_id=42,
            library_id=1,
        )
        remote_id = AuthorRemoteId(
            id=1,
            author_metadata_id=1,
            identifier_type="viaf",
            identifier_value="123456",
        )
        photo = AuthorPhoto(
            id=1,
            author_metadata_id=1,
            openlibrary_photo_id=12345,
        )
        alt_name = AuthorAlternateName(
            id=1,
            author_metadata_id=1,
            name="Alt Name",
        )
        link = AuthorLink(
            id=1,
            author_metadata_id=1,
            url="https://example.com",
            title="Website",
            link_type="web",
        )
        work = AuthorWork(
            id=1,
            author_metadata_id=1,
            work_key="OL1W",
            rank=0,
        )
        work.subjects = [
            WorkSubject(
                author_work_id=work.id,
                subject_name="Fiction",
                rank=0,
            ),
        ]

        # Set up session results for multiple exec calls
        session.set_exec_result([mapping])  # type: ignore[attr-defined]
        session.add_exec_result([remote_id])  # type: ignore[attr-defined]
        session.add_exec_result([photo])  # type: ignore[attr-defined]
        session.add_exec_result([alt_name])  # type: ignore[attr-defined]
        session.add_exec_result([link])  # type: ignore[attr-defined]
        session.add_exec_result([work])  # type: ignore[attr-defined]
        session.add_exec_result([])  # type: ignore[attr-defined]  # user_photos

        result = dict_builder.build(author_metadata_unmatched)

        assert result["name"] == "Unmatched Author"
        assert "remote_ids" in result
        assert "photos" in result
        assert "alternate_names" in result
        assert "links" in result
        assert "genres" in result

    def test_build_unmatched_persisted_loads_user_photos(
        self,
        dict_builder: AuthorDictBuilder,
        session: DummySession,
    ) -> None:
        """Test build for persisted unmatched author loads user photos."""
        # Create a mock author to avoid SQLAlchemy relationship conflicts
        author = MagicMock(spec=AuthorMetadata)
        author.id = 1
        author.openlibrary_key = None
        author.name = "Unmatched Author"
        author.location = None
        author.remote_ids = []
        author.photos = []
        author.alternate_names = []
        author.links = []
        author.works = []
        author.mappings = []
        # user_photos attribute doesn't exist initially
        delattr(author, "user_photos") if hasattr(author, "user_photos") else None

        mapping = AuthorMapping(
            id=1,
            author_metadata_id=1,
            calibre_author_id=42,
            library_id=1,
        )
        user_photo = AuthorUserPhoto(
            id=1,
            author_metadata_id=1,
            file_path="authors/1/photo.jpg",
            file_name="photo.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            is_primary=True,
            order=0,
            created_at=datetime.now(UTC),
        )

        session.set_exec_result([mapping])  # type: ignore[attr-defined]
        session.add_exec_result([])  # type: ignore[attr-defined]  # remote_ids
        session.add_exec_result([])  # type: ignore[attr-defined]  # photos
        session.add_exec_result([])  # type: ignore[attr-defined]  # alternate_names
        session.add_exec_result([])  # type: ignore[attr-defined]  # links
        session.add_exec_result([])  # type: ignore[attr-defined]  # works
        session.add_exec_result([user_photo])  # type: ignore[attr-defined]  # user_photos

        result = dict_builder.build(author)  # type: ignore[arg-type]

        assert "user_photos" in result
        assert len(result["user_photos"]) == 1  # type: ignore[index]


# ============================================================================
# build Tests - Matched
# ============================================================================


class TestBuildMatched:
    """Test build method for matched authors."""

    def test_build_matched_loads_user_metadata(
        self,
        dict_builder: AuthorDictBuilder,
        session: DummySession,
    ) -> None:
        """Test build for matched author loads user metadata when not present."""
        # Create a mock author to avoid SQLAlchemy relationship conflicts
        author = MagicMock(spec=AuthorMetadata)
        author.id = 1
        author.openlibrary_key = "OL123A"
        author.name = "Test Author"
        author.remote_ids = []
        author.photos = []
        author.alternate_names = []
        author.links = []
        author.works = []
        author.mappings = []
        # user_metadata and user_photos attributes don't exist initially
        delattr(author, "user_metadata") if hasattr(author, "user_metadata") else None
        delattr(author, "user_photos") if hasattr(author, "user_photos") else None

        user_metadata = AuthorUserMetadata(
            id=1,
            author_metadata_id=1,
            field_name="genres",
            field_value=["Fiction", "Sci-Fi"],
            is_user_defined=True,
        )

        # Order matches execution: _ensure_relationships_loaded first, then mappings, then user_metadata, then user_photos
        session.set_exec_result([])  # type: ignore[attr-defined]  # remote_ids (from _ensure_relationships_loaded)
        session.add_exec_result([])  # type: ignore[attr-defined]  # photos (from _ensure_relationships_loaded)
        session.add_exec_result([])  # type: ignore[attr-defined]  # alternate_names (from _ensure_relationships_loaded)
        session.add_exec_result([])  # type: ignore[attr-defined]  # links (from _ensure_relationships_loaded)
        session.add_exec_result([])  # type: ignore[attr-defined]  # works (from _ensure_relationships_loaded)
        session.add_exec_result([])  # type: ignore[attr-defined]  # mappings
        session.add_exec_result([user_metadata])  # type: ignore[attr-defined]  # user_metadata
        session.add_exec_result([])  # type: ignore[attr-defined]  # user_photos

        result = dict_builder.build(author)  # type: ignore[arg-type]

        assert result["name"] == "Test Author"
        assert result["key"] == "OL123A"

    def test_build_matched_loads_user_photos(
        self,
        dict_builder: AuthorDictBuilder,
        session: DummySession,
    ) -> None:
        """Test build for matched author loads user photos when not present."""
        # Create a mock author to avoid SQLAlchemy relationship conflicts
        author = MagicMock(spec=AuthorMetadata)
        author.id = 1
        author.openlibrary_key = "OL123A"
        author.name = "Test Author"
        author.remote_ids = []
        author.photos = []
        author.alternate_names = []
        author.links = []
        author.works = []
        author.mappings = []
        # user_metadata and user_photos attributes don't exist initially
        delattr(author, "user_metadata") if hasattr(author, "user_metadata") else None
        delattr(author, "user_photos") if hasattr(author, "user_photos") else None

        user_photo = AuthorUserPhoto(
            id=1,
            author_metadata_id=1,
            file_path="authors/1/photo.jpg",
            file_name="photo.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            is_primary=True,
            order=0,
            created_at=datetime.now(UTC),
        )

        # Order matches execution: _ensure_relationships_loaded first, then mappings, then user_metadata, then user_photos
        session.set_exec_result([])  # type: ignore[attr-defined]  # remote_ids (from _ensure_relationships_loaded)
        session.add_exec_result([])  # type: ignore[attr-defined]  # photos (from _ensure_relationships_loaded)
        session.add_exec_result([])  # type: ignore[attr-defined]  # alternate_names (from _ensure_relationships_loaded)
        session.add_exec_result([])  # type: ignore[attr-defined]  # links (from _ensure_relationships_loaded)
        session.add_exec_result([])  # type: ignore[attr-defined]  # works (from _ensure_relationships_loaded)
        session.add_exec_result([])  # type: ignore[attr-defined]  # mappings
        session.add_exec_result([])  # type: ignore[attr-defined]  # user_metadata
        session.add_exec_result([user_photo])  # type: ignore[attr-defined]  # user_photos

        result = dict_builder.build(author)  # type: ignore[arg-type]

        assert result["name"] == "Test Author"
        assert "user_photos" in result


# ============================================================================
# _add_user_photos_field Tests
# ============================================================================


class TestAddUserPhotosField:
    """Test _add_user_photos_field method."""

    def test_add_user_photos_skips_photo_with_none_id(
        self,
        dict_builder: AuthorDictBuilder,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test _add_user_photos_field skips photos with None id."""
        user_photo_no_id = AuthorUserPhoto(
            id=None,
            author_metadata_id=1,
            file_path="authors/1/photo.jpg",
            file_name="photo.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            is_primary=False,
            order=0,
            created_at=datetime.now(UTC),
        )
        user_photo_with_id = AuthorUserPhoto(
            id=1,
            author_metadata_id=1,
            file_path="authors/1/photo2.jpg",
            file_name="photo2.jpg",
            file_size=2048,
            mime_type="image/jpeg",
            is_primary=True,
            order=1,
            created_at=datetime.now(UTC),
        )
        author_metadata.user_photos = [user_photo_no_id, user_photo_with_id]
        author_metadata.id = 1

        author_data: dict[str, object] = {}

        dict_builder._add_user_photos_field(author_data, author_metadata)

        assert "user_photos" in author_data
        photos = author_data["user_photos"]  # type: ignore[assignment]
        assert isinstance(photos, list)
        assert len(photos) == 1  # Only photo with id should be included
        assert photos[0]["id"] == 1  # type: ignore[index]

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

"""Cross-library entity deduplication tests (Phase 6a).

Verifies that when the same OpenLibrary author is matched from two
different Calibre libraries, only one ``AuthorMetadata`` record is created
while each library gets its own ``AuthorMapping``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

import pytest

from bookcard.models.author_metadata import AuthorMetadata
from bookcard.services.library_scanning.data_sources.types import AuthorData
from bookcard.services.library_scanning.matching.types import MatchResult
from bookcard.services.library_scanning.pipeline.ingest_components import (
    AuthorMetadataRepository,
    AuthorMetadataService,
    PhotoUrlBuilder,
)
from bookcard.services.library_scanning.pipeline.link_components import (
    AuthorMappingRepository as LinkAuthorMappingRepository,
)
from bookcard.services.library_scanning.pipeline.link_components import (
    MappingService,
)

if TYPE_CHECKING:
    from sqlmodel import Session

    from tests.conftest import DummySession


# ============================================================================
# Fixtures
# ============================================================================

SHARED_OL_KEY = "/authors/OL23919A"
AUTHOR_NAME = "J. K. Rowling"

LIBRARY_A_ID = 1
LIBRARY_B_ID = 2
CALIBRE_AUTHOR_ID_LIB_A = 42
CALIBRE_AUTHOR_ID_LIB_B = 7


@pytest.fixture
def author_data() -> AuthorData:
    """Shared author data representing the same OL author."""
    return AuthorData(
        key=SHARED_OL_KEY,
        name=AUTHOR_NAME,
        work_count=15,
    )


@pytest.fixture
def metadata_record() -> AuthorMetadata:
    """Pre-existing AuthorMetadata that would be found on second upsert."""
    return AuthorMetadata(
        id=100,
        openlibrary_key=SHARED_OL_KEY,
        name=AUTHOR_NAME,
    )


# ============================================================================
# Tests
# ============================================================================


class TestCrossLibraryAuthorMetadataDeduplication:
    """Verify that ``upsert_author`` produces one ``AuthorMetadata`` regardless
    of how many libraries reference the same OpenLibrary key.
    """

    def test_upsert_creates_once_then_updates(
        self,
        session: DummySession,
        author_data: AuthorData,
    ) -> None:
        """First call creates; second call updates the same record."""
        metadata_repo = AuthorMetadataRepository(cast("Session", session))
        url_builder = PhotoUrlBuilder()
        service = AuthorMetadataService(
            metadata_repo=metadata_repo,
            photo_service=MagicMock(),
            remote_id_service=MagicMock(),
            alternate_name_service=MagicMock(),
            link_service=MagicMock(),
            url_builder=url_builder,
        )

        # First upsert — no existing record ⇒ create
        session.set_exec_result([])  # find_by_openlibrary_key returns None
        created = service.upsert_author(author_data)

        assert created.openlibrary_key == SHARED_OL_KEY
        assert created.name == AUTHOR_NAME

        # Second upsert — same key found ⇒ update
        session.set_exec_result([created])  # find_by_openlibrary_key returns existing
        updated = service.upsert_author(author_data)

        assert updated.id == created.id, (
            "Second upsert must update the existing record, not create a new one"
        )


class TestCrossLibraryMappingIsolation:
    """Verify that ``MappingService`` creates separate ``AuthorMapping`` rows
    per library while pointing at the same ``AuthorMetadata``.
    """

    def test_two_libraries_produce_two_mappings_one_metadata(
        self,
        session: DummySession,
        author_data: AuthorData,
        metadata_record: AuthorMetadata,
    ) -> None:
        """Library A and Library B each get their own mapping to one metadata."""
        mapping_repo = LinkAuthorMappingRepository(cast("Session", session))
        metadata_repo = MagicMock()
        metadata_repo.find_by_openlibrary_key.return_value = metadata_record

        service = MappingService(
            mapping_repo=mapping_repo,
            metadata_repo=metadata_repo,
        )

        match_lib_a = MatchResult(
            confidence_score=0.95,
            matched_entity=author_data,
            match_method="exact",
            calibre_author_id=CALIBRE_AUTHOR_ID_LIB_A,
        )
        match_lib_b = MatchResult(
            confidence_score=0.90,
            matched_entity=author_data,
            match_method="fuzzy",
            calibre_author_id=CALIBRE_AUTHOR_ID_LIB_B,
        )

        # Library A — no prior mapping exists
        session.set_exec_result([])  # delete_mappings_for_metadata_exclude_author
        session.add_exec_result([])  # find_by_calibre_author_id_and_library → None
        result_a = service.create_or_update_mapping(match_lib_a, LIBRARY_A_ID)

        # Library B — no prior mapping exists
        session.set_exec_result([])  # delete_mappings_for_metadata_exclude_author
        session.add_exec_result([])  # find_by_calibre_author_id_and_library → None
        result_b = service.create_or_update_mapping(match_lib_b, LIBRARY_B_ID)

        assert result_a is not None
        assert result_b is not None

        mapping_a, was_created_a = result_a
        mapping_b, was_created_b = result_b

        # Both should be new creations
        assert was_created_a is True
        assert was_created_b is True

        # Both point to the same metadata
        assert mapping_a.author_metadata_id == metadata_record.id
        assert mapping_b.author_metadata_id == metadata_record.id

        # But have different library IDs
        assert mapping_a.library_id == LIBRARY_A_ID
        assert mapping_b.library_id == LIBRARY_B_ID

        # And different calibre author IDs
        assert mapping_a.calibre_author_id == CALIBRE_AUTHOR_ID_LIB_A
        assert mapping_b.calibre_author_id == CALIBRE_AUTHOR_ID_LIB_B

    def test_same_library_same_author_updates_existing_mapping(
        self,
        session: DummySession,
        author_data: AuthorData,
        metadata_record: AuthorMetadata,
    ) -> None:
        """Re-matching the same author in the same library updates, not duplicates."""
        mapping_repo = LinkAuthorMappingRepository(cast("Session", session))
        metadata_repo = MagicMock()
        metadata_repo.find_by_openlibrary_key.return_value = metadata_record

        service = MappingService(
            mapping_repo=mapping_repo,
            metadata_repo=metadata_repo,
        )

        match_result = MatchResult(
            confidence_score=0.95,
            matched_entity=author_data,
            match_method="exact",
            calibre_author_id=CALIBRE_AUTHOR_ID_LIB_A,
        )

        # First mapping — create
        session.set_exec_result([])  # delete old mappings
        session.add_exec_result([])  # no existing mapping
        result_first = service.create_or_update_mapping(match_result, LIBRARY_A_ID)
        assert result_first is not None
        mapping_first, was_created = result_first
        assert was_created is True

        # Second mapping — existing found ⇒ update
        session.set_exec_result([])  # delete old mappings
        session.add_exec_result([mapping_first])  # existing mapping found
        result_second = service.create_or_update_mapping(match_result, LIBRARY_A_ID)
        assert result_second is not None
        mapping_second, was_created_2 = result_second
        assert was_created_2 is False
        assert mapping_second.id == mapping_first.id

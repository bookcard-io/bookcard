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

"""Tests for merge_commands to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fundamental.models.author_metadata import (
    AuthorAlternateName,
    AuthorLink,
    AuthorMapping,
    AuthorMetadata,
    AuthorPhoto,
    AuthorRemoteId,
    AuthorSimilarity,
    AuthorWork,
)
from fundamental.services.library_scanning.pipeline.context import PipelineContext
from fundamental.services.library_scanning.pipeline.duplicate_detector import (
    DuplicatePair,
)
from fundamental.services.library_scanning.pipeline.merge_commands import (
    AuthorMerger,
    MergeAlternateNames,
    MergeFields,
    MergeLinks,
    MergePhotos,
    MergeRemoteIds,
    MergeStats,
    MergeWorks,
    UpdateReferences,
)
from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def session() -> DummySession:
    """Create a dummy session."""
    return DummySession()


@pytest.fixture
def pipeline_context(session: DummySession) -> PipelineContext:
    """Create a pipeline context."""
    library = MagicMock()
    library.id = 1
    data_source = MagicMock()
    return PipelineContext(
        library_id=1,
        library=library,
        session=session,  # type: ignore[arg-type]
        data_source=data_source,
    )


@pytest.fixture
def keep_author() -> AuthorMetadata:
    """Create author to keep."""
    return AuthorMetadata(
        id=1,
        openlibrary_key="OL1A",
        name="Author One",
        work_count=10,
    )


@pytest.fixture
def merge_author() -> AuthorMetadata:
    """Create author to merge."""
    return AuthorMetadata(
        id=2,
        openlibrary_key="OL2A",
        name="Author Two",
        work_count=5,
    )


# ============================================================================
# Merge Command Tests
# ============================================================================


class TestMergeAlternateNames:
    """Test MergeAlternateNames."""

    def test_execute_new_names(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute with new alternate names."""
        alt1 = AuthorAlternateName(author_metadata_id=merge_author.id, name="Alt 1")
        alt2 = AuthorAlternateName(author_metadata_id=merge_author.id, name="Alt 2")
        merge_author.alternate_names = [alt1, alt2]
        keep_author.alternate_names = []
        command = MergeAlternateNames()

        command.execute(pipeline_context, keep_author, merge_author)

        assert len(pipeline_context.session.added) == 2  # type: ignore[attr-defined]
        assert alt1 in pipeline_context.session.deleted  # type: ignore[attr-defined]
        assert alt2 in pipeline_context.session.deleted  # type: ignore[attr-defined]

    def test_execute_duplicate_names(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute skips duplicate names."""
        existing = AuthorAlternateName(
            author_metadata_id=keep_author.id, name="Existing"
        )
        duplicate = AuthorAlternateName(
            author_metadata_id=merge_author.id, name="Existing"
        )
        new = AuthorAlternateName(author_metadata_id=merge_author.id, name="New")
        keep_author.alternate_names = [existing]
        merge_author.alternate_names = [duplicate, new]
        command = MergeAlternateNames()

        command.execute(pipeline_context, keep_author, merge_author)

        # Only new name should be added
        added = [
            a
            for a in pipeline_context.session.added  # type: ignore[attr-defined]
            if isinstance(a, AuthorAlternateName)
        ]
        assert len(added) == 1
        assert added[0].name == "New"


class TestMergeRemoteIds:
    """Test MergeRemoteIds."""

    def test_execute_new_ids(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute with new remote IDs."""
        rid1 = AuthorRemoteId(
            author_metadata_id=merge_author.id,
            identifier_type="viaf",
            identifier_value="123",
        )
        rid2 = AuthorRemoteId(
            author_metadata_id=merge_author.id,
            identifier_type="goodreads",
            identifier_value="456",
        )
        merge_author.remote_ids = [rid1, rid2]
        keep_author.remote_ids = []
        command = MergeRemoteIds()

        command.execute(pipeline_context, keep_author, merge_author)

        assert len(pipeline_context.session.added) == 2  # type: ignore[attr-defined]
        assert rid1 in pipeline_context.session.deleted  # type: ignore[attr-defined]
        assert rid2 in pipeline_context.session.deleted  # type: ignore[attr-defined]

    def test_execute_duplicate_ids(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute skips duplicate IDs."""
        existing = AuthorRemoteId(
            author_metadata_id=keep_author.id,
            identifier_type="viaf",
            identifier_value="123",
        )
        duplicate = AuthorRemoteId(
            author_metadata_id=merge_author.id,
            identifier_type="viaf",
            identifier_value="123",
        )
        new = AuthorRemoteId(
            author_metadata_id=merge_author.id,
            identifier_type="goodreads",
            identifier_value="456",
        )
        keep_author.remote_ids = [existing]
        merge_author.remote_ids = [duplicate, new]
        command = MergeRemoteIds()

        command.execute(pipeline_context, keep_author, merge_author)

        # Only new ID should be added
        added = [
            r
            for r in pipeline_context.session.added  # type: ignore[attr-defined]
            if isinstance(r, AuthorRemoteId)
        ]
        assert len(added) == 1
        assert added[0].identifier_type == "goodreads"


class TestMergePhotos:
    """Test MergePhotos."""

    def test_execute_new_photos(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute with new photos."""
        photo1 = AuthorPhoto(
            author_metadata_id=merge_author.id,
            openlibrary_photo_id=123,
            photo_url="https://example.com/1.jpg",
        )
        photo2 = AuthorPhoto(
            author_metadata_id=merge_author.id,
            openlibrary_photo_id=456,
            photo_url="https://example.com/2.jpg",
        )
        merge_author.photos = [photo1, photo2]
        keep_author.photos = []
        command = MergePhotos()

        command.execute(pipeline_context, keep_author, merge_author)

        assert len(pipeline_context.session.added) == 2  # type: ignore[attr-defined]
        assert photo1 in pipeline_context.session.deleted  # type: ignore[attr-defined]
        assert photo2 in pipeline_context.session.deleted  # type: ignore[attr-defined]

    def test_execute_duplicate_by_id(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute skips duplicate photos by ID."""
        existing = AuthorPhoto(
            author_metadata_id=keep_author.id,
            openlibrary_photo_id=123,
            photo_url="https://example.com/existing.jpg",
        )
        duplicate = AuthorPhoto(
            author_metadata_id=merge_author.id,
            openlibrary_photo_id=123,
            photo_url="https://example.com/duplicate.jpg",
        )
        keep_author.photos = [existing]
        merge_author.photos = [duplicate]
        command = MergePhotos()

        command.execute(pipeline_context, keep_author, merge_author)

        assert len(pipeline_context.session.added) == 0  # type: ignore[attr-defined]

    def test_execute_duplicate_by_url(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute skips duplicate photos by URL."""
        existing = AuthorPhoto(
            author_metadata_id=keep_author.id,
            openlibrary_photo_id=None,
            photo_url="https://example.com/same.jpg",
        )
        duplicate = AuthorPhoto(
            author_metadata_id=merge_author.id,
            openlibrary_photo_id=999,
            photo_url="https://example.com/same.jpg",
        )
        keep_author.photos = [existing]
        merge_author.photos = [duplicate]
        command = MergePhotos()

        command.execute(pipeline_context, keep_author, merge_author)

        assert len(pipeline_context.session.added) == 0  # type: ignore[attr-defined]

    def test_photo_exists_by_id(self) -> None:
        """Test _photo_exists returns True when ID matches."""
        command = MergePhotos()
        photo = AuthorPhoto(openlibrary_photo_id=123)
        existing_ids = {123}
        existing_urls = set()

        result = command._photo_exists(photo, existing_ids, existing_urls)

        assert result is True

    def test_photo_exists_by_url(self) -> None:
        """Test _photo_exists returns True when URL matches."""
        command = MergePhotos()
        photo = AuthorPhoto(photo_url="https://example.com/photo.jpg")
        existing_ids = set()
        existing_urls = {"https://example.com/photo.jpg"}

        result = command._photo_exists(photo, existing_ids, existing_urls)

        assert result is True

    def test_photo_exists_false(self) -> None:
        """Test _photo_exists returns False when no match."""
        command = MergePhotos()
        photo = AuthorPhoto(
            openlibrary_photo_id=123, photo_url="https://example.com/photo.jpg"
        )
        existing_ids = {456}
        existing_urls = {"https://example.com/other.jpg"}

        result = command._photo_exists(photo, existing_ids, existing_urls)

        assert result is False

    def test_update_existing_sets(self) -> None:
        """Test _update_existing_sets updates sets."""
        command = MergePhotos()
        photo = AuthorPhoto(
            openlibrary_photo_id=123, photo_url="https://example.com/photo.jpg"
        )
        existing_ids: set[int] = set()
        existing_urls: set[str] = set()

        command._update_existing_sets(photo, existing_ids, existing_urls)

        assert 123 in existing_ids
        assert "https://example.com/photo.jpg" in existing_urls

    def test_update_existing_sets_no_id(self) -> None:
        """Test _update_existing_sets with no photo ID."""
        command = MergePhotos()
        photo = AuthorPhoto(photo_url="https://example.com/photo.jpg")
        existing_ids: set[int] = set()
        existing_urls: set[str] = set()

        command._update_existing_sets(photo, existing_ids, existing_urls)

        assert len(existing_ids) == 0
        assert "https://example.com/photo.jpg" in existing_urls


class TestMergeLinks:
    """Test MergeLinks."""

    def test_execute_new_links(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute with new links."""
        link1 = AuthorLink(
            author_metadata_id=merge_author.id,
            url="https://example.com/1",
            title="Link 1",
        )
        link2 = AuthorLink(
            author_metadata_id=merge_author.id,
            url="https://example.com/2",
            title="Link 2",
        )
        merge_author.links = [link1, link2]
        keep_author.links = []
        command = MergeLinks()

        command.execute(pipeline_context, keep_author, merge_author)

        assert len(pipeline_context.session.added) == 2  # type: ignore[attr-defined]
        assert link1 in pipeline_context.session.deleted  # type: ignore[attr-defined]
        assert link2 in pipeline_context.session.deleted  # type: ignore[attr-defined]

    def test_execute_duplicate_links(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute skips duplicate links."""
        existing = AuthorLink(
            author_metadata_id=keep_author.id,
            url="https://example.com/existing",
            title="Existing",
        )
        duplicate = AuthorLink(
            author_metadata_id=merge_author.id,
            url="https://example.com/existing",
            title="Duplicate",
        )
        new = AuthorLink(
            author_metadata_id=merge_author.id,
            url="https://example.com/new",
            title="New",
        )
        keep_author.links = [existing]
        merge_author.links = [duplicate, new]
        command = MergeLinks()

        command.execute(pipeline_context, keep_author, merge_author)

        # Only new link should be added
        added = [
            link
            for link in pipeline_context.session.added  # type: ignore[attr-defined,unresolved-attribute]
            if isinstance(link, AuthorLink)
        ]
        assert len(added) == 1
        assert added[0].url == "https://example.com/new"


class TestMergeWorks:
    """Test MergeWorks."""

    def test_execute_keep_has_id(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute when keep has ID."""
        work1 = AuthorWork(
            author_metadata_id=keep_author.id,
            work_key="OL1W",
            rank=0,
        )
        work2 = AuthorWork(
            author_metadata_id=merge_author.id,
            work_key="OL2W",
            rank=0,
        )
        keep_author.works = [work1]
        merge_author.works = [work2]
        command = MergeWorks()

        command.execute(pipeline_context, keep_author, merge_author)

        # work2 should be moved to keep_author.works
        assert work2 in keep_author.works
        # work2 should be deleted from merge_author (removed from list)
        assert work2 not in merge_author.works

    def test_execute_merge_has_id(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute when merge has ID but keep doesn't."""
        keep_author.id = None
        work1 = AuthorWork(
            author_metadata_id=merge_author.id,
            work_key="OL1W",
            rank=0,
        )
        work2 = AuthorWork(
            author_metadata_id=keep_author.id,
            work_key="OL2W",
            rank=0,
        )
        keep_author.works = [work2]
        merge_author.works = [work1]
        command = MergeWorks()

        command.execute(pipeline_context, keep_author, merge_author)

        # Should swap and use merge as final_author
        assert work1.author_metadata_id == merge_author.id

    def test_execute_no_ids(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute when neither has ID."""
        keep_author.id = None
        merge_author.id = None
        command = MergeWorks()

        command.execute(pipeline_context, keep_author, merge_author)

        # Should return early
        assert len(pipeline_context.session.added) == 0  # type: ignore[attr-defined]

    def test_execute_duplicate_work_key(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute deletes duplicate work keys."""
        work1 = AuthorWork(
            author_metadata_id=keep_author.id,
            work_key="OL1W",
            rank=0,
        )
        work2 = AuthorWork(
            author_metadata_id=merge_author.id,
            work_key="OL1W",  # Duplicate
            rank=0,
        )
        keep_author.works = [work1]
        merge_author.works = [work2]
        command = MergeWorks()

        command.execute(pipeline_context, keep_author, merge_author)

        assert work2 in pipeline_context.session.deleted  # type: ignore[attr-defined]


class TestMergeFields:
    """Test MergeFields."""

    def test_execute_text_fields(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute merges text fields."""
        keep_author.biography = None
        merge_author.biography = "Test biography"
        keep_author.location = None
        merge_author.location = "Test location"
        command = MergeFields()

        command.execute(pipeline_context, keep_author, merge_author)

        assert keep_author.biography == "Test biography"
        assert keep_author.location == "Test location"

    def test_execute_text_fields_keep_has_value(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute doesn't overwrite existing text fields."""
        keep_author.biography = "Existing biography"
        merge_author.biography = "New biography"
        command = MergeFields()

        command.execute(pipeline_context, keep_author, merge_author)

        assert keep_author.biography == "Existing biography"

    def test_execute_numeric_fields(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute merges numeric fields."""
        keep_author.work_count = None
        merge_author.work_count = 20
        keep_author.ratings_count = 10
        merge_author.ratings_count = 15
        command = MergeFields()

        command.execute(pipeline_context, keep_author, merge_author)

        assert keep_author.work_count == 20
        assert keep_author.ratings_count == 15

    def test_execute_numeric_fields_keep_higher(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute keeps higher numeric value."""
        keep_author.work_count = 20
        merge_author.work_count = 10
        command = MergeFields()

        command.execute(pipeline_context, keep_author, merge_author)

        assert keep_author.work_count == 20


class TestUpdateReferences:
    """Test UpdateReferences."""

    def test_execute_updates_mappings(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute updates mappings."""
        mapping = AuthorMapping(
            library_id=1,
            calibre_author_id=1,
            author_metadata_id=merge_author.id,
        )
        pipeline_context.session.set_exec_result([mapping])  # type: ignore[attr-defined]
        command = UpdateReferences()

        command.execute(pipeline_context, keep_author, merge_author)

        assert mapping.author_metadata_id == keep_author.id
        assert mapping.updated_at is not None

    def test_execute_updates_similarities_author1(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute updates similarities where merge is author1."""
        sim = AuthorSimilarity(
            author1_id=merge_author.id,
            author2_id=999,
            similarity_score=0.9,
        )
        # execute() calls _update_mappings first, then _update_similarities
        pipeline_context.session.set_exec_result([])  # type: ignore[attr-defined]  # For mappings query
        pipeline_context.session.add_exec_result([  # type: ignore[attr-defined]
            sim
        ])  # For author1 similarities query
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # For author2 similarities query
        command = UpdateReferences()

        command.execute(pipeline_context, keep_author, merge_author)

        assert sim.author1_id == keep_author.id

    def test_execute_updates_similarities_author2(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute updates similarities where merge is author2."""
        sim = AuthorSimilarity(
            author1_id=999,
            author2_id=merge_author.id,
            similarity_score=0.9,
        )
        # execute() calls _update_mappings first, then _update_similarities
        pipeline_context.session.set_exec_result([])  # type: ignore[attr-defined]  # For mappings query
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # For author1 similarities query
        pipeline_context.session.add_exec_result([  # type: ignore[attr-defined]
            sim
        ])  # For author2 similarities query
        command = UpdateReferences()

        command.execute(pipeline_context, keep_author, merge_author)

        assert sim.author2_id == keep_author.id

    def test_execute_deletes_self_similarity_author1(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute deletes self-similarity when merge is author1."""
        sim = AuthorSimilarity(
            author1_id=merge_author.id,
            author2_id=keep_author.id,
            similarity_score=0.9,
        )
        # execute() calls _update_mappings first, then _update_similarities
        # _update_mappings queries for AuthorMapping, _update_similarities queries for AuthorSimilarity
        pipeline_context.session.set_exec_result([])  # type: ignore[attr-defined]  # For mappings query
        pipeline_context.session.add_exec_result([  # type: ignore[attr-defined]
            sim
        ])  # For author1 similarities query
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # For author2 similarities query
        command = UpdateReferences()

        command.execute(pipeline_context, keep_author, merge_author)

        # Check that sim was deleted (it should be in deleted list)
        deleted_sims = [
            s
            for s in pipeline_context.session.deleted  # type: ignore[attr-defined]
            if isinstance(s, AuthorSimilarity)
        ]
        assert len(deleted_sims) == 1
        assert deleted_sims[0].author1_id == merge_author.id
        assert deleted_sims[0].author2_id == keep_author.id

    def test_execute_deletes_self_similarity_author2(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test execute deletes self-similarity when merge is author2."""
        sim = AuthorSimilarity(
            author1_id=keep_author.id,
            author2_id=merge_author.id,
            similarity_score=0.9,
        )
        # execute() calls _update_mappings first, then _update_similarities
        # _update_mappings queries for AuthorMapping, _update_similarities queries for AuthorSimilarity
        pipeline_context.session.set_exec_result([])  # type: ignore[attr-defined]  # For mappings query
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # For author1 similarities query
        pipeline_context.session.add_exec_result([  # type: ignore[attr-defined]
            sim
        ])  # For author2 similarities query
        command = UpdateReferences()

        command.execute(pipeline_context, keep_author, merge_author)

        # Check that sim was deleted (it should be in deleted list)
        deleted_sims = [
            s
            for s in pipeline_context.session.deleted  # type: ignore[attr-defined]
            if isinstance(s, AuthorSimilarity)
        ]
        assert len(deleted_sims) == 1
        assert deleted_sims[0].author1_id == keep_author.id
        assert deleted_sims[0].author2_id == merge_author.id


# ============================================================================
# AuthorMerger Tests
# ============================================================================


class TestAuthorMerger:
    """Test AuthorMerger."""

    def test_init(self) -> None:
        """Test __init__ creates commands."""
        merger = AuthorMerger()

        assert len(merger.commands) == 7

    def test_ensure_keep_has_library_mapping_no_ids(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test _ensure_keep_has_library_mapping when no IDs."""
        keep_author.id = None
        merge_author.id = None
        merger = AuthorMerger()

        result_keep, result_merge = merger._ensure_keep_has_library_mapping(
            pipeline_context, keep_author, merge_author
        )

        assert result_keep == keep_author
        assert result_merge == merge_author

    def test_ensure_keep_has_library_mapping_merge_mapped(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test _ensure_keep_has_library_mapping swaps when merge is mapped."""
        mapping = AuthorMapping(
            library_id=1,
            calibre_author_id=1,
            author_metadata_id=merge_author.id,
        )
        # _has_library_mapping is called twice: once for keep.id, once for merge.id
        # First call checks keep.id (no mapping), second call checks merge.id (has mapping)
        pipeline_context.session.set_exec_result([])  # type: ignore[attr-defined]  # Keep has no mapping
        pipeline_context.session.add_exec_result([mapping])  # type: ignore[attr-defined]  # Merge has mapping
        merger = AuthorMerger()

        result_keep, result_merge = merger._ensure_keep_has_library_mapping(
            pipeline_context, keep_author, merge_author
        )

        # Should swap: merge becomes keep, keep becomes merge
        assert result_keep.id == merge_author.id
        assert result_merge.id == keep_author.id

    def test_ensure_keep_has_library_mapping_keep_mapped(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test _ensure_keep_has_library_mapping doesn't swap when keep is mapped."""
        mapping = AuthorMapping(
            library_id=1,
            calibre_author_id=1,
            author_metadata_id=keep_author.id,
        )
        pipeline_context.session.set_exec_result([mapping])  # type: ignore[attr-defined]  # Keep has mapping
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # Merge has no mapping
        merger = AuthorMerger()

        result_keep, result_merge = merger._ensure_keep_has_library_mapping(
            pipeline_context, keep_author, merge_author
        )

        assert result_keep == keep_author
        assert result_merge == merge_author

    def test_log_work_counts(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test _log_work_counts."""
        work1 = AuthorWork(
            author_metadata_id=keep_author.id,
            work_key="OL1W",
            rank=0,
        )
        work2 = AuthorWork(
            author_metadata_id=merge_author.id,
            work_key="OL2W",
            rank=0,
        )
        pipeline_context.session.set_exec_result([work1])  # type: ignore[attr-defined]
        pipeline_context.session.add_exec_result([work2])  # type: ignore[attr-defined]
        merger = AuthorMerger()

        keep_ids, merge_ids = merger._log_work_counts(
            pipeline_context, keep_author, merge_author
        )

        assert len(keep_ids) == 1
        assert len(merge_ids) == 1

    def test_log_work_counts_no_ids(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test _log_work_counts when authors have no IDs."""
        keep_author.id = None
        merge_author.id = None
        merger = AuthorMerger()

        keep_ids, merge_ids = merger._log_work_counts(
            pipeline_context, keep_author, merge_author
        )

        assert len(keep_ids) == 0
        assert len(merge_ids) == 0

    def test_cleanup_remaining_works(
        self,
        pipeline_context: PipelineContext,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test _cleanup_remaining_works deletes remaining works."""
        work = AuthorWork(
            author_metadata_id=merge_author.id,
            work_key="OL1W",
            rank=0,
        )
        pipeline_context.session.set_exec_result([work])  # type: ignore[attr-defined]
        merger = AuthorMerger()

        merger._cleanup_remaining_works(pipeline_context, merge_author)

        assert work in pipeline_context.session.deleted  # type: ignore[attr-defined]

    def test_cleanup_remaining_works_no_id(
        self,
        pipeline_context: PipelineContext,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test _cleanup_remaining_works returns early when no ID."""
        merge_author.id = None
        merger = AuthorMerger()

        merger._cleanup_remaining_works(pipeline_context, merge_author)

        assert len(pipeline_context.session.deleted) == 0  # type: ignore[attr-defined]

    def test_merge(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test merge executes all commands."""
        pipeline_context.session.set_exec_result([])  # type: ignore[attr-defined]  # Keep library mapping check
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # Merge library mapping check
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # Keep works
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # Merge works
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # Remaining works check
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # Final keep works
        merger = AuthorMerger()

        merger.merge(pipeline_context, keep_author, merge_author)

        assert merge_author in pipeline_context.session.deleted  # type: ignore[attr-defined]
        assert pipeline_context.session.flush_count > 0  # type: ignore[attr-defined]

    def test_merge_pair(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test merge_pair."""
        pair = DuplicatePair(
            keep=keep_author,
            merge=merge_author,
            keep_score=0.9,
            merge_score=0.8,
        )
        pipeline_context.session.set_exec_result([])  # type: ignore[attr-defined]  # Keep library mapping check
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # Merge library mapping check
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # Keep works
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # Merge works
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # Remaining works check
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # Final keep works
        merger = AuthorMerger()

        merger.merge_pair(pipeline_context, pair)

        assert merge_author in pipeline_context.session.deleted  # type: ignore[attr-defined]

    def test_merge_batch_success(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test merge_batch with successful merges."""
        pair1 = DuplicatePair(
            keep=keep_author,
            merge=merge_author,
            keep_score=0.9,
            merge_score=0.8,
        )
        pair2 = DuplicatePair(
            keep=keep_author,
            merge=merge_author,
            keep_score=0.9,
            merge_score=0.8,
        )
        # Setup results for 2 merges, each needs 6 queries
        pipeline_context.session.set_exec_result([])  # type: ignore[attr-defined]  # First merge: keep mapping
        for _ in range(11):  # 5 more for first merge + 6 for second merge
            pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]
        merger = AuthorMerger()

        stats = merger.merge_batch(pipeline_context, [pair1, pair2])

        assert stats.merged == 2
        assert stats.failed == 0
        assert stats.duplicates_found == 2

    def test_merge_batch_with_failure(
        self,
        pipeline_context: PipelineContext,
        keep_author: AuthorMetadata,
        merge_author: AuthorMetadata,
    ) -> None:
        """Test merge_batch handles failures."""
        pair1 = DuplicatePair(
            keep=keep_author,
            merge=merge_author,
            keep_score=0.9,
            merge_score=0.8,
        )
        pair2 = DuplicatePair(
            keep=keep_author,
            merge=merge_author,
            keep_score=0.9,
            merge_score=0.8,
        )
        # Setup results for 2 merges, first succeeds, second fails
        pipeline_context.session.set_exec_result([])  # type: ignore[attr-defined]  # First merge: keep mapping
        for _ in range(5):  # Remaining queries for first merge
            pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]
        # Second merge will fail, but still needs mapping checks
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # Second merge: keep mapping
        pipeline_context.session.add_exec_result([])  # type: ignore[attr-defined]  # Second merge: merge mapping
        # Make second merge fail
        merger = AuthorMerger()
        merger.commands[0].execute = MagicMock(  # type: ignore[assignment]
            side_effect=[None, RuntimeError("Test error")]
        )

        stats = merger.merge_batch(pipeline_context, [pair1, pair2])

        assert stats.merged == 1
        assert stats.failed == 1
        assert stats.duplicates_found == 2


# ============================================================================
# MergeStats Tests
# ============================================================================


class TestMergeStats:
    """Test MergeStats."""

    def test_init_defaults(self) -> None:
        """Test __init__ with defaults."""
        stats = MergeStats()

        assert stats.merged == 0
        assert stats.failed == 0
        assert stats.duplicates_found == 0
        assert stats.total_checked == 0

    def test_init_with_values(self) -> None:
        """Test __init__ with values."""
        stats = MergeStats(merged=5, failed=2, duplicates_found=7, total_checked=10)

        assert stats.merged == 5
        assert stats.failed == 2
        assert stats.duplicates_found == 7
        assert stats.total_checked == 10

    def test_to_dict(self) -> None:
        """Test to_dict."""
        stats = MergeStats(merged=5, failed=2, duplicates_found=7, total_checked=10)

        result = stats.to_dict()

        assert result == {
            "merged": 5,
            "failed": 2,
            "duplicates_found": 7,
            "total_checked": 10,
        }

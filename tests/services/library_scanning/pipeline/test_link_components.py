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

"""Tests for link_components to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from fundamental.models.author_metadata import AuthorMapping, AuthorMetadata
from fundamental.services.library_scanning.data_sources.types import AuthorData
from fundamental.services.library_scanning.matching.types import MatchResult
from fundamental.services.library_scanning.pipeline.link_components import (
    AuthorMappingRepository,
    AuthorMetadataRepository,
    LinkingStatistics,
    MappingBatchProcessor,
    MappingData,
    MappingService,
    ProgressReporter,
)

if TYPE_CHECKING:
    from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def author_metadata() -> AuthorMetadata:
    """Create sample author metadata."""
    return AuthorMetadata(
        id=1,
        openlibrary_key="OL12345A",
        name="Test Author",
    )


@pytest.fixture
def author_data() -> AuthorData:
    """Create sample author data."""
    return AuthorData(
        key="OL12345A",
        name="Test Author",
        work_count=10,
    )


@pytest.fixture
def match_result(author_data: AuthorData) -> MatchResult:
    """Create a match result."""
    return MatchResult(
        confidence_score=0.9,
        matched_entity=author_data,
        match_method="exact",
        calibre_author_id=1,
    )


@pytest.fixture
def mapping_data() -> MappingData:
    """Create sample mapping data."""
    return MappingData(
        library_id=1,
        calibre_author_id=1,
        author_metadata_id=1,
        confidence_score=0.9,
        matched_by="exact",
    )


# ============================================================================
# Repository Tests
# ============================================================================


class TestAuthorMappingRepository:
    """Test AuthorMappingRepository."""

    def test_find_by_calibre_author_id_found(self, session: DummySession) -> None:
        """Test find_by_calibre_author_id when found."""
        mapping = AuthorMapping(
            library_id=1,
            calibre_author_id=1,
            author_metadata_id=1,
        )
        session.add(mapping)
        session.flush()
        session.set_exec_result([mapping])  # type: ignore[attr-defined]
        repo = AuthorMappingRepository(session)  # type: ignore[arg-type]

        result = repo.find_by_calibre_author_id(1)

        assert result == mapping

    def test_find_by_calibre_author_id_not_found(self, session: DummySession) -> None:
        """Test find_by_calibre_author_id when not found."""
        session.set_exec_result([])  # type: ignore[attr-defined]
        repo = AuthorMappingRepository(session)  # type: ignore[arg-type]

        result = repo.find_by_calibre_author_id(1)

        assert result is None

    def test_find_by_calibre_author_id_and_library_found(
        self, session: DummySession
    ) -> None:
        """Test find_by_calibre_author_id_and_library when found."""
        mapping = AuthorMapping(
            library_id=1,
            calibre_author_id=1,
            author_metadata_id=1,
        )
        session.add(mapping)
        session.flush()
        session.set_exec_result([mapping])  # type: ignore[attr-defined]
        repo = AuthorMappingRepository(session)  # type: ignore[arg-type]

        result = repo.find_by_calibre_author_id_and_library(1, 1)

        assert result == mapping

    def test_find_by_calibre_author_id_and_library_not_found(
        self, session: DummySession
    ) -> None:
        """Test find_by_calibre_author_id_and_library when not found."""
        session.set_exec_result([])  # type: ignore[attr-defined]
        repo = AuthorMappingRepository(session)  # type: ignore[arg-type]

        result = repo.find_by_calibre_author_id_and_library(1, 1)

        assert result is None

    def test_create(self, session: DummySession, mapping_data: MappingData) -> None:
        """Test create mapping."""
        repo = AuthorMappingRepository(session)  # type: ignore[arg-type]

        result = repo.create(mapping_data)

        assert result.library_id == mapping_data.library_id
        assert result.calibre_author_id == mapping_data.calibre_author_id
        assert result.author_metadata_id == mapping_data.author_metadata_id
        assert result in session.added  # type: ignore[attr-defined]

    def test_update(self, session: DummySession, mapping_data: MappingData) -> None:
        """Test update mapping."""
        existing = AuthorMapping(
            library_id=1,
            calibre_author_id=1,
            author_metadata_id=1,
        )
        new_data = MappingData(
            library_id=1,
            calibre_author_id=1,
            author_metadata_id=2,
            confidence_score=0.95,
            matched_by="fuzzy",
        )
        repo = AuthorMappingRepository(session)  # type: ignore[arg-type]

        result = repo.update(existing, new_data)

        assert result.author_metadata_id == 2
        assert result.confidence_score == 0.95
        assert result.matched_by == "fuzzy"
        assert result.updated_at is not None


class TestAuthorMetadataRepository:
    """Test AuthorMetadataRepository."""

    def test_find_by_openlibrary_key_found(
        self, session: DummySession, author_metadata: AuthorMetadata
    ) -> None:
        """Test find_by_openlibrary_key when found."""
        session.add(author_metadata)
        session.flush()
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]
        repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]

        result = repo.find_by_openlibrary_key("OL12345A")

        assert result == author_metadata

    def test_find_by_openlibrary_key_not_found(self, session: DummySession) -> None:
        """Test find_by_openlibrary_key when not found."""
        session.set_exec_result([])  # type: ignore[attr-defined]
        repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]

        result = repo.find_by_openlibrary_key("OL12345A")

        assert result is None


# ============================================================================
# Service Tests
# ============================================================================


class TestMappingService:
    """Test MappingService."""

    def test_create_or_update_mapping_create(
        self,
        session: DummySession,
        match_result: MatchResult,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test create_or_update_mapping creates new mapping."""
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]  # Metadata found
        session.add_exec_result([])  # type: ignore[attr-defined]  # No existing mapping
        mapping_repo = AuthorMappingRepository(session)  # type: ignore[arg-type]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        service = MappingService(mapping_repo, metadata_repo)

        result = service.create_or_update_mapping(match_result, library_id=1)

        assert result is not None
        mapping, was_created = result
        assert was_created is True
        assert mapping.calibre_author_id == match_result.calibre_author_id

    def test_create_or_update_mapping_update(
        self,
        session: DummySession,
        match_result: MatchResult,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test create_or_update_mapping updates existing mapping."""
        existing_mapping = AuthorMapping(
            library_id=1,
            calibre_author_id=1,
            author_metadata_id=1,
        )
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]  # Metadata found
        session.add_exec_result([])  # type: ignore[attr-defined]  # delete_mappings_for_metadata_exclude_author returns empty
        session.add_exec_result([existing_mapping])  # type: ignore[attr-defined]  # Existing mapping
        mapping_repo = AuthorMappingRepository(session)  # type: ignore[arg-type]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        service = MappingService(mapping_repo, metadata_repo)

        result = service.create_or_update_mapping(match_result, library_id=1)

        assert result is not None
        mapping, was_created = result
        assert was_created is False
        assert mapping.author_metadata_id == author_metadata.id

    def test_create_or_update_mapping_no_calibre_id(
        self,
        session: DummySession,
        author_data: AuthorData,
    ) -> None:
        """Test create_or_update_mapping returns None when no calibre_author_id."""
        match_result = MatchResult(
            confidence_score=0.9,
            matched_entity=author_data,
            match_method="exact",
            calibre_author_id=None,
        )
        mapping_repo = AuthorMappingRepository(session)  # type: ignore[arg-type]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        service = MappingService(mapping_repo, metadata_repo)

        result = service.create_or_update_mapping(match_result, library_id=1)

        assert result is None

    def test_create_or_update_mapping_metadata_not_found(
        self,
        session: DummySession,
        match_result: MatchResult,
    ) -> None:
        """Test create_or_update_mapping returns None when metadata not found."""
        session.set_exec_result([])  # type: ignore[attr-defined]  # Metadata not found
        mapping_repo = AuthorMappingRepository(session)  # type: ignore[arg-type]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        service = MappingService(mapping_repo, metadata_repo)

        result = service.create_or_update_mapping(match_result, library_id=1)

        assert result is None

    def test_create_or_update_mapping_metadata_no_id(
        self,
        session: DummySession,
        match_result: MatchResult,
    ) -> None:
        """Test create_or_update_mapping returns None when metadata has no ID."""
        metadata = AuthorMetadata(
            openlibrary_key="OL12345A",
            name="Test Author",
        )
        metadata.id = None
        session.set_exec_result([metadata])  # type: ignore[attr-defined]  # Metadata found but no ID
        mapping_repo = AuthorMappingRepository(session)  # type: ignore[arg-type]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        service = MappingService(mapping_repo, metadata_repo)

        result = service.create_or_update_mapping(match_result, library_id=1)

        assert result is None


# ============================================================================
# Progress Tracking Tests
# ============================================================================


class TestProgressReporter:
    """Test ProgressReporter."""

    @pytest.mark.parametrize(
        ("total_items", "expected_interval"),
        [
            (100, 10),  # 10% of 100 = 10
            (25, 2),  # 10% of 25 = 2.5, min(25, 2) = 2
            (10, 1),  # 10% of 10 = 1, min(25, 1) = 1
            (5, 1),  # 10% of 5 = 0.5, max(1, 0) = 1
        ],
    )
    def test_init_calculates_interval(
        self, total_items: int, expected_interval: int
    ) -> None:
        """Test __init__ calculates log interval."""
        reporter = ProgressReporter(total_items=total_items)

        assert reporter.log_interval == expected_interval

    def test_init_custom_interval(self) -> None:
        """Test __init__ with custom log interval."""
        reporter = ProgressReporter(total_items=100, log_interval=5)

        assert reporter.log_interval == 5

    def test_update(self) -> None:
        """Test update progress."""
        reporter = ProgressReporter(total_items=10)

        result = reporter.update(current_index=5)

        assert reporter.processed_items == 5
        assert reporter._progress == 0.5
        assert result == 0.5

    def test_update_zero_total(self) -> None:
        """Test update with zero total."""
        reporter = ProgressReporter(total_items=0)

        result = reporter.update(current_index=1)

        assert reporter._progress == 0.0
        assert result == 0.0

    @pytest.mark.parametrize(
        ("current_index", "log_interval", "total_items", "expected"),
        [
            (10, 10, 100, True),  # Exactly at interval
            (20, 10, 100, True),  # Multiple of interval
            (5, 10, 100, False),  # Not at interval
            (100, 10, 100, True),  # At total
            (1, 1, 10, True),  # First item with interval 1
        ],
    )
    def test_should_log(
        self,
        current_index: int,
        log_interval: int,
        total_items: int,
        expected: bool,
    ) -> None:
        """Test should_log."""
        reporter = ProgressReporter(total_items=total_items, log_interval=log_interval)

        result = reporter.should_log(current_index)

        assert result == expected

    def test_progress_property(self) -> None:
        """Test progress property."""
        reporter = ProgressReporter(total_items=10)
        reporter.update(current_index=7)

        assert reporter.progress == 0.7


# ============================================================================
# Statistics Tests
# ============================================================================


class TestLinkingStatistics:
    """Test LinkingStatistics."""

    def test_init_defaults(self) -> None:
        """Test __init__ with defaults."""
        stats = LinkingStatistics()

        assert stats.mappings_created == 0
        assert stats.mappings_updated == 0
        assert stats.mappings_failed == 0
        assert stats.total_processed == 0

    def test_record_creation(self) -> None:
        """Test record_creation."""
        stats = LinkingStatistics()

        stats.record_creation()

        assert stats.mappings_created == 1
        assert stats.total_processed == 1

    def test_record_update(self) -> None:
        """Test record_update."""
        stats = LinkingStatistics()

        stats.record_update()

        assert stats.mappings_updated == 1
        assert stats.total_processed == 1

    def test_record_failure(self) -> None:
        """Test record_failure."""
        stats = LinkingStatistics()

        stats.record_failure()

        assert stats.mappings_failed == 1
        assert stats.total_processed == 1

    def test_to_dict(self) -> None:
        """Test to_dict."""
        stats = LinkingStatistics()
        stats.record_creation()
        stats.record_update()
        stats.record_failure()

        result = stats.to_dict()

        assert result == {
            "mappings_created": 1,
            "mappings_updated": 1,
            "mappings_failed": 1,
            "total_processed": 3,
        }


# ============================================================================
# Batch Processing Tests
# ============================================================================


class TestMappingBatchProcessor:
    """Test MappingBatchProcessor."""

    def test_process_item_success_create(
        self,
        session: DummySession,
        match_result: MatchResult,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test process_item successfully creates mapping."""
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]
        session.add_exec_result([])  # type: ignore[attr-defined]  # No existing mapping
        mapping_repo = AuthorMappingRepository(session)  # type: ignore[arg-type]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        mapping_service = MappingService(mapping_repo, metadata_repo)
        statistics = LinkingStatistics()
        processor = MappingBatchProcessor(mapping_service, statistics)

        result = processor.process_item(match_result, context={"library_id": 1})

        assert result is True
        assert statistics.mappings_created == 1
        assert statistics.mappings_updated == 0
        assert statistics.mappings_failed == 0

    def test_process_item_success_update(
        self,
        session: DummySession,
        match_result: MatchResult,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test process_item successfully updates mapping."""
        existing_mapping = AuthorMapping(
            library_id=1,
            calibre_author_id=1,
            author_metadata_id=1,
        )
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]  # find_by_openlibrary_key
        session.add_exec_result([])  # type: ignore[attr-defined]  # delete_mappings_for_metadata_exclude_author
        session.add_exec_result([existing_mapping])  # type: ignore[attr-defined]  # Existing mapping from find_by_calibre_author_id_and_library
        mapping_repo = AuthorMappingRepository(session)  # type: ignore[arg-type]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        mapping_service = MappingService(mapping_repo, metadata_repo)
        statistics = LinkingStatistics()
        processor = MappingBatchProcessor(mapping_service, statistics)

        result = processor.process_item(match_result, context={"library_id": 1})

        assert result is True
        assert statistics.mappings_created == 0
        assert statistics.mappings_updated == 1
        assert statistics.mappings_failed == 0

    def test_process_item_failure(
        self,
        session: DummySession,
        match_result: MatchResult,
    ) -> None:
        """Test process_item returns False on failure."""
        session.set_exec_result([])  # type: ignore[attr-defined]  # Metadata not found
        mapping_repo = AuthorMappingRepository(session)  # type: ignore[arg-type]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        mapping_service = MappingService(mapping_repo, metadata_repo)
        statistics = LinkingStatistics()
        processor = MappingBatchProcessor(mapping_service, statistics)

        result = processor.process_item(match_result, context={"library_id": 1})

        assert result is False
        assert statistics.mappings_created == 0
        assert statistics.mappings_updated == 0
        assert statistics.mappings_failed == 1

    def test_process_batch_success(
        self,
        session: DummySession,
        match_result: MatchResult,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test process_batch successfully processes items."""
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]  # First find_by_openlibrary_key
        session.add_exec_result([])  # type: ignore[attr-defined]  # First delete_mappings_for_metadata_exclude_author
        session.add_exec_result([])  # type: ignore[attr-defined]  # First find_by_calibre_author_id_and_library (no existing mapping)
        session.add_exec_result([author_metadata])  # type: ignore[attr-defined]  # Second find_by_openlibrary_key
        session.add_exec_result([])  # type: ignore[attr-defined]  # Second delete_mappings_for_metadata_exclude_author
        session.add_exec_result([])  # type: ignore[attr-defined]  # Second find_by_calibre_author_id_and_library (no existing mapping)
        mapping_repo = AuthorMappingRepository(session)  # type: ignore[arg-type]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        mapping_service = MappingService(mapping_repo, metadata_repo)
        statistics = LinkingStatistics()
        processor = MappingBatchProcessor(mapping_service, statistics)

        match_results = [match_result, match_result]
        result = processor.process_batch(match_results, context={"library_id": 1})

        assert result == 2
        assert statistics.mappings_created == 2

    def test_process_batch_with_progress_callback(
        self,
        session: DummySession,
        match_result: MatchResult,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test process_batch calls progress callback."""
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]  # First find_by_openlibrary_key
        session.add_exec_result([])  # type: ignore[attr-defined]  # First delete_mappings_for_metadata_exclude_author
        session.add_exec_result([])  # type: ignore[attr-defined]  # First find_by_calibre_author_id_and_library
        session.add_exec_result([author_metadata])  # type: ignore[attr-defined]  # Second find_by_openlibrary_key
        session.add_exec_result([])  # type: ignore[attr-defined]  # Second delete_mappings_for_metadata_exclude_author
        session.add_exec_result([])  # type: ignore[attr-defined]  # Second find_by_calibre_author_id_and_library
        mapping_repo = AuthorMappingRepository(session)  # type: ignore[arg-type]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        mapping_service = MappingService(mapping_repo, metadata_repo)
        statistics = LinkingStatistics()
        processor = MappingBatchProcessor(mapping_service, statistics)

        callback_calls: list[tuple[int, int]] = []

        def progress_callback(current: int, total: int) -> None:
            callback_calls.append((current, total))

        match_results = [match_result, match_result]
        processor.process_batch(
            match_results,
            context={"library_id": 1},
            progress_callback=progress_callback,
        )

        assert len(callback_calls) == 2
        assert callback_calls[0] == (1, 2)
        assert callback_calls[1] == (2, 2)

    def test_process_batch_with_cancellation_check(
        self,
        session: DummySession,
        match_result: MatchResult,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test process_batch respects cancellation check."""
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]
        session.add_exec_result([])  # type: ignore[attr-defined]
        mapping_repo = AuthorMappingRepository(session)  # type: ignore[arg-type]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        mapping_service = MappingService(mapping_repo, metadata_repo)
        statistics = LinkingStatistics()
        processor = MappingBatchProcessor(mapping_service, statistics)

        call_count = 0

        def cancellation_check() -> bool:
            nonlocal call_count
            call_count += 1
            # Cancel on first check (before processing first item)
            return call_count == 1

        match_results = [match_result, match_result]
        result = processor.process_batch(
            match_results,
            context={"library_id": 1},
            cancellation_check=cancellation_check,
        )

        assert call_count > 0
        assert result == 0  # No items processed due to early cancellation

    def test_process_batch_mixed_results(
        self,
        session: DummySession,
        match_result: MatchResult,
        author_metadata: AuthorMetadata,
        author_data: AuthorData,
    ) -> None:
        """Test process_batch with mixed success/failure."""
        # First item: success
        session.set_exec_result([author_metadata])  # type: ignore[attr-defined]
        session.add_exec_result([])  # type: ignore[attr-defined]
        # Second item: failure (no metadata)
        session.add_exec_result([])  # type: ignore[attr-defined]
        mapping_repo = AuthorMappingRepository(session)  # type: ignore[arg-type]
        metadata_repo = AuthorMetadataRepository(session)  # type: ignore[arg-type]
        mapping_service = MappingService(mapping_repo, metadata_repo)
        statistics = LinkingStatistics()
        processor = MappingBatchProcessor(mapping_service, statistics)

        match_results = [
            match_result,
            MatchResult(
                confidence_score=0.8,
                matched_entity=author_data,
                match_method="fuzzy",
                calibre_author_id=2,
            ),
        ]
        result = processor.process_batch(match_results, context={"library_id": 1})

        assert result == 1
        assert statistics.mappings_created == 1
        assert statistics.mappings_failed == 1

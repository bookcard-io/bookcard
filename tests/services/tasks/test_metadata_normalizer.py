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

"""Tests for TaskMetadataNormalizer."""

from __future__ import annotations

import pytest

from bookcard.services.tasks.metadata_normalizer import TaskMetadataNormalizer


@pytest.fixture
def normalizer() -> type[TaskMetadataNormalizer]:
    """Return TaskMetadataNormalizer class for testing."""
    return TaskMetadataNormalizer


class TestNormalizeMetadata:
    """Test normalize_metadata method."""

    def test_normalize_metadata_both_none(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test normalize_metadata with both inputs None."""
        result = normalizer.normalize_metadata(None, None)
        assert result == {}

    def test_normalize_metadata_task_instance_only(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test normalize_metadata with only task_instance_metadata."""
        task_metadata = {"key1": "value1", "key2": 42}
        result = normalizer.normalize_metadata(task_metadata, None)
        assert result == {"key1": "value1", "key2": 42}

    def test_normalize_metadata_task_data_only(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test normalize_metadata with only task_data."""
        task_data = {"key1": "value1", "book_ids": [1, 2, 3]}
        result = normalizer.normalize_metadata(None, task_data)
        assert result == {"book_ids": [1, 2, 3]}

    def test_normalize_metadata_both_provided(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test normalize_metadata with both inputs provided."""
        task_metadata = {"key1": "value1"}
        task_data = {"key2": "value2", "book_ids": [1, 2]}
        result = normalizer.normalize_metadata(task_metadata, task_data)
        assert result == {"key1": "value1", "book_ids": [1, 2]}

    def test_normalize_metadata_book_ids_from_task_instance(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test normalize_metadata prefers book_ids from task_instance."""
        task_metadata = {"book_ids": [1, 2, 3]}
        task_data = {"book_ids": [4, 5, 6]}
        result = normalizer.normalize_metadata(task_metadata, task_data)
        assert result == {"book_ids": [1, 2, 3]}

    def test_normalize_metadata_book_ids_from_task_data(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test normalize_metadata falls back to book_ids from task_data."""
        task_metadata = {"key1": "value1"}
        task_data = {"book_ids": [4, 5, 6]}
        result = normalizer.normalize_metadata(task_metadata, task_data)
        assert result == {"key1": "value1", "book_ids": [4, 5, 6]}

    def test_normalize_metadata_no_book_ids(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test normalize_metadata when no book_ids present."""
        task_metadata = {"key1": "value1"}
        task_data = {"key2": "value2"}
        result = normalizer.normalize_metadata(task_metadata, task_data)
        assert result == {"key1": "value1"}


class TestExtractBookIds:
    """Test _extract_book_ids method."""

    def test_extract_book_ids_from_task_instance(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test _extract_book_ids prefers task_instance_metadata."""
        task_metadata = {"book_ids": [1, 2, 3]}
        task_data = {"book_ids": [4, 5, 6]}
        result = normalizer._extract_book_ids(task_metadata, task_data)
        assert result == [1, 2, 3]

    def test_extract_book_ids_from_task_data(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test _extract_book_ids falls back to task_data."""
        task_metadata = {"key1": "value1"}
        task_data = {"book_ids": [4, 5, 6]}
        result = normalizer._extract_book_ids(task_metadata, task_data)
        assert result == [4, 5, 6]

    def test_extract_book_ids_none_found(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test _extract_book_ids returns None when not found."""
        task_metadata = {"key1": "value1"}
        task_data = {"key2": "value2"}
        result = normalizer._extract_book_ids(task_metadata, task_data)
        assert result is None

    def test_extract_book_ids_task_data_none(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test _extract_book_ids with task_data None."""
        task_metadata = {"key1": "value1"}
        result = normalizer._extract_book_ids(task_metadata, None)
        assert result is None


class TestTryGetBookIdsFromDict:
    """Test _try_get_book_ids_from_dict method."""

    @pytest.mark.parametrize(
        ("metadata", "expected"),
        [
            ({"book_ids": [1, 2, 3]}, [1, 2, 3]),
            ({"book_ids": ["1", "2", "3"]}, [1, 2, 3]),
            ({"book_ids": [1, "2", 3]}, [1, 2, 3]),
            ({"book_ids": [1, 2, 3, "invalid"]}, [1, 2, 3]),
            ({"book_ids": ["invalid"]}, None),
            ({"book_ids": []}, None),
            ({"key": "value"}, None),
            ({}, None),
        ],
    )
    def test_try_get_book_ids_from_dict(
        self,
        normalizer: type[TaskMetadataNormalizer],
        metadata: dict[str, list[int] | list[str] | list],
        expected: list[int] | None,
    ) -> None:
        """Test _try_get_book_ids_from_dict with various inputs."""
        result = normalizer._try_get_book_ids_from_dict(metadata)
        assert result == expected


class TestNormalizeBookIdsList:
    """Test _normalize_book_ids_list method."""

    @pytest.mark.parametrize(
        ("book_ids", "expected"),
        [
            ([1, 2, 3], [1, 2, 3]),
            (["1", "2", "3"], [1, 2, 3]),
            ([1, "2", 3], [1, 2, 3]),
            (["1", 2, "3"], [1, 2, 3]),
            ([], None),
            (["invalid"], None),
            (["1", "invalid", "2"], [1, 2]),
            ([1, 2, "invalid"], [1, 2]),
        ],
    )
    def test_normalize_book_ids_list_valid(
        self,
        normalizer: type[TaskMetadataNormalizer],
        book_ids: list[int] | list[str] | list,
        expected: list[int] | None,
    ) -> None:
        """Test _normalize_book_ids_list with valid inputs."""
        result = normalizer._normalize_book_ids_list(book_ids)
        assert result == expected

    def test_normalize_book_ids_list_not_list(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test _normalize_book_ids_list with non-list input."""
        result = normalizer._normalize_book_ids_list("not a list")  # type: ignore[arg-type]
        assert result is None

    def test_normalize_book_ids_list_empty_list(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test _normalize_book_ids_list with empty list."""
        result = normalizer._normalize_book_ids_list([])
        assert result is None

    def test_normalize_book_ids_list_all_invalid(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test _normalize_book_ids_list with all invalid values."""
        result = normalizer._normalize_book_ids_list(["invalid1", "invalid2"])
        assert result is None

    def test_normalize_book_ids_list_mixed_types(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test _normalize_book_ids_list with mixed valid/invalid types."""
        result = normalizer._normalize_book_ids_list([1, "2", 3.0, "invalid", "4"])
        assert result == [1, 2, 4]

    def test_normalize_book_ids_list_string_numbers(
        self, normalizer: type[TaskMetadataNormalizer]
    ) -> None:
        """Test _normalize_book_ids_list with string numbers."""
        result = normalizer._normalize_book_ids_list(["123", "456", "789"])
        assert result == [123, 456, 789]

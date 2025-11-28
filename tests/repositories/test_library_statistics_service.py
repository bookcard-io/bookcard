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

"""Tests for library statistics service to achieve 100% coverage."""

from __future__ import annotations

import pytest

from fundamental.repositories.library_statistics_service import (
    LibraryStatisticsService,
)
from tests.conftest import DummySession


@pytest.fixture
def service() -> LibraryStatisticsService:
    """Create LibraryStatisticsService instance."""
    return LibraryStatisticsService()


@pytest.fixture
def session() -> DummySession:
    """Create a dummy database session."""
    return DummySession()


class TestLibraryStatisticsServiceGetStatistics:
    """Test get_statistics method."""

    def test_get_statistics_all_values(
        self,
        service: LibraryStatisticsService,
        session: DummySession,
    ) -> None:
        """Test get_statistics returns all statistics."""
        # Add results for each query in order:
        # 1. total_books
        # 2. total_series
        # 3. total_authors
        # 4. total_tags
        # 5. total_ratings
        # 6. total_content_size
        session.add_exec_result([10])
        session.add_exec_result([5])
        session.add_exec_result([8])
        session.add_exec_result([12])
        session.add_exec_result([7])
        session.add_exec_result([1000000])

        result = service.get_statistics(session=session)  # type: ignore[arg-type]

        assert result["total_books"] == 10
        assert result["total_series"] == 5
        assert result["total_authors"] == 8
        assert result["total_tags"] == 12
        assert result["total_ratings"] == 7
        assert result["total_content_size"] == 1000000

    def test_get_statistics_zero_values(
        self,
        service: LibraryStatisticsService,
        session: DummySession,
    ) -> None:
        """Test get_statistics handles zero values."""
        for _ in range(6):
            session.add_exec_result([0])

        result = service.get_statistics(session=session)  # type: ignore[arg-type]

        assert result["total_books"] == 0
        assert result["total_series"] == 0
        assert result["total_authors"] == 0
        assert result["total_tags"] == 0
        assert result["total_ratings"] == 0
        assert result["total_content_size"] == 0

    def test_get_statistics_none_books(
        self,
        service: LibraryStatisticsService,
        session: DummySession,
    ) -> None:
        """Test get_statistics handles None for total_books."""
        session.add_exec_result([None])
        for _ in range(5):
            session.add_exec_result([0])

        result = service.get_statistics(session=session)  # type: ignore[arg-type]

        assert result["total_books"] == 0

    def test_get_statistics_none_content_size(
        self,
        service: LibraryStatisticsService,
        session: DummySession,
    ) -> None:
        """Test get_statistics handles None for total_content_size."""
        session.add_exec_result([10])
        session.add_exec_result([5])
        session.add_exec_result([8])
        session.add_exec_result([12])
        session.add_exec_result([7])
        session.add_exec_result([None])

        result = service.get_statistics(session=session)  # type: ignore[arg-type]

        assert result["total_content_size"] == 0

    def test_get_statistics_large_values(
        self,
        service: LibraryStatisticsService,
        session: DummySession,
    ) -> None:
        """Test get_statistics handles large values."""
        session.add_exec_result([1000000])
        session.add_exec_result([50000])
        session.add_exec_result([80000])
        session.add_exec_result([120000])
        session.add_exec_result([70000])
        session.add_exec_result([5000000000])

        result = service.get_statistics(session=session)  # type: ignore[arg-type]

        assert result["total_books"] == 1000000
        assert result["total_series"] == 50000
        assert result["total_authors"] == 80000
        assert result["total_tags"] == 120000
        assert result["total_ratings"] == 70000
        assert result["total_content_size"] == 5000000000

    def test_get_statistics_content_size_int_conversion(
        self,
        service: LibraryStatisticsService,
        session: DummySession,
    ) -> None:
        """Test get_statistics converts content_size to int."""
        session.add_exec_result([10])
        session.add_exec_result([5])
        session.add_exec_result([8])
        session.add_exec_result([12])
        session.add_exec_result([7])
        # Simulate float from database
        session.add_exec_result([1000000.5])

        result = service.get_statistics(session=session)  # type: ignore[arg-type]

        assert isinstance(result["total_content_size"], int)
        assert result["total_content_size"] == 1000000

    def test_get_statistics_content_size_not_none(
        self,
        service: LibraryStatisticsService,
        session: DummySession,
    ) -> None:
        """Test get_statistics handles non-None content_size value."""
        session.add_exec_result([10])
        session.add_exec_result([5])
        session.add_exec_result([8])
        session.add_exec_result([12])
        session.add_exec_result([7])
        session.add_exec_result([5000000])

        result = service.get_statistics(session=session)  # type: ignore[arg-type]

        # This tests the else branch where total_content_size is not None
        assert result["total_content_size"] == 5000000

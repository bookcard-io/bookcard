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

"""Tests for OpenLibrary adapters to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bookcard.services.tasks.openlibrary.adapters import (
    CancellationCheckerAdapter,
    DatabaseRepositoryAdapter,
)


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock SQLModel session.

    Returns
    -------
    MagicMock
        Mock session object.
    """
    session = MagicMock()
    mock_connection = MagicMock()
    mock_execute = MagicMock()
    mock_connection.execute = mock_execute
    session.connection.return_value = mock_connection
    return session


class TestDatabaseRepositoryAdapter:
    """Test DatabaseRepositoryAdapter."""

    @pytest.fixture
    def adapter(self, mock_session: MagicMock) -> DatabaseRepositoryAdapter:
        """Create adapter instance.

        Parameters
        ----------
        mock_session : MagicMock
            Mock session object.

        Returns
        -------
        DatabaseRepositoryAdapter
            Adapter instance.
        """
        return DatabaseRepositoryAdapter(mock_session)

    def test_init(
        self, adapter: DatabaseRepositoryAdapter, mock_session: MagicMock
    ) -> None:
        """Test adapter initialization.

        Parameters
        ----------
        adapter : DatabaseRepositoryAdapter
            Adapter instance.
        mock_session : MagicMock
            Mock session object.
        """
        assert adapter.session == mock_session

    def test_bulk_save_with_objects(
        self, adapter: DatabaseRepositoryAdapter, mock_session: MagicMock
    ) -> None:
        """Test bulk_save with objects.

        Parameters
        ----------
        adapter : DatabaseRepositoryAdapter
            Adapter instance.
        mock_session : MagicMock
            Mock session object.
        """
        objects = [MagicMock(), MagicMock()]

        adapter.bulk_save(objects)

        mock_session.bulk_save_objects.assert_called_once_with(objects)

    def test_bulk_save_empty(
        self, adapter: DatabaseRepositoryAdapter, mock_session: MagicMock
    ) -> None:
        """Test bulk_save with empty list.

        Parameters
        ----------
        adapter : DatabaseRepositoryAdapter
            Adapter instance.
        mock_session : MagicMock
            Mock session object.
        """
        adapter.bulk_save([])

        mock_session.bulk_save_objects.assert_not_called()

    def test_commit(
        self, adapter: DatabaseRepositoryAdapter, mock_session: MagicMock
    ) -> None:
        """Test commit.

        Parameters
        ----------
        adapter : DatabaseRepositoryAdapter
            Adapter instance.
        mock_session : MagicMock
            Mock session object.
        """
        adapter.commit()

        mock_session.commit.assert_called_once()

    def test_rollback(
        self, adapter: DatabaseRepositoryAdapter, mock_session: MagicMock
    ) -> None:
        """Test rollback.

        Parameters
        ----------
        adapter : DatabaseRepositoryAdapter
            Adapter instance.
        mock_session : MagicMock
            Mock session object.
        """
        adapter.rollback()

        mock_session.rollback.assert_called_once()

    def test_truncate_tables(
        self, adapter: DatabaseRepositoryAdapter, mock_session: MagicMock
    ) -> None:
        """Test truncate_tables.

        Parameters
        ----------
        adapter : DatabaseRepositoryAdapter
            Adapter instance.
        mock_session : MagicMock
            Mock session object.
        """
        table_names = ["table1", "table2", "table3"]

        adapter.truncate_tables(table_names)

        mock_session.connection.assert_called_once()
        connection = mock_session.connection.return_value
        connection.execute.assert_called_once()
        # Check that the SQL contains the table names
        call_args = connection.execute.call_args[0][0]
        assert "table1" in str(call_args)
        assert "table2" in str(call_args)
        assert "table3" in str(call_args)
        mock_session.commit.assert_called_once()


class TestCancellationCheckerAdapter:
    """Test CancellationCheckerAdapter."""

    @pytest.fixture
    def mock_check_cancelled(self) -> MagicMock:
        """Create mock check_cancelled callback.

        Returns
        -------
        MagicMock
            Mock callback.
        """
        return MagicMock(return_value=False)

    @pytest.fixture
    def adapter(self, mock_check_cancelled: MagicMock) -> CancellationCheckerAdapter:
        """Create adapter instance.

        Parameters
        ----------
        mock_check_cancelled : MagicMock
            Mock check_cancelled callback.

        Returns
        -------
        CancellationCheckerAdapter
            Adapter instance.
        """
        return CancellationCheckerAdapter(mock_check_cancelled)

    def test_init(
        self,
        adapter: CancellationCheckerAdapter,
        mock_check_cancelled: MagicMock,
    ) -> None:
        """Test adapter initialization.

        Parameters
        ----------
        adapter : CancellationCheckerAdapter
            Adapter instance.
        mock_check_cancelled : MagicMock
            Mock check_cancelled callback.
        """
        assert adapter.check_cancelled == mock_check_cancelled

    def test_is_cancelled_false(
        self,
        adapter: CancellationCheckerAdapter,
        mock_check_cancelled: MagicMock,
    ) -> None:
        """Test is_cancelled returns False.

        Parameters
        ----------
        adapter : CancellationCheckerAdapter
            Adapter instance.
        mock_check_cancelled : MagicMock
            Mock check_cancelled callback.
        """
        mock_check_cancelled.return_value = False

        result = adapter.is_cancelled()

        assert result is False
        mock_check_cancelled.assert_called_once()

    def test_is_cancelled_true(
        self,
        adapter: CancellationCheckerAdapter,
        mock_check_cancelled: MagicMock,
    ) -> None:
        """Test is_cancelled returns True.

        Parameters
        ----------
        adapter : CancellationCheckerAdapter
            Adapter instance.
        mock_check_cancelled : MagicMock
            Mock check_cancelled callback.
        """
        mock_check_cancelled.return_value = True

        result = adapter.is_cancelled()

        assert result is True
        mock_check_cancelled.assert_called_once()

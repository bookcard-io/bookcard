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

"""Tests for ProgressReporterAdapter to achieve 100% coverage."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from fundamental.services.tasks.openlibrary.progress import ProgressReporterAdapter


@pytest.fixture
def mock_update_progress() -> MagicMock:
    """Create a mock update_progress callback.

    Returns
    -------
    MagicMock
        Mock update_progress callback.
    """
    return MagicMock()


class TestProgressReporterAdapter:
    """Test ProgressReporterAdapter."""

    @pytest.fixture
    def adapter(self, mock_update_progress: MagicMock) -> ProgressReporterAdapter:
        """Create adapter instance.

        Parameters
        ----------
        mock_update_progress : MagicMock
            Mock update_progress callback.

        Returns
        -------
        ProgressReporterAdapter
            Adapter instance.
        """
        return ProgressReporterAdapter(mock_update_progress)

    def test_init(
        self,
        adapter: ProgressReporterAdapter,
        mock_update_progress: MagicMock,
    ) -> None:
        """Test adapter initialization.

        Parameters
        ----------
        adapter : ProgressReporterAdapter
            Adapter instance.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        """
        assert adapter.update_progress == mock_update_progress

    @pytest.mark.parametrize(
        ("progress", "metadata"),
        [
            (0.0, None),
            (0.5, {"status": "Processing"}),
            (1.0, {"status": "Completed", "records": 100}),
            (0.25, {}),
        ],
    )
    def test_report(
        self,
        adapter: ProgressReporterAdapter,
        mock_update_progress: MagicMock,
        progress: float,
        metadata: dict[str, Any] | None,
    ) -> None:
        """Test reporting progress.

        Parameters
        ----------
        adapter : ProgressReporterAdapter
            Adapter instance.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        progress : float
            Progress value.
        metadata : dict[str, Any] | None
            Optional metadata.
        """
        adapter.report(progress, metadata)

        mock_update_progress.assert_called_once_with(progress, metadata)

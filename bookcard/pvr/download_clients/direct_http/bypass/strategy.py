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

"""Abstract strategy for bypass operations."""

from abc import ABC, abstractmethod

from bookcard.pvr.download_clients.direct_http.bypass.result import BypassResult


class BypassStrategy(ABC):
    """Abstract bypass strategy."""

    @abstractmethod
    def fetch(self, url: str) -> BypassResult:
        """Fetch HTML with bypass.

        Parameters
        ----------
        url : str
            URL to fetch.

        Returns
        -------
        BypassResult
            Result containing HTML or error information.
        """

    @abstractmethod
    def validate_dependencies(self) -> None:
        """Validate required dependencies are available.

        Raises
        ------
        ImportError
            If required dependencies are not available.
        """

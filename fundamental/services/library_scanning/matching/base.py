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

"""Base matching strategy abstraction."""

from abc import ABC, abstractmethod

from fundamental.models.core import Author
from fundamental.services.library_scanning.data_sources.base import BaseDataSource
from fundamental.services.library_scanning.matching.types import MatchResult


class BaseMatchingStrategy(ABC):
    """Abstract base class for matching strategies.

    Matching strategies determine how Calibre entities (authors, books)
    are matched to external data sources. Each strategy implements a
    different matching algorithm with different confidence levels.

    Subclasses should implement:
    - `match()`: Attempt to match an entity to external data source
    """

    @abstractmethod
    def match(
        self,
        entity: Author,
        data_source: BaseDataSource,
    ) -> MatchResult | None:
        """Attempt to match an entity to external data source.

        Parameters
        ----------
        entity : Author
            Calibre author entity to match.
        data_source : BaseDataSource
            External data source to search.

        Returns
        -------
        MatchResult | None
            Match result if found, None otherwise.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this matching strategy.

        Returns
        -------
        str
            Strategy name (e.g., "identifier", "exact", "fuzzy").
        """
        raise NotImplementedError

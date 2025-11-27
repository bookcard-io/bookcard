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

"""Abstract base class for EPUB fixes.

Implements Open/Closed Principle - new fixes can be added without
modifying the orchestrator.
"""

from abc import ABC, abstractmethod

from fundamental.models.epub_fixer import EPUBFixType
from fundamental.services.epub_fixer.core.epub import EPUBContents, FixResult


class EPUBFix(ABC):
    """Abstract base class for EPUB fixes.

    Each fix implementation should handle a single type of fix,
    following Single Responsibility Principle.
    """

    @abstractmethod
    def apply(self, contents: EPUBContents) -> list[FixResult]:
        """Apply fix to EPUB contents.

        Parameters
        ----------
        contents : EPUBContents
            EPUB contents to fix (modified in place).

        Returns
        -------
        list[FixResult]
            List of fixes applied.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def fix_type(self) -> EPUBFixType:
        """Return the type of fix this class handles.

        Returns
        -------
        EPUBFixType
            Fix type enum value.
        """
        raise NotImplementedError

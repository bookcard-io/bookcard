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

"""EPUB fixer orchestrator.

Coordinates the fixing process using dependency injection.
Follows Open/Closed Principle - new fixes can be added without modification.
"""

from bookcard.services.epub_fixer.core.epub import EPUBContents, FixResult
from bookcard.services.epub_fixer.core.fixes.base import EPUBFix


class EPUBFixerOrchestrator:
    """Orchestrator for EPUB fixing process.

    Coordinates multiple fix implementations without knowing their details.
    Follows Dependency Inversion Principle - depends on abstractions (EPUBFix).

    Parameters
    ----------
    fixes : list[EPUBFix]
        List of fix implementations to apply.
    """

    def __init__(self, fixes: list[EPUBFix]) -> None:
        """Initialize orchestrator.

        Parameters
        ----------
        fixes : list[EPUBFix]
            List of fix implementations to apply.
        """
        self._fixes = fixes

    def process(self, contents: EPUBContents) -> list[FixResult]:
        """Apply all fixes to EPUB contents.

        Parameters
        ----------
        contents : EPUBContents
            EPUB contents to fix (modified in place).

        Returns
        -------
        list[FixResult]
            List of all fixes applied.
        """
        all_results: list[FixResult] = []

        for fix in self._fixes:
            results = fix.apply(contents)
            all_results.extend(results)

        return all_results

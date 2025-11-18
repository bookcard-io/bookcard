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

"""Matching strategies for linking Calibre entities to external data sources."""

from fundamental.services.library_scanning.matching.base import BaseMatchingStrategy
from fundamental.services.library_scanning.matching.exact import (
    ExactNameMatchingStrategy,
)
from fundamental.services.library_scanning.matching.fuzzy import (
    FuzzyNameMatchingStrategy,
)
from fundamental.services.library_scanning.matching.identifier import (
    IdentifierMatchingStrategy,
)
from fundamental.services.library_scanning.matching.orchestrator import (
    MatchingOrchestrator,
)
from fundamental.services.library_scanning.matching.types import MatchResult

__all__ = [
    "BaseMatchingStrategy",
    "ExactNameMatchingStrategy",
    "FuzzyNameMatchingStrategy",
    "IdentifierMatchingStrategy",
    "MatchResult",
    "MatchingOrchestrator",
]

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

"""Cover art extraction strategies for different book formats."""

from fundamental.services.cover_extractors.base import CoverExtractionStrategy
from fundamental.services.cover_extractors.epub import EpubCoverExtractor
from fundamental.services.cover_extractors.fb2 import Fb2CoverExtractor
from fundamental.services.cover_extractors.mobi import MobiCoverExtractor
from fundamental.services.cover_extractors.pdf import PdfCoverExtractor

__all__ = [
    "CoverExtractionStrategy",
    "EpubCoverExtractor",
    "Fb2CoverExtractor",
    "MobiCoverExtractor",
    "PdfCoverExtractor",
]

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

from bookcard.services.cover_extractors.base import CoverExtractionStrategy
from bookcard.services.cover_extractors.cbz import CbzCoverExtractor
from bookcard.services.cover_extractors.docx import DocxCoverExtractor
from bookcard.services.cover_extractors.epub import EpubCoverExtractor
from bookcard.services.cover_extractors.fb2 import Fb2CoverExtractor
from bookcard.services.cover_extractors.fbz import FbzCoverExtractor
from bookcard.services.cover_extractors.html import HtmlCoverExtractor
from bookcard.services.cover_extractors.kepub import KepubCoverExtractor
from bookcard.services.cover_extractors.mobi import MobiCoverExtractor
from bookcard.services.cover_extractors.odt import OdtCoverExtractor
from bookcard.services.cover_extractors.pdf import PdfCoverExtractor

__all__ = [
    "CbzCoverExtractor",
    "CoverExtractionStrategy",
    "DocxCoverExtractor",
    "EpubCoverExtractor",
    "Fb2CoverExtractor",
    "FbzCoverExtractor",
    "HtmlCoverExtractor",
    "KepubCoverExtractor",
    "MobiCoverExtractor",
    "OdtCoverExtractor",
    "PdfCoverExtractor",
]

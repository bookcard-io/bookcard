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

"""Metadata extraction strategies for various book formats."""

from bookcard.services.metadata_extractors.base import MetadataExtractionStrategy
from bookcard.services.metadata_extractors.docx import DocxMetadataExtractor
from bookcard.services.metadata_extractors.epub import EpubMetadataExtractor
from bookcard.services.metadata_extractors.fb2 import Fb2MetadataExtractor
from bookcard.services.metadata_extractors.fbz import FbzMetadataExtractor
from bookcard.services.metadata_extractors.filename import (
    FilenameMetadataExtractor,
)
from bookcard.services.metadata_extractors.html import HtmlMetadataExtractor
from bookcard.services.metadata_extractors.kepub import KepubMetadataExtractor
from bookcard.services.metadata_extractors.mobi import MobiMetadataExtractor
from bookcard.services.metadata_extractors.odt import OdtMetadataExtractor
from bookcard.services.metadata_extractors.opds import OpdsMetadataExtractor
from bookcard.services.metadata_extractors.pdf import PdfMetadataExtractor
from bookcard.services.metadata_extractors.rtf import RtfMetadataExtractor
from bookcard.services.metadata_extractors.txt import TxtMetadataExtractor

__all__ = [
    "DocxMetadataExtractor",
    "EpubMetadataExtractor",
    "Fb2MetadataExtractor",
    "FbzMetadataExtractor",
    "FilenameMetadataExtractor",
    "HtmlMetadataExtractor",
    "KepubMetadataExtractor",
    "MetadataExtractionStrategy",
    "MobiMetadataExtractor",
    "OdtMetadataExtractor",
    "OpdsMetadataExtractor",
    "PdfMetadataExtractor",
    "RtfMetadataExtractor",
    "TxtMetadataExtractor",
]

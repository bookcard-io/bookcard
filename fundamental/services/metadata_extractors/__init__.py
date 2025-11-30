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

from fundamental.services.metadata_extractors.base import MetadataExtractionStrategy
from fundamental.services.metadata_extractors.docx import DocxMetadataExtractor
from fundamental.services.metadata_extractors.epub import EpubMetadataExtractor
from fundamental.services.metadata_extractors.fb2 import Fb2MetadataExtractor
from fundamental.services.metadata_extractors.fbz import FbzMetadataExtractor
from fundamental.services.metadata_extractors.filename import (
    FilenameMetadataExtractor,
)
from fundamental.services.metadata_extractors.html import HtmlMetadataExtractor
from fundamental.services.metadata_extractors.kepub import KepubMetadataExtractor
from fundamental.services.metadata_extractors.mobi import MobiMetadataExtractor
from fundamental.services.metadata_extractors.odt import OdtMetadataExtractor
from fundamental.services.metadata_extractors.opds import OpdsMetadataExtractor
from fundamental.services.metadata_extractors.pdf import PdfMetadataExtractor
from fundamental.services.metadata_extractors.rtf import RtfMetadataExtractor
from fundamental.services.metadata_extractors.txt import TxtMetadataExtractor

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

# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Metadata extraction strategies for various book formats."""

from fundamental.services.metadata_extractors.base import MetadataExtractionStrategy
from fundamental.services.metadata_extractors.epub import EpubMetadataExtractor
from fundamental.services.metadata_extractors.fb2 import Fb2MetadataExtractor
from fundamental.services.metadata_extractors.filename import (
    FilenameMetadataExtractor,
)
from fundamental.services.metadata_extractors.mobi import MobiMetadataExtractor
from fundamental.services.metadata_extractors.opds import OpdsMetadataExtractor
from fundamental.services.metadata_extractors.pdf import PdfMetadataExtractor

__all__ = [
    "EpubMetadataExtractor",
    "Fb2MetadataExtractor",
    "FilenameMetadataExtractor",
    "MetadataExtractionStrategy",
    "MobiMetadataExtractor",
    "OpdsMetadataExtractor",
    "PdfMetadataExtractor",
]

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

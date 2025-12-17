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

"""Tests for BookMetadataExtractor."""

from pathlib import Path
from unittest.mock import patch

from bookcard.services.book_metadata import BookMetadata
from bookcard.services.book_metadata_extractor import BookMetadataExtractor
from bookcard.services.metadata_extractors import MetadataExtractionStrategy


class MockMetadataStrategy(MetadataExtractionStrategy):
    """Mock strategy for testing."""

    def __init__(
        self, can_handle_format: str, extract_result: BookMetadata | None = None
    ) -> None:
        """Initialize mock strategy.

        Parameters
        ----------
        can_handle_format : str
            Format this strategy can handle.
        extract_result : BookMetadata | None
            Result to return from extract.
        """
        self._can_handle_format = can_handle_format
        self._extract_result = extract_result

    def can_handle(self, file_format: str) -> bool:
        """Check if strategy can handle format."""
        return file_format.upper() == self._can_handle_format.upper()

    def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
        """Extract metadata from file."""
        if self._extract_result is None:
            raise ValueError("Extraction failed")
        return self._extract_result


def test_book_metadata_extractor_init() -> None:
    """Test BookMetadataExtractor initialization (covers lines 58-67)."""
    extractor = BookMetadataExtractor()
    assert len(extractor._strategies) == 13  # Updated: 13 extractors (was 6)
    # Last strategy should be FilenameMetadataExtractor (fallback)
    from bookcard.services.metadata_extractors import FilenameMetadataExtractor

    assert isinstance(extractor._strategies[-1], FilenameMetadataExtractor)


def test_register_strategy() -> None:
    """Test register_strategy inserts before filename fallback (covers line 78)."""
    extractor = BookMetadataExtractor()
    initial_count = len(extractor._strategies)
    last_strategy = extractor._strategies[-1]

    mock_strategy = MockMetadataStrategy("TEST")
    extractor.register_strategy(mock_strategy)

    assert len(extractor._strategies) == initial_count + 1
    assert extractor._strategies[-2] is mock_strategy
    assert (
        extractor._strategies[-1] is last_strategy
    )  # FilenameMetadataExtractor still last


def test_extract_metadata_success() -> None:
    """Test extract_metadata returns metadata when strategy succeeds (covers lines 103-116)."""
    extractor = BookMetadataExtractor()
    metadata = BookMetadata(title="Test Book", author="Test Author")
    mock_strategy = MockMetadataStrategy("EPUB", extract_result=metadata)
    extractor._strategies = [mock_strategy]  # Replace with our mock

    file_path = Path("/tmp/test.epub")
    result = extractor.extract_metadata(file_path, "epub")

    assert result.title == "Test Book"
    assert result.author == "Test Author"


def test_extract_metadata_original_filename_none() -> None:
    """Test extract_metadata uses file_path.name when original_filename is None (covers lines 103-104)."""
    extractor = BookMetadataExtractor()
    metadata = BookMetadata(title="test", author="Unknown")
    mock_strategy = MockMetadataStrategy("EPUB", extract_result=metadata)
    extractor._strategies = [mock_strategy]

    file_path = Path("/tmp/test.epub")
    with patch.object(mock_strategy, "extract") as mock_extract:
        mock_extract.return_value = metadata
        extractor.extract_metadata(file_path, "epub", original_filename=None)

        mock_extract.assert_called_once_with(file_path, "test.epub")


def test_extract_metadata_format_upper() -> None:
    """Test extract_metadata converts format to uppercase (covers line 106)."""
    extractor = BookMetadataExtractor()
    metadata = BookMetadata(title="Test Book", author="Test Author")
    mock_strategy = MockMetadataStrategy("PDF", extract_result=metadata)
    extractor._strategies = [mock_strategy]

    file_path = Path("/tmp/test.pdf")
    result = extractor.extract_metadata(file_path, ".pdf")

    assert result.title == "Test Book"


def test_extract_metadata_strategy_raises_valueerror() -> None:
    """Test extract_metadata continues when strategy raises ValueError (covers lines 112-116)."""
    extractor = BookMetadataExtractor()

    class FailingStrategy(MetadataExtractionStrategy):
        def can_handle(self, file_format: str) -> bool:
            return file_format.upper() == "EPUB"

        def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
            raise ValueError("Extraction failed")

    metadata = BookMetadata(title="Test Book", author="Test Author")
    mock_strategy = MockMetadataStrategy("EPUB", extract_result=metadata)
    extractor._strategies = [FailingStrategy(), mock_strategy]

    file_path = Path("/tmp/test.epub")
    result = extractor.extract_metadata(file_path, "epub")

    assert result.title == "Test Book"


def test_extract_metadata_strategy_raises_importerror() -> None:
    """Test extract_metadata continues when strategy raises ImportError (covers lines 112-116)."""
    extractor = BookMetadataExtractor()

    class FailingStrategy(MetadataExtractionStrategy):
        def can_handle(self, file_format: str) -> bool:
            return file_format.upper() == "EPUB"

        def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
            raise ImportError("Module not found")

    metadata = BookMetadata(title="Test Book", author="Test Author")
    mock_strategy = MockMetadataStrategy("EPUB", extract_result=metadata)
    extractor._strategies = [FailingStrategy(), mock_strategy]

    file_path = Path("/tmp/test.epub")
    result = extractor.extract_metadata(file_path, "epub")

    assert result.title == "Test Book"


def test_extract_metadata_strategy_raises_oserror() -> None:
    """Test extract_metadata continues when strategy raises OSError (covers lines 112-116)."""
    extractor = BookMetadataExtractor()

    class FailingStrategy(MetadataExtractionStrategy):
        def can_handle(self, file_format: str) -> bool:
            return file_format.upper() == "EPUB"

        def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
            raise OSError("File not found")

    metadata = BookMetadata(title="Test Book", author="Test Author")
    mock_strategy = MockMetadataStrategy("EPUB", extract_result=metadata)
    extractor._strategies = [FailingStrategy(), mock_strategy]

    file_path = Path("/tmp/test.epub")
    result = extractor.extract_metadata(file_path, "epub")

    assert result.title == "Test Book"


def test_extract_metadata_strategy_raises_keyerror() -> None:
    """Test extract_metadata continues when strategy raises KeyError (covers lines 112-116)."""
    extractor = BookMetadataExtractor()

    class FailingStrategy(MetadataExtractionStrategy):
        def can_handle(self, file_format: str) -> bool:
            return file_format.upper() == "EPUB"

        def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
            raise KeyError("Key not found")

    metadata = BookMetadata(title="Test Book", author="Test Author")
    mock_strategy = MockMetadataStrategy("EPUB", extract_result=metadata)
    extractor._strategies = [FailingStrategy(), mock_strategy]

    file_path = Path("/tmp/test.epub")
    result = extractor.extract_metadata(file_path, "epub")

    assert result.title == "Test Book"


def test_extract_metadata_fallback_to_filename() -> None:
    """Test extract_metadata falls back to FilenameMetadataExtractor (covers lines 118-119)."""
    extractor = BookMetadataExtractor()

    class FailingStrategy(MetadataExtractionStrategy):
        def can_handle(self, file_format: str) -> bool:
            return file_format.upper() == "EPUB"

        def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
            raise ValueError("Extraction failed")

    # Remove all strategies except the last one (FilenameMetadataExtractor)
    extractor._strategies = [FailingStrategy(), *extractor._strategies[-1:]]

    file_path = Path("/tmp/My Great Book.epub")
    result = extractor.extract_metadata(file_path, "epub")

    # FilenameMetadataExtractor should extract from filename
    assert result.title is not None


def test_extract_metadata_strategy_skips_when_cannot_handle() -> None:
    """Test extract_metadata skips strategy when can_handle returns False (covers line 111)."""
    extractor = BookMetadataExtractor()
    metadata = BookMetadata(title="Test Book", author="Test Author")
    mock_strategy = MockMetadataStrategy("PDF", extract_result=metadata)
    extractor._strategies = [mock_strategy]

    file_path = Path("/tmp/test.epub")
    # Should fall back to FilenameMetadataExtractor since PDF strategy can't handle EPUB
    result = extractor.extract_metadata(file_path, "epub")

    # FilenameMetadataExtractor should extract from filename
    assert result.title is not None

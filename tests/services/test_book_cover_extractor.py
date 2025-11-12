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

"""Tests for BookCoverExtractor."""

from pathlib import Path

from fundamental.services.book_cover_extractor import BookCoverExtractor
from fundamental.services.cover_extractors import CoverExtractionStrategy


class MockStrategy(CoverExtractionStrategy):
    """Mock strategy for testing."""

    def __init__(
        self, can_handle_format: str, extract_result: bytes | None = None
    ) -> None:
        """Initialize mock strategy.

        Parameters
        ----------
        can_handle_format : str
            Format this strategy can handle.
        extract_result : bytes | None
            Result to return from extract_cover.
        """
        self._can_handle_format = can_handle_format
        self._extract_result = extract_result

    def can_handle(self, file_format: str) -> bool:
        """Check if strategy can handle format."""
        return file_format.upper() == self._can_handle_format.upper()

    def extract_cover(self, file_path: Path) -> bytes | None:
        """Extract cover from file."""
        return self._extract_result


def test_book_cover_extractor_init() -> None:
    """Test BookCoverExtractor initialization (covers lines 55-62)."""
    extractor = BookCoverExtractor()
    assert len(extractor._strategies) == 4
    assert all(isinstance(s, CoverExtractionStrategy) for s in extractor._strategies)


def test_register_strategy() -> None:
    """Test register_strategy adds strategy to list (covers line 72)."""
    extractor = BookCoverExtractor()
    initial_count = len(extractor._strategies)

    mock_strategy = MockStrategy("TEST")
    extractor.register_strategy(mock_strategy)

    assert len(extractor._strategies) == initial_count + 1
    assert extractor._strategies[-1] is mock_strategy


def test_extract_cover_success() -> None:
    """Test extract_cover returns cover data when strategy succeeds (covers lines 93-104)."""
    extractor = BookCoverExtractor()
    mock_strategy = MockStrategy("EPUB", extract_result=b"cover data")
    extractor._strategies = [mock_strategy]  # Replace with our mock

    file_path = Path("/tmp/test.epub")
    result = extractor.extract_cover(file_path, "epub")

    assert result == b"cover data"


def test_extract_cover_format_upper() -> None:
    """Test extract_cover converts format to uppercase (covers line 93)."""
    extractor = BookCoverExtractor()
    mock_strategy = MockStrategy("PDF", extract_result=b"cover data")
    extractor._strategies = [mock_strategy]

    file_path = Path("/tmp/test.pdf")
    result = extractor.extract_cover(file_path, ".pdf")

    assert result == b"cover data"


def test_extract_cover_no_match() -> None:
    """Test extract_cover returns None when no strategy matches (covers lines 96-104)."""
    extractor = BookCoverExtractor()
    mock_strategy = MockStrategy("UNKNOWN", extract_result=b"cover data")
    extractor._strategies = [mock_strategy]

    file_path = Path("/tmp/test.epub")
    result = extractor.extract_cover(file_path, "epub")

    assert result is None


def test_extract_cover_strategy_returns_none() -> None:
    """Test extract_cover continues when strategy returns None (covers lines 99-104)."""
    extractor = BookCoverExtractor()
    mock_strategy1 = MockStrategy("EPUB", extract_result=None)
    mock_strategy2 = MockStrategy("EPUB", extract_result=b"cover data")
    extractor._strategies = [mock_strategy1, mock_strategy2]

    file_path = Path("/tmp/test.epub")
    result = extractor.extract_cover(file_path, "epub")

    assert result == b"cover data"


def test_extract_cover_strategy_raises_exception() -> None:
    """Test extract_cover suppresses exceptions and continues (covers lines 99-104)."""
    extractor = BookCoverExtractor()

    class FailingStrategy(CoverExtractionStrategy):
        def can_handle(self, file_format: str) -> bool:
            return file_format.upper() == "EPUB"

        def extract_cover(self, file_path: Path) -> bytes | None:
            raise ValueError("Extraction failed")

    mock_strategy = MockStrategy("EPUB", extract_result=b"cover data")
    extractor._strategies = [FailingStrategy(), mock_strategy]

    file_path = Path("/tmp/test.epub")
    result = extractor.extract_cover(file_path, "epub")

    assert result == b"cover data"


def test_extract_cover_all_fail() -> None:
    """Test extract_cover returns None when all strategies fail (covers lines 96-104)."""
    extractor = BookCoverExtractor()

    class FailingStrategy(CoverExtractionStrategy):
        def can_handle(self, file_format: str) -> bool:
            return file_format.upper() == "EPUB"

        def extract_cover(self, file_path: Path) -> bytes | None:
            raise ValueError("Extraction failed")

    extractor._strategies = [FailingStrategy()]

    file_path = Path("/tmp/test.epub")
    result = extractor.extract_cover(file_path, "epub")

    assert result is None

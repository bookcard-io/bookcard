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

"""Tests for text cleaner to achieve 100% coverage."""

import pytest

from bookcard.metadata.providers.dnb._text_cleaner import TextCleaner


def test_text_cleaner_init(text_cleaner: TextCleaner) -> None:
    """Test TextCleaner initialization."""
    assert text_cleaner is not None
    assert hasattr(text_cleaner, "UNWANTED_SERIES_PATTERNS")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Normal text", "Normal text"),
        ("Text with sorting\x98\x9c", "Text with sorting"),
        (None, None),
        ("", ""),
    ],
)
def test_text_cleaner_remove_sorting_characters(
    text_cleaner: TextCleaner,
    text: str | None,
    expected: str | None,
) -> None:
    """Test sorting character removal."""
    result = text_cleaner.remove_sorting_characters(text)
    if expected is None:
        assert result is None
    else:
        assert result == expected


@pytest.mark.parametrize(
    ("title", "expected_contains"),
    [
        ("Simple Title", "Simple Title"),
        ("Title / Aus dem Englischen von Translator", "Title"),
        ("Title : Aus dem Französischen von Max Mustermann", "Title"),
        (None, ""),
        ("", ""),
    ],
)
def test_text_cleaner_clean_title(
    text_cleaner: TextCleaner,
    title: str | None,
    expected_contains: str,
) -> None:
    """Test title cleaning."""
    result = text_cleaner.clean_title(title)
    if expected_contains:
        assert expected_contains in result or result == expected_contains
    else:
        assert result == ""


@pytest.mark.parametrize(
    ("author", "expected"),
    [
        ("Last, First", "First Last"),
        ("Mustermann, Max", "Max Mustermann"),
        ("Single Name", "Single Name"),
        ("Last, First Middle", "First Middle Last"),
    ],
)
def test_text_cleaner_clean_author_name(
    text_cleaner: TextCleaner,
    author: str,
    expected: str,
) -> None:
    """Test author name cleaning."""
    result = text_cleaner.clean_author_name(author)
    assert result == expected


def test_text_cleaner_clean_series_simple(text_cleaner: TextCleaner) -> None:
    """Test series cleaning for simple series."""
    result = text_cleaner.clean_series("Test Series")
    assert result == "Test Series"


def test_text_cleaner_clean_series_none(text_cleaner: TextCleaner) -> None:
    """Test series cleaning returns None for None input."""
    result = text_cleaner.clean_series(None)
    assert result is None


def test_text_cleaner_clean_series_empty(text_cleaner: TextCleaner) -> None:
    """Test series cleaning returns None for empty string."""
    result = text_cleaner.clean_series("")
    assert result is None


def test_text_cleaner_clean_series_whitespace_only(text_cleaner: TextCleaner) -> None:
    """Test series cleaning returns None for whitespace only."""
    result = text_cleaner.clean_series("   \t\n  ")
    assert result is None


def test_text_cleaner_clean_series_publisher_match(text_cleaner: TextCleaner) -> None:
    """Test series cleaning filters out publisher name."""
    result = text_cleaner.clean_series("Test Verlag", publisher_name="Test Verlag")
    assert result is None


def test_text_cleaner_clean_series_publisher_prefix(text_cleaner: TextCleaner) -> None:
    """Test series cleaning filters out series starting with publisher prefix."""
    result = text_cleaner.clean_series(
        "TestVerlag Series",
        publisher_name="TestVerlag Publishing",
    )
    assert result is None


def test_text_cleaner_clean_series_unwanted_pattern(text_cleaner: TextCleaner) -> None:
    """Test series cleaning filters out unwanted patterns."""
    result = text_cleaner.clean_series("Roman")
    assert result is None

    result = text_cleaner.clean_series("dtv Taschenbuch")
    assert result is None


def test_text_cleaner_is_publisher_series_exact_match(
    text_cleaner: TextCleaner,
) -> None:
    """Test publisher series detection with exact match."""
    result = text_cleaner._is_publisher_series("Test Verlag", "Test Verlag")
    assert result is True


def test_text_cleaner_is_publisher_series_prefix_match(
    text_cleaner: TextCleaner,
) -> None:
    """Test publisher series detection with prefix match."""
    result = text_cleaner._is_publisher_series(
        "TestVerlag Series",
        "TestVerlag Publishing",
    )
    assert result is True


def test_text_cleaner_is_publisher_series_no_match(text_cleaner: TextCleaner) -> None:
    """Test publisher series detection with no match."""
    result = text_cleaner._is_publisher_series("Different Series", "Test Verlag")
    assert result is False


def test_text_cleaner_is_publisher_series_no_regex_match_final_return(
    text_cleaner: TextCleaner,
) -> None:
    """Test publisher series detection returns False when regex doesn't match."""
    # Publisher with 4+ word chars, but regex match doesn't find a prefix match in series
    # The regex r"^(\w{4,})" matches "Test" from "Test Verlag"
    # But series doesn't start with "Test", so should return False at line 244
    result = text_cleaner._is_publisher_series(
        "Completely Different Series", "Test Verlag"
    )
    assert result is False


def test_text_cleaner_is_publisher_series_regex_no_match(
    text_cleaner: TextCleaner,
) -> None:
    """Test publisher series detection when regex doesn't match publisher."""
    # Publisher with non-word characters that prevent regex match
    # This should skip the regex check and go to line 244
    result = text_cleaner._is_publisher_series("Some Series", "!!!")
    assert result is False


def test_text_cleaner_is_publisher_series_none_publisher(
    text_cleaner: TextCleaner,
) -> None:
    """Test publisher series detection with None publisher."""
    result = text_cleaner._is_publisher_series("Test Series", None)
    assert result is False


def test_text_cleaner_is_publisher_series_empty_publisher_after_cleaning(
    text_cleaner: TextCleaner,
) -> None:
    """Test publisher series detection when publisher becomes empty after cleaning."""
    result = text_cleaner._is_publisher_series("Test Series", "\x98\x9c")
    assert result is False


def test_text_cleaner_is_publisher_series_no_prefix_match(
    text_cleaner: TextCleaner,
) -> None:
    """Test publisher series detection when no prefix match found."""
    result = text_cleaner._is_publisher_series("Different Series", "Test")
    assert result is False


def test_text_cleaner_matches_unwanted_pattern_invalid_regex(
    text_cleaner: TextCleaner,
) -> None:
    """Test unwanted pattern matching handles invalid regex patterns."""
    from bookcard.metadata.providers.dnb._text_cleaner import TextCleaner

    # Temporarily add an invalid pattern to the class
    original_patterns = TextCleaner.UNWANTED_SERIES_PATTERNS.copy()
    TextCleaner.UNWANTED_SERIES_PATTERNS.append("[invalid[regex")
    try:
        result = text_cleaner._matches_unwanted_pattern("Test Series")
        assert result is False
    finally:
        TextCleaner.UNWANTED_SERIES_PATTERNS = original_patterns


def test_text_cleaner_matches_unwanted_pattern(text_cleaner: TextCleaner) -> None:
    """Test unwanted pattern matching."""
    result = text_cleaner._matches_unwanted_pattern("Roman")
    assert result is True

    result = text_cleaner._matches_unwanted_pattern("Test Series")
    assert result is False


def test_text_cleaner_matches_unwanted_pattern_case_insensitive(
    text_cleaner: TextCleaner,
) -> None:
    """Test unwanted pattern matching is case insensitive."""
    result = text_cleaner._matches_unwanted_pattern("ROMAN")
    assert result is True

    result = text_cleaner._matches_unwanted_pattern("roman")
    assert result is True


def test_text_cleaner_clean_series_with_sorting_characters(
    text_cleaner: TextCleaner,
) -> None:
    """Test series cleaning removes sorting characters."""
    series_with_sorting = "Test\x98Series"
    result = text_cleaner.clean_series(series_with_sorting)
    assert result == "TestSeries"


def test_text_cleaner_clean_series_only_sorting_characters(
    text_cleaner: TextCleaner,
) -> None:
    """Test series cleaning returns None when only sorting characters remain."""
    series_only_sorting = "\x98\x9c"
    result = text_cleaner.clean_series(series_only_sorting)
    assert result is None


def test_text_cleaner_clean_series_valid_series(text_cleaner: TextCleaner) -> None:
    """Test series cleaning preserves valid series."""
    valid_series = "Harry Potter"
    result = text_cleaner.clean_series(valid_series)
    assert result == valid_series


@pytest.mark.parametrize(
    ("series", "publisher", "expected"),
    [
        ("Test Series", None, "Test Series"),
        ("Test Series", "Other Publisher", "Test Series"),
        ("Test Verlag", "Test Verlag", None),
        ("Roman", None, None),
        ("", None, None),
        (None, None, None),
    ],
)
def test_text_cleaner_clean_series_parametrized(
    text_cleaner: TextCleaner,
    series: str | None,
    publisher: str | None,
    expected: str | None,
) -> None:
    """Test series cleaning with various inputs."""
    result = text_cleaner.clean_series(series, publisher)
    assert result == expected

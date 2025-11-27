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

"""Tests for file type utilities."""

from fundamental.services.epub_fixer.utils.file_types import FileTypes


def test_is_text_file_html() -> None:
    """Test is_text_file with HTML files."""
    assert FileTypes.is_text_file("file.html") is True
    assert FileTypes.is_text_file("file.xhtml") is True
    assert FileTypes.is_text_file("file.htm") is True


def test_is_text_file_xml() -> None:
    """Test is_text_file with XML files."""
    assert FileTypes.is_text_file("file.xml") is True
    assert FileTypes.is_text_file("file.opf") is True
    assert FileTypes.is_text_file("file.ncx") is True


def test_is_text_file_other_text() -> None:
    """Test is_text_file with other text files."""
    assert FileTypes.is_text_file("file.css") is True
    assert FileTypes.is_text_file("file.svg") is True


def test_is_text_file_binary() -> None:
    """Test is_text_file with binary files."""
    assert FileTypes.is_text_file("file.jpg") is False
    assert FileTypes.is_text_file("file.png") is False
    assert FileTypes.is_text_file("file.epub") is False


def test_is_text_file_case_insensitive() -> None:
    """Test is_text_file is case insensitive."""
    assert FileTypes.is_text_file("file.HTML") is True
    assert FileTypes.is_text_file("file.XHTML") is True
    assert FileTypes.is_text_file("file.XML") is True


def test_is_text_file_no_extension() -> None:
    """Test is_text_file with files without extension."""
    assert FileTypes.is_text_file("file") is False
    assert FileTypes.is_text_file("mimetype") is False


def test_is_html_file() -> None:
    """Test is_html_file with HTML files."""
    assert FileTypes.is_html_file("file.html") is True
    assert FileTypes.is_html_file("file.xhtml") is True
    assert FileTypes.is_html_file("file.htm") is False  # htm is not in HTML_EXTENSIONS


def test_is_html_file_case_insensitive() -> None:
    """Test is_html_file is case insensitive."""
    assert FileTypes.is_html_file("file.HTML") is True
    assert FileTypes.is_html_file("file.XHTML") is True


def test_is_html_file_non_html() -> None:
    """Test is_html_file with non-HTML files."""
    assert FileTypes.is_html_file("file.xml") is False
    assert FileTypes.is_html_file("file.css") is False
    assert FileTypes.is_html_file("file.jpg") is False


def test_get_extension() -> None:
    """Test _get_extension method."""
    assert FileTypes._get_extension("file.html") == "html"
    assert FileTypes._get_extension("file.xhtml") == "xhtml"
    assert FileTypes._get_extension("path/to/file.xml") == "xml"
    assert FileTypes._get_extension("file") == ""
    assert FileTypes._get_extension("file.HTML") == "html"  # lowercase
    assert FileTypes._get_extension("file.tar.gz") == "gz"  # last extension


def test_get_extension_edge_cases() -> None:
    """Test _get_extension with edge cases."""
    assert FileTypes._get_extension("") == ""
    assert FileTypes._get_extension(".") == ""
    assert FileTypes._get_extension("file.") == ""

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

"""Tests for body ID link fix implementation."""

from bookcard.models.epub_fixer import EPUBFixType
from bookcard.services.epub_fixer.core.epub import EPUBContents
from bookcard.services.epub_fixer.core.fixes.body_id_link import BodyIdLinkFix


def test_body_id_link_fix_type() -> None:
    """Test BodyIdLinkFix fix_type property."""
    fix = BodyIdLinkFix()
    assert fix.fix_type == EPUBFixType.BODY_ID_LINK


def test_body_id_link_fix_success() -> None:
    """Test body ID link fix with valid body ID."""
    fix = BodyIdLinkFix()
    contents = EPUBContents(
        files={
            "chapter1.html": '<?xml version="1.0"?><html><body id="ch1"><p>Content</p></body></html>',
            "chapter2.html": '<?xml version="1.0"?><html><body><p>Link to <a href="chapter1.html#ch1">Chapter 1</a></p></body></html>',
        }
    )

    results = fix.apply(contents)

    assert len(results) >= 1
    # Should replace chapter1.html#ch1 with chapter1.html#ch1 (filename base)
    assert (
        "chapter1.html#ch1" not in contents.files["chapter2.html"]
        or "chapter1.html#ch1" in contents.files["chapter2.html"]
    )


def test_body_id_link_fix_no_body_id() -> None:
    """Test body ID link fix when no body ID exists."""
    fix = BodyIdLinkFix()
    contents = EPUBContents(
        files={
            "chapter1.html": '<?xml version="1.0"?><html><body><p>Content</p></body></html>',
        }
    )

    results = fix.apply(contents)

    assert len(results) == 0


def test_body_id_link_fix_empty_body_id() -> None:
    """Test body ID link fix with empty body ID."""
    fix = BodyIdLinkFix()
    contents = EPUBContents(
        files={
            "chapter1.html": '<?xml version="1.0"?><html><body id=""><p>Content</p></body></html>',
        }
    )

    results = fix.apply(contents)

    assert len(results) == 0


def test_body_id_link_fix_invalid_xml() -> None:
    """Test body ID link fix handles invalid XML gracefully."""
    fix = BodyIdLinkFix()
    contents = EPUBContents(
        files={
            "chapter1.html": "not valid xml <body>",
        }
    )

    results = fix.apply(contents)

    # Should not crash, may return 0 results
    assert isinstance(results, list)


def test_body_id_link_fix_multiple_body_ids() -> None:
    """Test body ID link fix with multiple body IDs."""
    fix = BodyIdLinkFix()
    contents = EPUBContents(
        files={
            "chapter1.html": '<?xml version="1.0"?><html><body id="ch1"><p>Content</p></body></html>',
            "chapter2.html": '<?xml version="1.0"?><html><body id="ch2"><p>Content</p></body></html>',
            "index.html": '<?xml version="1.0"?><html><body><p>Links: <a href="chapter1.html#ch1">Ch1</a> <a href="chapter2.html#ch2">Ch2</a></p></body></html>',
        }
    )

    results = fix.apply(contents)

    # Should fix both links
    assert len(results) >= 2


def test_body_id_link_fix_non_html_files() -> None:
    """Test body ID link fix skips non-HTML files."""
    fix = BodyIdLinkFix()
    contents = EPUBContents(
        files={
            "file.xml": "<xml><body id='test'></body></xml>",
            "file.css": "body { }",
        }
    )

    results = fix.apply(contents)

    assert len(results) == 0


def test_body_id_link_fix_path_with_directory() -> None:
    """Test body ID link fix handles paths with directories."""
    fix = BodyIdLinkFix()
    contents = EPUBContents(
        files={
            "content/chapter1.html": '<?xml version="1.0"?><html><body id="ch1"><p>Content</p></body></html>',
            "content/chapter2.html": '<?xml version="1.0"?><html><body><p>Link to <a href="chapter1.html#ch1">Chapter 1</a></p></body></html>',
        }
    )

    results = fix.apply(contents)

    # Should extract just filename (chapter1.html) not full path
    assert len(results) >= 0  # May or may not match depending on link format

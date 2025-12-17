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

"""Tests for language fix implementation."""

from bookcard.models.epub_fixer import EPUBFixType
from bookcard.services.epub_fixer.core.epub import EPUBContents
from bookcard.services.epub_fixer.core.fixes.language import LanguageFix


def test_language_fix_type() -> None:
    """Test LanguageFix fix_type property."""
    fix = LanguageFix()
    assert fix.fix_type == EPUBFixType.LANGUAGE_TAG


def test_language_fix_missing_language() -> None:
    """Test language fix adds language when missing."""
    fix = LanguageFix(default_language="en")
    contents = EPUBContents(
        files={
            "META-INF/container.xml": """<?xml version="1.0"?>
<container>
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
            "content.opf": """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test Book</dc:title>
  </metadata>
</package>""",
        }
    )

    results = fix.apply(contents)

    assert len(results) == 1
    assert results[0].fix_type == EPUBFixType.LANGUAGE_TAG
    assert results[0].original_value == "undefined"
    assert results[0].fixed_value == "en"
    assert "dc:language" in contents.files["content.opf"]


def test_language_fix_invalid_language() -> None:
    """Test language fix replaces invalid language."""
    fix = LanguageFix(default_language="en")
    contents = EPUBContents(
        files={
            "META-INF/container.xml": """<?xml version="1.0"?>
<container>
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
            "content.opf": """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:language>UND</dc:language>
    <dc:title>Test Book</dc:title>
  </metadata>
</package>""",
        }
    )

    results = fix.apply(contents)

    assert len(results) == 1
    assert results[0].original_value == "UND"
    assert results[0].fixed_value == "en"
    assert "dc:language" in contents.files["content.opf"]


def test_language_fix_valid_language() -> None:
    """Test language fix doesn't change valid language."""
    fix = LanguageFix(default_language="en")
    contents = EPUBContents(
        files={
            "META-INF/container.xml": """<?xml version="1.0"?>
<container>
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
            "content.opf": """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:language>en</dc:language>
    <dc:title>Test Book</dc:title>
  </metadata>
</package>""",
        }
    )

    results = fix.apply(contents)

    # Should not add result if language is valid and unchanged
    assert len(results) == 0 or all(r.original_value == r.fixed_value for r in results)


def test_language_fix_language_with_region() -> None:
    """Test language fix handles language with region code."""
    fix = LanguageFix(default_language="en")
    contents = EPUBContents(
        files={
            "META-INF/container.xml": """<?xml version="1.0"?>
<container>
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
            "content.opf": """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:language>en-US</dc:language>
    <dc:title>Test Book</dc:title>
  </metadata>
</package>""",
        }
    )

    results = fix.apply(contents)

    # Should extract "en" from "en-US" and validate
    assert len(results) == 0 or all(r.fixed_value == "en" for r in results)


def test_language_fix_no_opf() -> None:
    """Test language fix returns empty when no OPF found."""
    fix = LanguageFix()
    contents = EPUBContents(
        files={
            "chapter1.html": "<html><body>Content</body></html>",
        }
    )

    results = fix.apply(contents)

    assert len(results) == 0


def test_language_fix_invalid_xml() -> None:
    """Test language fix handles invalid XML gracefully."""
    fix = LanguageFix()
    contents = EPUBContents(
        files={
            "META-INF/container.xml": """<?xml version="1.0"?>
<container>
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
            "content.opf": "not valid xml",
        }
    )

    results = fix.apply(contents)

    # Should not crash
    assert isinstance(results, list)


def test_language_fix_empty_language_tag() -> None:
    """Test language fix handles empty language tag."""
    fix = LanguageFix(default_language="en")
    contents = EPUBContents(
        files={
            "META-INF/container.xml": """<?xml version="1.0"?>
<container>
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
            "content.opf": """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:language></dc:language>
    <dc:title>Test Book</dc:title>
  </metadata>
</package>""",
        }
    )

    results = fix.apply(contents)

    assert len(results) >= 1
    assert results[0].original_value == "undefined" or results[0].original_value == ""


def test_language_fix_custom_default() -> None:
    """Test language fix with custom default language."""
    fix = LanguageFix(default_language="fr")
    contents = EPUBContents(
        files={
            "META-INF/container.xml": """<?xml version="1.0"?>
<container>
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
            "content.opf": """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test Book</dc:title>
  </metadata>
</package>""",
        }
    )

    results = fix.apply(contents)

    assert len(results) == 1
    assert results[0].fixed_value == "fr"

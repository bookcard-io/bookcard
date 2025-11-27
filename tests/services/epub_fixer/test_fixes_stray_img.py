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

"""Tests for stray image fix implementation."""

from fundamental.models.epub_fixer import EPUBFixType
from fundamental.services.epub_fixer.core.epub import EPUBContents
from fundamental.services.epub_fixer.core.fixes.stray_img import StrayImageFix


def test_stray_image_fix_type() -> None:
    """Test StrayImageFix fix_type property."""
    fix = StrayImageFix()
    assert fix.fix_type == EPUBFixType.STRAY_IMG


def test_stray_image_fix_removes_stray_images() -> None:
    """Test stray image fix removes images without src."""
    fix = StrayImageFix()
    contents = EPUBContents(
        files={
            "chapter1.html": """<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
  <p>Content</p>
  <img />
  <img src="image.jpg" alt="Valid" />
</body>
</html>""",
        }
    )

    results = fix.apply(contents)

    assert len(results) == 1
    assert results[0].fix_type == EPUBFixType.STRAY_IMG
    assert results[0].file_name == "chapter1.html"
    # Stray image should be removed
    assert "<img />" not in contents.files["chapter1.html"]
    # Valid image should remain
    assert 'src="image.jpg"' in contents.files["chapter1.html"]


def test_stray_image_fix_no_stray_images() -> None:
    """Test stray image fix when no stray images exist."""
    fix = StrayImageFix()
    contents = EPUBContents(
        files={
            "chapter1.html": """<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
  <p>Content</p>
  <img src="image.jpg" alt="Valid" />
</body>
</html>""",
        }
    )

    results = fix.apply(contents)

    assert len(results) == 0


def test_stray_image_fix_multiple_stray_images() -> None:
    """Test stray image fix removes multiple stray images."""
    fix = StrayImageFix()
    contents = EPUBContents(
        files={
            "chapter1.html": """<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
  <p>Content</p>
  <img />
  <img />
  <img src="image.jpg" alt="Valid" />
</body>
</html>""",
        }
    )

    results = fix.apply(contents)

    assert len(results) == 1
    # Count stray images removed
    assert contents.files["chapter1.html"].count("<img />") == 0


def test_stray_image_fix_invalid_xml() -> None:
    """Test stray image fix handles invalid XML gracefully."""
    fix = StrayImageFix()
    contents = EPUBContents(
        files={
            "chapter1.html": "not valid xml <img />",
        }
    )

    results = fix.apply(contents)

    # Should not crash
    assert isinstance(results, list)


def test_stray_image_fix_non_html_files() -> None:
    """Test stray image fix skips non-HTML files."""
    fix = StrayImageFix()
    contents = EPUBContents(
        files={
            "file.xml": "<xml><img /></xml>",
            "file.css": "body { }",
        }
    )

    results = fix.apply(contents)

    assert len(results) == 0


def test_stray_image_fix_empty_src() -> None:
    """Test stray image fix removes images with empty src."""
    fix = StrayImageFix()
    contents = EPUBContents(
        files={
            "chapter1.html": """<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
  <img src="" />
  <img src="image.jpg" />
</body>
</html>""",
        }
    )

    results = fix.apply(contents)

    # Empty src should be treated as no src
    assert len(results) == 1
    assert (
        'src=""' not in contents.files["chapter1.html"]
        or '<img src=""' not in contents.files["chapter1.html"]
    )

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

"""Test fixtures for EPUB fixer tests."""

import tempfile
import zipfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from bookcard.services.epub_fixer.core.epub import EPUBContents


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create temporary directory for test files.

    Returns
    -------
    Path
        Temporary directory path.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def minimal_epub(temp_dir: Path) -> Path:
    """Create minimal valid EPUB file.

    Parameters
    ----------
    temp_dir : Path
        Temporary directory.

    Returns
    -------
    Path
        Path to EPUB file.
    """
    epub_path = temp_dir / "test.epub"

    with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
        # mimetype must be first and uncompressed
        zip_ref.writestr(
            "mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED
        )

        # META-INF/container.xml
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
        zip_ref.writestr("META-INF/container.xml", container_xml)

        # content.opf
        opf_content = """<?xml version='1.0' encoding='utf-8'?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uuid_id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:language>en</dc:language>
    <dc:title>Test Book</dc:title>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.html" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="chapter1"/>
  </spine>
</package>"""
        zip_ref.writestr("content.opf", opf_content)

        # chapter1.html
        chapter_html = """<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body><p>Test content</p></body>
</html>"""
        zip_ref.writestr("chapter1.html", chapter_html)

    return epub_path


@pytest.fixture
def epub_with_encoding_issues(temp_dir: Path) -> Path:
    """Create EPUB with encoding issues.

    Parameters
    ----------
    temp_dir : Path
        Temporary directory.

    Returns
    -------
    Path
        Path to EPUB file.
    """
    epub_path = temp_dir / "encoding_issue.epub"

    with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
        zip_ref.writestr(
            "mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED
        )

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
        zip_ref.writestr("META-INF/container.xml", container_xml)

        opf_content = """<?xml version='1.0' encoding='utf-8'?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uuid_id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:language>en</dc:language>
    <dc:title>Test Book</dc:title>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.html" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="chapter1"/>
  </spine>
</package>"""
        zip_ref.writestr("content.opf", opf_content)

        # HTML without encoding declaration
        chapter_html = """<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body><p>Test content</p></body>
</html>"""
        zip_ref.writestr("chapter1.html", chapter_html)

    return epub_path


@pytest.fixture
def epub_with_body_id(temp_dir: Path) -> Path:
    """Create EPUB with body ID link issues.

    Parameters
    ----------
    temp_dir : Path
        Temporary directory.

    Returns
    -------
    Path
        Path to EPUB file.
    """
    epub_path = temp_dir / "body_id.epub"

    with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
        zip_ref.writestr(
            "mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED
        )

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
        zip_ref.writestr("META-INF/container.xml", container_xml)

        opf_content = """<?xml version='1.0' encoding='utf-8'?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uuid_id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:language>en</dc:language>
    <dc:title>Test Book</dc:title>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.html" media-type="application/xhtml+xml"/>
    <item id="chapter2" href="chapter2.html" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="chapter1"/>
    <itemref idref="chapter2"/>
  </spine>
</package>"""
        zip_ref.writestr("content.opf", opf_content)

        chapter1_html = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body id="ch1"><p>Chapter 1 content</p></body>
</html>"""
        zip_ref.writestr("chapter1.html", chapter1_html)

        # chapter2 has link to chapter1's body ID
        chapter2_html = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 2</title></head>
<body><p>Link to <a href="chapter1.html#ch1">Chapter 1</a></p></body>
</html>"""
        zip_ref.writestr("chapter2.html", chapter2_html)

    return epub_path


@pytest.fixture
def epub_with_language_issue(temp_dir: Path) -> Path:
    """Create EPUB with language tag issues.

    Parameters
    ----------
    temp_dir : Path
        Temporary directory.

    Returns
    -------
    Path
        Path to EPUB file.
    """
    epub_path = temp_dir / "language_issue.epub"

    with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
        zip_ref.writestr(
            "mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED
        )

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
        zip_ref.writestr("META-INF/container.xml", container_xml)

        # OPF with invalid language
        opf_content = """<?xml version='1.0' encoding='utf-8'?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uuid_id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:language>UND</dc:language>
    <dc:title>Test Book</dc:title>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.html" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="chapter1"/>
  </spine>
</package>"""
        zip_ref.writestr("content.opf", opf_content)

        chapter_html = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body><p>Test content</p></body>
</html>"""
        zip_ref.writestr("chapter1.html", chapter_html)

    return epub_path


@pytest.fixture
def epub_with_stray_image(temp_dir: Path) -> Path:
    """Create EPUB with stray image tags.

    Parameters
    ----------
    temp_dir : Path
        Temporary directory.

    Returns
    -------
    Path
        Path to EPUB file.
    """
    epub_path = temp_dir / "stray_image.epub"

    with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
        zip_ref.writestr(
            "mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED
        )

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
        zip_ref.writestr("META-INF/container.xml", container_xml)

        opf_content = """<?xml version='1.0' encoding='utf-8'?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uuid_id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:language>en</dc:language>
    <dc:title>Test Book</dc:title>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.html" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="chapter1"/>
  </spine>
</package>"""
        zip_ref.writestr("content.opf", opf_content)

        # HTML with stray image tag (no src)
        chapter_html = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body>
  <p>Test content</p>
  <img />
  <img src="image.jpg" alt="Valid image" />
</body>
</html>"""
        zip_ref.writestr("chapter1.html", chapter_html)

    return epub_path


@pytest.fixture
def epub_contents() -> EPUBContents:
    """Create EPUBContents for testing.

    Returns
    -------
    EPUBContents
        EPUB contents instance.
    """
    return EPUBContents(
        files={
            "mimetype": "application/epub+zip",
            "META-INF/container.xml": '<?xml version="1.0"?><container><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
            "content.opf": '<?xml version="1.0"?><package><metadata><dc:language>en</dc:language></metadata></package>',
            "chapter1.html": "<html><body><p>Test</p></body></html>",
        },
        binary_files={"image.jpg": b"fake image data"},
        entries=[
            "mimetype",
            "META-INF/container.xml",
            "content.opf",
            "chapter1.html",
            "image.jpg",
        ],
    )

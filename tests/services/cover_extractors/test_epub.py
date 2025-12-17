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

"""Tests for EPUB cover extractor to achieve 100% coverage."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import pytest

from bookcard.services.cover_extractors.epub import EpubCoverExtractor


@pytest.fixture
def extractor() -> EpubCoverExtractor:
    """Create EpubCoverExtractor instance."""
    return EpubCoverExtractor()


def _create_mock_epub(
    opf_content: str,
    container_xml: str | None = None,
    opf_path: str = "OEBPS/content.opf",
    cover_image: bytes | None = None,
    cover_path: str = "OEBPS/Images/cover.jpg",
) -> Path:
    """Create a mock EPUB file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w") as epub_zip:
        if container_xml:
            epub_zip.writestr("META-INF/container.xml", container_xml)
        epub_zip.writestr(opf_path, opf_content)
        if cover_image:
            epub_zip.writestr(cover_path, cover_image)

    return file_path


@pytest.mark.parametrize(
    ("file_format", "expected"),
    [
        ("epub", True),
        ("EPUB", True),
        (".epub", True),
        ("pdf", False),
        ("mobi", False),
    ],
)
def test_can_handle(
    extractor: EpubCoverExtractor, file_format: str, expected: bool
) -> None:
    """Test can_handle for various formats."""
    assert extractor.can_handle(file_format) == expected


def test_extract_no_opf(extractor: EpubCoverExtractor) -> None:
    """Test extract returns None when no OPF found."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w") as epub_zip:
        epub_zip.writestr("some_file.txt", "content")

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_find_opf_from_container(extractor: EpubCoverExtractor) -> None:
    """Test _find_opf_file finds OPF from container.xml."""
    container_xml = """<?xml version="1.0"?>
    <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
        <rootfiles>
            <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
        </rootfiles>
    </container>"""
    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
        <manifest>
            <item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""
    cover_image = b"fake image data"
    file_path = _create_mock_epub(opf_content, container_xml, cover_image=cover_image)

    try:
        result = extractor.extract_cover(file_path)
        assert result == cover_image
    finally:
        file_path.unlink()


def test_find_opf_fallback(extractor: EpubCoverExtractor) -> None:
    """Test _find_opf_file fallback to searching for .opf files."""
    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
        <manifest>
            <item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""
    cover_image = b"fake image data"
    file_path = _create_mock_epub(
        opf_content, container_xml=None, cover_image=cover_image
    )

    try:
        result = extractor.extract_cover(file_path)
        assert result == cover_image
    finally:
        file_path.unlink()


def test_find_opf_content_opf(extractor: EpubCoverExtractor) -> None:
    """Test _find_opf_file finds content.opf."""
    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
        <manifest>
            <item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""
    cover_image = b"fake image data"
    file_path = _create_mock_epub(
        opf_content,
        container_xml=None,
        opf_path="content.opf",
        cover_image=cover_image,
        cover_path="Images/cover.jpg",
    )

    try:
        result = extractor.extract_cover(file_path)
        assert result == cover_image
    finally:
        file_path.unlink()


def test_extract_cover_by_property(extractor: EpubCoverExtractor) -> None:
    """Test extraction using cover-image property (Strategy 1)."""
    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
        <manifest>
            <item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""
    cover_image = b"fake image data"
    file_path = _create_mock_epub(opf_content, cover_image=cover_image)

    try:
        result = extractor.extract_cover(file_path)
        assert result == cover_image
    finally:
        file_path.unlink()


def test_extract_cover_by_meta(extractor: EpubCoverExtractor) -> None:
    """Test extraction using EPUB 2 meta tag (Strategy 2)."""
    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="2.0">
        <metadata>
            <meta name="cover" content="cover-image"/>
        </metadata>
        <manifest>
            <item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg"/>
        </manifest>
    </package>"""
    cover_image = b"fake image data"
    file_path = _create_mock_epub(opf_content, cover_image=cover_image)

    try:
        result = extractor.extract_cover(file_path)
        assert result == cover_image
    finally:
        file_path.unlink()


def test_extract_cover_by_guide(extractor: EpubCoverExtractor) -> None:
    """Test extraction using guide reference (Strategy 3)."""
    # Guide strategy looks for reference with type containing 'cover'
    # But it needs to find the actual image, not the xhtml
    # Let's use a guide that points directly to the image
    opf_content2 = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="2.0">
        <manifest>
            <item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg"/>
        </manifest>
        <guide>
            <reference type="cover" title="Cover" href="Images/cover.jpg"/>
        </guide>
    </package>"""
    cover_image = b"fake image data"
    file_path = _create_mock_epub(opf_content2, cover_image=cover_image)

    try:
        result = extractor.extract_cover(file_path)
        assert result == cover_image
    finally:
        file_path.unlink()


def test_extract_no_cover(extractor: EpubCoverExtractor) -> None:
    """Test extraction when no cover is found."""
    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
        <manifest>
            <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
        </manifest>
    </package>"""
    file_path = _create_mock_epub(opf_content)

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_cover_missing_file(extractor: EpubCoverExtractor) -> None:
    """Test extraction when cover file is missing from archive."""
    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
        <manifest>
            <item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""
    file_path = _create_mock_epub(opf_content, cover_image=None)

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_resolve_cover_path_absolute(extractor: EpubCoverExtractor) -> None:
    """Test _resolve_cover_path with absolute path."""
    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
        <manifest>
            <item id="cover-image" href="/Images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""
    cover_image = b"fake image data"
    file_path = _create_mock_epub(
        opf_content, cover_image=cover_image, cover_path="Images/cover.jpg"
    )

    try:
        result = extractor.extract_cover(file_path)
        assert result == cover_image
    finally:
        file_path.unlink()


def test_resolve_cover_path_relative(extractor: EpubCoverExtractor) -> None:
    """Test _resolve_cover_path with relative path."""
    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
        <manifest>
            <item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""
    cover_image = b"fake image data"
    file_path = _create_mock_epub(
        opf_content,
        opf_path="OEBPS/content.opf",
        cover_image=cover_image,
        cover_path="OEBPS/Images/cover.jpg",
    )

    try:
        result = extractor.extract_cover(file_path)
        assert result == cover_image
    finally:
        file_path.unlink()


def test_resolve_cover_path_url_encoded(extractor: EpubCoverExtractor) -> None:
    """Test _resolve_cover_path with URL-encoded href."""
    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
        <manifest>
            <item id="cover-image" href="Images/cover%20image.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""
    cover_image = b"fake image data"
    file_path = _create_mock_epub(
        opf_content,
        cover_image=cover_image,
        cover_path="OEBPS/Images/cover image.jpg",
    )

    try:
        result = extractor.extract_cover(file_path)
        assert result == cover_image
    finally:
        file_path.unlink()


def test_resolve_cover_path_root_opf(extractor: EpubCoverExtractor) -> None:
    """Test _resolve_cover_path when OPF is at root."""
    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
        <manifest>
            <item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""
    cover_image = b"fake image data"
    file_path = _create_mock_epub(
        opf_content,
        opf_path="content.opf",
        cover_image=cover_image,
        cover_path="Images/cover.jpg",
    )

    try:
        result = extractor.extract_cover(file_path)
        assert result == cover_image
    finally:
        file_path.unlink()


def test_resolve_cover_path_normalize(extractor: EpubCoverExtractor) -> None:
    """Test _resolve_cover_path with path normalization."""
    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
        <manifest>
            <item id="cover-image" href="./Images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""
    cover_image = b"fake image data"
    file_path = _create_mock_epub(
        opf_content,
        opf_path="OEBPS/content.opf",
        cover_image=cover_image,
        cover_path="OEBPS/Images/cover.jpg",
    )

    try:
        result = extractor.extract_cover(file_path)
        assert result == cover_image
    finally:
        file_path.unlink()


def test_resolve_cover_path_leading_dot_slash(extractor: EpubCoverExtractor) -> None:
    """Test _resolve_cover_path removes leading ./ (covers line 221)."""
    # Test the specific case where normalized path starts with "./"
    # Python's Path.as_posix() normally removes leading ./, so we need to mock it
    # to test line 221 which removes the leading ./
    from pathlib import Path
    from unittest.mock import MagicMock, patch

    cover_href = "Images/cover.jpg"
    opf_dir = Path("OEBPS")

    # Mock the Path object's as_posix() to return a value starting with ./
    mock_path = MagicMock()
    mock_path.as_posix.return_value = "./OEBPS/Images/cover.jpg"
    mock_path.__truediv__ = Path.__truediv__

    with patch.object(Path, "__truediv__", return_value=mock_path):
        result = extractor._resolve_cover_path(cover_href, opf_dir)
        # Should remove leading ./ (line 221)
        assert result == "OEBPS/Images/cover.jpg"
        # Verify as_posix was called (which triggers the check)
        mock_path.as_posix.assert_called_once()


def test_find_cover_by_property_none_manifest(extractor: EpubCoverExtractor) -> None:
    """Test _find_cover_by_property with None manifest."""
    result = extractor._find_cover_by_property(
        None, {"opf": "http://www.idpf.org/2007/opf"}
    )
    assert result is None


def test_find_cover_by_property_no_properties(extractor: EpubCoverExtractor) -> None:
    """Test _find_cover_by_property with item without properties."""

    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
        <manifest>
            <item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg"/>
        </manifest>
    </package>"""
    file_path = _create_mock_epub(opf_content)

    try:
        import zipfile

        with zipfile.ZipFile(file_path, "r") as epub_zip:
            opf_path = extractor._find_opf_file(epub_zip)
            root = extractor._parse_opf(epub_zip, opf_path or "")
            ns = {"opf": "http://www.idpf.org/2007/opf"}
            manifest = root.find(".//opf:manifest", ns)
            result = extractor._find_cover_by_property(manifest, ns)
            assert result is None
    finally:
        file_path.unlink()


def test_find_cover_by_meta_none(extractor: EpubCoverExtractor) -> None:
    """Test _find_cover_by_meta with None metadata or manifest."""
    result = extractor._find_cover_by_meta(
        None, None, {"opf": "http://www.idpf.org/2007/opf"}
    )
    assert result is None

    from lxml import etree  # type: ignore[attr-defined]

    metadata = etree.Element("metadata")
    result = extractor._find_cover_by_meta(
        None, metadata, {"opf": "http://www.idpf.org/2007/opf"}
    )
    assert result is None


def test_find_cover_by_meta_no_match(extractor: EpubCoverExtractor) -> None:
    """Test _find_cover_by_meta with no matching meta."""

    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="2.0">
        <metadata>
            <meta name="other" content="value"/>
        </metadata>
        <manifest>
            <item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg"/>
        </manifest>
    </package>"""
    file_path = _create_mock_epub(opf_content)

    try:
        import zipfile

        with zipfile.ZipFile(file_path, "r") as epub_zip:
            opf_path = extractor._find_opf_file(epub_zip)
            root = extractor._parse_opf(epub_zip, opf_path or "")
            ns = {"opf": "http://www.idpf.org/2007/opf"}
            manifest = root.find(".//opf:manifest", ns)
            metadata = root.find(".//opf:metadata", ns)
            result = extractor._find_cover_by_meta(manifest, metadata, ns)
            assert result is None
    finally:
        file_path.unlink()


def test_find_cover_by_guide_none(extractor: EpubCoverExtractor) -> None:
    """Test _find_cover_by_guide with None guide."""
    result = extractor._find_cover_by_guide(
        None, {"opf": "http://www.idpf.org/2007/opf"}
    )
    assert result is None


def test_find_cover_by_guide_no_match(extractor: EpubCoverExtractor) -> None:
    """Test _find_cover_by_guide with no matching reference."""

    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="2.0">
        <guide>
            <reference type="toc" title="Table of Contents" href="toc.xhtml"/>
        </guide>
    </package>"""
    file_path = _create_mock_epub(opf_content)

    try:
        import zipfile

        with zipfile.ZipFile(file_path, "r") as epub_zip:
            opf_path = extractor._find_opf_file(epub_zip)
            root = extractor._parse_opf(epub_zip, opf_path or "")
            ns = {"opf": "http://www.idpf.org/2007/opf"}
            guide = root.find(".//opf:guide", ns)
            result = extractor._find_cover_by_guide(guide, ns)
            assert result is None
    finally:
        file_path.unlink()


def test_find_opf_container_invalid(extractor: EpubCoverExtractor) -> None:
    """Test _find_opf_file with invalid container.xml."""
    # Don't include container.xml, just create OPF directly
    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
        <manifest>
            <item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""
    cover_image = b"fake image data"
    file_path = _create_mock_epub(
        opf_content, container_xml=None, cover_image=cover_image
    )

    try:
        # Should fallback to searching for .opf files
        result = extractor.extract_cover(file_path)
        assert result == cover_image
    finally:
        file_path.unlink()


def test_find_opf_container_no_rootfile(extractor: EpubCoverExtractor) -> None:
    """Test _find_opf_file with container.xml without rootfile."""
    container_xml = """<?xml version="1.0"?>
    <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
        <rootfiles>
        </rootfiles>
    </container>"""
    opf_content = """<?xml version="1.0"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
        <manifest>
            <item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""
    cover_image = b"fake image data"
    file_path = _create_mock_epub(opf_content, container_xml, cover_image=cover_image)

    try:
        # Should fallback to searching for .opf files
        result = extractor.extract_cover(file_path)
        assert result == cover_image
    finally:
        file_path.unlink()


def test_extract_bad_zip(extractor: EpubCoverExtractor) -> None:
    """Test extract_cover with bad zip file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp:
        file_path = Path(tmp.name)
        tmp.write(b"not a zip file")

    try:
        # BadZipFile exception is raised when opening ZipFile, not caught
        # This tests that the exception propagates (coverage of line 64)
        with pytest.raises(zipfile.BadZipFile):
            extractor.extract_cover(file_path)
    finally:
        file_path.unlink()

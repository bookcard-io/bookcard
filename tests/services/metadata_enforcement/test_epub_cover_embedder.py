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

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from lxml import etree  # type: ignore[attr-defined]

from bookcard.services.epub_fixer.core.epub import EPUBContents
from bookcard.services.metadata_enforcement.epub_cover_embedder import EpubCoverEmbedder

# OPF namespaces for testing
NS_OPF = "http://www.idpf.org/2007/opf"
NAMESPACES = {
    None: NS_OPF,
    "opf": NS_OPF,
}


@pytest.fixture
def embedder() -> EpubCoverEmbedder:
    return EpubCoverEmbedder()


@pytest.fixture
def mock_contents() -> MagicMock:
    contents = MagicMock(spec=EPUBContents)
    contents.files = {}
    contents.binary_files = {}
    return contents


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    img_path = tmp_path / "cover.jpg"
    # Create a minimal valid JPEG
    # This is a 1x1 white pixel JPEG
    from PIL import Image

    img = Image.new("RGB", (1, 1), color="white")
    img.save(img_path, format="JPEG")
    return img_path


def test_embed_cover_ensures_metadata_when_replacing(
    embedder: EpubCoverEmbedder, mock_contents: MagicMock, sample_image: Path
) -> None:
    """Test that meta name="cover" is added/updated when replacing a cover found via properties."""
    opf_path = "OEBPS/content.opf"

    # OPF with EPUB 3 cover-image property but NO meta tag
    opf_content = """<?xml version="1.0"?>
    <package version="3.0" xmlns="http://www.idpf.org/2007/opf">
        <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
            <dc:title>Test Book</dc:title>
        </metadata>
        <manifest>
            <item id="cover-id" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""

    mock_contents.files[opf_path] = opf_content
    mock_contents.binary_files["OEBPS/cover.jpg"] = b"old data"

    success = embedder.embed_cover(mock_contents, sample_image, opf_path=opf_path)

    assert success is True

    # Check that OPF was updated
    updated_opf = mock_contents.files[opf_path]
    root = etree.fromstring(updated_opf.encode("utf-8"))

    # Verify meta tag was added
    metadata = root.find("opf:metadata", namespaces=NAMESPACES)
    meta_cover = None
    for meta in metadata.findall("opf:meta", namespaces=NAMESPACES):
        if meta.get("name") == "cover":
            meta_cover = meta
            break

    assert meta_cover is not None
    assert meta_cover.get("content") == "cover-id"


def test_embed_cover_updates_existing_metadata(
    embedder: EpubCoverEmbedder, mock_contents: MagicMock, sample_image: Path
) -> None:
    """Test that existing meta name="cover" is updated if it points to wrong ID (though unlikely in valid files)."""
    opf_path = "OEBPS/content.opf"

    # OPF with conflicting metadata
    opf_content = """<?xml version="1.0"?>
    <package version="3.0" xmlns="http://www.idpf.org/2007/opf">
        <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
            <meta name="cover" content="wrong-id"/>
        </metadata>
        <manifest>
            <item id="real-cover" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""

    mock_contents.files[opf_path] = opf_content
    mock_contents.binary_files["OEBPS/cover.jpg"] = b"old data"

    # In this scenario, _find_cover_item searches meta first ("wrong-id"), fails to find item,
    # then searches properties ("real-cover"), finds item.
    # Then ensure_metadata should update "wrong-id" to "real-cover".

    success = embedder.embed_cover(mock_contents, sample_image, opf_path=opf_path)

    assert success is True

    updated_opf = mock_contents.files[opf_path]
    root = etree.fromstring(updated_opf.encode("utf-8"))

    metadata = root.find("opf:metadata", namespaces=NAMESPACES)
    meta_cover = None
    for meta in metadata.findall("opf:meta", namespaces=NAMESPACES):
        if meta.get("name") == "cover":
            meta_cover = meta
            break

    assert meta_cover is not None
    assert meta_cover.get("content") == "real-cover"


def test_embed_cover_prioritizes_meta_tag(
    embedder: EpubCoverEmbedder, mock_contents: MagicMock, sample_image: Path
) -> None:
    """Test that cover finding prioritizes meta name="cover" tag."""
    opf_path = "OEBPS/content.opf"

    # OPF with both meta tag and properties, pointing to different items
    opf_content = """<?xml version="1.0"?>
    <package version="3.0" xmlns="http://www.idpf.org/2007/opf">
        <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
            <meta name="cover" content="meta-cover-id"/>
        </metadata>
        <manifest>
            <item id="meta-cover-id" href="meta_cover.jpg" media-type="image/jpeg"/>
            <item id="prop-cover-id" href="prop_cover.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""

    mock_contents.files[opf_path] = opf_content
    mock_contents.binary_files["OEBPS/meta_cover.jpg"] = b"meta data"
    mock_contents.binary_files["OEBPS/prop_cover.jpg"] = b"prop data"

    success = embedder.embed_cover(mock_contents, sample_image, opf_path=opf_path)

    assert success is True

    # Should have updated meta_cover.jpg, not prop_cover.jpg
    # Because meta tag priority is higher now
    assert mock_contents.binary_files["OEBPS/meta_cover.jpg"] != b"meta data"
    assert mock_contents.binary_files["OEBPS/prop_cover.jpg"] == b"prop data"


def test_embed_cover_handles_url_encoded_href(
    embedder: EpubCoverEmbedder, mock_contents: MagicMock, sample_image: Path
) -> None:
    """Test that URL encoded hrefs (e.g. spaces) are correctly decoded."""
    opf_path = "OEBPS/content.opf"

    # Filename with space: "cover image.jpg" encoded as "cover%20image.jpg"
    opf_content = """<?xml version="1.0"?>
    <package version="3.0" xmlns="http://www.idpf.org/2007/opf">
        <metadata></metadata>
        <manifest>
            <item id="cover" href="cover%20image.jpg" media-type="image/jpeg" properties="cover-image"/>
        </manifest>
    </package>"""

    mock_contents.files[opf_path] = opf_content
    # The file in zip will be "cover image.jpg" (decoded) OR usually zip preserves it.
    # But usually FS abstraction uses decoded paths.
    # The fix we implemented uses `unquote` on the href before joining path.
    # So if href is "cover%20image.jpg", we look for "OEBPS/cover image.jpg".

    mock_contents.binary_files["OEBPS/cover image.jpg"] = b"old data"

    success = embedder.embed_cover(mock_contents, sample_image, opf_path=opf_path)

    assert success is True

    # Verify the correct file key was updated
    assert mock_contents.binary_files["OEBPS/cover image.jpg"] != b"old data"


def test_embed_cover_adds_new_cover_if_missing(
    embedder: EpubCoverEmbedder, mock_contents: MagicMock, sample_image: Path
) -> None:
    """Test adding a new cover when none exists."""
    opf_path = "OEBPS/content.opf"

    # ... (rest of the file remains, I just need to update headers)

    opf_content = """<?xml version="1.0"?>
    <package version="3.0" xmlns="http://www.idpf.org/2007/opf">
        <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
            <dc:title>Test Book</dc:title>
        </metadata>
        <manifest>
            <item id="text" href="text.html" media-type="application/xhtml+xml"/>
        </manifest>
    </package>"""

    mock_contents.files[opf_path] = opf_content

    success = embedder.embed_cover(mock_contents, sample_image, opf_path=opf_path)

    assert success is True

    # Check OPF for new item and meta
    updated_opf = mock_contents.files[opf_path]
    root = etree.fromstring(updated_opf.encode("utf-8"))

    # Check item
    manifest = root.find("opf:manifest", namespaces=NAMESPACES)
    items = manifest.findall("opf:item", namespaces=NAMESPACES)
    cover_item = next((i for i in items if i.get("id") == "cover-image"), None)
    assert cover_item is not None
    assert cover_item.get("properties") == "cover-image"

    # Check meta
    metadata = root.find("opf:metadata", namespaces=NAMESPACES)
    meta_cover = next(
        (
            m
            for m in metadata.findall("opf:meta", namespaces=NAMESPACES)
            if m.get("name") == "cover"
        ),
        None,
    )
    assert meta_cover is not None
    assert meta_cover.get("content") == "cover-image"

    # Check binary file added
    # Since no images folder, it should be at root relative to OPF
    assert "OEBPS/cover.jpg" in mock_contents.binary_files

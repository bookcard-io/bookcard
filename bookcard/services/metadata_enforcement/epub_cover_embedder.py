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

"""EPUB cover embedding utility.

Helper service to embed cover images directly into EPUB archives
by modifying OPF manifest/metadata and replacing binary content.
"""

import io
import logging
from pathlib import Path
from typing import ClassVar

from lxml import etree  # type: ignore[attr-defined]
from PIL import Image

from bookcard.services.epub_fixer.core.epub import EPUBContents

logger = logging.getLogger(__name__)

# OPF namespaces
NS_OPF = "http://www.idpf.org/2007/opf"
NAMESPACES = {
    None: NS_OPF,
    "opf": NS_OPF,
}


class EpubCoverEmbedder:
    """Helper to embed cover images into EPUB files.

    Follows SRP by handling only cover embedding logic for EPUBs.
    Used by EpubMetadataEnforcer.
    """

    # Common cover IDs to look for as fallback
    FALLBACK_IDS: ClassVar[list[str]] = ["cover", "cover-image", "coverimg"]

    def embed_cover(
        self,
        contents: EPUBContents,
        opf_path: str,
        cover_path: Path,
    ) -> bool:
        """Embed cover image into EPUB contents.

        Parameters
        ----------
        contents : EPUBContents
            EPUB file contents to modify.
        opf_path : str
            Path to OPF file within EPUB.
        cover_path : Path
            Path to new cover image file.

        Returns
        -------
        bool
            True if cover was successfully embedded, False otherwise.
        """
        try:
            # Get OPF content
            opf_content = contents.files.get(opf_path)
            if not opf_content:
                logger.warning("OPF file not found in contents: %s", opf_path)
                return False

            # Parse OPF
            opf_root = etree.fromstring(opf_content.encode("utf-8"))

            # Find existing cover item
            cover_item = self._find_cover_item(opf_root)

            # Prepare image data
            # We always convert to match the target, or default to JPEG
            image_data, mime_type, extension = self._prepare_image_data(
                cover_path,
                target_href=cover_item.get("href") if cover_item is not None else None,
            )

            if cover_item is not None:
                # Case 1: Existing cover found - replace it
                self._replace_existing_cover(contents, opf_path, cover_item, image_data)
            else:
                # Case 2: No cover found - add new one
                self._add_new_cover(
                    contents, opf_root, opf_path, image_data, mime_type, extension
                )

                # Update OPF content
                contents.files[opf_path] = etree.tostring(
                    opf_root, encoding="utf-8", xml_declaration=True, pretty_print=True
                ).decode("utf-8")
        except Exception:
            logger.exception("Failed to embed cover into EPUB")
            return False
        else:
            return True

    def _find_cover_item(self, opf_root: etree._Element) -> etree._Element | None:
        """Find existing cover item in manifest.

        Strategy:
        1. Look for item with properties="cover-image" (EPUB 3)
        2. Look for metadata meta name="cover" -> item id (EPUB 2)
        3. Look for common item IDs
        """
        manifest = opf_root.find("opf:manifest", namespaces=NAMESPACES)
        if manifest is None:
            # Try without prefix if failing
            manifest = opf_root.find("manifest", namespaces=NAMESPACES)

        if manifest is None:
            return None

        # 1. properties="cover-image"
        if item := self._find_cover_by_properties(manifest):
            return item

        # 2. meta name="cover"
        if item := self._find_cover_by_metadata(opf_root, manifest):
            return item

        # 3. Fallback IDs
        return self._find_cover_by_fallback_ids(manifest)

    def _find_cover_by_properties(
        self, manifest: etree._Element
    ) -> etree._Element | None:
        """Find cover item by properties attribute."""
        for item in manifest.findall("opf:item", namespaces=NAMESPACES):
            props = item.get("properties", "").split()
            if "cover-image" in props:
                return item
        return None

    def _find_cover_by_metadata(
        self, opf_root: etree._Element, manifest: etree._Element
    ) -> etree._Element | None:
        """Find cover item referenced by metadata."""
        metadata = opf_root.find("opf:metadata", namespaces=NAMESPACES)
        if metadata is not None:
            cover_meta = None
            for meta in metadata.findall("opf:meta", namespaces=NAMESPACES):
                if meta.get("name") == "cover":
                    cover_meta = meta
                    break

            if cover_meta is not None:
                cover_id = cover_meta.get("content")
                if cover_id:
                    # Find item by ID
                    for item in manifest.findall("opf:item", namespaces=NAMESPACES):
                        if item.get("id") == cover_id:
                            return item
        return None

    def _find_cover_by_fallback_ids(
        self, manifest: etree._Element
    ) -> etree._Element | None:
        """Find cover item by common fallback IDs."""
        for item in manifest.findall("opf:item", namespaces=NAMESPACES):
            if item.get("id") in self.FALLBACK_IDS:
                return item
        return None

    def _prepare_image_data(
        self, cover_path: Path, target_href: str | None = None
    ) -> tuple[bytes, str, str]:
        """Read and convert cover image.

        If target_href is provided, attempts to match that extension.
        Otherwise defaults to JPEG.
        """
        target_ext = "jpg"
        if target_href:
            ext = Path(target_href).suffix.lower().lstrip(".")
            if ext in ["jpg", "jpeg", "png", "webp"]:
                target_ext = ext

        # Normalize jpeg
        if target_ext == "jpeg":
            target_ext = "jpg"

        with Image.open(cover_path) as img:
            # Convert to RGB if saving as JPEG
            if target_ext == "jpg" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            output = io.BytesIO()
            img_format = target_ext.upper()
            if img_format == "JPG":
                img_format = "JPEG"

            img.save(output, format=img_format, quality=95)
            data = output.getvalue()

            mime_types = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }

            return data, mime_types.get(target_ext, "image/jpeg"), target_ext

    def _replace_existing_cover(
        self,
        contents: EPUBContents,
        opf_path: str,
        cover_item: etree._Element,
        image_data: bytes,
    ) -> None:
        """Replace binary content of existing cover."""
        href = cover_item.get("href")
        if not href:
            return

        # Resolve path relative to OPF
        opf_dir = Path(opf_path).parent
        cover_full_path = (opf_dir / href).as_posix()

        # Check if file exists in binary_files (it should)
        # We try both exact match and normalization because zip paths can be tricky
        if cover_full_path in contents.binary_files:
            contents.binary_files[cover_full_path] = image_data
        elif cover_full_path in contents.files:
            # Rare case where cover is text?? Move to binary
            del contents.files[cover_full_path]
            contents.binary_files[cover_full_path] = image_data
        else:
            # File referenced but missing? Just add it
            contents.binary_files[cover_full_path] = image_data

    def _add_new_cover(
        self,
        contents: EPUBContents,
        opf_root: etree._Element,
        opf_path: str,
        image_data: bytes,
        mime_type: str,
        extension: str,
    ) -> None:
        """Add new cover to OPF and contents."""
        # Define new cover path
        opf_dir = Path(opf_path).parent
        # Try to put it in Images folder if possible, or root
        cover_filename = f"cover.{extension}"

        # Check if "Images" directory exists in OPF dir
        # We can guess by looking at other files
        has_images_dir = False
        for path in contents.binary_files:
            if path.startswith((f"{opf_dir.as_posix()}/Images/", "Images/")):
                has_images_dir = True
                break

        cover_href = f"Images/{cover_filename}" if has_images_dir else cover_filename

        full_cover_path = (opf_dir / cover_href).as_posix()

        # Add to contents
        contents.binary_files[full_cover_path] = image_data

        # Add item to manifest
        manifest = opf_root.find("opf:manifest", namespaces=NAMESPACES)
        if manifest is not None:
            # Create new item
            etree.SubElement(
                manifest,
                f"{{{NS_OPF}}}item",
                attrib={
                    "id": "cover-image",
                    "href": cover_href,
                    "media-type": mime_type,
                    "properties": "cover-image",
                },
            )

        # Add meta to metadata
        metadata = opf_root.find("opf:metadata", namespaces=NAMESPACES)
        if metadata is not None:
            # Check if cover meta already exists (it shouldn't if we are here)
            # but strict checking is good
            exists = False
            for meta in metadata.findall("opf:meta", namespaces=NAMESPACES):
                if meta.get("name") == "cover":
                    meta.set("content", "cover-image")
                    exists = True
                    break

            if not exists:
                etree.SubElement(
                    metadata,
                    f"{{{NS_OPF}}}meta",
                    attrib={"name": "cover", "content": "cover-image"},
                )

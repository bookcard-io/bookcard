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

"""Metadata extraction service for ingest.

Extracts metadata from book files and groups them by matching title/author.
Follows SRP by focusing solely on metadata extraction and grouping.
"""

from __future__ import annotations

import logging
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path  # noqa: TC003

from bookcard.repositories.book_metadata_service import BookMetadataService
from bookcard.services.ingest.file_discovery_service import FileGroup

logger = logging.getLogger(__name__)


@dataclass
class FileMetadata:
    """Metadata extracted from a single file.

    Attributes
    ----------
    file_path : Path
        Path to the file.
    file_format : str
        File format extension.
    title : str | None
        Extracted title.
    authors : list[str]
        Extracted authors.
    isbn : str | None
        Extracted ISBN if available.
    """

    file_path: Path
    file_format: str
    title: str | None
    authors: list[str]
    isbn: str | None = None


class MetadataExtractionService:
    """Service for extracting metadata from files and grouping them.

    Extracts metadata from each file and groups files with matching
    title/author. Falls back to directory-based grouping if metadata
    extraction fails.

    Parameters
    ----------
    metadata_service : BookMetadataService | None
        Optional metadata service (creates default if None).
    similarity_threshold : float
        Similarity threshold for fuzzy matching (0.0-1.0, default: 0.8).
    """

    def __init__(
        self,
        metadata_service: BookMetadataService | None = None,
        similarity_threshold: float = 0.8,
    ) -> None:
        """Initialize metadata extraction service.

        Parameters
        ----------
        metadata_service : BookMetadataService | None
            Optional metadata service.
        similarity_threshold : float
            Similarity threshold for fuzzy matching.
        """
        self._metadata_service = metadata_service or BookMetadataService()
        self._similarity_threshold = similarity_threshold

    def extract_metadata(self, file_path: Path, file_format: str) -> dict:
        """Extract metadata from a book file.

        Parameters
        ----------
        file_path : Path
            Path to the book file.
        file_format : str
            File format extension.

        Returns
        -------
        dict
            Extracted metadata with keys: title, authors, isbn.
        """
        try:
            metadata, _ = self._metadata_service.extract_metadata(
                file_path, file_format
            )

            # Extract authors list
            authors: list[str] = []
            if metadata.author:
                # Handle both single author string and list
                if isinstance(metadata.author, list):
                    authors = [str(a) for a in metadata.author]
                else:
                    authors = [str(metadata.author)]

            return {
                "title": metadata.title or None,
                "authors": authors,
                "isbn": getattr(metadata, "isbn", None),
            }
        except (
            ValueError,
            ImportError,
            OSError,
            KeyError,
            AttributeError,
            zipfile.BadZipFile,
            struct.error,
            UnicodeDecodeError,
            EOFError,
        ) as e:
            logger.warning(
                "Failed to extract metadata from %s: %s",
                file_path,
                e,
            )
            # Fallback to filename-based metadata
            return {
                "title": file_path.stem,
                "authors": [],
                "isbn": None,
            }

    def group_files_by_metadata(self, files: list[Path]) -> list[FileGroup]:
        """Group files by matching metadata (title/author).

        Extracts metadata from each file and groups files with matching
        or similar title and author. Falls back to directory-based grouping
        if metadata extraction fails.

        Parameters
        ----------
        files : list[Path]
            List of file paths to group.

        Returns
        -------
        list[FileGroup]
            List of file groups, one per book.
        """
        if not files:
            return []

        # Extract metadata from all files
        file_metadata_list = self._extract_metadata_from_files(files)

        # Group files by matching metadata
        groups = self._group_metadata_by_matching(file_metadata_list)

        # Convert to FileGroup objects
        return self._convert_groups_to_file_groups(groups)

    def _extract_metadata_from_files(self, files: list[Path]) -> list[FileMetadata]:
        """Extract metadata from a list of files.

        Parameters
        ----------
        files : list[Path]
            List of file paths to extract metadata from.

        Returns
        -------
        list[FileMetadata]
            List of file metadata objects.
        """
        file_metadata_list: list[FileMetadata] = []
        for file_path in files:
            file_format = file_path.suffix.lower().lstrip(".")
            if not file_format:
                continue

            file_meta = self._extract_single_file_metadata(file_path, file_format)
            if file_meta:
                file_metadata_list.append(file_meta)

        return file_metadata_list

    def _extract_single_file_metadata(
        self, file_path: Path, file_format: str
    ) -> FileMetadata | None:
        """Extract metadata from a single file.

        Parameters
        ----------
        file_path : Path
            Path to the file.
        file_format : str
            File format extension.

        Returns
        -------
        FileMetadata | None
            File metadata or None if extraction fails completely.
        """
        try:
            metadata = self.extract_metadata(file_path, file_format)
            return FileMetadata(
                file_path=file_path,
                file_format=file_format,
                title=metadata.get("title"),
                authors=metadata.get("authors", []),
                isbn=metadata.get("isbn"),
            )
        except (
            ValueError,
            OSError,
            AttributeError,
            zipfile.BadZipFile,
            struct.error,
            UnicodeDecodeError,
            EOFError,
        ) as e:
            logger.warning(
                "Failed to extract metadata from %s: %s",
                file_path,
                e,
            )
            # Add with minimal metadata
            return FileMetadata(
                file_path=file_path,
                file_format=file_format,
                title=None,
                authors=[],
                isbn=None,
            )

    def _group_metadata_by_matching(
        self, file_metadata_list: list[FileMetadata]
    ) -> list[list[FileMetadata]]:
        """Group file metadata by matching title/author.

        Parameters
        ----------
        file_metadata_list : list[FileMetadata]
            List of file metadata to group.

        Returns
        -------
        list[list[FileMetadata]]
            List of groups, where each group contains matching files.
        """
        groups: list[list[FileMetadata]] = []
        for file_meta in file_metadata_list:
            matched_group = self._find_matching_group(groups, file_meta)
            if matched_group is not None:
                matched_group.append(file_meta)
            else:
                groups.append([file_meta])
        return groups

    def _find_matching_group(
        self, groups: list[list[FileMetadata]], file_meta: FileMetadata
    ) -> list[FileMetadata] | None:
        """Find a group that matches the given file metadata.

        Parameters
        ----------
        groups : list[list[FileMetadata]]
            Existing groups to search.
        file_meta : FileMetadata
            File metadata to match.

        Returns
        -------
        list[FileMetadata] | None
            Matching group or None if no match found.
        """
        for group in groups:
            if self._files_match(group[0], file_meta):
                return group
        return None

    def _convert_groups_to_file_groups(
        self, groups: list[list[FileMetadata]]
    ) -> list[FileGroup]:
        """Convert metadata groups to FileGroup objects.

        Parameters
        ----------
        groups : list[list[FileMetadata]]
            Groups of file metadata.

        Returns
        -------
        list[FileGroup]
            List of FileGroup objects.
        """
        file_groups: list[FileGroup] = []
        for group in groups:
            first_meta = group[0]
            metadata_hint = {
                "title": first_meta.title,
                "authors": first_meta.authors,
                "isbn": first_meta.isbn,
            }
            book_key = self._create_book_key_from_metadata(first_meta)
            file_groups.append(
                FileGroup(
                    book_key=book_key,
                    files=[fm.file_path for fm in group],
                    metadata_hint=metadata_hint,
                )
            )
        return file_groups

    def _files_match(self, file_meta1: FileMetadata, file_meta2: FileMetadata) -> bool:
        """Check if two files belong to the same book.

        Uses exact and fuzzy matching on title and authors.

        Parameters
        ----------
        file_meta1 : FileMetadata
            First file metadata.
        file_meta2 : FileMetadata
            Second file metadata.

        Returns
        -------
        bool
            True if files match, False otherwise.
        """
        # If both have ISBNs, match by ISBN
        if file_meta1.isbn and file_meta2.isbn:
            # Normalize ISBNs (remove hyphens, spaces)
            isbn1 = "".join(c for c in file_meta1.isbn if c.isalnum())
            isbn2 = "".join(c for c in file_meta2.isbn if c.isalnum())
            if isbn1.lower() == isbn2.lower():
                return True

        # Match by title and authors
        title1 = (file_meta1.title or "").strip().lower()
        title2 = (file_meta2.title or "").strip().lower()

        # If no titles, can't match
        if not title1 or not title2:
            # Fallback: check if in same immediate parent directory
            return file_meta1.file_path.parent == file_meta2.file_path.parent

        # Check exact title match
        if title1 == title2:
            # If titles match, check authors
            return self._authors_match(file_meta1.authors, file_meta2.authors)

        # Check fuzzy title match
        similarity = self._string_similarity(title1, title2)
        if similarity >= self._similarity_threshold:
            # If titles are similar, check authors
            return self._authors_match(file_meta1.authors, file_meta2.authors)

        # No match
        return False

    def _authors_match(self, authors1: list[str], authors2: list[str]) -> bool:
        """Check if two author lists match.

        Parameters
        ----------
        authors1 : list[str]
            First author list.
        authors2 : list[str]
            Second author list.

        Returns
        -------
        bool
            True if authors match, False otherwise.
        """
        # Normalize authors (lowercase, strip)
        norm1 = {a.strip().lower() for a in authors1 if a.strip()}
        norm2 = {a.strip().lower() for a in authors2 if a.strip()}

        # If both lists are empty, consider it a match (unknown authors)
        if not norm1 and not norm2:
            return True

        # If one is empty and the other isn't, no match
        if not norm1 or not norm2:
            return False

        # Check if there's any overlap
        return bool(norm1 & norm2)

    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings.

        Uses SequenceMatcher for fuzzy matching.

        Parameters
        ----------
        str1 : str
            First string.
        str2 : str
            Second string.

        Returns
        -------
        float
            Similarity score (0.0-1.0).
        """
        try:
            from difflib import SequenceMatcher

            return SequenceMatcher(None, str1, str2).ratio()
        except ImportError:
            # Fallback: simple character-based similarity
            if not str1 or not str2:
                return 0.0
            if str1 == str2:
                return 1.0
            # Simple Jaccard similarity on character sets
            set1 = set(str1.lower())
            set2 = set(str2.lower())
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            return intersection / union if union > 0 else 0.0

    def _create_book_key_from_metadata(self, file_meta: FileMetadata) -> str:
        """Create a book key from metadata.

        Parameters
        ----------
        file_meta : FileMetadata
            File metadata.

        Returns
        -------
        str
            Normalized book key.
        """
        # Use title and first author if available
        parts: list[str] = []
        if file_meta.title:
            parts.append(file_meta.title)
        if file_meta.authors:
            parts.append(file_meta.authors[0])

        key = " - ".join(parts) if parts else file_meta.file_path.stem

        # Normalize: lowercase, replace spaces with underscores
        key = key.lower().replace(" ", "_")
        # Remove special characters
        key = "".join(c for c in key if c.isalnum() or c in ("_", "-"))
        return key or "unknown"

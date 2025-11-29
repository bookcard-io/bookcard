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

"""Cover file enforcement service.

Updates cover.jpg files in book directories and embeds covers into ebook files.
"""

import logging
import shutil
import subprocess  # noqa: S404
from pathlib import Path
from typing import ClassVar

from PIL import Image
from sqlmodel import select

from fundamental.models.config import Library
from fundamental.models.media import Data
from fundamental.repositories.calibre_book_repository import CalibreBookRepository
from fundamental.repositories.models import BookWithFullRelations
from fundamental.services.metadata_enforcement.library_path_resolver import (
    LibraryPathResolver,
)

logger = logging.getLogger(__name__)


class CoverEnforcementService:
    """Service for enforcing cover image files.

    Updates cover.jpg files in book directories and embeds covers into
    ebook files (EPUB, AZW3) for device compatibility. Follows SRP by
    focusing solely on cover file updates and embedding.

    Parameters
    ----------
    library : Library
        Library configuration for path resolution.
    """

    # Supported formats for cover embedding
    SUPPORTED_FORMATS: ClassVar[list[str]] = ["epub", "azw3"]

    def __init__(self, library: Library) -> None:
        """Initialize cover enforcement service.

        Parameters
        ----------
        library : Library
            Library configuration.
        """
        self._library = library
        self._path_resolver = LibraryPathResolver(library)

    def enforce_cover(self, book_with_rels: BookWithFullRelations) -> bool:
        """Enforce cover image file for a book.

        Verifies cover.jpg exists in the book directory and embeds the cover
        into supported ebook files (EPUB, AZW3) for device compatibility.
        If the book has no cover, the operation is skipped gracefully.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with all related metadata.

        Returns
        -------
        bool
            True if cover file was verified and embedded successfully,
            False otherwise. Returns False if book has no cover (not an error).
        """
        try:
            book = book_with_rels.book

            # Check if book has a cover
            if not book.has_cover:
                logger.debug(
                    "Book has no cover, skipping cover enforcement: book_id=%d",
                    book.id,
                )
                return False

            # Get book directory path
            library_path = self._path_resolver.get_library_root()
            book_path = library_path / book.path

            # Ensure book directory exists
            book_path.mkdir(parents=True, exist_ok=True)

            # Find existing cover file in book directory
            # Calibre stores covers as cover.jpg
            cover_file_path = book_path / "cover.jpg"

            # Verify cover file exists and is valid
            if not cover_file_path.exists():
                logger.warning(
                    "Cover file not found in book directory: book_id=%d, path=%s",
                    book.id,
                    cover_file_path,
                )
                return False

            # Verify it's actually an image file
            try:
                with Image.open(cover_file_path) as img:
                    img.verify()
            except (OSError, ValueError, TypeError, AttributeError) as e:
                logger.warning(
                    "Cover file exists but is invalid: book_id=%d, path=%s, error=%s",
                    book.id,
                    cover_file_path,
                    e,
                )
                return False

            # Embed cover into supported ebook files
            embedded = self._embed_cover_into_ebooks(
                book_with_rels, book_path, cover_file_path
            )

            if embedded:
                logger.info(
                    "Cover file verified and embedded: book_id=%d, path=%s",
                    book.id,
                    cover_file_path,
                )
            else:
                logger.info(
                    "Cover file verified (no supported formats to embed): book_id=%d, path=%s",
                    book.id,
                    cover_file_path,
                )
        except OSError:
            logger.exception(
                "Failed to access cover file for book_id=%d",
                book_with_rels.book.id,
            )
            return False
        except (ValueError, TypeError, AttributeError):
            logger.exception(
                "Unexpected error updating cover file for book_id=%d",
                book_with_rels.book.id,
            )
            return False
        else:
            return True

    def _embed_cover_into_ebooks(
        self,
        book_with_rels: BookWithFullRelations,
        book_path: Path,
        cover_file_path: Path,
    ) -> bool:
        """Embed cover image into supported ebook files.

        Uses ebook-polish to embed the cover into EPUB and AZW3 files.
        This ensures covers display correctly on Kindle and other devices.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with all related metadata.
        book_path : Path
            Book directory path.
        cover_file_path : Path
            Path to cover.jpg file.

        Returns
        -------
        bool
            True if at least one ebook file was updated, False otherwise.
        """
        book = book_with_rels.book
        if book.id is None:
            logger.warning("Book ID is None, cannot embed cover")
            return False

        # Get ebook-polish binary path
        polish_path = self._get_ebook_polish_path()
        if polish_path is None:
            logger.warning(
                "ebook-polish not found, skipping cover embedding: book_id=%d",
                book.id,
            )
            return False

        book_repo = CalibreBookRepository(
            calibre_db_path=self._library.calibre_db_path,
            calibre_db_file=self._library.calibre_db_file,
        )

        with book_repo.get_session() as calibre_session:
            data_stmt = select(Data).where(Data.book == book.id)
            data_records = list(calibre_session.exec(data_stmt).all())

        any_embedded = False

        for data_record in data_records:
            format_lower = data_record.format.lower()

            # Only process supported formats
            if format_lower not in self.SUPPORTED_FORMATS:
                continue

            # Find ebook file
            file_path = self._find_ebook_file(book_path, book.id, data_record)
            if file_path is None:
                logger.debug(
                    "Ebook file not found for cover embedding: book_id=%d, format=%s",
                    book.id,
                    format_lower,
                )
                continue

            # Embed cover using ebook-polish
            try:
                success = self._run_ebook_polish(
                    polish_path, cover_file_path, file_path
                )
                if success:
                    any_embedded = True
                    logger.info(
                        "Cover embedded into ebook: book_id=%d, format=%s, path=%s",
                        book.id,
                        format_lower,
                        file_path,
                    )
            except Exception:
                logger.exception(
                    "Failed to embed cover into ebook: book_id=%d, format=%s, path=%s",
                    book.id,
                    format_lower,
                    file_path,
                )

        return any_embedded

    def _get_ebook_polish_path(self) -> str | None:
        """Get path to Calibre ebook-polish binary.

        Returns
        -------
        str | None
            Path to ebook-polish if found, None otherwise.
        """
        # Check Docker installation path first
        docker_path = Path("/app/calibre/ebook-polish")
        if docker_path.exists():
            return str(docker_path)

        # Fallback to PATH lookup
        polish = shutil.which("ebook-polish")
        if polish:
            return polish

        return None

    def _run_ebook_polish(
        self, polish_path: str, cover_path: Path, ebook_path: Path
    ) -> bool:
        """Run ebook-polish to embed cover into ebook file.

        Parameters
        ----------
        polish_path : str
            Path to ebook-polish binary.
        cover_path : Path
            Path to cover image file.
        ebook_path : Path
            Path to ebook file to update.

        Returns
        -------
        bool
            True if successful, False otherwise.
        """
        try:
            # ebook-polish -c cover.jpg -U file.epub file.epub
            # -c: cover image path
            # -U: update file in place
            cmd = [
                polish_path,
                "-c",
                str(cover_path),
                "-U",
                str(ebook_path),
                str(ebook_path),
            ]

            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                return True

            logger.warning(
                "ebook-polish failed: path=%s, returncode=%d, stderr=%s",
                ebook_path,
                result.returncode,
                result.stderr[:500] if result.stderr else "",
            )
        except subprocess.TimeoutExpired:
            logger.exception(
                "ebook-polish timed out after 5 minutes: path=%s",
                ebook_path,
            )
            return False
        except Exception:
            logger.exception(
                "Error running ebook-polish: path=%s",
                ebook_path,
            )
            return False
        else:
            return False

    def _find_ebook_file(
        self, book_dir: Path, book_id: int, data_record: Data
    ) -> Path | None:
        """Find ebook file path.

        Parameters
        ----------
        book_dir : Path
            Book directory path.
        book_id : int
            Book ID.
        data_record : Data
            Data record for the format.

        Returns
        -------
        Path | None
            Path to ebook file if found, None otherwise.
        """
        file_name = data_record.name or str(book_id)
        format_lower = data_record.format.lower()

        # Try primary path: {name}.{format}
        primary = book_dir / f"{file_name}.{format_lower}"
        if primary.exists():
            return primary

        # Try alternative path: {book_id}.{format}
        alt = book_dir / f"{book_id}.{format_lower}"
        if alt.exists():
            return alt

        # Try to find by extension
        for file_path in book_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == f".{format_lower}":
                return file_path

        return None

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

"""Core EPUB data structures and I/O operations.

Provides EPUBContents data class and EPUBReader/EPUBWriter classes
following Single Responsibility Principle.
"""

import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fundamental.models.epub_fixer import EPUBFixType


@dataclass
class EPUBContents:
    """Data class holding EPUB file contents.

    Attributes
    ----------
    files : dict[str, str]
        Text-based files (HTML, XML, CSS, etc.) mapped by filename.
    binary_files : dict[str, bytes]
        Binary files (images, fonts, etc.) mapped by filename.
    entries : list[str]
        List of all file entries in the EPUB archive.
    """

    files: dict[str, str] = field(default_factory=dict)
    binary_files: dict[str, bytes] = field(default_factory=dict)
    entries: list[str] = field(default_factory=list)


@dataclass
class FixResult:
    """Structured result from a fix operation.

    Attributes
    ----------
    fix_type : EPUBFixType
        Type of fix that was applied.
    description : str
        Human-readable description of the fix.
    file_name : str | None
        Filename within EPUB that was fixed (for encoding, body_id_link, stray_img).
    original_value : str | None
        Original value before fix (for language tag changes).
    fixed_value : str | None
        New value after fix (for language tag changes).
    """

    fix_type: "EPUBFixType"
    description: str
    file_name: str | None = None
    original_value: str | None = None
    fixed_value: str | None = None


class EPUBReader:
    """Responsible only for reading EPUB file contents.

    Follows Single Responsibility Principle - only handles file I/O.
    """

    def read(self, epub_path: str | Path) -> EPUBContents:
        """Read EPUB file contents.

        Parameters
        ----------
        epub_path : str | Path
            Path to EPUB file.

        Returns
        -------
        EPUBContents
            EPUB file contents.

        Raises
        ------
        FileNotFoundError
            If EPUB file does not exist.
        zipfile.BadZipFile
            If file is not a valid ZIP archive.
        """
        epub_path = Path(epub_path)
        if not epub_path.exists():
            msg = f"EPUB file not found: {epub_path}"
            raise FileNotFoundError(msg)

        contents = EPUBContents()

        with zipfile.ZipFile(epub_path, "r") as zip_ref:
            contents.entries = zip_ref.namelist()

            for filename in contents.entries:
                ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
                if filename == "mimetype" or ext in [
                    "html",
                    "xhtml",
                    "htm",
                    "xml",
                    "svg",
                    "css",
                    "opf",
                    "ncx",
                ]:
                    try:
                        contents.files[filename] = zip_ref.read(filename).decode(
                            "utf-8"
                        )
                    except UnicodeDecodeError:
                        # Fallback to latin-1 if UTF-8 fails
                        contents.files[filename] = zip_ref.read(filename).decode(
                            "latin-1"
                        )
                else:
                    contents.binary_files[filename] = zip_ref.read(filename)

        return contents


class EPUBWriter:
    """Responsible only for writing EPUB file contents.

    Follows Single Responsibility Principle - only handles file I/O.
    """

    def write(self, contents: EPUBContents, output_path: str | Path) -> None:
        """Write EPUB file contents to disk.

        Parameters
        ----------
        contents : EPUBContents
            EPUB contents to write.
        output_path : str | Path
            Output file path.

        Raises
        ------
        OSError
            If file cannot be written.
        """
        output_path = Path(output_path)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
            # First write mimetype file (must be uncompressed)
            if "mimetype" in contents.files:
                zip_ref.writestr(
                    "mimetype",
                    contents.files["mimetype"],
                    compress_type=zipfile.ZIP_STORED,
                )

            # Add text files
            for filename, content in contents.files.items():
                if filename != "mimetype":
                    zip_ref.writestr(filename, content)

            # Add binary files
            for filename, content in contents.binary_files.items():
                zip_ref.writestr(filename, content)

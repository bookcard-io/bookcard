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

"""File type utilities for EPUB processing.

Provides helper methods for checking file extensions to avoid code duplication.
"""


class FileTypes:
    """Helper class for file type checking.

    Provides constants and methods for checking file extensions,
    avoiding repeated extension checking code throughout the codebase.
    """

    TEXT_EXTENSIONS = frozenset([
        "html",
        "xhtml",
        "htm",
        "xml",
        "svg",
        "css",
        "opf",
        "ncx",
    ])
    HTML_EXTENSIONS = frozenset(["html", "xhtml"])

    @classmethod
    def is_text_file(cls, filename: str) -> bool:
        """Check if file is a text-based EPUB file.

        Parameters
        ----------
        filename : str
            Filename to check.

        Returns
        -------
        bool
            True if file has a text-based extension.
        """
        return cls._get_extension(filename) in cls.TEXT_EXTENSIONS

    @classmethod
    def is_html_file(cls, filename: str) -> bool:
        """Check if file is an HTML file.

        Parameters
        ----------
        filename : str
            Filename to check.

        Returns
        -------
        bool
            True if file has an HTML extension.
        """
        return cls._get_extension(filename) in cls.HTML_EXTENSIONS

    @staticmethod
    def _get_extension(filename: str) -> str:
        """Extract file extension in lowercase.

        Parameters
        ----------
        filename : str
            Filename to extract extension from.

        Returns
        -------
        str
            File extension in lowercase, or empty string if no extension.
        """
        if "." not in filename:
            return ""
        return filename.rsplit(".", 1)[-1].lower()

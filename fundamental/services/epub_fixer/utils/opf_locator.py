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

"""OPF file locator utility.

Extracts OPF file path from EPUB container.xml to avoid code duplication.
"""

from contextlib import suppress
from xml.parsers.expat import ExpatError

from defusedxml import minidom


class OPFLocator:
    """Utility class for locating OPF file in EPUB container."""

    @staticmethod
    def find_opf_path(files: dict[str, str]) -> str | None:
        """Extract OPF file path from container.xml.

        Parameters
        ----------
        files : dict[str, str]
            Dictionary of EPUB file contents (filename -> content).

        Returns
        -------
        str | None
            OPF file path if found, None otherwise.
        """
        if "META-INF/container.xml" not in files:
            return None

        with suppress(ExpatError, ValueError):
            container_xml = minidom.parseString(files["META-INF/container.xml"])
            for rootfile in container_xml.getElementsByTagName("rootfile"):
                if (
                    rootfile.getAttribute("media-type")
                    == "application/oebps-package+xml"
                ):
                    return rootfile.getAttribute("full-path")

        return None

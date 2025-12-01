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

"""Protocol for conversion strategies.

Defines the interface that all conversion strategies must implement,
following the Strategy pattern and DIP.
"""

from pathlib import Path
from typing import Protocol


class ConversionStrategy(Protocol):
    """Strategy for executing format conversions.

    This protocol defines the interface that all conversion strategies
    must implement, allowing different converters to be used
    interchangeably.
    """

    def supports(self, source_format: str, target_format: str) -> bool:
        """Check if this strategy handles the given conversion.

        Parameters
        ----------
        source_format : str
            Source format (e.g., "MOBI", "AZW3").
        target_format : str
            Target format (e.g., "EPUB", "KEPUB").

        Returns
        -------
        bool
            True if this strategy can handle the conversion, False otherwise.
        """
        ...

    def convert(
        self,
        input_path: Path,
        target_format: str,
        output_path: Path,
    ) -> Path:
        """Execute the conversion.

        Parameters
        ----------
        input_path : Path
            Path to input file.
        target_format : str
            Target format (e.g., "EPUB").
        output_path : Path
            Path where converted file should be saved.

        Returns
        -------
        Path
            Path to converted file.

        Raises
        ------
        ConversionError
            If conversion fails.
        """
        ...

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

"""Calibre-based conversion strategy.

Implements conversion using Calibre's ebook-convert command,
following the ConversionStrategy protocol.
"""

import logging
import subprocess  # noqa: S404
from contextlib import suppress
from pathlib import Path
from typing import NoReturn

from fundamental.services.conversion.exceptions import ConversionError

logger = logging.getLogger(__name__)


class CalibreConversionStrategy:
    """Calibre-based conversion strategy.

    Executes format conversion using Calibre's ebook-convert command.

    Parameters
    ----------
    converter_path : Path
        Path to ebook-convert binary.
    timeout : int
        Conversion timeout in seconds (default: 300).
    """

    def __init__(self, converter_path: Path, timeout: int = 300) -> None:
        """Initialize Calibre conversion strategy.

        Parameters
        ----------
        converter_path : Path
            Path to ebook-convert binary.
        timeout : int
            Conversion timeout in seconds (default: 300).
        """
        self._converter_path = converter_path
        self._timeout = timeout

    def supports(self, source_format: str, target_format: str) -> bool:  # noqa: ARG002
        """Check if this strategy handles the given conversion.

        Calibre handles most e-book format conversions.

        Parameters
        ----------
        source_format : str
            Source format (e.g., "MOBI", "AZW3").
        target_format : str
            Target format (e.g., "EPUB", "KEPUB").

        Returns
        -------
        bool
            Always returns True (Calibre handles most formats).
        """
        return True

    def convert(
        self,
        input_path: Path,
        target_format: str,  # noqa: ARG002
        output_path: Path,
    ) -> Path:
        """Execute the conversion using Calibre ebook-convert.

        Parameters
        ----------
        input_path : Path
            Path to input file.
        _target_format : str
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
            If conversion fails or times out.
        """

        def _raise_conversion_error(msg: str) -> NoReturn:
            """Raise ConversionError with message."""
            raise ConversionError(msg)

        try:
            # Run ebook-convert command
            cmd = [
                str(self._converter_path),
                str(input_path),
                str(output_path),
            ]

            logger.debug("Running conversion: %s", " ".join(cmd))
            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=self._timeout,
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown conversion error"
                msg = f"Conversion failed: {error_msg}"
                _raise_conversion_error(msg)

            if not output_path.exists():
                msg = "Conversion completed but output file not found"
                _raise_conversion_error(msg)
            else:
                logger.debug("Converted file saved to: %s", output_path)
                return output_path
        except subprocess.TimeoutExpired:
            msg = f"Conversion timed out after {self._timeout} seconds"
            raise ConversionError(msg) from None
        except ConversionError:
            raise
        except Exception as e:
            # Clean up output file on error
            with suppress(OSError):
                if output_path.exists():
                    output_path.unlink()
            msg = f"Conversion failed: {e!s}"
            raise ConversionError(msg) from e

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

"""Composite conversion strategy that routes between KCC and Calibre.

Routes comic formats to KCC with priority, other formats to Calibre.
Implements the ConversionStrategy protocol.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from bookcard.services.conversion.exceptions import ConversionError

if TYPE_CHECKING:
    from collections.abc import Callable

    from bookcard.models.kcc_config import KCCConversionProfile
    from bookcard.services.conversion.strategies.calibre import (
        CalibreConversionStrategy,
    )
    from bookcard.services.conversion.strategies.kcc import KCCConversionStrategy

logger = logging.getLogger(__name__)

# Comic input formats that should use KCC
COMIC_FORMATS = {"CBZ", "CBR", "CB7", "PDF"}


def is_comic_format(format_name: str) -> bool:
    """Check if format is a comic format.

    Parameters
    ----------
    format_name : str
        Format name to check.

    Returns
    -------
    bool
        True if format is a comic format (CBZ, CBR, CB7, PDF).
    """
    return format_name.upper() in COMIC_FORMATS


class CompositeConversionStrategy:
    """Composite strategy that routes conversions between KCC and Calibre.

    For comic input formats (CBZ, CBR, CB7, PDF), tries KCC first,
    then falls back to Calibre if KCC fails or is unavailable.
    For other formats, uses Calibre only.

    Parameters
    ----------
    kcc_strategy : KCCConversionStrategy | None
        KCC conversion strategy (None if KCC unavailable).
    calibre_strategy : CalibreConversionStrategy
        Calibre conversion strategy.
    """

    def __init__(
        self,
        kcc_strategy: "KCCConversionStrategy | None",
        calibre_strategy: "CalibreConversionStrategy",
    ) -> None:
        """Initialize composite conversion strategy.

        Parameters
        ----------
        kcc_strategy : KCCConversionStrategy | None
            KCC conversion strategy (None if KCC unavailable).
        calibre_strategy : CalibreConversionStrategy
            Calibre conversion strategy.
        """
        self._kcc_strategy = kcc_strategy
        self._calibre_strategy = calibre_strategy

    def supports(self, source_format: str, target_format: str) -> bool:
        """Check if this strategy handles the given conversion.

        Returns True if either KCC or Calibre supports the conversion.

        Parameters
        ----------
        source_format : str
            Source format (e.g., "MOBI", "CBZ").
        target_format : str
            Target format (e.g., "EPUB", "MOBI").

        Returns
        -------
        bool
            True if either strategy can handle the conversion, False otherwise.
        """
        source_upper = source_format.upper()

        # For comic formats, check if KCC supports it
        if (
            is_comic_format(source_upper)
            and self._kcc_strategy
            and self._kcc_strategy.supports(source_format, target_format)
        ):
            return True
        # If KCC doesn't support it, fall through to Calibre

        # For all formats, check if Calibre supports it
        return self._calibre_strategy.supports(source_format, target_format)

    def convert(
        self,
        input_path: Path,
        target_format: str,
        output_path: Path,
        profile_getter: "Callable[[], KCCConversionProfile | None] | None" = None,
    ) -> Path:
        """Execute the conversion using appropriate strategy.

        For comic formats, tries KCC first, then falls back to Calibre.
        For other formats, uses Calibre only.

        Parameters
        ----------
        input_path : Path
            Path to input file.
        target_format : str
            Target format (e.g., "EPUB").
        output_path : Path
            Path where converted file should be saved.
        profile_getter : callable[[], KCCConversionProfile | None] | None
            Optional function to retrieve KCC profile when needed.

        Returns
        -------
        Path
            Path to converted file.

        Raises
        ------
        ConversionError
            If conversion fails.
        """
        # Determine source format from file extension
        source_format = input_path.suffix.upper().lstrip(".")
        if not source_format:
            # Try to infer from filename
            source_format = input_path.stem.split(".")[-1].upper()

        source_upper = source_format.upper()

        # For comic formats, try KCC first
        if (
            is_comic_format(source_upper)
            and self._kcc_strategy
            and self._kcc_strategy.supports(source_format, target_format)
        ):
            try:
                # Update KCC strategy with user profile if available
                if profile_getter:
                    profile = profile_getter()
                    if profile:
                        # Create a new KCC strategy instance with the profile
                        from bookcard.services.conversion.strategies.kcc import (
                            KCCConversionStrategy,
                        )

                        kcc_path = self._kcc_strategy.kcc_path
                        timeout = self._kcc_strategy.timeout
                        kcc_strategy_with_profile = KCCConversionStrategy(
                            kcc_path, profile=profile, timeout=timeout
                        )
                        logger.info(
                            "Using KCC for comic conversion with profile: %s -> %s",
                            source_format,
                            target_format,
                        )
                        return kcc_strategy_with_profile.convert(
                            input_path, target_format, output_path
                        )

                logger.info(
                    "Using KCC for comic conversion: %s -> %s",
                    source_format,
                    target_format,
                )
                return self._kcc_strategy.convert(
                    input_path, target_format, output_path
                )
            except ConversionError as e:
                logger.warning(
                    "KCC conversion failed, falling back to Calibre: %s",
                    e,
                )
                # Fall through to Calibre

        # Use Calibre for all other formats or as fallback
        logger.info(
            "Using Calibre for conversion: %s -> %s",
            source_format,
            target_format,
        )
        return self._calibre_strategy.convert(input_path, target_format, output_path)

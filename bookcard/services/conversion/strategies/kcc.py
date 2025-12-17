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

"""KCC (Kindle Comic Converter) conversion strategy.

Implements conversion using KCC's kcc-c2e.py CLI tool,
following the ConversionStrategy protocol.
"""

import logging
import subprocess  # noqa: S404
from contextlib import suppress
from pathlib import Path
from typing import NoReturn

from bookcard.models.kcc_config import KCCConversionProfile
from bookcard.services.conversion.exceptions import ConversionError

logger = logging.getLogger(__name__)

# Comic input formats that KCC supports
COMIC_INPUT_FORMATS = {"CBZ", "CBR", "CB7", "PDF"}

# KCC output formats mapping
KCC_OUTPUT_FORMATS = {
    "MOBI": "MOBI",
    "AZW3": "MOBI",  # KCC generates dual MOBI/AZW3 files with .mobi extension
    "EPUB": "EPUB",
    "KEPUB": "KEPUB",
    "CBZ": "CBZ",
    "PDF": "PDF",
    "KFX": "KFX",
}


class KCCConversionStrategy:
    """KCC-based conversion strategy.

    Executes format conversion using KCC's kcc-c2e.py CLI tool.
    Supports comic formats (CBZ, CBR, CB7, PDF) as input.

    Parameters
    ----------
    kcc_path : Path
        Path to kcc-c2e.py executable.
    profile : KCCConversionProfile | None
        Optional KCC conversion profile with user settings.
        If None, uses default settings.
    timeout : int
        Conversion timeout in seconds (default: 600).
    """

    def __init__(
        self,
        kcc_path: Path,
        profile: KCCConversionProfile | None = None,
        timeout: int = 600,
    ) -> None:
        """Initialize KCC conversion strategy.

        Parameters
        ----------
        kcc_path : Path
            Path to kcc-c2e.py executable.
        profile : KCCConversionProfile | None
            Optional KCC conversion profile with user settings.
        timeout : int
            Conversion timeout in seconds (default: 600).
        """
        self._kcc_path = kcc_path
        self._profile = profile
        self._timeout = timeout

    @property
    def kcc_path(self) -> Path:
        """Get KCC executable path.

        Returns
        -------
        Path
            Path to kcc-c2e.py executable.
        """
        return self._kcc_path

    @property
    def timeout(self) -> int:
        """Get conversion timeout.

        Returns
        -------
        int
            Timeout in seconds.
        """
        return self._timeout

    def supports(self, source_format: str, target_format: str) -> bool:
        """Check if this strategy handles the given conversion.

        KCC supports comic formats (CBZ, CBR, CB7, PDF) as input
        and can output MOBI, EPUB, KEPUB, CBZ, PDF, KFX.

        Parameters
        ----------
        source_format : str
            Source format (e.g., "CBZ", "CBR", "PDF").
        target_format : str
            Target format (e.g., "MOBI", "EPUB", "KEPUB").

        Returns
        -------
        bool
            True if this strategy can handle the conversion, False otherwise.
        """
        source_upper = source_format.upper()
        target_upper = target_format.upper()

        # Check if source is a comic format
        if source_upper not in COMIC_INPUT_FORMATS:
            return False

        # Check if target format is supported by KCC
        return target_upper in KCC_OUTPUT_FORMATS

    def convert(
        self,
        input_path: Path,
        target_format: str,
        output_path: Path,
    ) -> Path:
        """Execute the conversion using KCC kcc-c2e.py.

        Parameters
        ----------
        input_path : Path
            Path to input file.
        target_format : str
            Target format (e.g., "MOBI", "EPUB").
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
            # Build KCC command
            cmd = self._build_kcc_command(input_path, target_format, output_path)

            logger.debug("Running KCC conversion: %s", " ".join(str(c) for c in cmd))

            # Determine Python interpreter (use venv if available)
            python_cmd = self._get_python_command()

            # Run kcc-c2e.py
            full_cmd = [python_cmd, str(self._kcc_path), *cmd]

            result = subprocess.run(  # noqa: S603
                full_cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=self._timeout,
                cwd=str(input_path.parent),
            )

            if result.returncode != 0:
                error_msg = (
                    result.stderr or result.stdout or "Unknown KCC conversion error"
                )
                msg = f"KCC conversion failed: {error_msg}"
                _raise_conversion_error(msg)

            # KCC outputs to the same directory as input by default
            # We need to find the output file and move it to the desired location
            expected_output = self._find_kcc_output(
                input_path, target_format, output_path
            )

            if not expected_output.exists():
                msg = "KCC conversion completed but output file not found"
                _raise_conversion_error(msg)

            # Move to final location if different
            if expected_output != output_path:
                from shutil import move

                move(str(expected_output), str(output_path))
                logger.debug("KCC converted file moved to: %s", output_path)
            else:
                logger.debug("KCC converted file saved to: %s", output_path)
        except subprocess.TimeoutExpired:
            msg = f"KCC conversion timed out after {self._timeout} seconds"
            raise ConversionError(msg) from None
        except ConversionError:
            raise
        except Exception as e:
            # Clean up output file on error
            with suppress(OSError):
                if output_path.exists():
                    output_path.unlink()
            msg = f"KCC conversion failed: {e!s}"
            raise ConversionError(msg) from e
        else:
            return output_path

    def _get_python_command(self) -> str:
        """Get Python command to use for running KCC.

        Returns
        -------
        str
            Python command (python3 or python).
        """
        # Check if KCC venv exists and use it
        venv_python = self._kcc_path.parent / "venv" / "bin" / "python3"
        if venv_python.exists():
            return str(venv_python)

        # Fallback to system python3
        return "python3"

    def _build_kcc_command(
        self,
        input_path: Path,
        target_format: str,
        output_path: Path,
    ) -> list[str]:
        """Build KCC command line arguments.

        Parameters
        ----------
        input_path : Path
            Path to input file.
        target_format : str
            Target format.
        output_path : Path
            Desired output path.

        Returns
        -------
        list[str]
            List of command line arguments for kcc-c2e.py.
        """
        cmd: list[str] = []

        # Profile settings
        profile = self._profile

        # Device profile
        device_profile = profile.device_profile if profile else "KV"
        cmd.extend(["-p", device_profile])

        # Output format
        kcc_format = KCC_OUTPUT_FORMATS.get(target_format.upper(), "MOBI")
        cmd.extend(["-f", kcc_format])

        # Output directory
        cmd.extend(["-o", str(output_path.parent)])

        # Processing options
        if profile:
            self._add_profile_options(cmd, profile)

        # Input file (must be last)
        cmd.append(str(input_path))

        return cmd

    def _add_profile_options(
        self, cmd: list[str], profile: KCCConversionProfile
    ) -> None:
        """Add profile-specific options to command.

        Parameters
        ----------
        cmd : list[str]
            Command list to append to.
        profile : KCCConversionProfile
            KCC conversion profile.
        """
        self._add_basic_options(cmd, profile)
        self._add_processing_options(cmd, profile)
        self._add_cropping_options(cmd, profile)
        self._add_output_options(cmd, profile)

    def _add_basic_options(self, cmd: list[str], profile: KCCConversionProfile) -> None:
        """Add basic profile options.

        Parameters
        ----------
        cmd : list[str]
            Command list to append to.
        profile : KCCConversionProfile
            KCC conversion profile.
        """
        if profile.manga_style:
            cmd.append("-m")
        if profile.hq:
            cmd.append("-q")
        if profile.two_panel:
            cmd.append("-2")
        if profile.webtoon:
            cmd.append("-w")
        if profile.upscale:
            cmd.append("-u")
        if profile.stretch:
            cmd.append("-s")

    def _add_processing_options(
        self, cmd: list[str], profile: KCCConversionProfile
    ) -> None:
        """Add image processing options.

        Parameters
        ----------
        cmd : list[str]
            Command list to append to.
        profile : KCCConversionProfile
            KCC conversion profile.
        """
        if profile.gamma is not None:
            cmd.extend(["-g", str(profile.gamma)])
        if profile.autolevel:
            cmd.append("--autolevel")
        if not profile.autocontrast:
            cmd.append("--noautocontrast")
        if profile.colorautocontrast:
            cmd.append("--colorautocontrast")

    def _add_cropping_options(
        self, cmd: list[str], profile: KCCConversionProfile
    ) -> None:
        """Add cropping-related options.

        Parameters
        ----------
        cmd : list[str]
            Command list to append to.
        profile : KCCConversionProfile
            KCC conversion profile.
        """
        if profile.cropping is not None:
            cmd.extend(["-c", str(profile.cropping)])
        if profile.cropping_power is not None:
            cmd.extend(["--cp", str(profile.cropping_power)])
        if profile.preserve_margin is not None:
            cmd.extend(["--preservemargin", str(profile.preserve_margin)])
        if profile.cropping_minimum is not None:
            cmd.extend(["--cm", str(profile.cropping_minimum)])
        if profile.inter_panel_crop is not None:
            cmd.extend(["--ipc", str(profile.inter_panel_crop)])
        if profile.black_borders:
            cmd.append("--blackborders")
        if profile.white_borders:
            cmd.append("--whiteborders")

    def _add_output_options(
        self, cmd: list[str], profile: KCCConversionProfile
    ) -> None:
        """Add output format options.

        Parameters
        ----------
        cmd : list[str]
            Command list to append to.
        profile : KCCConversionProfile
            KCC conversion profile.
        """
        if profile.force_color:
            cmd.append("--forcecolor")
        if profile.force_png:
            cmd.append("--forcepng")
        if profile.mozjpeg:
            cmd.append("--mozjpeg")
        if profile.maximize_strips:
            cmd.append("--maximizestrips")
        if profile.splitter is not None:
            cmd.extend(["-r", str(profile.splitter)])
        if profile.target_size is not None:
            cmd.extend(["--ts", str(profile.target_size)])

    def _find_kcc_output(
        self,
        input_path: Path,
        target_format: str,
        output_path: Path,
    ) -> Path:
        """Find the output file created by KCC.

        KCC outputs files in the same directory as input with a specific naming pattern.

        Parameters
        ----------
        input_path : Path
            Original input file path.
        target_format : str
            Target format.
        output_path : Path
            Desired output path.

        Returns
        -------
        Path
            Path to the output file created by KCC.
        """
        # KCC outputs to input directory with format-specific naming
        input_dir = input_path.parent
        input_stem = input_path.stem

        # Map format to extension
        format_extensions = {
            "MOBI": "mobi",
            "AZW3": "mobi",  # KCC creates .mobi files that are dual MOBI/AZW3
            "EPUB": "epub",
            "KEPUB": "kepub.epub",
            "CBZ": "cbz",
            "PDF": "pdf",
            "KFX": "kfx",
        }

        ext = format_extensions.get(target_format.upper(), "mobi")

        # Try different naming patterns
        possible_names = [
            f"{input_stem}.{ext}",
            f"{input_path.name}.{ext}",
        ]

        for name in possible_names:
            candidate = input_dir / name
            if candidate.exists():
                return candidate

        # If not found, return the expected output path
        # (KCC might have used a different naming scheme)
        return output_path

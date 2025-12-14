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


def _raise_conversion_error(message: str) -> NoReturn:
    """Raise a conversion error with consistent chaining.

    Parameters
    ----------
    message : str
        Error message describing the conversion failure.

    Raises
    ------
    ConversionError
        Always raised.
    """
    raise ConversionError(message) from None


def _cleanup_output_file(output_path: Path) -> None:
    """Best-effort cleanup for partially written output file."""
    with suppress(OSError):
        if output_path.exists():
            output_path.unlink()


def _run_ebook_convert(
    *,
    converter_path: Path,
    input_path: Path,
    output_path: Path,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    """Run `ebook-convert` and normalize errors.

    Parameters
    ----------
    converter_path : Path
        Path to `ebook-convert` binary.
    input_path : Path
        Path to input file.
    output_path : Path
        Path to output file.
    timeout : int
        Timeout in seconds.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Completed process result.

    Raises
    ------
    ConversionError
        If the subprocess cannot be executed or times out.
    """
    cmd = [str(converter_path), str(input_path), str(output_path)]
    try:
        return subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        msg = f"Conversion timed out after {timeout} seconds"
        _raise_conversion_error(msg)
    except ConversionError:
        raise
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        msg = f"Conversion failed: {e!s}"
        _raise_conversion_error(msg)
    except Exception as e:  # noqa: BLE001
        # Defensive: tests (and potentially third-party subprocess wrappers)
        # can raise unexpected exceptions. Convert them to ConversionError.
        msg = f"Conversion failed: {e!s}"
        _raise_conversion_error(msg)


def _summarize_calibre_failure_output(output: str) -> str:
    """Summarize Calibre output into a user-friendly one-liner.

    Calibre failures often include long Python tracebacks (including many
    "During handling of the above exception..." blocks). Embedding that full
    traceback into exception messages creates very noisy logs when those
    exceptions are also logged with stack traces at higher layers.

    Parameters
    ----------
    output : str
        Raw stderr/stdout from `ebook-convert`.

    Returns
    -------
    str
        A concise failure summary.
    """
    text = (output or "").strip()
    if not text:
        return "Unknown conversion error"

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "Unknown conversion error"

    # Prefer the last non-empty line; this is commonly the actual error
    # (e.g. "calibre.ebooks.DRMError: <title>").
    last_line = lines[-1]

    # If the output ends with a separator or unhelpful marker, look upward
    # for something that looks like an error.
    if last_line.lower() in {"traceback (most recent call last):"}:
        for line in reversed(lines[:-1]):
            if "error" in line.lower() or ":" in line:
                return line
        return last_line

    return last_line


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
        try:
            cmd = [str(self._converter_path), str(input_path), str(output_path)]
            logger.debug("Running conversion: %s", " ".join(cmd))
            result = _run_ebook_convert(
                converter_path=self._converter_path,
                input_path=input_path,
                output_path=output_path,
                timeout=self._timeout,
            )

            if result.returncode != 0:
                raw_output = (result.stderr or result.stdout or "").strip()
                summary = _summarize_calibre_failure_output(raw_output)
                if raw_output:
                    # Keep full details available for debugging without
                    # embedding it into exception messages (which get logged
                    # again with stack traces in task orchestration layers).
                    logger.debug("ebook-convert failure output:\n%s", raw_output)
                msg = f"Conversion failed: {summary}"
                _raise_conversion_error(msg)

            if not output_path.exists():
                msg = "Conversion completed but output file not found"
                _raise_conversion_error(msg)

            logger.debug("Converted file saved to: %s", output_path)
        except ConversionError:
            # Cleanup and re-raise, preserving the message.
            _cleanup_output_file(output_path)
            raise
        except Exception as e:  # noqa: BLE001
            # Defensive catch for unexpected errors (tests may raise plain Exception).
            _cleanup_output_file(output_path)
            msg = f"Conversion failed: {e!s}"
            _raise_conversion_error(msg)
        else:
            return output_path

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

"""ZIP filename encoding detection for comic archives."""

from __future__ import annotations

import logging
import zipfile
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING

from bookcard.services.comic.archive.exceptions import (
    ArchiveCorruptedError,
    ArchiveReadError,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ZipEncodingProbeResult:
    """Result of a ZIP encoding probe.

    Attributes
    ----------
    encoding : str | None
        Encoding that successfully decoded archive filenames, or None if the
        default ZIP behavior was used.
    filenames : list[str]
        Filenames returned by the probe (raw names from the ZIP central directory).
    """

    encoding: str | None
    filenames: list[str]


class ZipEncodingDetector:
    """Detect a ZIP filename encoding by probing known encodings."""

    def __init__(self, encodings: tuple[str, ...]) -> None:
        """Create a detector.

        Parameters
        ----------
        encodings : tuple[str, ...]
            Candidate encodings to try.
        """
        self._encodings = encodings

    def probe_path(
        self,
        zip_path: Path,
        *,
        preferred: str | None = None,
    ) -> ZipEncodingProbeResult:
        """Probe encodings for a ZIP file on disk.

        Parameters
        ----------
        zip_path : Path
            Path to the ZIP file.
        preferred : str | None
            Preferred encoding to try first if present in the candidate set.

        Returns
        -------
        ZipEncodingProbeResult
            Probe result including the first successful encoding and filenames.

        Raises
        ------
        ArchiveCorruptedError
            If the file is not a valid ZIP archive.
        ArchiveReadError
            If the file cannot be read.
        """

        def open_zip(encoding: str | None) -> zipfile.ZipFile:
            if encoding is None:
                return zipfile.ZipFile(zip_path, "r")
            return zipfile.ZipFile(zip_path, "r", metadata_encoding=encoding)

        return self._probe(open_zip, preferred=preferred, label=str(zip_path))

    def probe_bytes(
        self,
        zip_bytes: bytes,
        *,
        preferred: str | None = None,
        label: str = "<bytes>",
    ) -> ZipEncodingProbeResult:
        """Probe encodings for a ZIP provided as bytes.

        Parameters
        ----------
        zip_bytes : bytes
            ZIP bytes.
        preferred : str | None
            Preferred encoding to try first.
        label : str
            Label used for debug logging.

        Returns
        -------
        ZipEncodingProbeResult
            Probe result.
        """

        def open_zip(encoding: str | None) -> zipfile.ZipFile:
            bio = BytesIO(zip_bytes)
            if encoding is None:
                return zipfile.ZipFile(bio, "r")
            return zipfile.ZipFile(bio, "r", metadata_encoding=encoding)

        return self._probe(open_zip, preferred=preferred, label=label)

    def _probe(
        self,
        opener: Callable[[str | None], zipfile.ZipFile],
        *,
        preferred: str | None,
        label: str,
    ) -> ZipEncodingProbeResult:
        encodings = list(self._encodings)
        if preferred and preferred in encodings:
            encodings.remove(preferred)
            encodings.insert(0, preferred)

        last_error: Exception | None = None
        for enc in encodings:
            try:
                with opener(enc) as zf:
                    names = zf.namelist()
                logger.debug("ZIP encoding probe succeeded: %s -> %s", label, enc)
                return ZipEncodingProbeResult(encoding=enc, filenames=names)
            except UnicodeDecodeError as e:
                logger.debug("ZIP encoding probe failed: %s -> %s (%s)", label, enc, e)
                last_error = e
            except zipfile.BadZipFile as e:
                msg = f"Invalid ZIP archive: {label}: {e}"
                raise ArchiveCorruptedError(msg) from e
            except OSError as e:
                msg = f"Failed to read ZIP archive: {label}: {e}"
                raise ArchiveReadError(msg) from e

        # Fall back to default ZIP behavior (no metadata override)
        try:
            with opener(None) as zf:
                names = zf.namelist()
            logger.debug("ZIP encoding probe used default behavior: %s", label)
            return ZipEncodingProbeResult(encoding=None, filenames=names)
        except zipfile.BadZipFile as e:
            msg = f"Invalid ZIP archive: {label}: {e}"
            raise ArchiveCorruptedError(msg) from e
        except OSError as e:
            msg = f"Failed to read ZIP archive: {label}: {e}"
            raise ArchiveReadError(msg) from e
        except UnicodeDecodeError as e:
            msg = f"Failed to decode ZIP filenames for {label}: {last_error}"
            raise ArchiveReadError(msg) from e

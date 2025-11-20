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

"""Parser for OpenLibrary dump files."""

import gzip
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from fundamental.services.tasks.openlibrary.models import DumpRecord

logger = logging.getLogger(__name__)


class DumpFileParser(ABC):
    """Abstract base class for parsing dump files.

    Follows the Open/Closed Principle - can be extended for different
    dump file formats without modifying existing code.
    """

    @abstractmethod
    def parse_line(self, line: str) -> DumpRecord | None:
        """Parse a single line from dump file.

        Parameters
        ----------
        line : str
            Line from dump file.

        Returns
        -------
        DumpRecord | None
            Parsed record or None if line is invalid.
        """
        ...

    def parse_file(self, file_path: Path) -> Iterator[DumpRecord]:
        """Parse entire file and yield records.

        Parameters
        ----------
        file_path : Path
            Path to dump file.

        Yields
        ------
        DumpRecord
            Parsed records from the file.

        Raises
        ------
        FileNotFoundError
            If file does not exist.
        Exception
            If file parsing fails.
        """
        if not file_path.exists():
            logger.warning("File not found: %s", file_path)
            return

        try:
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                for line in f:
                    record = self.parse_line(line)
                    if record:
                        yield record
        except Exception:
            logger.exception("Error parsing file %s", file_path)
            raise


class OpenLibraryDumpParser(DumpFileParser):
    r"""Parser for OpenLibrary dump files.

    Parses tab-separated dump files with format:
    type\tkey\trevision\tlast_modified\tjson
    """

    def parse_line(self, line: str) -> DumpRecord | None:
        r"""Parse a single line from dump file.

        Format: type\tkey\trevision\tlast_modified\tjson

        Parameters
        ----------
        line : str
            Line from dump file.

        Returns
        -------
        DumpRecord | None
            Parsed record or None if line is invalid.
        """
        parts = line.split("\t")
        if len(parts) < 5:
            return None

        try:
            record_type = parts[0]
            key = parts[1]
            revision_str = parts[2]
            last_modified_str = parts[3]
            json_str = parts[4]

            # Parse revision
            revision = int(revision_str) if revision_str else None

            # Parse last_modified date
            last_modified = None
            if last_modified_str:
                try:
                    # OpenLibrary uses ISO format: 2008-04-01T00:00:00
                    dt = datetime.fromisoformat(
                        last_modified_str.replace("Z", "+00:00")
                    )
                    last_modified = dt.date()
                except (ValueError, AttributeError):
                    pass

            # Parse JSON data
            data = json.loads(json_str)

            return DumpRecord(
                record_type=record_type,
                key=key,
                revision=revision,
                last_modified=last_modified,
                data=data,
            )
        except (json.JSONDecodeError, ValueError, IndexError):
            return None

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

"""Cover art extraction strategy for MOBI files.

Extracts cover image from MOBI files using coverOffset or thumbnailOffset
from EXTH headers, following the approach of foliate-js.
"""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING, BinaryIO

from fundamental.services.cover_extractors.base import CoverExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path


class MobiCoverExtractor(CoverExtractionStrategy):
    """Cover extraction strategy for MOBI files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is MOBI or AZW."""
        format_upper = file_format.upper().lstrip(".")
        return format_upper in ("MOBI", "AZW", "AZW3", "AZW4", "PRC")

    def extract_cover(self, file_path: Path) -> bytes | None:
        """Extract cover image from MOBI file.

        Parameters
        ----------
        file_path : Path
            Path to the MOBI file.

        Returns
        -------
        bytes | None
            Cover image data as bytes, or None if no cover found.
        """
        try:
            with file_path.open("rb") as mobi_file:
                # Check magic number
                mobi_file.seek(60)
                magic = mobi_file.read(8).decode("ascii", errors="ignore")
                if magic != "BOOKMOBI":
                    return None

                # Read PDB header
                mobi_file.seek(0)
                pdb_header = self._read_pdb_header(mobi_file)

                # Read record 0 (contains MOBI header)
                mobi_file.seek(78)
                record_offsets = []
                for _ in range(pdb_header["num_records"]):
                    offset = struct.unpack(">I", mobi_file.read(4))[0]
                    next_offset = struct.unpack(">I", mobi_file.read(4))[0]
                    record_offsets.append((offset, next_offset))

                # Read record 0
                record0_start, record0_end = record_offsets[0]
                mobi_file.seek(record0_start)
                record0 = mobi_file.read(record0_end - record0_start)

                # Parse MOBI header
                mobi_header = self._parse_mobi_header(record0)

                # Parse EXTH header if present
                exth_data = None
                exth_flag = mobi_header.get("exth_flag", 0)
                if isinstance(exth_flag, int) and exth_flag & 0b1000000:
                    exth_offset = mobi_header["length"] + 16
                    if exth_offset < len(record0):
                        exth_data = self._parse_exth_header(
                            record0[exth_offset:], mobi_header["encoding"]
                        )

                # Extract cover offset (following foliate-js: coverOffset ?? thumbnailOffset)
                cover_offset = None
                if exth_data:
                    cover_offset = exth_data.get("coverOffset")
                    if cover_offset is None or cover_offset >= 0xFFFFFFFF:
                        cover_offset = exth_data.get("thumbnailOffset")
                        if cover_offset is not None and cover_offset >= 0xFFFFFFFF:
                            cover_offset = None

                if cover_offset is None:
                    return None

                # Load cover resource at offset
                return self._load_resource(mobi_file, record_offsets, cover_offset)
        except (ValueError, struct.error, OSError, KeyError):
            return None

    def _read_pdb_header(self, file: BinaryIO) -> dict:
        """Read PDB (Palm Database) header."""
        name = file.read(32).rstrip(b"\x00").decode("ascii", errors="ignore")
        file.seek(60)
        file_type = file.read(4).decode("ascii", errors="ignore")
        file.seek(76)
        num_records = struct.unpack(">H", file.read(2))[0]
        return {
            "name": name,
            "type": file_type,
            "num_records": num_records,
        }

    def _parse_mobi_header(self, record0: bytes) -> dict:
        """Parse MOBI header from record 0."""
        if len(record0) < 244:
            msg = "Record 0 too short for MOBI header"
            raise ValueError(msg)

        magic = record0[16:20].decode("ascii", errors="ignore")
        if magic != "MOBI":
            msg = f"Invalid MOBI header: magic is {magic!r}"
            raise ValueError(msg)

        length = struct.unpack(">I", record0[20:24])[0]
        encoding = struct.unpack(">I", record0[28:32])[0]
        exth_flag = struct.unpack(">I", record0[128:132])[0]

        return {
            "magic": magic,
            "length": length,
            "encoding": encoding,
            "exth_flag": exth_flag,
        }

    def _parse_exth_header(self, exth_data: bytes, _encoding: int) -> dict:
        """Parse EXTH (Extended Header) records."""
        if len(exth_data) < 12:
            return {}

        magic = exth_data[0:4].decode("ascii", errors="ignore")
        if magic != "EXTH":
            return {}

        count = struct.unpack(">I", exth_data[8:12])[0]
        results: dict = {}
        offset = 12

        for _ in range(count):
            if offset + 8 > len(exth_data):
                break

            record_type = struct.unpack(">I", exth_data[offset : offset + 4])[0]
            record_length = struct.unpack(">I", exth_data[offset + 4 : offset + 8])[0]

            # Extract coverOffset (201) or thumbnailOffset (202)
            if record_type in (201, 202):
                field_name = "coverOffset" if record_type == 201 else "thumbnailOffset"
                data = exth_data[offset + 8 : offset + record_length]
                if len(data) >= 4:
                    value = struct.unpack(">I", data[:4])[0]
                    results[field_name] = value

            offset += record_length

        return results

    def _load_resource(
        self, mobi_file: BinaryIO, record_offsets: list[tuple[int, int]], offset: int
    ) -> bytes | None:
        """Load resource at given offset.

        Following foliate-js: this.loadResource(offset)
        """
        # Find which record contains the offset
        for _record_idx, (record_start, record_end) in enumerate(record_offsets):
            if record_start <= offset < record_end:
                # Offset is relative to record start
                relative_offset = offset - record_start
                mobi_file.seek(record_start + relative_offset)
                # Read remaining bytes in record (or reasonable chunk)
                remaining = record_end - (record_start + relative_offset)
                # For images, we need to read the full resource
                # This is a simplified version - in practice, you'd parse the image format
                return mobi_file.read(min(remaining, 10 * 1024 * 1024))  # Max 10MB

        return None

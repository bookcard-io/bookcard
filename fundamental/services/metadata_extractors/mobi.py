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

"""Metadata extraction strategy for MOBI files.

Implements MOBI metadata extraction following the approach of foliate-js,
supporting both MOBI and KF8 (AZW3) formats.

This implementation is based on the MOBI metadata extraction logic from
foliate-js (https://github.com/johnfactotum/foliate-js.git), adapted for
Python and integrated into this project's metadata extraction framework.
"""

from __future__ import annotations

import html
import struct
from datetime import UTC, datetime
from typing import TYPE_CHECKING, BinaryIO

from fundamental.services.book_metadata import BookMetadata, Contributor
from fundamental.services.metadata_extractors.base import MetadataExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path

# MOBI encoding constants
MOBI_ENCODING = {
    1252: "windows-1252",
    65001: "utf-8",
}

# EXTH record types (from foliate-js)
EXTH_RECORD_TYPE = {
    100: ("creator", True),  # Array of strings
    101: ("publisher", False),
    103: ("description", False),
    104: ("isbn", False),
    105: ("subject", True),  # Array of strings
    106: ("date", False),
    108: ("contributor", True),  # Array of strings
    109: ("rights", False),
    110: ("subjectCode", True),  # Array of strings
    112: ("source", True),  # Array of strings
    113: ("asin", False),
    201: ("coverOffset", False),  # uint offset
    202: ("thumbnailOffset", False),  # uint offset
    503: ("title", False),
    524: ("language", True),  # Array of strings
}

# MOBI language codes (subset from foliate-js)
MOBI_LANG = {
    1: ["ar", "ar-SA", "ar-IQ", "ar-EG"],
    2: ["bg"],
    3: ["ca"],
    4: ["zh", "zh-TW", "zh-CN", "zh-HK"],
    5: ["cs"],
    6: ["da"],
    7: ["de", "de-DE", "de-CH", "de-AT"],
    8: ["el"],
    9: ["en", "en-US", "en-GB", "en-AU", "en-CA"],
    10: ["es", "es-ES", "es-MX"],
    11: ["fi"],
    12: ["fr", "fr-FR", "fr-BE", "fr-CA"],
    13: ["he"],
    14: ["hu"],
    15: ["is"],
    16: ["it", "it-IT"],
    17: ["ja"],
    18: ["ko"],
    19: ["nl", "nl-NL"],
    20: ["no", "nb", "nn"],
    21: ["pl"],
    22: ["pt", "pt-BR", "pt-PT"],
    23: ["ro"],
    24: ["ru"],
    25: ["hr", "sr"],
    26: ["sk"],
    27: ["sv", "sv-SE"],
    28: ["th"],
    29: ["tr"],
    30: ["ur"],
    31: ["id"],
    32: ["uk"],
    33: ["be"],
    34: ["sl"],
    35: ["et"],
    36: ["lv"],
    37: ["lt"],
    38: ["fa"],
    39: ["vi"],
}


class MobiMetadataExtractor(MetadataExtractionStrategy):
    """Metadata extraction strategy for MOBI files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is MOBI or AZW."""
        format_upper = file_format.upper().lstrip(".")
        return format_upper in ("MOBI", "AZW", "AZW3", "AZW4", "PRC")

    def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
        """Extract metadata from MOBI file.

        Parameters
        ----------
        file_path : Path
            Path to the MOBI file.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.

        Raises
        ------
        ValueError
            If file is not a valid MOBI file or parsing fails.
        """
        with file_path.open("rb") as mobi_file:
            # Check magic number
            mobi_file.seek(60)
            magic = mobi_file.read(8).decode("ascii", errors="ignore")
            if magic != "BOOKMOBI":
                msg = (
                    f"Invalid MOBI file: magic number is {magic!r}, expected 'BOOKMOBI'"
                )
                raise ValueError(msg)

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

            # Extract metadata
            return self._build_metadata(mobi_header, exth_data, original_filename)

    def _read_pdb_header(self, file: BinaryIO) -> dict:
        """Read PDB (Palm Database) header.

        Parameters
        ----------
        file : file
            File object positioned at start.

        Returns
        -------
        dict
            PDB header fields.
        """
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
        """Parse MOBI header from record 0.

        Parameters
        ----------
        record0 : bytes
            Record 0 data.

        Returns
        -------
        dict
            MOBI header fields.
        """
        if len(record0) < 244:
            msg = "Record 0 too short for MOBI header"
            raise ValueError(msg)

        # Read MOBI header (starts at offset 16)
        magic = record0[16:20].decode("ascii", errors="ignore")
        if magic != "MOBI":
            msg = f"Invalid MOBI header: magic is {magic!r}"
            raise ValueError(msg)

        length = struct.unpack(">I", record0[20:24])[0]
        mobi_type = struct.unpack(">I", record0[24:28])[0]
        encoding = struct.unpack(">I", record0[28:32])[0]
        uid = struct.unpack(">I", record0[32:36])[0]
        version = struct.unpack(">I", record0[36:40])[0]
        title_offset = struct.unpack(">I", record0[84:88])[0]
        title_length = struct.unpack(">I", record0[88:92])[0]
        locale_region = record0[94]
        locale_language = record0[95]
        exth_flag = struct.unpack(">I", record0[128:132])[0]

        # Extract title
        title_bytes = record0[title_offset : title_offset + title_length]

        # Get language
        language = self._get_language(locale_language, locale_region)

        # Decode title
        encoding_name = MOBI_ENCODING.get(encoding, "utf-8")
        try:
            title = title_bytes.decode(encoding_name)
        except UnicodeDecodeError:
            title = title_bytes.decode("utf-8", errors="replace")

        return {
            "magic": magic,
            "length": length,
            "type": mobi_type,
            "encoding": encoding,
            "uid": uid,
            "version": version,
            "title": title,
            "language": language,
            "exth_flag": exth_flag,
            "encoding_name": encoding_name,
        }

    def _parse_exth_header(self, exth_data: bytes, encoding: int) -> dict:
        """Parse EXTH (Extended Header) records.

        Parameters
        ----------
        exth_data : bytes
            EXTH header data.
        encoding : int
            MOBI encoding code.

        Returns
        -------
        dict
            EXTH record fields.
        """
        if len(exth_data) < 12:
            return {}

        magic = exth_data[0:4].decode("ascii", errors="ignore")
        if magic != "EXTH":
            return {}

        count = struct.unpack(">I", exth_data[8:12])[0]

        encoding_name = MOBI_ENCODING.get(encoding, "utf-8")
        results: dict = {}
        offset = 12

        for _ in range(count):
            if offset + 8 > len(exth_data):
                break

            record_type = struct.unpack(">I", exth_data[offset : offset + 4])[0]
            record_length = struct.unpack(">I", exth_data[offset + 4 : offset + 8])[0]

            if record_type in EXTH_RECORD_TYPE:
                field_name, is_array = EXTH_RECORD_TYPE[record_type]
                data = exth_data[offset + 8 : offset + record_length]

                try:
                    if record_type in (201, 202):  # coverOffset, thumbnailOffset (uint)
                        value = struct.unpack(">I", data[:4])[0]
                    else:
                        # String value
                        value = data.rstrip(b"\x00").decode(
                            encoding_name, errors="replace"
                        )
                        value = html.unescape(value)

                    if is_array:
                        if field_name not in results:
                            results[field_name] = []
                        results[field_name].append(value)
                    else:
                        results[field_name] = value
                except (UnicodeDecodeError, struct.error):
                    pass

            offset += record_length

        return results

    def _get_language(self, locale_language: int, locale_region: int) -> str | None:
        """Get language code from MOBI locale.

        Parameters
        ----------
        locale_language : int
            Language code from MOBI header.
        locale_region : int
            Region code from MOBI header.

        Returns
        -------
        str | None
            Language code (e.g., 'en', 'en-US') or None.
        """
        lang_list = MOBI_LANG.get(locale_language)
        if not lang_list:
            return None

        # Region is encoded in upper 6 bits
        region_index = locale_region >> 2
        if region_index < len(lang_list) and lang_list[region_index]:
            return lang_list[region_index]

        # Fallback to first language in list
        return lang_list[0] if lang_list else None

    @staticmethod
    def _normalize_list(value: list | str | None) -> list:
        """Normalize value to list.

        Parameters
        ----------
        value : list | str | None
            Value to normalize.

        Returns
        -------
        list
            List of values.
        """
        if not value:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _extract_languages(self, exth: dict, mobi_header: dict) -> list[str]:
        """Extract languages from EXTH or MOBI header.

        Parameters
        ----------
        exth : dict
            EXTH header data.
        mobi_header : dict
            MOBI header data.

        Returns
        -------
        list[str]
            List of language codes.
        """
        languages = []
        exth_lang = exth.get("language")
        if exth_lang:
            if isinstance(exth_lang, list):
                languages.extend(exth_lang)
            else:
                languages.append(exth_lang)
        elif mobi_header.get("language"):
            languages.append(mobi_header["language"])
        return languages

    def _extract_identifiers(
        self, mobi_header: dict, exth: dict
    ) -> list[dict[str, str]]:
        """Extract identifiers from MOBI and EXTH headers.

        Parameters
        ----------
        mobi_header : dict
            MOBI header data.
        exth : dict
            EXTH header data.

        Returns
        -------
        list[dict[str, str]]
            List of identifier dictionaries.
        """
        identifiers = []
        if mobi_header.get("uid"):
            identifiers.append({"type": "mobi", "val": str(mobi_header["uid"])})
        if exth.get("isbn"):
            identifiers.append({"type": "isbn", "val": exth["isbn"]})
        if exth.get("asin"):
            identifiers.append({"type": "asin", "val": exth["asin"]})
        return identifiers

    def _extract_pubdate(self, exth: dict) -> datetime | None:
        """Extract publication date from EXTH header.

        Parameters
        ----------
        exth : dict
            EXTH header data.

        Returns
        -------
        datetime | None
            Publication date or None.
        """
        date_str = exth.get("date")
        if date_str:
            return self._parse_date(date_str)
        return None

    def _build_metadata(
        self, mobi_header: dict, exth_data: dict | None, original_filename: str
    ) -> BookMetadata:
        """Build BookMetadata from MOBI and EXTH headers.

        Parameters
        ----------
        mobi_header : dict
            Parsed MOBI header.
        exth_data : dict | None
            Parsed EXTH header data.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        exth = exth_data or {}

        # Title: prefer EXTH title, fallback to MOBI title
        title = exth.get("title") or mobi_header.get("title") or original_filename

        # Author: from EXTH creator (array)
        authors = self._normalize_list(exth.get("creator", []))
        primary_author = authors[0] if authors else "Unknown"

        # Contributors
        contributors = [Contributor(name=author, role="author") for author in authors]

        # Add EXTH contributors
        exth_contributors = self._normalize_list(exth.get("contributor", []))
        contributors.extend(
            Contributor(name=contrib, role="contributor")
            for contrib in exth_contributors
        )

        # Publisher
        publisher = exth.get("publisher")

        # Description
        description = exth.get("description") or ""

        # Language: prefer EXTH language, fallback to MOBI language
        languages = self._extract_languages(exth, mobi_header)

        # Tags (subjects)  # noqa: ERA001
        tags = self._normalize_list(exth.get("subject", []))

        # Identifiers
        identifiers = self._extract_identifiers(mobi_header, exth)

        # Publication date
        pubdate = self._extract_pubdate(exth)

        # Rights
        rights = exth.get("rights")

        return BookMetadata(
            title=title,
            author=primary_author,
            description=description,
            tags=tags,
            publisher=publisher,
            pubdate=pubdate,
            languages=languages,
            identifiers=identifiers,
            contributors=contributors,
            rights=rights,
        )

    def _parse_date(self, date_str: str) -> datetime | None:
        """Parse publication date string.

        Parameters
        ----------
        date_str : str
            Date string from EXTH.

        Returns
        -------
        datetime | None
            Parsed datetime or None.
        """
        if not date_str:
            return None

        # Try common date formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m",
            "%Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
        ]

        for fmt in formats:
            try:
                if len(date_str) >= len(
                    fmt.replace("%", "").replace("T", "").replace("Z", "")
                ):
                    return datetime.strptime(date_str[: len(fmt)], fmt).replace(
                        tzinfo=UTC
                    )
            except (ValueError, TypeError):
                continue

        return None

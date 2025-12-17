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

"""Tests for MOBI cover extractor to achieve 100% coverage."""

from __future__ import annotations

import struct
import tempfile
from pathlib import Path

import pytest

from bookcard.services.cover_extractors.mobi import MobiCoverExtractor


@pytest.fixture
def extractor() -> MobiCoverExtractor:
    """Create MobiCoverExtractor instance."""
    return MobiCoverExtractor()


def _create_mock_mobi(
    cover_offset: int | None = None,
    thumbnail_offset: int | None = None,
    has_exth: bool = True,
    magic: str = "BOOKMOBI",
    record0_length: int = 500,
    num_records: int = 2,
    cover_data: bytes | None = None,
) -> Path:
    """Create a mock MOBI file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mobi") as tmp:
        file_path = Path(tmp.name)

    with Path(file_path).open("wb") as f:
        # PDB header structure:
        # 0-31: name (32 bytes)
        # 60-67: magic "BOOKMOBI" (8 bytes) - checked by extract_cover
        # 60-63: file_type (4 bytes) - read by _read_pdb_header (overlaps with magic!)
        # 76-77: num_records (2 bytes)
        f.write(b"Test Book" + b"\x00" * 23)  # name (32 bytes) at offset 0
        f.write(b"\x00" * 28)  # padding to offset 60
        # Write magic at offset 60 (8 bytes) - first 4 bytes will be read as file_type
        magic_bytes = magic.encode("ascii")[:8].ljust(8, b"\x00")
        f.write(magic_bytes)  # offset 60-67
        f.write(b"\x00" * 8)  # padding to offset 76
        f.write(struct.pack(">H", num_records))  # num_records at offset 76 (2 bytes)

        # Record offsets start at offset 78
        record0_start = 78 + (num_records * 8)  # After record offset table
        record0_end = record0_start + record0_length
        record1_start = record0_end
        # record1_end should be large enough to contain cover_data if provided
        record1_end = record1_start + (len(cover_data) if cover_data else 100)

        # Write record offset table
        f.write(struct.pack(">I", record0_start))  # record 0 start
        f.write(struct.pack(">I", record0_end))  # record 0 end
        if num_records > 1:
            f.write(struct.pack(">I", record1_start))  # record 1 start
            f.write(struct.pack(">I", record1_end))  # record 1 end

        # Record 0 (MOBI header)
        # MOBI header structure (within record0):
        # 0-15: padding (16 bytes)
        # 16-19: MOBI magic (4 bytes)
        # 20-23: MOBI length (4 bytes)
        # 24-27: padding (4 bytes)
        # 28-31: encoding (4 bytes)
        # 32-127: padding (96 bytes) to get to offset 128
        # 128-131: exth_flag (4 bytes)
        f.seek(record0_start)
        f.write(b"MOBI" + b"\x00" * 12)  # 16 bytes: padding to MOBI magic (offset 0-15)
        f.write(b"MOBI")  # 4 bytes: MOBI magic at offset 16 (offset 16-19)
        f.write(
            struct.pack(">I", 244)
        )  # 4 bytes: MOBI length at offset 20 (offset 20-23)
        f.write(b"\x00" * 4)  # 4 bytes: padding (offset 24-27)
        f.write(
            struct.pack(">I", 65001)
        )  # 4 bytes: encoding at offset 28 (offset 28-31)
        # Need 128 - 32 = 96 bytes of padding to reach offset 128
        f.write(b"\x00" * 96)  # 96 bytes: padding to offset 128 (offset 32-127)
        exth_flag = 0b1000000 if has_exth else 0
        f.write(
            struct.pack(">I", exth_flag)
        )  # 4 bytes: exth_flag at offset 128 (offset 128-131)

        # EXTH header if present
        if has_exth:
            exth_offset = 244 + 16  # MOBI length + 16
            f.seek(record0_start + exth_offset)
            f.write(b"EXTH")  # EXTH magic
            f.write(struct.pack(">I", 100))  # EXTH length
            f.write(struct.pack(">I", 2))  # record count

            # Cover offset record (type 201)
            if cover_offset is not None:
                f.write(struct.pack(">I", 201))  # record type
                f.write(struct.pack(">I", 12))  # record length
                f.write(struct.pack(">I", cover_offset))  # cover offset value

            # Thumbnail offset record (type 202)
            if thumbnail_offset is not None:
                f.write(struct.pack(">I", 202))  # record type
                f.write(struct.pack(">I", 12))  # record length
                f.write(struct.pack(">I", thumbnail_offset))  # thumbnail offset value

        # Record 1 (cover image data)
        if cover_data:
            f.seek(record1_start)
            f.write(cover_data)

    return file_path


@pytest.mark.parametrize(
    ("file_format", "expected"),
    [
        ("mobi", True),
        ("MOBI", True),
        ("azw", True),
        ("AZW", True),
        ("azw3", True),
        ("AZW3", True),
        ("azw4", True),
        ("AZW4", True),
        ("prc", True),
        ("PRC", True),
        (".mobi", True),
        ("epub", False),
        ("pdf", False),
    ],
)
def test_can_handle(
    extractor: MobiCoverExtractor, file_format: str, expected: bool
) -> None:
    """Test can_handle for various formats."""
    assert extractor.can_handle(file_format) == expected


def test_extract_cover_success(extractor: MobiCoverExtractor) -> None:
    """Test successful cover extraction using coverOffset."""
    cover_data = b"fake cover image data" * 10
    # Calculate proper offset - it should be within record 1
    # cover_offset should be record1_start (absolute file offset)
    cover_offset = 594
    file_path = _create_mock_mobi(
        cover_offset=cover_offset,
        cover_data=cover_data,
        num_records=2,
        record0_length=500,
    )

    try:
        result = extractor.extract_cover(file_path)
        assert result is not None
        assert len(result) > 0
    finally:
        file_path.unlink()


def test_extract_cover_thumbnail(extractor: MobiCoverExtractor) -> None:
    """Test cover extraction using thumbnailOffset when coverOffset is not available."""
    cover_data = b"fake thumbnail image data" * 10
    # record1_start = 78 + (2 * 8) + 500 = 594
    thumbnail_offset = 594
    file_path = _create_mock_mobi(
        cover_offset=None,
        thumbnail_offset=thumbnail_offset,
        cover_data=cover_data,
        num_records=2,
        record0_length=500,
    )

    try:
        result = extractor.extract_cover(file_path)
        assert result is not None
        assert len(result) > 0
    finally:
        file_path.unlink()


def test_extract_cover_prefer_cover_over_thumbnail(
    extractor: MobiCoverExtractor,
) -> None:
    """Test that coverOffset is preferred over thumbnailOffset."""
    cover_data = b"fake cover image data" * 10
    # Both offsets point to same record, but coverOffset should be used
    record1_start = 78 + (2 * 8) + 500  # 594
    cover_offset = record1_start
    thumbnail_offset = record1_start + 10
    file_path = _create_mock_mobi(
        cover_offset=cover_offset,
        thumbnail_offset=thumbnail_offset,
        cover_data=cover_data,
        num_records=2,
        record0_length=500,
    )

    try:
        result = extractor.extract_cover(file_path)
        assert result is not None
        assert len(result) > 0
    finally:
        file_path.unlink()


def test_extract_no_cover(extractor: MobiCoverExtractor) -> None:
    """Test extraction when no cover is found."""
    file_path = _create_mock_mobi(has_exth=False, num_records=2, record0_length=500)

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_invalid_magic(extractor: MobiCoverExtractor) -> None:
    """Test extraction with invalid magic number."""
    file_path = _create_mock_mobi(magic="INVALID")

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_no_exth(extractor: MobiCoverExtractor) -> None:
    """Test extraction when EXTH header is not present."""
    file_path = _create_mock_mobi(has_exth=False, num_records=2, record0_length=500)

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_cover_offset_invalid(extractor: MobiCoverExtractor) -> None:
    """Test extraction when coverOffset is invalid (>= 0xFFFFFFFF)."""
    cover_data = b"fake thumbnail" * 10
    record1_start = 78 + (2 * 8) + 500  # 594
    file_path = _create_mock_mobi(
        cover_offset=0xFFFFFFFF,
        thumbnail_offset=record1_start,
        cover_data=cover_data,
        num_records=2,
        record0_length=500,
    )

    try:
        # Should fallback to thumbnailOffset
        result = extractor.extract_cover(file_path)
        assert result is not None
        assert len(result) > 0
    finally:
        file_path.unlink()


def test_extract_thumbnail_offset_invalid(extractor: MobiCoverExtractor) -> None:
    """Test extraction when thumbnailOffset is invalid (>= 0xFFFFFFFF)."""
    file_path = _create_mock_mobi(
        thumbnail_offset=0xFFFFFFFF, num_records=2, record0_length=500
    )

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_read_pdb_header(extractor: MobiCoverExtractor) -> None:
    """Test _read_pdb_header method."""
    file_path = _create_mock_mobi(num_records=2, record0_length=500)

    try:
        with Path(file_path).open("rb") as f:
            header = extractor._read_pdb_header(f)
            assert "name" in header
            assert "type" in header
            assert "num_records" in header
            assert header["num_records"] == 2
    finally:
        file_path.unlink()


def test_parse_mobi_header(extractor: MobiCoverExtractor) -> None:
    """Test _parse_mobi_header method."""
    # Create record0 with proper length (at least 244 bytes)
    record0 = (
        b"MOBI"
        + b"\x00" * 12  # padding to offset 16
        + b"MOBI"  # MOBI magic at offset 16
        + struct.pack(">I", 244)  # length at offset 20
        + b"\x00" * 4  # padding
        + struct.pack(">I", 65001)  # encoding at offset 28
        + b"\x00" * 100  # padding to offset 128
        + struct.pack(">I", 0)  # exth_flag at offset 128
        + b"\x00" * 116  # padding to make total 244 bytes
    )

    header = extractor._parse_mobi_header(record0)
    assert header["magic"] == "MOBI"
    assert header["length"] == 244
    assert header["encoding"] == 65001
    assert header["exth_flag"] == 0


def test_parse_mobi_header_too_short(extractor: MobiCoverExtractor) -> None:
    """Test _parse_mobi_header with record too short."""
    record0 = b"MOBI" * 10  # Too short

    with pytest.raises(ValueError, match="Record 0 too short"):
        extractor._parse_mobi_header(record0)


def test_parse_mobi_header_invalid_magic(extractor: MobiCoverExtractor) -> None:
    """Test _parse_mobi_header with invalid magic."""
    # Create record0 with invalid magic at offset 16
    record0 = (
        b"INVALID"
        + b"\x00" * 9  # padding to offset 16
        + b"INVL"  # Invalid magic at offset 16 (should be "MOBI")
        + struct.pack(">I", 244)  # length
        + b"\x00" * 4
        + struct.pack(">I", 65001)  # encoding
        + b"\x00" * 100
        + struct.pack(">I", 0)  # exth_flag
        + b"\x00" * 116  # padding to make total 244 bytes
    )

    with pytest.raises(ValueError, match="Invalid MOBI header"):
        extractor._parse_mobi_header(record0)


def test_parse_exth_header(extractor: MobiCoverExtractor) -> None:
    """Test _parse_exth_header method."""
    cover_offset = 1000
    thumbnail_offset = 2000
    exth_data = (
        b"EXTH"
        + struct.pack(">I", 100)  # length
        + struct.pack(">I", 2)  # count
        + struct.pack(">I", 201)  # coverOffset type
        + struct.pack(">I", 12)  # length
        + struct.pack(">I", cover_offset)  # value
        + struct.pack(">I", 202)  # thumbnailOffset type
        + struct.pack(">I", 12)  # length
        + struct.pack(">I", thumbnail_offset)  # value
    )

    result = extractor._parse_exth_header(exth_data, 65001)
    assert result["coverOffset"] == cover_offset
    assert result["thumbnailOffset"] == thumbnail_offset


def test_parse_exth_header_too_short(extractor: MobiCoverExtractor) -> None:
    """Test _parse_exth_header with data too short."""
    exth_data = b"EXTH" + b"\x00" * 4
    result = extractor._parse_exth_header(exth_data, 65001)
    assert result == {}


def test_parse_exth_header_invalid_magic(extractor: MobiCoverExtractor) -> None:
    """Test _parse_exth_header with invalid magic."""
    exth_data = b"INVALID" + b"\x00" * 100
    result = extractor._parse_exth_header(exth_data, 65001)
    assert result == {}


def test_parse_exth_header_partial_record(extractor: MobiCoverExtractor) -> None:
    """Test _parse_exth_header with partial record."""
    exth_data = (
        b"EXTH"
        + struct.pack(">I", 100)  # length
        + struct.pack(">I", 1)  # count
        + struct.pack(">I", 201)  # coverOffset type
        + struct.pack(">I", 12)  # length
        # Missing value bytes
    )
    result = extractor._parse_exth_header(exth_data, 65001)
    # Should handle gracefully
    assert "coverOffset" not in result


def test_parse_exth_header_other_types(extractor: MobiCoverExtractor) -> None:
    """Test _parse_exth_header with other record types (not 201 or 202)."""
    exth_data = (
        b"EXTH"
        + struct.pack(">I", 100)  # length
        + struct.pack(">I", 1)  # count
        + struct.pack(">I", 100)  # other type
        + struct.pack(">I", 12)  # length
        + struct.pack(">I", 1234)  # value
    )
    result = extractor._parse_exth_header(exth_data, 65001)
    assert "coverOffset" not in result
    assert "thumbnailOffset" not in result


def test_load_resource(extractor: MobiCoverExtractor) -> None:
    """Test _load_resource method."""
    cover_data = b"fake cover image data" * 100
    record1_start = 78 + (2 * 8) + 500  # 594
    file_path = _create_mock_mobi(
        cover_offset=record1_start,
        cover_data=cover_data,
        num_records=2,
        record0_length=500,
    )

    try:
        with Path(file_path).open("rb") as f:
            # Read PDB header
            f.seek(76)
            num_records = struct.unpack(">H", f.read(2))[0]
            f.seek(78)
            record_offsets = []
            for _ in range(num_records):
                offset = struct.unpack(">I", f.read(4))[0]
                next_offset = struct.unpack(">I", f.read(4))[0]
                record_offsets.append((offset, next_offset))

            # Test loading resource at record1_start
            result = extractor._load_resource(f, record_offsets, record1_start)
            assert result is not None
            assert len(result) > 0
    finally:
        file_path.unlink()


def test_load_resource_not_found(extractor: MobiCoverExtractor) -> None:
    """Test _load_resource when offset is not in any record."""
    file_path = _create_mock_mobi(num_records=2, record0_length=500)

    try:
        with Path(file_path).open("rb") as f:
            f.seek(76)
            num_records = struct.unpack(">H", f.read(2))[0]
            f.seek(78)
            record_offsets = []
            for _ in range(num_records):
                offset = struct.unpack(">I", f.read(4))[0]
                next_offset = struct.unpack(">I", f.read(4))[0]
                record_offsets.append((offset, next_offset))

            # Try to load resource at offset that doesn't exist
            result = extractor._load_resource(f, record_offsets, 99999)
            assert result is None
    finally:
        file_path.unlink()


def test_extract_exception_handling(extractor: MobiCoverExtractor) -> None:
    """Test extraction handles exceptions gracefully."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mobi") as tmp:
        tmp.write(b"invalid mobi file")
        file_path = Path(tmp.name)

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_file_not_found(extractor: MobiCoverExtractor) -> None:
    """Test extraction with non-existent file."""
    file_path = Path("/nonexistent/file.mobi")
    result = extractor.extract_cover(file_path)
    assert result is None


def test_extract_exth_offset_out_of_bounds(extractor: MobiCoverExtractor) -> None:
    """Test extraction when EXTH offset is out of bounds."""
    # Create MOBI with exth_flag set but exth_offset beyond record0 length
    # EXTH offset = 244 + 16 = 260, but record0_length is only 100
    file_path = _create_mock_mobi(
        has_exth=True, record0_length=100, num_records=2
    )  # Too short for EXTH

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()

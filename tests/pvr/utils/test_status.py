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

"""Tests for download status utilities."""

import pytest

from bookcard.pvr.utils.status import (
    DownloadStatus,
    StatusMapper,
    StatusMappingPresets,
)

# ============================================================================
# DownloadStatus Tests
# ============================================================================


class TestDownloadStatus:
    """Test DownloadStatus enum."""

    @pytest.mark.parametrize(
        "status",
        [
            DownloadStatus.COMPLETED,
            DownloadStatus.DOWNLOADING,
            DownloadStatus.PAUSED,
            DownloadStatus.QUEUED,
            DownloadStatus.FAILED,
            DownloadStatus.SEEDING,
            DownloadStatus.STALLED,
            DownloadStatus.CHECKING,
            DownloadStatus.METADATA,
        ],
    )
    def test_download_status_values(self, status: DownloadStatus) -> None:
        """Test all DownloadStatus enum values."""
        assert isinstance(status, str)
        assert status in [
            "completed",
            "downloading",
            "paused",
            "queued",
            "failed",
            "seeding",
            "stalled",
            "checking",
            "metadata",
        ]


# ============================================================================
# StatusMapper Tests
# ============================================================================


class TestStatusMapperInit:
    """Test StatusMapper initialization."""

    def test_init_no_mappings(self) -> None:
        """Test StatusMapper initialization with no mappings."""
        mapper = StatusMapper()
        assert mapper._mappings == {}
        assert mapper._default == DownloadStatus.DOWNLOADING
        assert mapper._rules == []

    def test_init_with_mappings(self) -> None:
        """Test StatusMapper initialization with mappings."""
        mappings = {
            "uploading": DownloadStatus.COMPLETED,
            "downloading": DownloadStatus.DOWNLOADING,
            6: DownloadStatus.COMPLETED,
        }
        mapper = StatusMapper(mappings)
        assert mapper._mappings == mappings
        assert mapper._default == DownloadStatus.DOWNLOADING

    def test_init_with_custom_default(self) -> None:
        """Test StatusMapper initialization with custom default."""
        mapper = StatusMapper(default=DownloadStatus.PAUSED)
        assert mapper._default == DownloadStatus.PAUSED

    def test_init_with_mappings_and_default(self) -> None:
        """Test StatusMapper initialization with mappings and custom default."""
        mappings = {"test": DownloadStatus.COMPLETED}
        mapper = StatusMapper(mappings, default=DownloadStatus.FAILED)
        assert mapper._mappings == mappings
        assert mapper._default == DownloadStatus.FAILED


class TestStatusMapperAddMapping:
    """Test StatusMapper.add_mapping method."""

    def test_add_mapping_string_key(self) -> None:
        """Test add_mapping with string key."""
        mapper = StatusMapper()
        result = mapper.add_mapping("uploading", DownloadStatus.COMPLETED)
        assert result is mapper
        assert mapper._mappings["uploading"] == DownloadStatus.COMPLETED

    def test_add_mapping_int_key(self) -> None:
        """Test add_mapping with integer key."""
        mapper = StatusMapper()
        result = mapper.add_mapping(6, DownloadStatus.COMPLETED)
        assert result is mapper
        assert mapper._mappings[6] == DownloadStatus.COMPLETED

    def test_add_mapping_overwrites_existing(self) -> None:
        """Test add_mapping overwrites existing mapping."""
        mapper = StatusMapper()
        mapper.add_mapping("test", DownloadStatus.DOWNLOADING)
        mapper.add_mapping("test", DownloadStatus.COMPLETED)
        assert mapper._mappings["test"] == DownloadStatus.COMPLETED

    def test_add_mapping_fluent_chaining(self) -> None:
        """Test add_mapping supports fluent chaining."""
        mapper = StatusMapper()
        mapper.add_mapping("a", DownloadStatus.COMPLETED).add_mapping(
            "b", DownloadStatus.DOWNLOADING
        )
        assert mapper._mappings["a"] == DownloadStatus.COMPLETED
        assert mapper._mappings["b"] == DownloadStatus.DOWNLOADING


class TestStatusMapperAddRule:
    """Test StatusMapper.add_rule method."""

    def test_add_rule(self) -> None:
        """Test add_rule adds a rule function."""
        mapper = StatusMapper()

        def rule(s: str | int) -> str | None:
            return str(DownloadStatus.FAILED) if "error" in str(s).lower() else None

        result = mapper.add_rule(rule)
        assert result is mapper
        assert len(mapper._rules) == 1
        assert mapper._rules[0] == rule

    def test_add_rule_multiple(self) -> None:
        """Test add_rule adds multiple rules in order."""
        mapper = StatusMapper()

        def rule1(s: str | int) -> str | None:
            return str(DownloadStatus.FAILED) if "error" in str(s).lower() else None

        def rule2(s: str | int) -> str | None:
            return str(DownloadStatus.COMPLETED) if "done" in str(s).lower() else None

        mapper.add_rule(rule1).add_rule(rule2)
        assert len(mapper._rules) == 2
        assert mapper._rules[0] == rule1
        assert mapper._rules[1] == rule2

    def test_add_rule_fluent_chaining(self) -> None:
        """Test add_rule supports fluent chaining."""
        mapper = StatusMapper()

        def rule(s: str | int) -> None:
            return None

        mapper.add_rule(rule).add_rule(rule)
        assert len(mapper._rules) == 2


class TestStatusMapperMap:
    """Test StatusMapper.map method."""

    def test_map_with_static_mapping_string(self) -> None:
        """Test map with string key in mappings."""
        mapper = StatusMapper({"uploading": DownloadStatus.COMPLETED})
        result = mapper.map("uploading")
        assert result == DownloadStatus.COMPLETED

    def test_map_with_static_mapping_int(self) -> None:
        """Test map with integer key in mappings."""
        mapper = StatusMapper({6: DownloadStatus.COMPLETED})
        result = mapper.map(6)
        assert result == DownloadStatus.COMPLETED

    def test_map_with_default(self) -> None:
        """Test map returns default when no mapping found."""
        mapper = StatusMapper()
        result = mapper.map("unknown")
        assert result == DownloadStatus.DOWNLOADING

    def test_map_with_custom_default(self) -> None:
        """Test map returns custom default when no mapping found."""
        mapper = StatusMapper(default=DownloadStatus.PAUSED)
        result = mapper.map("unknown")
        assert result == DownloadStatus.PAUSED

    def test_map_with_rule(self) -> None:
        """Test map uses rule when rule returns non-None."""
        mapper = StatusMapper()
        mapper.add_rule(
            lambda s: DownloadStatus.FAILED if "error" in str(s).lower() else None
        )
        result = mapper.map("error_state")
        assert result == DownloadStatus.FAILED

    def test_map_rule_returns_none(self) -> None:
        """Test map falls back to mapping when rule returns None."""
        mapper = StatusMapper({"test": DownloadStatus.COMPLETED})
        mapper.add_rule(lambda s: None)
        result = mapper.map("test")
        assert result == DownloadStatus.COMPLETED

    def test_map_rules_checked_before_mappings(self) -> None:
        """Test map checks rules before static mappings."""
        mapper = StatusMapper({"error": DownloadStatus.DOWNLOADING})
        mapper.add_rule(
            lambda s: DownloadStatus.FAILED if "error" in str(s).lower() else None
        )
        result = mapper.map("error")
        # Rule should take precedence
        assert result == DownloadStatus.FAILED

    def test_map_multiple_rules_first_match_wins(self) -> None:
        """Test map uses first rule that returns non-None."""
        mapper = StatusMapper()
        mapper.add_rule(
            lambda s: DownloadStatus.FAILED if "error" in str(s).lower() else None
        )
        mapper.add_rule(
            lambda s: DownloadStatus.COMPLETED if "done" in str(s).lower() else None
        )
        result = mapper.map("error_done")
        # First rule should win
        assert result == DownloadStatus.FAILED

    def test_map_rule_then_mapping_then_default(self) -> None:
        """Test map checks rule, then mapping, then default."""
        mapper = StatusMapper(
            {"test": DownloadStatus.COMPLETED}, default=DownloadStatus.PAUSED
        )
        mapper.add_rule(lambda s: None)  # Rule returns None
        # Rule doesn't match, check mapping
        result = mapper.map("test")
        assert result == DownloadStatus.COMPLETED
        # No rule, no mapping, use default
        result2 = mapper.map("unknown")
        assert result2 == DownloadStatus.PAUSED


# ============================================================================
# StatusMappingPresets Tests
# ============================================================================


class TestStatusMappingPresetsTorrentStringBased:
    """Test StatusMappingPresets.torrent_string_based method."""

    def test_torrent_string_based_returns_dict(self) -> None:
        """Test torrent_string_based returns a dictionary."""
        mapping = StatusMappingPresets.torrent_string_based()
        assert isinstance(mapping, dict)

    @pytest.mark.parametrize(
        ("client_status", "expected"),
        [
            ("completed", DownloadStatus.COMPLETED),
            ("seeding", DownloadStatus.COMPLETED),
            ("uploading", DownloadStatus.COMPLETED),
            ("downloading", DownloadStatus.DOWNLOADING),
            ("paused", DownloadStatus.PAUSED),
            ("queued", DownloadStatus.QUEUED),
            ("error", DownloadStatus.FAILED),
            ("failed", DownloadStatus.FAILED),
            ("stalled", DownloadStatus.STALLED),
            ("checking", DownloadStatus.CHECKING),
            ("metadata", DownloadStatus.METADATA),
        ],
    )
    def test_torrent_string_based_mappings(
        self, client_status: str, expected: str
    ) -> None:
        """Test torrent_string_based mapping values."""
        mapping = StatusMappingPresets.torrent_string_based()
        assert mapping[client_status] == expected


class TestStatusMappingPresetsTransmissionNumeric:
    """Test StatusMappingPresets.transmission_numeric method."""

    def test_transmission_numeric_returns_dict(self) -> None:
        """Test transmission_numeric returns a dictionary."""
        mapping = StatusMappingPresets.transmission_numeric()
        assert isinstance(mapping, dict)

    @pytest.mark.parametrize(
        ("status_code", "expected"),
        [
            (0, DownloadStatus.PAUSED),
            (1, DownloadStatus.QUEUED),
            (2, DownloadStatus.CHECKING),
            (3, DownloadStatus.QUEUED),
            (4, DownloadStatus.DOWNLOADING),
            (5, DownloadStatus.QUEUED),
            (6, DownloadStatus.COMPLETED),
        ],
    )
    def test_transmission_numeric_mappings(
        self, status_code: int, expected: str
    ) -> None:
        """Test transmission_numeric mapping values."""
        mapping = StatusMappingPresets.transmission_numeric()
        assert mapping[status_code] == expected

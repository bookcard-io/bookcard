# Copyright (C) 2026 knguyen and others
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

"""Configuration for book merge operations."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScoringConfig:
    """Configuration for book scoring."""

    cover_weight: int = 10
    file_count_weight: int = 2
    format_weights: dict[str, int] = field(
        default_factory=lambda: {
            "CBZ": 10,
            "CBR": 10,
            "CB7": 10,
            "CBC": 10,
            "EPUB": 5,
            "PDF": 3,
            "MOBI": 2,
        }
    )
    metadata_field_weight: int = 1

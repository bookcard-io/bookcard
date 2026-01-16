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

"""Configuration for Anna's Archive resolver."""

from dataclasses import dataclass, field


@dataclass
class AnnaArchiveConfig:
    """Configuration for Anna's Archive resolver."""

    mirrors: list[str] = field(
        default_factory=lambda: [
            "https://annas-archive.se",
            "https://annas-archive.li",
            "https://annas-archive.pm",
            "https://annas-archive.in",
        ]
    )
    donator_key: str | None = None
    max_countdown_seconds: int = 300
    retry_delay_seconds: float = 1.0

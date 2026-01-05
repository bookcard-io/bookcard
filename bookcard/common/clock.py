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

"""Clock abstraction for testability."""

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Protocol for time provider."""

    def now(self) -> datetime:
        """Get current time."""
        ...


class UTCClock:
    """Production clock implementation using UTC."""

    def now(self) -> datetime:
        """Get current UTC time."""
        return datetime.now(UTC)

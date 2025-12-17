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

"""Conversion strategies for different converter implementations.

Provides strategy pattern implementation for format conversion,
allowing different converters to be used without modifying the
main service code.
"""

from bookcard.services.conversion.strategies.calibre import (
    CalibreConversionStrategy,
)
from bookcard.services.conversion.strategies.composite import (
    CompositeConversionStrategy,
    is_comic_format,
)
from bookcard.services.conversion.strategies.kcc import KCCConversionStrategy
from bookcard.services.conversion.strategies.protocol import (
    ConversionStrategy,
)

__all__ = [
    "CalibreConversionStrategy",
    "CompositeConversionStrategy",
    "ConversionStrategy",
    "KCCConversionStrategy",
    "is_comic_format",
]

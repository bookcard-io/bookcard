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

"""Book format conversion module.

Refactored to follow SOLID principles with clear separation of concerns:
- Service: High-level orchestration
- Repository: Database operations
- Strategies: Conversion execution implementations
- Backup: File backup operations
- Locator: Converter discovery
"""

from bookcard.services.conversion.exceptions import (
    BookNotFoundError,
    ConversionError,
    ConverterNotAvailableError,
    FormatNotFoundError,
)
from bookcard.services.conversion.factory import create_conversion_service
from bookcard.services.conversion.repository import ConversionRepository
from bookcard.services.conversion.service import ConversionService

__all__ = [
    "BookNotFoundError",
    "ConversionError",
    "ConversionRepository",
    "ConversionService",
    "ConverterNotAvailableError",
    "FormatNotFoundError",
    "create_conversion_service",
]

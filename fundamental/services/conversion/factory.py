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

"""Factory for creating ConversionService instances.

Provides a convenient factory function to create ConversionService
with all dependencies properly configured.
"""

from typing import TYPE_CHECKING

from sqlmodel import Session  # type: ignore[type-arg]

from fundamental.models.config import Library
from fundamental.repositories import CalibreBookRepository
from fundamental.services.conversion.backup import FileBackupService
from fundamental.services.conversion.book_repository import (
    CalibreBookRepositoryAdapter,
)
from fundamental.services.conversion.exceptions import (
    ConverterNotAvailableError,
)
from fundamental.services.conversion.locator import ConverterLocator
from fundamental.services.conversion.repository import ConversionRepository
from fundamental.services.conversion.service import ConversionService
from fundamental.services.conversion.strategies.calibre import (
    CalibreConversionStrategy,
)

if TYPE_CHECKING:
    from fundamental.services.conversion.strategies.protocol import (
        ConversionStrategy,
    )


def create_conversion_service(
    session: Session,  # type: ignore[type-arg]
    library: Library,
    backup_service: FileBackupService | None = None,
) -> ConversionService:
    """Create a ConversionService instance with all dependencies.

    Parameters
    ----------
    session : Session
        Database session.
    library : Library
        Library configuration.
    backup_service : FileBackupService | None
        Optional backup service (default: creates new instance).

    Returns
    -------
    ConversionService
        Configured conversion service instance.

    Raises
    ------
    ConverterNotAvailableError
        If converter is not available.
    """
    # Create book repository adapter
    calibre_repo = CalibreBookRepository(
        calibre_db_path=str(library.calibre_db_path),
    )
    book_repository = CalibreBookRepositoryAdapter(calibre_repo)

    # Create conversion repository
    conversion_repository = ConversionRepository(session)

    # Locate converter
    locator = ConverterLocator()
    converter_path = locator.find_converter()
    if converter_path is None:
        msg = (
            "Calibre converter not found. Please configure converter_path in settings."
        )
        raise ConverterNotAvailableError(msg)

    # Create conversion strategy
    conversion_strategy: ConversionStrategy = CalibreConversionStrategy(converter_path)

    # Create backup service if not provided
    if backup_service is None:
        backup_service = FileBackupService()

    # Create and return service
    return ConversionService(
        session=session,
        library=library,
        book_repository=book_repository,
        conversion_repository=conversion_repository,
        conversion_strategy=conversion_strategy,
        backup_service=backup_service,
    )

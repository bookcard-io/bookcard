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

import logging
from typing import TYPE_CHECKING

from sqlmodel import Session

from bookcard.models.config import Library
from bookcard.repositories import CalibreBookRepository
from bookcard.services.conversion.backup import FileBackupService
from bookcard.services.conversion.book_repository import (
    CalibreBookRepositoryAdapter,
)
from bookcard.services.conversion.exceptions import (
    ConverterNotAvailableError,
)
from bookcard.services.conversion.kcc_locator import KCCLocator
from bookcard.services.conversion.locator import ConverterLocator
from bookcard.services.conversion.repository import ConversionRepository
from bookcard.services.conversion.service import ConversionService
from bookcard.services.conversion.strategies.calibre import (
    CalibreConversionStrategy,
)
from bookcard.services.conversion.strategies.composite import (
    CompositeConversionStrategy,
)
from bookcard.services.conversion.strategies.kcc import KCCConversionStrategy

if TYPE_CHECKING:
    from bookcard.services.conversion.strategies.protocol import (
        ConversionStrategy,
    )

logger = logging.getLogger(__name__)


def create_conversion_service(
    session: Session,
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

    # Locate Calibre converter
    locator = ConverterLocator()
    converter_path = locator.find_converter()
    if converter_path is None:
        msg = (
            "Calibre converter not found. Please configure converter_path in settings."
        )
        raise ConverterNotAvailableError(msg)

    # Create Calibre strategy
    calibre_strategy = CalibreConversionStrategy(converter_path)

    # Try to locate KCC (optional, graceful degradation if not available)
    kcc_strategy: KCCConversionStrategy | None = None
    try:
        kcc_locator = KCCLocator()
        kcc_path = kcc_locator.find_kcc()
        if kcc_path:
            # Create KCC strategy without profile (profile will be retrieved when needed)
            kcc_strategy = KCCConversionStrategy(kcc_path, profile=None)
            logger.info("KCC converter found and enabled")
        else:
            logger.info("KCC converter not found, using Calibre only")
    except (OSError, ValueError, AttributeError) as e:
        logger.warning("Failed to initialize KCC converter: %s", e)

    # Create composite strategy
    conversion_strategy: ConversionStrategy = CompositeConversionStrategy(
        kcc_strategy=kcc_strategy,
        calibre_strategy=calibre_strategy,
    )

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

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

"""Tests for create_conversion_service factory to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.config import Library
from bookcard.services.conversion.backup import FileBackupService
from bookcard.services.conversion.exceptions import ConverterNotAvailableError
from bookcard.services.conversion.factory import create_conversion_service

if TYPE_CHECKING:
    from tests.conftest import DummySession
else:
    from tests.conftest import DummySession  # noqa: TC001


@pytest.fixture
def library() -> Library:
    """Create a test library configuration.

    Returns
    -------
    Library
        Library instance.
    """
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library/metadata.db",
        library_root="/path/to/library",
    )


@pytest.mark.parametrize(
    ("converter_path", "should_raise"),
    [
        (Path("/app/calibre/ebook-convert"), False),
        (Path("/usr/bin/ebook-convert"), False),
        (None, True),
    ],
)
def test_create_conversion_service(
    session: DummySession,
    library: Library,
    converter_path: Path | None,
    should_raise: bool,
) -> None:
    """Test create_conversion_service creates service with dependencies.

    Parameters
    ----------
    session : DummySession
        Session fixture.
    library : Library
        Library fixture.
    converter_path : Path | None
        Converter path to return.
    should_raise : bool
        Whether to expect an exception.
    """
    with (
        patch(
            "bookcard.services.conversion.factory.CalibreBookRepository"
        ) as mock_repo_class,
        patch(
            "bookcard.services.conversion.factory.ConverterLocator"
        ) as mock_locator_class,
        patch(
            "bookcard.services.conversion.factory.CalibreConversionStrategy"
        ) as mock_strategy_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get_session.return_value.__enter__ = MagicMock(
            return_value=MagicMock()
        )
        mock_repo.get_session.return_value.__exit__ = MagicMock(return_value=False)
        mock_repo_class.return_value = mock_repo

        mock_locator = MagicMock()
        mock_locator.find_converter.return_value = converter_path
        mock_locator_class.return_value = mock_locator

        mock_strategy = MagicMock()
        mock_strategy_class.return_value = mock_strategy

        if should_raise:
            with pytest.raises(
                ConverterNotAvailableError,
                match="Calibre converter not found",
            ):
                create_conversion_service(session, library)  # type: ignore[arg-type]
        else:
            service = create_conversion_service(session, library)  # type: ignore[arg-type]

            assert service is not None
            mock_repo_class.assert_called_once_with(
                calibre_db_path=str(library.calibre_db_path)
            )
            mock_locator_class.assert_called_once()
            mock_strategy_class.assert_called_once_with(converter_path)


def test_create_conversion_service_with_backup_service(
    session: DummySession,
    library: Library,
) -> None:
    """Test create_conversion_service accepts optional backup service.

    Parameters
    ----------
    session : DummySession
        Session fixture.
    library : Library
        Library fixture.
    """
    backup_service = FileBackupService()

    with (
        patch(
            "bookcard.services.conversion.factory.CalibreBookRepository"
        ) as mock_repo_class,
        patch(
            "bookcard.services.conversion.factory.ConverterLocator"
        ) as mock_locator_class,
        patch(
            "bookcard.services.conversion.factory.CalibreConversionStrategy"
        ) as mock_strategy_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get_session.return_value.__enter__ = MagicMock(
            return_value=MagicMock()
        )
        mock_repo.get_session.return_value.__exit__ = MagicMock(return_value=False)
        mock_repo_class.return_value = mock_repo

        mock_locator = MagicMock()
        mock_locator.find_converter.return_value = Path("/app/calibre/ebook-convert")
        mock_locator_class.return_value = mock_locator

        mock_strategy = MagicMock()
        mock_strategy_class.return_value = mock_strategy

        service = create_conversion_service(
            session,  # type: ignore[invalid-argument-type]
            library,
            backup_service=backup_service,
        )

        assert service is not None
        assert service._backup_service == backup_service


def test_create_conversion_service_creates_default_backup_service(
    session: DummySession,
    library: Library,
) -> None:
    """Test create_conversion_service creates default backup service when not provided.

    Parameters
    ----------
    session : DummySession
        Session fixture.
    library : Library
        Library fixture.
    """
    with (
        patch(
            "bookcard.services.conversion.factory.CalibreBookRepository"
        ) as mock_repo_class,
        patch(
            "bookcard.services.conversion.factory.ConverterLocator"
        ) as mock_locator_class,
        patch(
            "bookcard.services.conversion.factory.CalibreConversionStrategy"
        ) as mock_strategy_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get_session.return_value.__enter__ = MagicMock(
            return_value=MagicMock()
        )
        mock_repo.get_session.return_value.__exit__ = MagicMock(return_value=False)
        mock_repo_class.return_value = mock_repo

        mock_locator = MagicMock()
        mock_locator.find_converter.return_value = Path("/app/calibre/ebook-convert")
        mock_locator_class.return_value = mock_locator

        mock_strategy = MagicMock()
        mock_strategy_class.return_value = mock_strategy

        service = create_conversion_service(session, library)  # type: ignore[arg-type]

        assert service is not None
        assert isinstance(service._backup_service, FileBackupService)

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

"""Tests for post_processors to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from tests.conftest import DummySession

from bookcard.models.auth import UserSetting
from bookcard.models.config import EPUBFixerConfig, Library, ScheduledTasksConfig
from bookcard.models.conversion import ConversionMethod
from bookcard.models.core import Book
from bookcard.models.media import Data
from bookcard.services.tasks.post_processors import (
    ConversionAutoConvertPolicy,
    ConversionPostIngestProcessor,
    EPUBAutoFixPolicy,
    EPUBPostIngestProcessor,
    LibraryPathResolver,
    PostIngestProcessor,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def library() -> Generator[Library, None, None]:
    """Create a library instance for testing.

    Returns
    -------
    Library
        Library instance.
    """
    # Create a mock library root and metadata.db
    import shutil
    import tempfile
    from pathlib import Path

    tmp_dir = Path(tempfile.mkdtemp())
    (tmp_dir / "metadata.db").touch()

    lib = Library(id=1, name="Test Library", calibre_db_path=str(tmp_dir))

    yield lib

    shutil.rmtree(tmp_dir)


@pytest.fixture
def book() -> Book:
    """Create a book instance for testing.

    Returns
    -------
    Book
        Book instance.
    """
    return Book(id=1, title="Test Book", path="author/book (1)")


@pytest.fixture
def epub_data() -> Data:
    """Create EPUB data instance for testing.

    Returns
    -------
    Data
        Data instance with EPUB format.
    """
    return Data(id=1, book=1, format="EPUB", name="test_book")


@pytest.fixture
def scheduled_tasks_config() -> ScheduledTasksConfig:
    """Create scheduled tasks config for testing.

    Returns
    -------
    ScheduledTasksConfig
        Scheduled tasks config instance.
    """
    return ScheduledTasksConfig(id=1)


@pytest.fixture
def epub_fixer_config() -> EPUBFixerConfig:
    """Create EPUB fixer config for testing.

    Returns
    -------
    EPUBFixerConfig
        EPUB fixer config instance.
    """
    return EPUBFixerConfig(id=1, enabled=True, library_id=1)


@pytest.fixture
def user_setting() -> UserSetting:
    """Create user setting for testing.

    Returns
    -------
    UserSetting
        User setting instance.
    """
    return UserSetting(id=1, user_id=1, key="test_key", value="test_value")


@pytest.fixture
def mock_calibre_repo_class() -> Generator[MagicMock, None, None]:
    """Mock CalibreBookRepository class."""
    with patch("bookcard.services.tasks.post_processors.CalibreBookRepository") as mock:
        yield mock


@pytest.fixture
def mock_calibre_session(mock_calibre_repo_class: MagicMock) -> MagicMock:
    """Mock Calibre database session."""
    session = MagicMock()
    mock_calibre_repo_class.return_value.get_session.return_value.__enter__.return_value = session
    return session


@pytest.fixture
def mock_path_resolver_class() -> Generator[MagicMock, None, None]:
    """Mock LibraryPathResolver class."""
    with patch("bookcard.services.tasks.post_processors.LibraryPathResolver") as mock:
        yield mock


@pytest.fixture
def mock_create_conversion_service() -> Generator[MagicMock, None, None]:
    """Mock create_conversion_service function."""
    with patch("bookcard.services.conversion.create_conversion_service") as mock:
        yield mock


# ============================================================================
# Tests for PostIngestProcessor (Abstract Base Class)
# ============================================================================


def test_post_ingest_processor_cannot_instantiate() -> None:
    """Test that PostIngestProcessor cannot be instantiated directly."""
    with pytest.raises(TypeError):
        PostIngestProcessor()


# ============================================================================
# Tests for EPUBAutoFixPolicy
# ============================================================================


class TestEPUBAutoFixPolicy:
    """Test EPUBAutoFixPolicy class."""

    def test_init(self, session: DummySession, library: Library) -> None:
        """Test EPUBAutoFixPolicy initialization.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        """
        policy = EPUBAutoFixPolicy(session, library)  # type: ignore[arg-type]
        assert policy._session == session
        assert policy._library == library

    @pytest.mark.parametrize(
        ("library_auto_fix", "epub_config", "expected"),
        [
            (False, EPUBFixerConfig(id=1, enabled=True, library_id=1), False),
            (True, None, False),
            (True, EPUBFixerConfig(id=1, enabled=False, library_id=1), False),
            (True, EPUBFixerConfig(id=1, enabled=True, library_id=1), True),
        ],
    )
    def test_should_auto_fix(
        self,
        session: DummySession,
        library: Library,
        library_auto_fix: bool,
        epub_config: EPUBFixerConfig | None,
        expected: bool,
    ) -> None:
        """Test should_auto_fix with various configurations.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        library_auto_fix : bool
            Whether library has auto-fix enabled.
        epub_config : EPUBFixerConfig | None
            EPUB fixer config or None.
        expected : bool
            Expected result.
        """
        # Set library auto-fix setting
        library.epub_fixer_auto_fix_on_ingest = library_auto_fix

        policy = EPUBAutoFixPolicy(session, library)  # type: ignore[arg-type]

        # Set up exec results for EPUB fixer config
        if epub_config is not None:
            session.add_exec_result([epub_config])
        else:
            session.add_exec_result([None])

        result = policy.should_auto_fix()
        assert result == expected


# ============================================================================
# Tests for LibraryPathResolver
# ============================================================================


class TestLibraryPathResolver:
    """Test LibraryPathResolver class."""

    def test_init(self, library: Library) -> None:
        """Test LibraryPathResolver initialization.

        Parameters
        ----------
        library : Library
            Library instance.
        """
        resolver = LibraryPathResolver(library)
        assert resolver._library == library

    def test_get_library_root(self, library: Library, tmp_path: Path) -> None:
        """Test get_library_root returns correct path.

        Parameters
        ----------
        library : Library
            Library instance.
        tmp_path : Path
            Temporary directory path.
        """
        resolver = LibraryPathResolver(library)

        with patch(
            "bookcard.services.epub_fixer.services.library.LibraryLocator"
        ) as mock_locator_class:
            mock_locator = MagicMock()
            mock_locator.get_location.return_value = tmp_path
            mock_locator_class.return_value = mock_locator

            result = resolver.get_library_root()
            assert result == tmp_path
            mock_locator.get_location.assert_called_once()

    @pytest.mark.parametrize(
        ("primary_exists", "alt_exists", "expected_path"),
        [
            (True, False, "primary"),
            (False, True, "alt"),
            (False, False, None),
        ],
    )
    def test_get_book_file_path(
        self,
        library: Library,
        book: Book,
        epub_data: Data,
        tmp_path: Path,
        primary_exists: bool,
        alt_exists: bool,
        expected_path: str | None,
    ) -> None:
        """Test get_book_file_path with various file existence scenarios.

        Parameters
        ----------
        library : Library
            Library instance.
        book : Book
            Book instance.
        epub_data : Data
            Data instance.
        tmp_path : Path
            Temporary directory path.
        primary_exists : bool
            Whether primary path exists.
        alt_exists : bool
            Whether alternative path exists.
        expected_path : str | None
            Expected path type or None.
        """
        resolver = LibraryPathResolver(library)

        # Set up library root
        library_root = tmp_path / "library"
        library_root.mkdir()
        book_dir = library_root / book.path
        book_dir.mkdir(parents=True)

        primary = book_dir / f"{epub_data.name}.epub"
        alt = book_dir / f"{book.id}.epub"

        if primary_exists:
            primary.touch()
        if alt_exists:
            alt.touch()

        with patch.object(resolver, "get_library_root", return_value=library_root):
            result = resolver.get_book_file_path(book, epub_data)

        if expected_path == "primary":
            assert result == primary
        elif expected_path == "alt":
            assert result == alt
        else:
            assert result is None

    def test_get_book_file_path_with_none_name(
        self, library: Library, book: Book, tmp_path: Path
    ) -> None:
        """Test get_book_file_path when data.name is None.

        Parameters
        ----------
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        resolver = LibraryPathResolver(library)
        data = Data(id=1, book=1, format="EPUB", name=None)

        library_root = tmp_path / "library"
        library_root.mkdir()
        book_dir = library_root / book.path
        book_dir.mkdir(parents=True)

        primary = book_dir / f"{book.id}.epub"
        primary.touch()

        with patch.object(resolver, "get_library_root", return_value=library_root):
            result = resolver.get_book_file_path(book, data)

        assert result == primary


# ============================================================================
# Tests for EPUBPostIngestProcessor
# ============================================================================


class TestEPUBPostIngestProcessor:
    """Test EPUBPostIngestProcessor class."""

    def test_init(self, session: DummySession) -> None:
        """Test EPUBPostIngestProcessor initialization.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        """
        processor = EPUBPostIngestProcessor(session)  # type: ignore[arg-type]
        assert processor._session == session

    @pytest.mark.parametrize(
        ("file_format", "expected"),
        [
            ("epub", True),
            ("EPUB", True),
            ("Epub", True),
            ("mobi", False),
            ("pdf", False),
            ("", False),
        ],
    )
    def test_supports_format(
        self, session: DummySession, file_format: str, expected: bool
    ) -> None:
        """Test supports_format with various formats.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        file_format : str
            File format to test.
        expected : bool
            Expected result.
        """
        processor = EPUBPostIngestProcessor(session)  # type: ignore[arg-type]
        result = processor.supports_format(file_format)
        assert result == expected

    def test_process_auto_fix_disabled(
        self,
        session: DummySession,
        library: Library,
        book: Book,
    ) -> None:
        """Test process when auto-fix is disabled.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        """
        processor = EPUBPostIngestProcessor(session)  # type: ignore[arg-type]

        # Mock library to have auto-fix disabled
        library.epub_fixer_auto_fix_on_ingest = False

        assert book.id is not None
        processor.process(
            session,  # type: ignore[arg-type]
            book.id,
            library,
            user_id=1,
        )

        # Process should return early without fixing
        # (no assertion needed as the method should complete without error)

    def test_process_epub_not_found(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        mock_calibre_session: MagicMock,
    ) -> None:
        """Test process when EPUB format is not found.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        mock_calibre_session : MagicMock
            Mock Calibre session.
        """
        processor = EPUBPostIngestProcessor(session)  # type: ignore[arg-type]

        # Enable auto-fix for library
        library.epub_fixer_auto_fix_on_ingest = True

        # EPUB fixer config enabled
        epub_config = EPUBFixerConfig(id=1, enabled=True, library_id=1)
        session.add_exec_result([epub_config])

        # Mock query result
        mock_calibre_session.exec.return_value.first.return_value = None

        assert book.id is not None
        processor.process(
            session,  # type: ignore[arg-type]
            book.id,
            library,
            user_id=1,
        )

    def test_process_file_not_found(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        epub_data: Data,
        mock_calibre_session: MagicMock,
        mock_path_resolver_class: MagicMock,
    ) -> None:
        """Test process when EPUB file is not found.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        epub_data : Data
            EPUB data instance.
        mock_calibre_session : MagicMock
            Mock Calibre session.
        mock_path_resolver_class : MagicMock
            Mock LibraryPathResolver class.
        """
        processor = EPUBPostIngestProcessor(session)  # type: ignore[arg-type]

        # Enable auto-fix for library
        library.epub_fixer_auto_fix_on_ingest = True

        # EPUB fixer config enabled
        epub_config = EPUBFixerConfig(id=1, enabled=True, library_id=1)
        session.add_exec_result([epub_config])

        # Mock query result
        mock_calibre_session.exec.return_value.first.return_value = (book, epub_data)

        # Mock path resolver to return None
        mock_resolver = MagicMock()
        mock_resolver.get_book_file_path.return_value = None
        mock_path_resolver_class.return_value = mock_resolver

        assert book.id is not None
        processor.process(
            session,  # type: ignore[arg-type]
            book.id,
            library,
            user_id=1,
        )

    def test_process_success_with_fixes(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        epub_data: Data,
        tmp_path: Path,
        mock_calibre_session: MagicMock,
        mock_path_resolver_class: MagicMock,
    ) -> None:
        """Test process when EPUB fix succeeds with fixes applied.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        epub_data : Data
            EPUB data instance.
        tmp_path : Path
            Temporary directory path.
        mock_calibre_session : MagicMock
            Mock Calibre session.
        mock_path_resolver_class : MagicMock
            Mock LibraryPathResolver class.
        """
        processor = EPUBPostIngestProcessor(session)  # type: ignore[arg-type]

        # Enable auto-fix for library
        library.epub_fixer_auto_fix_on_ingest = True

        # EPUB fixer config enabled
        epub_config = EPUBFixerConfig(id=1, enabled=True, library_id=1)
        session.add_exec_result([epub_config])

        # Mock query results
        mock_calibre_session.exec.return_value.first.side_effect = [
            (book, epub_data),  # For process()
            (
                book,
                epub_data,
            ),  # For process_epub_file() inside service if called again
        ]

        file_path = tmp_path / "book.epub"
        file_path.touch()

        # Mock path resolver
        mock_resolver = MagicMock()
        mock_resolver.get_book_file_path.return_value = file_path
        mock_path_resolver_class.return_value = mock_resolver

        # Mock EPUB fixer service
        with patch(
            "bookcard.services.epub_fixer_service.EPUBFixerService"
        ) as mock_fixer_class:
            mock_fixer = MagicMock()
            fix_run = MagicMock()
            fix_run.id = 1
            mock_fixer.process_epub_file.return_value = fix_run
            mock_fixer.get_fixes_for_run.return_value = [
                MagicMock(),
                MagicMock(),
            ]  # 2 fixes
            mock_fixer_class.return_value = mock_fixer

            assert book.id is not None
            processor.process(
                session,  # type: ignore[arg-type]
                book.id,
                library,
                user_id=1,
            )

            mock_fixer.process_epub_file.assert_called_once_with(
                file_path=file_path,
                book_id=book.id,
                book_title=book.title,
                user_id=1,
                library_id=library.id,
                manually_triggered=False,
            )

    def test_process_success_no_fixes(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        epub_data: Data,
        tmp_path: Path,
        mock_calibre_session: MagicMock,
        mock_path_resolver_class: MagicMock,
    ) -> None:
        """Test process when EPUB fix succeeds with no fixes needed.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        epub_data : Data
            EPUB data instance.
        tmp_path : Path
            Temporary directory path.
        mock_calibre_session : MagicMock
            Mock Calibre session.
        mock_path_resolver_class : MagicMock
            Mock LibraryPathResolver class.
        """
        processor = EPUBPostIngestProcessor(session)  # type: ignore[arg-type]

        # Enable auto-fix for library
        library.epub_fixer_auto_fix_on_ingest = True

        # EPUB fixer config enabled
        epub_config = EPUBFixerConfig(id=1, enabled=True, library_id=1)
        session.add_exec_result([epub_config])

        # Mock query results
        mock_calibre_session.exec.return_value.first.return_value = (book, epub_data)

        file_path = tmp_path / "book.epub"
        file_path.touch()

        # Mock path resolver
        mock_resolver = MagicMock()
        mock_resolver.get_book_file_path.return_value = file_path
        mock_path_resolver_class.return_value = mock_resolver

        # Mock EPUB fixer service
        with patch(
            "bookcard.services.epub_fixer_service.EPUBFixerService"
        ) as mock_fixer_class:
            mock_fixer = MagicMock()
            fix_run = MagicMock()
            fix_run.id = 1
            mock_fixer.process_epub_file.return_value = fix_run
            mock_fixer.get_fixes_for_run.return_value = []  # No fixes
            mock_fixer_class.return_value = mock_fixer

            assert book.id is not None
            processor.process(
                session,  # type: ignore[arg-type]
                book.id,
                library,
                user_id=1,
            )

    def test_process_success_no_fix_run_id(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        epub_data: Data,
        tmp_path: Path,
        mock_calibre_session: MagicMock,
        mock_path_resolver_class: MagicMock,
    ) -> None:
        """Test process when EPUB fix succeeds but fix_run.id is None.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        epub_data : Data
            EPUB data instance.
        tmp_path : Path
            Temporary directory path.
        mock_calibre_session : MagicMock
            Mock Calibre session.
        mock_path_resolver_class : MagicMock
            Mock LibraryPathResolver class.
        """
        processor = EPUBPostIngestProcessor(session)  # type: ignore[arg-type]

        # Enable auto-fix for library
        library.epub_fixer_auto_fix_on_ingest = True

        # EPUB fixer config enabled
        epub_config = EPUBFixerConfig(id=1, enabled=True, library_id=1)
        session.add_exec_result([epub_config])

        # Mock query results
        mock_calibre_session.exec.return_value.first.return_value = (book, epub_data)

        file_path = tmp_path / "book.epub"
        file_path.touch()

        # Mock path resolver
        mock_resolver = MagicMock()
        mock_resolver.get_book_file_path.return_value = file_path
        mock_path_resolver_class.return_value = mock_resolver

        # Mock EPUB fixer service
        with patch(
            "bookcard.services.epub_fixer_service.EPUBFixerService"
        ) as mock_fixer_class:
            mock_fixer = MagicMock()
            fix_run = MagicMock()
            fix_run.id = None
            mock_fixer.process_epub_file.return_value = fix_run
            mock_fixer_class.return_value = mock_fixer

            assert book.id is not None
            processor.process(
                session,  # type: ignore[arg-type]
                book.id,
                library,
                user_id=1,
            )

    def test_process_library_none(
        self,
        session: DummySession,
        book: Book,
    ) -> None:
        """Test process when library is None.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        book : Book
            Book instance.
        """
        processor = EPUBPostIngestProcessor(session)  # type: ignore[arg-type]

        # When library is None, auto-fix should be disabled (policy returns False early)
        # The process method should return early when policy.should_auto_fix() returns False
        # So process_epub_file should not be called

        assert book.id is not None
        processor.process(
            session,  # type: ignore[arg-type]
            book.id,
            None,
            user_id=1,
        )


# ============================================================================
# Tests for ConversionAutoConvertPolicy
# ============================================================================


class TestConversionAutoConvertPolicy:
    """Test ConversionAutoConvertPolicy class."""

    def test_init(self, session: DummySession) -> None:
        """Test ConversionAutoConvertPolicy initialization.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        """
        policy = ConversionAutoConvertPolicy(session, user_id=1)  # type: ignore[arg-type]
        assert policy._session == session
        assert policy._user_id == 1

    @pytest.mark.parametrize(
        ("setting_value", "expected"),
        [
            (None, False),
            (
                UserSetting(
                    id=1, user_id=1, key="auto_convert_on_import", value="true"
                ),
                True,
            ),
            (
                UserSetting(
                    id=1, user_id=1, key="auto_convert_on_import", value="True"
                ),
                True,
            ),
            (
                UserSetting(
                    id=1, user_id=1, key="auto_convert_on_import", value="TRUE"
                ),
                True,
            ),
            (
                UserSetting(
                    id=1, user_id=1, key="auto_convert_on_import", value="false"
                ),
                False,
            ),
            (
                UserSetting(
                    id=1, user_id=1, key="auto_convert_on_import", value="False"
                ),
                False,
            ),
        ],
    )
    def test_should_auto_convert(
        self,
        session: DummySession,
        setting_value: UserSetting | None,
        expected: bool,
    ) -> None:
        """Test should_auto_convert with various settings.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        setting_value : UserSetting | None
            User setting or None.
        expected : bool
            Expected result.
        """
        policy = ConversionAutoConvertPolicy(session, user_id=1)  # type: ignore[arg-type]
        session.add_exec_result([setting_value])
        result = policy.should_auto_convert()
        assert result == expected

    @pytest.mark.parametrize(
        ("setting_value", "expected"),
        [
            (None, "epub"),
            (
                UserSetting(
                    id=1, user_id=1, key="auto_convert_target_format", value="mobi"
                ),
                "mobi",
            ),
            (
                UserSetting(
                    id=1, user_id=1, key="auto_convert_target_format", value="PDF"
                ),
                "pdf",
            ),
            (
                UserSetting(
                    id=1, user_id=1, key="auto_convert_target_format", value="EPUB"
                ),
                "epub",
            ),
        ],
    )
    def test_get_target_format(
        self,
        session: DummySession,
        setting_value: UserSetting | None,
        expected: str,
    ) -> None:
        """Test get_target_format with various settings.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        setting_value : UserSetting | None
            User setting or None.
        expected : str
            Expected format.
        """
        policy = ConversionAutoConvertPolicy(session, user_id=1)  # type: ignore[arg-type]
        session.add_exec_result([setting_value])
        result = policy.get_target_format()
        assert result == expected

    @pytest.mark.parametrize(
        ("setting_value", "expected"),
        [
            (None, []),
            (
                UserSetting(
                    id=1,
                    user_id=1,
                    key="auto_convert_ignored_formats",
                    value='["MOBI", "PDF"]',
                ),
                ["MOBI", "PDF"],
            ),
            (
                UserSetting(
                    id=1,
                    user_id=1,
                    key="auto_convert_ignored_formats",
                    value="MOBI,PDF",
                ),
                ["MOBI", "PDF"],
            ),
            (
                UserSetting(
                    id=1,
                    user_id=1,
                    key="auto_convert_ignored_formats",
                    value="MOBI, PDF, AZW3",
                ),
                ["MOBI", "PDF", "AZW3"],
            ),
            (
                UserSetting(
                    id=1,
                    user_id=1,
                    key="auto_convert_ignored_formats",
                    value='["mobi", "pdf"]',
                ),
                ["MOBI", "PDF"],
            ),
            (
                UserSetting(
                    id=1,
                    user_id=1,
                    key="auto_convert_ignored_formats",
                    value="",
                ),
                [],
            ),
        ],
    )
    def test_get_ignored_formats(
        self,
        session: DummySession,
        setting_value: UserSetting | None,
        expected: list[str],
    ) -> None:
        """Test get_ignored_formats with various settings.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        setting_value : UserSetting | None
            User setting or None.
        expected : list[str]
            Expected ignored formats.
        """
        policy = ConversionAutoConvertPolicy(session, user_id=1)  # type: ignore[arg-type]
        session.add_exec_result([setting_value])
        result = policy.get_ignored_formats()
        assert result == expected

    def test_get_ignored_formats_invalid_json(self, session: DummySession) -> None:
        """Test get_ignored_formats with invalid JSON.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        """
        policy = ConversionAutoConvertPolicy(session, user_id=1)  # type: ignore[arg-type]
        setting = UserSetting(
            id=1,
            user_id=1,
            key="auto_convert_ignored_formats",
            value="MOBI,PDF",  # Not JSON, will fallback to comma-separated
        )
        session.add_exec_result([setting])
        result = policy.get_ignored_formats()
        assert result == ["MOBI", "PDF"]

    def test_get_ignored_formats_non_list_json(self, session: DummySession) -> None:
        """Test get_ignored_formats with JSON that's not a list.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        """
        policy = ConversionAutoConvertPolicy(session, user_id=1)  # type: ignore[arg-type]
        setting = UserSetting(
            id=1,
            user_id=1,
            key="auto_convert_ignored_formats",
            value='{"formats": ["MOBI"]}',  # JSON object, not list
        )
        session.add_exec_result([setting])
        result = policy.get_ignored_formats()
        assert result == []

    @pytest.mark.parametrize(
        ("setting_value", "expected"),
        [
            (None, True),
            (
                UserSetting(
                    id=1, user_id=1, key="auto_convert_backup_originals", value="true"
                ),
                True,
            ),
            (
                UserSetting(
                    id=1, user_id=1, key="auto_convert_backup_originals", value="True"
                ),
                True,
            ),
            (
                UserSetting(
                    id=1, user_id=1, key="auto_convert_backup_originals", value="false"
                ),
                False,
            ),
            (
                UserSetting(
                    id=1, user_id=1, key="auto_convert_backup_originals", value="False"
                ),
                False,
            ),
        ],
    )
    def test_should_backup_original(
        self,
        session: DummySession,
        setting_value: UserSetting | None,
        expected: bool,
    ) -> None:
        """Test should_backup_original with various settings.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        setting_value : UserSetting | None
            User setting or None.
        expected : bool
            Expected result.
        """
        policy = ConversionAutoConvertPolicy(session, user_id=1)  # type: ignore[arg-type]
        session.add_exec_result([setting_value])
        result = policy.should_backup_original()
        assert result == expected


# ============================================================================
# Tests for ConversionPostIngestProcessor
# ============================================================================


class TestConversionPostIngestProcessor:
    """Test ConversionPostIngestProcessor class."""

    def test_init(self, session: DummySession) -> None:
        """Test ConversionPostIngestProcessor initialization.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        """
        processor = ConversionPostIngestProcessor(session, user_id=1)  # type: ignore[arg-type]
        assert processor._session == session
        assert processor._user_id == 1
        assert isinstance(processor._policy, ConversionAutoConvertPolicy)
        assert processor._uploaded_format is None

    @pytest.mark.parametrize(
        ("file_format", "expected_stored"),
        [
            ("epub", "EPUB"),
            ("MOBI", "MOBI"),
            ("pdf", "PDF"),
            ("", ""),
        ],
    )
    def test_supports_format(
        self,
        session: DummySession,
        file_format: str,
        expected_stored: str,
    ) -> None:
        """Test supports_format stores format and always returns True.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        file_format : str
            File format to test.
        expected_stored : str
            Expected stored format.
        """
        processor = ConversionPostIngestProcessor(session, user_id=1)  # type: ignore[arg-type]
        result = processor.supports_format(file_format)
        assert result is True
        assert processor._uploaded_format == expected_stored

    def test_process_auto_convert_disabled(
        self,
        session: DummySession,
        library: Library,
        book: Book,
    ) -> None:
        """Test process when auto-convert is disabled.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        """
        processor = ConversionPostIngestProcessor(session, user_id=1)  # type: ignore[arg-type]

        # Mock policy to return False
        processor._policy.should_auto_convert = MagicMock(return_value=False)  # type: ignore[method-assign]

        assert book.id is not None
        processor.process(
            session,  # type: ignore[arg-type]
            book.id,
            library,
            user_id=1,
        )

        processor._policy.should_auto_convert.assert_called_once()

    def test_process_book_not_found(
        self,
        session: DummySession,
        library: Library,
        mock_calibre_session: MagicMock,
        mock_create_conversion_service: MagicMock,
    ) -> None:
        """Test process when book is not found.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        mock_calibre_session : MagicMock
            Mock Calibre session.
        mock_create_conversion_service : MagicMock
            Mock create_conversion_service.
        """
        processor = ConversionPostIngestProcessor(session, user_id=1)  # type: ignore[arg-type]
        processor._uploaded_format = "MOBI"

        # Mock policy to return True
        processor._policy.should_auto_convert = MagicMock(return_value=True)  # type: ignore[method-assign]

        # Mock query result
        mock_calibre_session.exec.return_value.first.return_value = None

        processor.process(
            session,  # type: ignore[arg-type]
            book_id=999,
            library=library,
            user_id=1,
        )

    def test_process_format_not_found_fallback(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        epub_data: Data,
        mock_calibre_session: MagicMock,
    ) -> None:
        """Test process when uploaded format is None and falls back to querying.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        epub_data : Data
            EPUB data instance.
        mock_calibre_session : MagicMock
            Mock Calibre session.
        """
        processor = ConversionPostIngestProcessor(session, user_id=1)  # type: ignore[arg-type]
        processor._uploaded_format = None  # Not set

        # Mock policy to return True
        processor._policy.should_auto_convert = MagicMock(return_value=True)  # type: ignore[method-assign]
        processor._policy.get_target_format = MagicMock(return_value="epub")  # type: ignore[method-assign]
        processor._policy.get_ignored_formats = MagicMock(return_value=[])  # type: ignore[method-assign]

        # Mock query results
        # First query: fallback get original format
        # Second query: check if target format exists (None means not exists)
        mock_calibre_session.exec.return_value.first.side_effect = [epub_data, None]

        assert book.id is not None
        processor.process(
            session,  # type: ignore[arg-type]
            book.id,
            library,
            user_id=1,
        )

    def test_process_format_not_found_no_data(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        mock_calibre_session: MagicMock,
    ) -> None:
        """Test process when format data is not found in fallback.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        mock_calibre_session : MagicMock
            Mock Calibre session.
        """
        processor = ConversionPostIngestProcessor(session, user_id=1)  # type: ignore[arg-type]
        processor._uploaded_format = None  # Not set

        # Mock policy to return True
        processor._policy.should_auto_convert = MagicMock(return_value=True)  # type: ignore[method-assign]

        # Data not found in fallback query
        mock_calibre_session.exec.return_value.first.return_value = None

        assert book.id is not None
        processor.process(
            session,  # type: ignore[arg-type]
            book.id,
            library,
            user_id=1,
        )

    def test_process_format_not_found_with_uploaded_format(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        mock_calibre_session: MagicMock,
        mock_create_conversion_service: MagicMock,
    ) -> None:
        """Test process when uploaded format is set but data not found.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        mock_calibre_session : MagicMock
            Mock Calibre session.
        mock_create_conversion_service : MagicMock
            Mock create_conversion_service.
        """
        processor = ConversionPostIngestProcessor(session, user_id=1)  # type: ignore[arg-type]
        processor._uploaded_format = "MOBI"

        # Mock policy to return True
        processor._policy.should_auto_convert = MagicMock(return_value=True)  # type: ignore[method-assign]

        # Data not found for uploaded format
        mock_calibre_session.exec.return_value.first.return_value = None

        assert book.id is not None
        processor.process(
            session,  # type: ignore[arg-type]
            book.id,
            library,
            user_id=1,
        )
        # Verify that create_conversion_service WAS called because fallback to uploaded format works
        mock_create_conversion_service.assert_called_once()

    @pytest.mark.parametrize(
        ("original_format", "target_format", "ignored_formats", "should_convert"),
        [
            ("EPUB", "EPUB", [], False),  # Already in target format
            ("MOBI", "EPUB", ["MOBI"], False),  # In ignored formats
            ("MOBI", "EPUB", [], True),  # Should convert
        ],
    )
    def test_process_conversion_skipped(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        original_format: str,
        target_format: str,
        ignored_formats: list[str],
        should_convert: bool,
        mock_calibre_session: MagicMock,
        mock_create_conversion_service: MagicMock,
    ) -> None:
        """Test process when conversion is skipped for various reasons.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        original_format : str
            Original format.
        target_format : str
            Target format.
        ignored_formats : list[str]
            Ignored formats.
        should_convert : bool
            Whether conversion should happen.
        mock_calibre_session : MagicMock
            Mock Calibre session.
        mock_create_conversion_service : MagicMock
            Mock create_conversion_service.
        """
        processor = ConversionPostIngestProcessor(session, user_id=1)  # type: ignore[arg-type]
        processor._uploaded_format = original_format

        # Mock policy
        processor._policy.should_auto_convert = MagicMock(return_value=True)  # type: ignore[method-assign,assignment]
        processor._policy.get_target_format = MagicMock(  # type: ignore[method-assign,assignment]
            return_value=target_format.lower()
        )
        processor._policy.get_ignored_formats = MagicMock(return_value=ignored_formats)  # type: ignore[method-assign,assignment]

        assert book.id is not None
        data = Data(id=1, book=book.id, format=original_format, name="test")

        side_effects = [data]  # First query for original format

        # Check if target format already exists query
        if should_convert:
            side_effects.append(None)  # Target format doesn't exist

        mock_calibre_session.exec.return_value.first.side_effect = side_effects

        assert book.id is not None
        processor.process(
            session,  # type: ignore[arg-type]
            book.id,
            library,
            user_id=1,
        )

    def test_process_target_format_exists(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        mock_calibre_session: MagicMock,
    ) -> None:
        """Test process when target format already exists.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        mock_calibre_session : MagicMock
            Mock Calibre session.
        """
        processor = ConversionPostIngestProcessor(session, user_id=1)  # type: ignore[arg-type]
        processor._uploaded_format = "MOBI"

        # Mock policy
        processor._policy.should_auto_convert = MagicMock(return_value=True)  # type: ignore[method-assign]
        processor._policy.get_target_format = MagicMock(return_value="epub")  # type: ignore[method-assign]
        processor._policy.get_ignored_formats = MagicMock(return_value=[])  # type: ignore[method-assign]

        mobi_data = Data(id=1, book=book.id, format="MOBI", name="test")
        epub_data = Data(id=2, book=book.id, format="EPUB", name="test")

        # Mock query results
        # First query: get original format data
        # Second query: check if target format exists (returns data meaning it exists)
        mock_calibre_session.exec.return_value.first.side_effect = [
            mobi_data,
            epub_data,
        ]

        assert book.id is not None
        processor.process(
            session,  # type: ignore[arg-type]
            book.id,
            library,
            user_id=1,
        )

    def test_process_conversion_success(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        mock_calibre_session: MagicMock,
        mock_create_conversion_service: MagicMock,
    ) -> None:
        """Test process when conversion succeeds.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        mock_calibre_session : MagicMock
            Mock Calibre session.
        mock_create_conversion_service : MagicMock
            Mock create_conversion_service.
        """
        processor = ConversionPostIngestProcessor(session, user_id=1)  # type: ignore[arg-type]
        processor._uploaded_format = "MOBI"

        # Mock policy
        processor._policy.should_auto_convert = MagicMock(return_value=True)  # type: ignore[method-assign]
        processor._policy.get_target_format = MagicMock(return_value="epub")  # type: ignore[method-assign]
        processor._policy.get_ignored_formats = MagicMock(return_value=[])  # type: ignore[method-assign]
        processor._policy.should_backup_original = MagicMock(return_value=True)  # type: ignore[method-assign]

        mobi_data = Data(id=1, book=book.id, format="MOBI", name="test")

        # Mock query results
        # First query: get original format data
        # Second query: check if target format exists (returns None meaning it doesn't)
        mock_calibre_session.exec.return_value.first.side_effect = [mobi_data, None]

        # Mock conversion service
        mock_conversion = MagicMock()
        mock_create_conversion_service.return_value = mock_conversion

        assert book.id is not None
        processor.process(
            session,  # type: ignore[arg-type]
            book.id,
            library,
            user_id=1,
        )

        mock_conversion.convert_book.assert_called_once_with(
            book_id=book.id,
            original_format="MOBI",
            target_format="EPUB",
            user_id=1,
            conversion_method=ConversionMethod.AUTO_IMPORT,
            backup_original=True,
        )

    @pytest.mark.parametrize(
        "exception_type",
        [
            ValueError,
            OSError,
            RuntimeError,
        ],
    )
    def test_process_conversion_error(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        exception_type: type[Exception],
        mock_calibre_session: MagicMock,
        mock_create_conversion_service: MagicMock,
    ) -> None:
        """Test process when conversion raises an error.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        exception_type : type[Exception]
            Exception type to raise.
        mock_calibre_session : MagicMock
            Mock Calibre session.
        mock_create_conversion_service : MagicMock
            Mock create_conversion_service.
        """
        processor = ConversionPostIngestProcessor(session, user_id=1)  # type: ignore[arg-type]
        processor._uploaded_format = "MOBI"

        # Mock policy
        processor._policy.should_auto_convert = MagicMock(return_value=True)  # type: ignore[method-assign]
        processor._policy.get_target_format = MagicMock(return_value="epub")  # type: ignore[method-assign]
        processor._policy.get_ignored_formats = MagicMock(return_value=[])  # type: ignore[method-assign]
        processor._policy.should_backup_original = MagicMock(return_value=True)  # type: ignore[method-assign]

        mobi_data = Data(id=1, book=book.id, format="MOBI", name="test")

        # Mock query results
        # First query: get original format data
        # Second query: check if target format exists (returns None meaning it doesn't)
        mock_calibre_session.exec.return_value.first.side_effect = [mobi_data, None]

        # Mock conversion service to raise error
        mock_conversion = MagicMock()
        mock_conversion.convert_book.side_effect = exception_type("Test error")
        mock_create_conversion_service.return_value = mock_conversion

        # Should not raise, just log warning
        assert book.id is not None
        processor.process(
            session,  # type: ignore[arg-type]
            book.id,
            library,
            user_id=1,
        )

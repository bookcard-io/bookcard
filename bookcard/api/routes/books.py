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

"""Book endpoints: list, search, and retrieve books from Calibre library.

Routes handle only HTTP concerns: request/response, status codes, exceptions.
Business logic is delegated to services following SOLID principles.
"""

import logging
import math
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlmodel import Session

from bookcard.api.deps import (
    _resolve_active_library,
    get_active_library_id,
    get_current_user,
    get_db_session,
    get_optional_user,
)
from bookcard.api.schemas import (
    BookBatchUploadResponse,
    BookBulkSendRequest,
    BookConversionListResponse,
    BookConversionRead,
    BookConvertRequest,
    BookConvertResponse,
    BookDeleteRequest,
    BookFilterRequest,
    BookFixEpubResponse,
    BookListResponse,
    BookMergeRecommendRequest,
    BookMergeRequest,
    BookRead,
    BookSendRequest,
    BookStripDrmResponse,
    BookUpdate,
    BookUploadResponse,
    CoverFromUrlRequest,
    CoverFromUrlResponse,
    FilterSuggestionsResponse,
    FormatMetadataResponse,
    SearchSuggestionItem,
    SearchSuggestionsResponse,
    TagLookupItem,
    TagLookupResponse,
)
from bookcard.models.auth import User
from bookcard.models.tasks import TaskType
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.repositories.session_manager import CalibreSessionManager
from bookcard.services.book_conversion_orchestration_service import (
    BookConversionOrchestrationService,
)
from bookcard.services.book_cover_service import BookCoverService
from bookcard.services.book_dedrm_orchestration_service import (
    BookDeDRMOrchestrationService,
)
from bookcard.services.book_exception_mapper import BookExceptionMapper
from bookcard.services.book_file_service import BookFileService
from bookcard.services.book_merge.exceptions import BookMergeError
from bookcard.services.book_merge_service import BookMergeService
from bookcard.services.book_permission_helper import BookPermissionHelper
from bookcard.services.book_read_model_service import BookReadModelService
from bookcard.services.book_response_builder import BookResponseBuilder
from bookcard.services.book_service import BookService
from bookcard.services.config_service import FileHandlingConfigService
from bookcard.services.email_config_service import EmailConfigService
from bookcard.services.format_metadata_service import FormatMetadataService
from bookcard.services.metadata_enforcement_trigger_service import (
    MetadataEnforcementTriggerService,
)
from bookcard.services.metadata_export_service import MetadataExportService
from bookcard.services.metadata_import_service import MetadataImportService
from bookcard.services.multi_library_book_service import MultiLibraryBookService
from bookcard.services.multi_library_response_builder import (
    MultiLibraryResponseBuilder,
)
from bookcard.services.security import DataEncryptor

if TYPE_CHECKING:
    from bookcard.models import Library
    from bookcard.services.tasks.base import TaskRunner

router = APIRouter(prefix="/books", tags=["books"])
logger = logging.getLogger(__name__)

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
OptionalUserDep = Annotated[User | None, Depends(get_optional_user)]
ActiveLibraryIdDep = Annotated[int, Depends(get_active_library_id)]

# Temporary cover storage (in-memory for now, could be moved to disk/DB)
_temp_cover_storage: dict[str, Path] = {}

# Media types mapping for book file formats
FILE_FORMAT_MEDIA_TYPES = {
    "EPUB": "application/epub+zip",
    "PDF": "application/pdf",
    "MOBI": "application/x-mobipocket-ebook",
    "AZW3": "application/vnd.amazon.ebook",
    "FB2": "application/x-fictionbook+xml",
    "LIT": "application/x-ms-reader",
    "LRF": "application/x-sony-bbeb",
    "ODT": "application/vnd.oasis.opendocument.text",
    "RTF": "application/rtf",
    "TXT": "text/plain",
    "HTML": "text/html",
    "HTM": "text/html",
}


def _find_format_data(
    formats: list[dict[str, str | int]], requested_format: str
) -> tuple[dict[str, str | int] | None, list[str]]:
    """Find format data matching the requested format.

    Parameters
    ----------
    formats : list[dict[str, str | int]]
        List of format dictionaries from book data.
    requested_format : str
        Requested file format (e.g., 'EPUB', 'PDF').

    Returns
    -------
    tuple[dict[str, str | int] | None, list[str]]
        Tuple of (format data if found, list of available formats).
    """
    format_upper = requested_format.upper()
    available_formats = []
    format_data = None
    for fmt in formats:
        fmt_format = fmt.get("format", "")
        available_formats.append(str(fmt_format))
        if isinstance(fmt_format, str) and fmt_format.upper() == format_upper:
            format_data = fmt
    return format_data, available_formats


def _get_media_type(format_upper: str) -> str:
    """Get media type for file format.

    Parameters
    ----------
    format_upper : str
        File format in uppercase.

    Returns
    -------
    str
        Media type string.
    """
    return FILE_FORMAT_MEDIA_TYPES.get(format_upper, "application/octet-stream")


def _email_config_service(request: Request, session: Session) -> EmailConfigService:
    """Get email configuration service.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : Session
        Database session.

    Returns
    -------
    EmailConfigService
        Email configuration service instance.
    """
    cfg = request.app.state.config
    encryptor = DataEncryptor(cfg.encryption_key)
    return EmailConfigService(session, encryptor=encryptor)


def _get_active_library_service(
    session: SessionDep,
    current_user: OptionalUserDep,
) -> BookService:
    """Get book service for the active library.

    Resolves the active library via the per-user ``UserLibrary`` table
    when an authenticated user is present, falling back to the global
    ``Library.is_active`` flag otherwise.

    Parameters
    ----------
    session : SessionDep
        Database session.
    current_user : OptionalUserDep
        Optionally-resolved authenticated user.

    Returns
    -------
    BookService
        Book service instance.

    Raises
    ------
    HTTPException
        If no active library is configured (404).
    """
    user_id = current_user.id if current_user else None
    library = _resolve_active_library(session, user_id)

    if library is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    return BookService(library, session=session)


def _get_book_file_service(
    book_service: Annotated[BookService, Depends(_get_active_library_service)],
) -> BookFileService:
    """Construct the book file service.

    Parameters
    ----------
    book_service : BookService
        Book service for the active library.

    Returns
    -------
    BookFileService
        Book file service instance.
    """
    return BookFileService(book_service)


def _get_permission_helper(session: SessionDep) -> BookPermissionHelper:
    """Get book permission helper instance.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    BookPermissionHelper
        Permission helper instance.
    """
    return BookPermissionHelper(session)


def _get_response_builder(
    book_service: Annotated[BookService, Depends(_get_active_library_service)],
) -> BookResponseBuilder:
    """Get book response builder instance.

    Parameters
    ----------
    book_service : BookService
        Book service instance.

    Returns
    -------
    BookResponseBuilder
        Response builder instance.
    """
    return BookResponseBuilder(book_service)


def _get_cover_service(
    book_service: Annotated[BookService, Depends(_get_active_library_service)],
) -> BookCoverService:
    """Get book cover service instance.

    Parameters
    ----------
    book_service : BookService
        Book service instance.

    Returns
    -------
    BookCoverService
        Cover service instance.
    """
    return BookCoverService(book_service)


def _get_book_merge_service(
    session: SessionDep,
    current_user: OptionalUserDep,
) -> Generator[BookMergeService, None, None]:
    """Get book merge service instance.

    Parameters
    ----------
    session : SessionDep
        Database session.
    current_user : OptionalUserDep
        Optionally-resolved authenticated user.

    Yields
    ------
    BookMergeService
        Book merge service instance.
    """
    user_id = current_user.id if current_user else None
    active_library = _resolve_active_library(session, user_id)

    if not active_library or not active_library.calibre_db_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    # Determine paths
    db_path = Path(active_library.calibre_db_path)
    if db_path.is_dir():
        library_root = db_path
        db_file = "metadata.db"
    else:
        library_root = db_path.parent
        db_file = db_path.name

    # Create session manager and yield service with Calibre session
    session_manager = CalibreSessionManager(str(library_root), db_file)
    with session_manager.get_session() as calibre_session:
        yield BookMergeService(calibre_session, str(library_root))


BookMergeServiceDep = Annotated[BookMergeService, Depends(_get_book_merge_service)]
BookServiceDep = Annotated[BookService, Depends(_get_active_library_service)]
BookFileServiceDep = Annotated[BookFileService, Depends(_get_book_file_service)]
PermissionHelperDep = Annotated[
    BookPermissionHelper,
    Depends(_get_permission_helper),
]


# -- Library-aware dependency chain ------------------------------------------
# These resolve the BookService (and derived services) from an optional
# ``?library_id=`` query parameter, falling back to the user's active library.
# Use for single-book endpoints that must work across libraries.


def _get_library_aware_book_service(
    session: SessionDep,
    current_user: OptionalUserDep,
    library_id: Annotated[
        int | None,
        Query(description="Library this book belongs to"),
    ] = None,
) -> BookService:
    """Resolve :class:`BookService` from an explicit library or the active one.

    Parameters
    ----------
    session : Session
        Database session.
    current_user : User | None
        Authenticated user.
    library_id : int | None
        Optional explicit library ID.

    Returns
    -------
    BookService
    """
    user_id = current_user.id if current_user else None

    if library_id is not None:
        from bookcard.repositories.user_library_repository import (
            UserLibraryRepository,
        )

        if current_user is None or current_user.id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="authentication_required",
            )
        ul_repo = UserLibraryRepository(session)
        assoc = ul_repo.find_by_user_and_library(current_user.id, library_id)
        if assoc is None or not assoc.is_visible:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="library_access_denied",
            )
        lib_repo = LibraryRepository(session)
        lib = lib_repo.get(library_id)
        if lib is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="library_not_found",
            )
        return BookService(lib, session=session)

    library = _resolve_active_library(session, user_id)
    if library is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )
    return BookService(library, session=session)


def _get_library_aware_file_service(
    book_service: Annotated[BookService, Depends(_get_library_aware_book_service)],
) -> BookFileService:
    """Build :class:`BookFileService` from the library-aware book service."""
    return BookFileService(book_service)


def _get_library_aware_cover_service(
    book_service: Annotated[BookService, Depends(_get_library_aware_book_service)],
) -> BookCoverService:
    """Build :class:`BookCoverService` from the library-aware book service."""
    return BookCoverService(book_service)


def _get_library_aware_response_builder(
    book_service: Annotated[BookService, Depends(_get_library_aware_book_service)],
) -> BookResponseBuilder:
    """Build :class:`BookResponseBuilder` from the library-aware book service."""
    return BookResponseBuilder(book_service)


LibAwareBookServiceDep = Annotated[
    BookService, Depends(_get_library_aware_book_service)
]
LibAwareFileServiceDep = Annotated[
    BookFileService, Depends(_get_library_aware_file_service)
]
LibAwareCoverServiceDep = Annotated[
    BookCoverService, Depends(_get_library_aware_cover_service)
]
LibAwareResponseBuilderDep = Annotated[
    BookResponseBuilder, Depends(_get_library_aware_response_builder)
]


def _get_conversion_orchestration_service(
    request: Request,
    session: SessionDep,
    book_service: BookServiceDep,
    current_user: OptionalUserDep,
) -> BookConversionOrchestrationService:
    """Get book conversion orchestration service instance.

    Parameters
    ----------
    request : Request
        FastAPI request object for accessing app state.
    session : SessionDep
        Database session dependency.
    book_service : BookServiceDep
        Book service dependency.
    current_user : OptionalUserDep
        Optionally-resolved authenticated user.

    Returns
    -------
    BookConversionOrchestrationService
        Conversion orchestration service instance.

    Raises
    ------
    HTTPException
        If no active library exists.
    """
    # Get task runner (optional for read operations)
    task_runner: TaskRunner | None = None
    if hasattr(request.app.state, "task_runner"):
        task_runner = request.app.state.task_runner

    # Get active library (user-aware)
    user_id = current_user.id if current_user else None
    library = _resolve_active_library(session, user_id)
    if library is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    return BookConversionOrchestrationService(
        session=session,
        book_service=book_service,
        library=library,
        task_runner=task_runner,
    )


ConversionOrchestrationServiceDep = Annotated[
    BookConversionOrchestrationService,
    Depends(_get_conversion_orchestration_service),
]


def _get_dedrm_orchestration_service(
    request: Request,
    session: SessionDep,
    book_service: BookServiceDep,
) -> BookDeDRMOrchestrationService:
    """Get book DeDRM orchestration service instance.

    Parameters
    ----------
    request : Request
        FastAPI request object for accessing app state.
    session : SessionDep
        Database session dependency.
    book_service : BookServiceDep
        Book service dependency.

    Returns
    -------
    BookDeDRMOrchestrationService
        DeDRM orchestration service instance.
    """
    task_runner: TaskRunner | None = None
    if hasattr(request.app.state, "task_runner"):
        task_runner = request.app.state.task_runner

    return BookDeDRMOrchestrationService(
        session=session,
        book_service=book_service,
        task_runner=task_runner,
    )


DeDRMOrchestrationServiceDep = Annotated[
    BookDeDRMOrchestrationService,
    Depends(_get_dedrm_orchestration_service),
]
ResponseBuilderDep = Annotated[
    BookResponseBuilder,
    Depends(_get_response_builder),
]
CoverServiceDep = Annotated[
    BookCoverService,
    Depends(_get_cover_service),
]


def _resolve_requested_library(
    session: Session,
    current_user: User | None,
    requested_library_id: int,
) -> tuple[BookService, BookResponseBuilder, int]:
    """Build a BookService and ResponseBuilder for an explicitly requested library.

    Validates that the authenticated user has visibility access to the
    requested library (via the ``UserLibrary`` table).  Anonymous users
    are denied access.

    Parameters
    ----------
    session : Session
        Database session.
    current_user : User | None
        Authenticated user, or ``None`` for anonymous access.
    requested_library_id : int
        Library ID requested by the caller.

    Returns
    -------
    tuple[BookService, BookResponseBuilder, int]
        A ``(book_service, response_builder, library_id)`` triple for the
        requested library.

    Raises
    ------
    HTTPException
        If the user is anonymous (401), has no access (403), or the library
        does not exist (404).
    """
    from bookcard.repositories.user_library_repository import (
        UserLibraryRepository,
    )

    if current_user is None or current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication_required",
        )

    # Check the user has visibility access to the requested library
    ul_repo = UserLibraryRepository(session)
    assoc = ul_repo.find_by_user_and_library(current_user.id, requested_library_id)
    if assoc is None or not assoc.is_visible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="library_access_denied",
        )

    # Fetch the actual Library model
    lib_repo = LibraryRepository(session)
    library = lib_repo.get(requested_library_id)
    if library is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="library_not_found",
        )

    svc = BookService(library, session=session)
    builder = BookResponseBuilder(svc)
    return svc, builder, requested_library_id


def _build_multi_library_context(
    session: Session,
    user: User,
) -> tuple[dict[int, BookService], dict[int, "Library"]] | None:
    """Build per-library BookService instances for the user's visible libraries.

    Returns ``None`` when the user has only one (or zero) visible libraries,
    signaling that the caller should fall back to the single-library path.

    Parameters
    ----------
    session : Session
        Database session.
    user : User
        Authenticated user.

    Returns
    -------
    tuple[dict[int, BookService], dict[int, Library]] | None
        ``(services_map, libraries_map)`` or ``None``.
    """
    from bookcard.repositories.user_library_repository import (
        UserLibraryRepository,
    )

    if user.id is None:
        return None

    ul_repo = UserLibraryRepository(session)
    visible = ul_repo.list_visible_for_user(user.id)
    if len(visible) <= 1:
        return None

    lib_repo = LibraryRepository(session)
    services: dict[int, BookService] = {}
    libraries: dict[int, Library] = {}
    for ul in visible:
        lib = lib_repo.get(ul.library_id)
        if lib is not None and lib.id is not None:
            services[lib.id] = BookService(lib, session=session)
            libraries[lib.id] = lib
    if len(services) <= 1:
        return None
    return services, libraries


def _resolve_effective_book_service(
    session: Session,
    current_user: User | None,
    book_service: BookService,
    requested_library_id: int | None,
) -> BookService:
    """Return a :class:`BookService` for the requested library or the default.

    Used by single-book endpoints that accept an optional ``library_id``
    query parameter.

    Parameters
    ----------
    session : Session
        Database session.
    current_user : User | None
        Authenticated user (or ``None``).
    book_service : BookService
        Default book service (active library).
    requested_library_id : int | None
        Explicit library ID from the caller, or ``None`` to keep the default.

    Returns
    -------
    BookService
        Resolved service instance.
    """
    if requested_library_id is None:
        return book_service
    if book_service.library.id == requested_library_id:
        return book_service
    svc, _, _ = _resolve_requested_library(session, current_user, requested_library_id)
    return svc


@router.get("", response_model=BookListResponse)
def list_books(
    current_user: OptionalUserDep,
    book_service: BookServiceDep,
    permission_helper: PermissionHelperDep,
    response_builder: ResponseBuilderDep,
    session: SessionDep,
    library_id: ActiveLibraryIdDep,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    author_id: int | None = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    full: bool = False,
    pubdate_month: int | None = None,
    pubdate_day: int | None = None,
    include: Annotated[
        str | None,
        Query(
            description="Comma-separated list of optional includes (e.g., 'reading_summary')"
        ),
    ] = None,
    requested_library_id: Annotated[
        int | None,
        Query(
            alias="library_id",
            description="Optional library ID to list books from a specific library",
        ),
    ] = None,
) -> BookListResponse:
    """List books with pagination and optional search.

    When *requested_library_id* is supplied (via ``?library_id=``), the
    endpoint validates that the current user has access to that library
    and returns books from it instead of the user's active library.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : OptionalUserDep
        Optionally-resolved authenticated user.
    book_service : BookServiceDep
        Book service instance (active library).
    permission_helper : PermissionHelperDep
        Permission helper instance.
    response_builder : ResponseBuilderDep
        Response builder instance.
    library_id : ActiveLibraryIdDep
        Active library ID (resolved automatically).
    page : int
        Page number (1-indexed, default: 1).
    page_size : int
        Number of items per page (default: 20, max: 100).
    search : str | None
        Optional search query to filter by title or author.
    author_id : int | None
        Optional author ID to filter by.
    sort_by : str
        Field to sort by: 'timestamp', 'pubdate', 'title', 'author_sort',
        'series_index', 'random' (default: 'timestamp').
    sort_order : str
        Sort order: 'asc' or 'desc' (default: 'desc').
    full : bool
        If True, return full book details with all metadata (default: False).
    pubdate_month : int | None
        Optional month (1-12) to filter books by publication date month.
    pubdate_day : int | None
        Optional day (1-31) to filter books by publication date day.
    requested_library_id : int | None
        Optional explicit library ID to fetch books from.

    Returns
    -------
    BookListResponse
        Paginated list of books.

    Raises
    ------
    HTTPException
        If no active library is configured (404), permission denied (403),
        or requested library not accessible (403).
    """
    if current_user is not None:
        permission_helper.check_read_permission(current_user)

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    effective_library_id: int | None = library_id

    if requested_library_id is not None and requested_library_id != library_id:
        # Explicit single-library override
        eff_svc, eff_builder, effective_library_id = _resolve_requested_library(
            session, current_user, requested_library_id
        )
        books, total = eff_svc.list_books(
            page=page,
            page_size=page_size,
            search_query=search,
            author_id=author_id,
            sort_by=sort_by,
            sort_order=sort_order,
            full=full,
            pubdate_month=pubdate_month,
            pubdate_day=pubdate_day,
        )
        book_reads = eff_builder.build_book_read_list(books, full=full)
    elif (
        requested_library_id is None
        and current_user is not None
        and (ctx := _build_multi_library_context(session, current_user)) is not None
    ):
        # All-libraries view for users with >1 visible library
        services, libraries = ctx
        multi_svc = MultiLibraryBookService(libraries)
        multi_builder = MultiLibraryResponseBuilder(services)
        books, total = multi_svc.list_books(
            page=page,
            page_size=page_size,
            search_query=search,
            author_id=author_id,
            sort_by=sort_by,
            sort_order=sort_order,
            full=full,
            pubdate_month=pubdate_month,
            pubdate_day=pubdate_day,
        )
        book_reads = multi_builder.build_book_read_list(books, full=full)
        effective_library_id = None
    else:
        # Default: single active library
        books, total = book_service.list_books(
            page=page,
            page_size=page_size,
            search_query=search,
            author_id=author_id,
            sort_by=sort_by,
            sort_order=sort_order,
            full=full,
            pubdate_month=pubdate_month,
            pubdate_day=pubdate_day,
        )
        book_reads = response_builder.build_book_read_list(books, full=full)

    read_model_service = BookReadModelService(session)
    read_model_service.apply_includes(
        book_reads=book_reads,
        include=include,
        user_id=current_user.id if current_user is not None else None,
        library_id=effective_library_id,
    )
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    return BookListResponse(
        items=book_reads,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{book_id}", response_model=BookRead)
def get_book(
    current_user: OptionalUserDep,
    book_id: int,
    book_service: BookServiceDep,
    permission_helper: PermissionHelperDep,
    response_builder: ResponseBuilderDep,
    session: SessionDep,
    library_id: ActiveLibraryIdDep,
    full: bool = False,
    include: Annotated[
        str | None,
        Query(
            description="Comma-separated list of optional includes (e.g., 'reading_summary')"
        ),
    ] = None,
    requested_library_id: Annotated[
        int | None,
        Query(
            alias="library_id",
            description="Optional library ID to fetch book from a specific library",
        ),
    ] = None,
) -> BookRead:
    """Get a book by ID.

    When *requested_library_id* is supplied (via ``?library_id=``), the
    endpoint validates that the current user has access to that library
    and looks the book up there instead of in the user's active library.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : OptionalUserDep
        Optionally-resolved authenticated user.
    book_id : int
        Calibre book ID.
    book_service : BookServiceDep
        Book service instance (active library).
    permission_helper : PermissionHelperDep
        Permission helper instance.
    response_builder : ResponseBuilderDep
        Response builder instance.
    library_id : ActiveLibraryIdDep
        Active library ID (resolved automatically).
    full : bool
        If True, return full book details with all metadata (default: False).
    requested_library_id : int | None
        Optional explicit library ID to fetch the book from.

    Returns
    -------
    BookRead
        Book data.

    Raises
    ------
    HTTPException
        If book not found (404), no active library (404), permission denied (403),
        or requested library not accessible (403).
    """
    # Override book service / response builder when an explicit library is requested
    effective_book_service = book_service
    effective_response_builder = response_builder
    effective_library_id = library_id
    if requested_library_id is not None and requested_library_id != library_id:
        effective_book_service, effective_response_builder, effective_library_id = (
            _resolve_requested_library(session, current_user, requested_library_id)
        )

    if full:
        book_with_rels = effective_book_service.get_book_full(book_id)
    else:
        book_with_rels = effective_book_service.get_book(book_id)

    if book_with_rels is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    if current_user is not None:
        permission_helper.check_read_permission(current_user, book_with_rels)

    try:
        book_read = effective_response_builder.build_book_read(
            book_with_rels, full=full
        )
        read_model_service = BookReadModelService(session)
        read_model_service.apply_includes_to_one(
            book_read=book_read,
            include=include,
            user_id=current_user.id if current_user is not None else None,
            library_id=effective_library_id,
        )
    except ValueError as exc:
        raise BookExceptionMapper.map_value_error_to_http_exception(exc) from exc
    else:
        return book_read


@router.put("/{book_id}", response_model=BookRead)
def update_book(
    current_user: CurrentUserDep,
    book_id: int,
    update: BookUpdate,
    book_service: LibAwareBookServiceDep,
    permission_helper: PermissionHelperDep,
    response_builder: ResponseBuilderDep,
    session: SessionDep,
) -> BookRead:
    """Update book metadata.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    book_id : int
        Calibre book ID.
    update : BookUpdate
        Book update payload.

    Returns
    -------
    BookRead
        Updated book data with all metadata.

    Raises
    ------
    HTTPException
        If book not found (404), no active library (404), or permission denied (403).
    """
    existing_book = book_service.get_book_full(book_id)
    if existing_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    permission_helper.check_write_permission(current_user, existing_book)

    isbn_to_set: str | None = None
    # Pydantic: distinguish omitted field vs explicit null so we can clear ISBN.
    if "isbn" in update.model_fields_set:
        # Calibre stores missing ISBN as empty string; response layer maps "" -> null.
        isbn_to_set = (update.isbn or "").strip()

    updated_book = book_service.update_book(
        book_id=book_id,
        title=update.title,
        pubdate=update.pubdate,
        author_names=update.author_names,
        series_name=update.series_name,
        series_id=update.series_id,
        series_index=update.series_index,
        isbn=isbn_to_set,
        tag_names=update.tag_names,
        identifiers=update.identifiers,
        description=update.description,
        publisher_name=update.publisher_name,
        publisher_id=update.publisher_id,
        language_codes=update.language_codes,
        language_ids=update.language_ids,
        rating_value=update.rating_value,
        rating_id=update.rating_id,
        author_sort=update.author_sort,
        title_sort=update.title_sort,
    )

    if updated_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    # Trigger metadata enforcement if enabled (non-blocking)
    enforcement_trigger = MetadataEnforcementTriggerService(session=session)
    enforcement_trigger.trigger_enforcement_if_enabled(
        book_id=book_id,
        book_with_rels=updated_book,
        user_id=current_user.id,
    )

    try:
        return response_builder.build_book_read(updated_book, full=True)
    except ValueError as exc:
        raise BookExceptionMapper.map_value_error_to_http_exception(exc) from exc


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    current_user: CurrentUserDep,
    book_id: int,
    delete_request: BookDeleteRequest,
    book_service: LibAwareBookServiceDep,
    permission_helper: PermissionHelperDep,
) -> None:
    """Delete a book and all its related data.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    book_id : int
        Calibre book ID.
    delete_request : BookDeleteRequest
        Delete request payload with filesystem deletion option.

    Raises
    ------
    HTTPException
        If book not found (404), no active library (404), permission denied (403),
        or filesystem operation fails (500).
    """
    existing_book = book_service.get_book_full(book_id)
    if existing_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    permission_helper.check_write_permission(current_user, existing_book)

    try:
        book_service.delete_book(
            book_id=book_id,
            delete_files_from_drive=delete_request.delete_files_from_drive,
        )
    except ValueError as exc:
        raise BookExceptionMapper.map_value_error_to_http_exception(exc) from exc
    except OSError as exc:
        # Filesystem operation failed - return error but don't crash worker
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete files from filesystem: {exc}",
        ) from exc


@router.get("/{book_id}/cover", response_model=None)
def get_book_cover(
    current_user: OptionalUserDep,
    book_id: int,
    book_service: LibAwareBookServiceDep,
    permission_helper: PermissionHelperDep,
) -> FileResponse | Response:
    """Get book cover thumbnail image.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    book_id : int
        Calibre book ID.

    Returns
    -------
    FileResponse | Response
        Cover image file or 404 response.

    Raises
    ------
    HTTPException
        If book not found (404) or no active library (404).
    """
    book_with_rels = book_service.get_book(book_id)

    if book_with_rels is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    if current_user is not None:
        permission_helper.check_read_permission(current_user, book_with_rels)

    cover_path = book_service.get_thumbnail_path(book_with_rels)
    book_id_for_filename = book_with_rels.book.id
    if cover_path is None or not cover_path.exists():
        logger.warning(
            "Main API: Cover path not found for book %s: %s", book_id, cover_path
        )
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return FileResponse(
        path=str(cover_path),
        media_type="image/jpeg",
        filename=f"cover_{book_id_for_filename}.jpg",
    )


@router.post("/{book_id}/cover", response_model=CoverFromUrlResponse)
def upload_cover_image(
    book_id: int,
    current_user: CurrentUserDep,
    book_service: LibAwareBookServiceDep,
    permission_helper: PermissionHelperDep,
    cover_service: LibAwareCoverServiceDep,
    session: SessionDep,
    file: Annotated[UploadFile, File(...)],
) -> CoverFromUrlResponse:
    """Upload a cover image file.

    Parameters
    ----------
    book_id : int
        Calibre book ID.
    current_user : CurrentUserDep
        Current authenticated user.
    book_service : BookServiceDep
        Book service dependency.
    permission_helper : PermissionHelperDep
        Permission helper dependency.
    cover_service : CoverServiceDep
        Cover service dependency.
    session : SessionDep
        Database session dependency.
    file : UploadFile
        Cover image file.

    Returns
    -------
    CoverFromUrlResponse
        Response containing URL to access the saved cover image.

    Raises
    ------
    HTTPException
        If book not found, permission denied, or upload fails.
    """
    existing_book = book_service.get_book_full(book_id)
    if existing_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    permission_helper.check_write_permission(current_user, existing_book)

    try:
        content = file.file.read()
        cover_url = cover_service.save_cover_image(book_id, content)

        # Refresh book data to get updated cover status
        updated_book = book_service.get_book_full(book_id)

        # Trigger metadata enforcement if enabled (includes cover embedding)
        if updated_book is not None:
            enforcement_trigger = MetadataEnforcementTriggerService(session=session)
            enforcement_trigger.trigger_enforcement_if_enabled(
                book_id=book_id,
                book_with_rels=updated_book,
                user_id=current_user.id,
            )

        return CoverFromUrlResponse(temp_url=cover_url)
    except ValueError as exc:
        raise BookExceptionMapper.map_cover_error_to_http_exception(exc) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"internal_error: {exc!s}",
        ) from exc


@router.get("/{book_id}/download/{file_format}", response_model=None)
def download_book_file(
    current_user: OptionalUserDep,
    book_id: int,
    file_format: str,
    book_service: LibAwareBookServiceDep,
    permission_helper: PermissionHelperDep,
    book_file_service: LibAwareFileServiceDep,
) -> FileResponse | Response:
    """Download a book file in the specified format.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    book_id : int
        Calibre book ID.
    file_format : str
        File format (e.g., 'EPUB', 'PDF', 'MOBI').

    Returns
    -------
    FileResponse | Response
        Book file or 404 response.

    Raises
    ------
    HTTPException
        If book not found (404), format not found (404), or no active library (404).
    """
    book_with_rels = book_service.get_book_full(book_id)

    if book_with_rels is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    if current_user is not None:
        permission_helper.check_read_permission(current_user, book_with_rels)

    book = book_with_rels.book
    if book.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="book_missing_id",
        )

    format_upper = file_format.upper()
    format_data, available_formats = _find_format_data(
        book_with_rels.formats, file_format
    )
    if format_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"format_not_found: requested '{format_upper}', available: {available_formats}",
        )

    file_path, _file_name = book_file_service.resolve_file_path(
        book, book_id, file_format, format_data
    )
    media_type = _get_media_type(format_upper)
    filename = book_file_service.build_download_filename(
        book_with_rels, book_id, file_format
    )

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )


@router.get("/{book_id}/metadata", response_model=None)
def download_book_metadata(
    current_user: OptionalUserDep,
    book_id: int,
    format: str,  # noqa: A002
    book_service: LibAwareBookServiceDep,
    permission_helper: PermissionHelperDep,
) -> Response:
    """Download book metadata in the specified format.

    Generates metadata file in OPF (XML), JSON, or YAML format.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    book_id : int
        Calibre book ID.
    format : str
        Export format: 'opf', 'json', or 'yaml' (default: 'opf').

    Returns
    -------
    Response
        Metadata file response with appropriate headers.

    Raises
    ------
    HTTPException
        If book not found (404), no active library (404), or format unsupported (400).
    """
    book_with_rels = book_service.get_book_full(book_id)

    if book_with_rels is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    if current_user is not None:
        permission_helper.check_read_permission(current_user, book_with_rels)

    format_lower = format.lower() if format else "opf"
    export_service = MetadataExportService()
    try:
        export_result = export_service.export_metadata(book_with_rels, format_lower)
    except ValueError as exc:
        error_msg = str(exc)
        if "Unsupported format" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from exc

    return Response(
        content=export_result.content,
        media_type=export_result.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{export_result.filename}"',
        },
    )


@router.post(
    "/metadata/import",
    response_model=BookUpdate,
    dependencies=[Depends(get_current_user)],
)
def import_book_metadata(
    file: Annotated[UploadFile, File()],
) -> BookUpdate:
    """Import book metadata from file.

    Accepts metadata files in OPF (XML) or YAML format and returns
    a BookUpdate object ready for staging in the form.

    Parameters
    ----------
    file : UploadFile
        Metadata file to import (OPF or YAML).

    Returns
    -------
    BookUpdate
        Book update object ready for form application.

    Raises
    ------
    HTTPException
        If file format is unsupported (400), file is invalid (400),
        or parsing fails (500).
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="filename_required",
        )

    # Determine format from file extension
    file_ext = Path(file.filename).suffix.lower().lstrip(".")
    if file_ext not in ("opf", "yaml", "yml"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: {file_ext}. Supported formats: opf, yaml, yml",
        )

    # Read file content
    try:
        content_bytes = file.file.read()
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file encoding: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed_to_read_file: {exc!s}",
        ) from exc

    # Import metadata using service (SRP, IOC, SOC)
    import_service = MetadataImportService()
    try:
        book_update = import_service.import_metadata(content, file_ext)
    except ValueError as exc:
        # ValueError from import_metadata indicates unsupported format or parsing error
        error_msg = str(exc)
        if "Unsupported format" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            ) from exc
        # Other ValueError cases (parsing errors) are treated as client errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        ) from exc
    except Exception as exc:
        # Unexpected errors are treated as server errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import metadata: {exc!s}",
        ) from exc

    return book_update


@router.post("/{book_id}/send", status_code=status.HTTP_204_NO_CONTENT)
def send_book_to_device(
    request: Request,
    session: SessionDep,
    book_id: int,
    current_user: CurrentUserDep,
    send_request: BookSendRequest,
    book_service: BookServiceDep,
    permission_helper: PermissionHelperDep,
    library_id: ActiveLibraryIdDep,
) -> None:
    """Send a book via email as a background task.

    Enqueues a background task to send the book to the specified email address,
    or to the user's default device if no email is provided.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    book_id : int
        Calibre book ID.
    current_user : CurrentUserDep
        Current authenticated user.
    send_request : BookSendRequest
        Send request containing optional email and file format.

    Returns
    -------
    None
        Success response (204 No Content).

    Raises
    ------
    HTTPException
        If book not found (404), no default device when email not provided (400),
        email server not configured (400), format not found (404),
        permission denied (403), task runner unavailable (503),
        or user missing ID (500).
    """
    existing_book = book_service.get_book_full(book_id)
    if existing_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    permission_helper.check_send_permission(current_user, existing_book)

    # Get email configuration to validate it's enabled
    email_config_service = _email_config_service(request, session)
    email_config = email_config_service.get_config(decrypt=False)
    if email_config is None or not email_config.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email_server_not_configured_or_disabled",
        )

    # Validate user ID
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    # Get task runner
    if (
        not hasattr(request.app.state, "task_runner")
        or request.app.state.task_runner is None
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task runner not available",
        )
    task_runner: TaskRunner = request.app.state.task_runner

    # Get encryption key from app config
    cfg = request.app.state.config
    encryption_key = cfg.encryption_key

    task_runner.enqueue(
        task_type=TaskType.EMAIL_SEND,
        payload={
            "book_id": book_id,
            "to_email": send_request.to_email,
            "file_format": send_request.file_format,
            "encryption_key": encryption_key,  # In payload, not metadata (not stored in DB)
        },
        user_id=current_user.id,
        metadata={
            "task_type": TaskType.EMAIL_SEND,
            "book_id": book_id,
            "to_email": send_request.to_email,
            "file_format": send_request.file_format,
            "library_id": library_id,
            # encryption_key intentionally excluded from metadata to avoid exposing it
        },
    )


@router.post("/send/batch", status_code=status.HTTP_204_NO_CONTENT)
def send_books_to_device_batch(
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
    send_request: BookBulkSendRequest,
    book_service: BookServiceDep,
    permission_helper: PermissionHelperDep,
    library_id: ActiveLibraryIdDep,
) -> None:
    """Send multiple books via email as background tasks.

    Enqueues a background task for each book to send to the specified email address,
    or to the user's default device if no email is provided.
    Each book is sent individually (one book per email, as Kindle doesn't accept batches).

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    send_request : BookBulkSendRequest
        Send request containing list of book IDs, optional email and file format.

    Returns
    -------
    None
        Success response (204 No Content).

    Raises
    ------
    HTTPException
        If any book not found (404), no default device when email not provided (400),
        email server not configured (400), format not found (404),
        permission denied (403), task runner unavailable (503),
        or user missing ID (500).
    """
    if not send_request.book_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="book_ids_required",
        )

    # Get email configuration to validate it's enabled
    email_config_service = _email_config_service(request, session)
    email_config = email_config_service.get_config(decrypt=False)
    if email_config is None or not email_config.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email_server_not_configured_or_disabled",
        )

    # Validate user ID
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    # Get task runner
    if (
        not hasattr(request.app.state, "task_runner")
        or request.app.state.task_runner is None
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task runner not available",
        )
    task_runner: TaskRunner = request.app.state.task_runner

    # Get encryption key from app config
    cfg = request.app.state.config
    encryption_key = cfg.encryption_key

    # Validate all books exist and user has permission, then enqueue tasks
    for book_id in send_request.book_ids:
        existing_book = book_service.get_book_full(book_id)
        if existing_book is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"book_not_found: {book_id}",
            )

        permission_helper.check_send_permission(current_user, existing_book)

        # Enqueue task for each book
        task_runner.enqueue(
            task_type=TaskType.EMAIL_SEND,
            payload={
                "book_id": book_id,
                "to_email": send_request.to_email,
                "file_format": send_request.file_format,
                "encryption_key": encryption_key,  # In payload, not metadata (not stored in DB)
            },
            user_id=current_user.id,
            metadata={
                "task_type": TaskType.EMAIL_SEND,
                "book_id": book_id,
                "to_email": send_request.to_email,
                "file_format": send_request.file_format,
                "library_id": library_id,
                # encryption_key intentionally excluded from metadata to avoid exposing it
            },
        )


@router.post(
    "/{book_id}/convert",
    response_model=BookConvertResponse,
    status_code=status.HTTP_201_CREATED,
)
def convert_book_format(
    book_id: int,
    current_user: CurrentUserDep,
    convert_request: BookConvertRequest,
    book_service: BookServiceDep,
    permission_helper: PermissionHelperDep,
    orchestration_service: ConversionOrchestrationServiceDep,
    library_id: ActiveLibraryIdDep,
) -> BookConvertResponse:
    """Convert a book from one format to another.

    Enqueues a background task to convert the book format.
    Returns a friendly message if conversion already exists.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    book_id : int
        Calibre book ID.
    current_user : CurrentUserDep
        Current authenticated user.
    convert_request : BookConvertRequest
        Conversion request containing source and target formats.
    book_service : BookServiceDep
        Book service dependency.
    permission_helper : PermissionHelperDep
        Permission helper dependency.
    orchestration_service : ConversionOrchestrationServiceDep
        Conversion orchestration service dependency.

    Returns
    -------
    BookConvertResponse
        Response containing task ID and optional message.

    Raises
    ------
    HTTPException
        If book not found (404), format not found (404),
        permission denied (403), task runner unavailable (503),
        or user missing ID (500).
    """
    # Verify book exists for permission check
    existing_book = book_service.get_book_full(book_id)
    if existing_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    # Check create permission
    permission_helper.check_create_permission(current_user)

    # Validate user ID
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    # Delegate business logic to service
    try:
        result = orchestration_service.initiate_conversion(
            book_id=book_id,
            source_format=convert_request.source_format,
            target_format=convert_request.target_format,
            user_id=current_user.id,
            library_id=library_id,
        )
    except ValueError as e:
        # Map business exceptions to HTTP exceptions
        raise BookExceptionMapper.map_value_error_to_http_exception(e) from e
    except RuntimeError as e:
        # Map runtime errors (e.g., task runner unavailable) to HTTP exceptions
        error_msg = str(e)
        if "Task runner" in error_msg or "not available" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=error_msg,
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e

    # Build response
    return BookConvertResponse(
        task_id=result.task_id,
        message=result.message,
        existing_conversion_id=result.existing_conversion.id
        if result.existing_conversion
        else None,
    )


@router.post(
    "/{book_id}/strip-drm",
    response_model=BookStripDrmResponse,
    status_code=status.HTTP_201_CREATED,
)
def strip_book_drm(
    book_id: int,
    current_user: CurrentUserDep,
    book_service: BookServiceDep,
    permission_helper: PermissionHelperDep,
    orchestration_service: DeDRMOrchestrationServiceDep,
    library_id: ActiveLibraryIdDep,
) -> BookStripDrmResponse:
    """Strip DRM from a book format if present.

    Enqueues a background task that runs DeDRM for a selected source format.
    If DRM is removed (content changes), the DRM-free file is added as an
    additional format on the same Calibre book.

    Parameters
    ----------
    book_id : int
        Calibre book ID.
    current_user : CurrentUserDep
        Current authenticated user.
    book_service : BookServiceDep
        Book service dependency.
    permission_helper : PermissionHelperDep
        Permission helper dependency.
    orchestration_service : DeDRMOrchestrationServiceDep
        DeDRM orchestration service dependency.

    Returns
    -------
    BookStripDrmResponse
        Response containing task ID and optional message.
    """
    existing_book = book_service.get_book_full(book_id)
    if existing_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    permission_helper.check_write_permission(current_user, existing_book)

    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    try:
        result = orchestration_service.initiate_strip_drm(
            book_id=book_id,
            user_id=current_user.id,
            library_id=library_id,
        )
    except ValueError as e:
        msg = str(e)
        if "book_not_found" in msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="book_not_found",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        ) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e

    return BookStripDrmResponse(task_id=result.task_id, message=result.message)


@router.post(
    "/{book_id}/fix-epub",
    response_model=BookFixEpubResponse,
    status_code=status.HTTP_201_CREATED,
)
def fix_book_epub(
    book_id: int,
    current_user: CurrentUserDep,
    book_service: BookServiceDep,
    book_file_service: BookFileServiceDep,
    permission_helper: PermissionHelperDep,
    request: Request,
    active_library_id: ActiveLibraryIdDep,
) -> BookFixEpubResponse:
    """Fix EPUB file for a book.

    Enqueues a background task that runs the EPUB fixer on the book's EPUB file.
    Fixes common issues like encoding, stray images, and broken links.

    Parameters
    ----------
    book_id : int
        Calibre book ID.
    current_user : CurrentUserDep
        Current authenticated user.
    book_service : BookServiceDep
        Book service dependency.
    book_file_service : BookFileServiceDep
        Book file service dependency.
    permission_helper : PermissionHelperDep
        Permission helper dependency.
    request : Request
        FastAPI request object (for task runner).

    Returns
    -------
    BookFixEpubResponse
        Response containing task ID and optional message.

    Raises
    ------
    HTTPException
        If book not found (404), permission denied (403), or task runner unavailable (503).
    """
    existing_book = book_service.get_book_full(book_id)
    if existing_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    permission_helper.check_write_permission(current_user, existing_book)

    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    # Find EPUB format
    formats = existing_book.formats or []
    epub_format_data = next(
        (f for f in formats if str(f.get("format", "")).upper() == "EPUB"), None
    )

    if not epub_format_data:
        return BookFixEpubResponse(task_id=0, message="No EPUB format found")

    # Resolve file path
    try:
        file_path, _ = book_file_service.resolve_file_path(
            existing_book.book, book_id, "EPUB", epub_format_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve file path: {e}",
        ) from e

    # Get task runner
    task_runner = _get_task_runner(request)

    # Enqueue task
    metadata: dict[str, Any] = {
        "task_type": TaskType.EPUB_FIX_SINGLE.value,
        "file_path": str(file_path),
        "book_id": book_id,
        "book_title": existing_book.book.title,
        "library_id": active_library_id,
    }

    try:
        task_id = task_runner.enqueue(
            task_type=TaskType.EPUB_FIX_SINGLE,
            payload={},  # Empty payload, all data in metadata
            user_id=current_user.id,
            metadata=metadata,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue fix task: {e}",
        ) from e

    return BookFixEpubResponse(task_id=task_id, message="EPUB fix task created")


@router.get(
    "/{book_id}/conversions",
    response_model=BookConversionListResponse,
)
def get_book_conversions(
    book_id: int,
    current_user: CurrentUserDep,
    book_service: LibAwareBookServiceDep,
    permission_helper: PermissionHelperDep,
    orchestration_service: ConversionOrchestrationServiceDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> BookConversionListResponse:
    """Get conversion history for a book.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    book_id : int
        Calibre book ID.
    current_user : CurrentUserDep
        Current authenticated user.
    book_service : BookServiceDep
        Book service dependency.
    permission_helper : PermissionHelperDep
        Permission helper dependency.
    orchestration_service : ConversionOrchestrationServiceDep
        Conversion orchestration service dependency.
    page : int
        Page number (1-indexed).
    page_size : int
        Number of items per page.

    Returns
    -------
    BookConversionListResponse
        Paginated list of conversion records.

    Raises
    ------
    HTTPException
        If book not found (404) or permission denied (403).
    """
    # Verify book exists for permission check
    existing_book = book_service.get_book_full(book_id)
    if existing_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    # Check read permission
    permission_helper.check_read_permission(current_user, existing_book)

    # Delegate business logic to service
    try:
        result = orchestration_service.get_conversions(
            book_id=book_id,
            page=page,
            page_size=page_size,
        )
    except ValueError as e:
        # Map business exceptions to HTTP exceptions
        raise BookExceptionMapper.map_value_error_to_http_exception(e) from e

    items = [
        BookConversionRead(
            id=conv.id or 0,
            book_id=conv.book_id,
            original_format=conv.original_format,
            target_format=conv.target_format,
            conversion_method=conv.conversion_method.value,
            status=conv.status.value,
            error_message=conv.error_message,
            original_backed_up=conv.original_backed_up,
            created_at=conv.created_at,
            completed_at=conv.completed_at,
            duration=conv.duration,
        )
        for conv in result.conversions
    ]

    return BookConversionListResponse(
        items=items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


# Temporary cover storage (in-memory for now, could be moved to disk/DB)
_temp_cover_storage: dict[str, Path] = {}


@router.post("/{book_id}/cover-from-url", response_model=CoverFromUrlResponse)
def download_cover_from_url(
    current_user: CurrentUserDep,
    book_id: int,
    request: CoverFromUrlRequest,
    book_service: LibAwareBookServiceDep,
    permission_helper: PermissionHelperDep,
    cover_service: LibAwareCoverServiceDep,
    session: SessionDep,
) -> CoverFromUrlResponse:
    """Download cover image from URL and save directly to book.

    Downloads an image from the provided URL, validates it's an image,
    saves it directly to the book's directory as cover.jpg, updates
    the database to mark the book as having a cover, and embeds the
    cover into supported ebook files (EPUB, AZW3) for device compatibility.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    book_id : int
        Calibre book ID.
    request : CoverFromUrlRequest
        Request containing the image URL.

    Returns
    -------
    CoverFromUrlResponse
        Response containing URL to access the saved cover image.

    Raises
    ------
    HTTPException
        If book not found (404), URL is invalid (400), image download fails (400),
        or image validation fails (400).
    """
    url = request.url.strip()
    book_with_rels = book_service.get_book_full(book_id)

    if book_with_rels is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    permission_helper.check_write_permission(current_user, book_with_rels)

    try:
        cover_url = cover_service.save_cover_from_url(book_id, url)

        # Refresh book data to get updated cover status
        updated_book_with_rels = book_service.get_book_full(book_id)

        # Trigger metadata enforcement if enabled (includes cover embedding)
        # This embeds the cover into EPUB/AZW3 files for Kindle compatibility
        if updated_book_with_rels is not None:
            enforcement_trigger = MetadataEnforcementTriggerService(session=session)
            enforcement_trigger.trigger_enforcement_if_enabled(
                book_id=book_id,
                book_with_rels=updated_book_with_rels,
                user_id=current_user.id,
            )

        return CoverFromUrlResponse(temp_url=cover_url)
    except ValueError as exc:
        raise BookExceptionMapper.map_cover_error_to_http_exception(exc) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"internal_error: {exc!s}",
        ) from exc


@router.get("/temp-covers/{hash_and_ext}", response_model=None)
def get_temp_cover(
    hash_and_ext: str,
    current_user: CurrentUserDep,
    permission_helper: PermissionHelperDep,
) -> FileResponse | Response:
    """Serve temporary cover image.

    Parameters
    ----------
    hash_and_ext : str
        Hash and extension (e.g., "abc123def456.jpg").
    current_user : CurrentUserDep
        Current authenticated user.
    permission_helper : PermissionHelperDep
        Permission helper instance.

    Returns
    -------
    FileResponse | Response
        Cover image file or 404 response.

    Raises
    ------
    HTTPException
        If permission denied (403).
    """
    permission_helper.check_read_permission(current_user)
    # Extract hash from filename
    if "." not in hash_and_ext:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    content_hash = hash_and_ext.rsplit(".", 1)[0]

    if content_hash not in _temp_cover_storage:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    temp_path = _temp_cover_storage[content_hash]
    if not temp_path.exists():
        # Clean up stale entry
        _temp_cover_storage.pop(content_hash, None)
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return FileResponse(
        path=str(temp_path),
        media_type="image/jpeg",
    )


@router.get("/search/suggestions", response_model=SearchSuggestionsResponse)
def search_suggestions(
    current_user: OptionalUserDep,
    q: str,
    book_service: LibAwareBookServiceDep,
    permission_helper: PermissionHelperDep,
) -> SearchSuggestionsResponse:
    """Get search suggestions for autocomplete.

    Searches across book titles, authors, tags, and series.
    Returns top matches for each category.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    q : str
        Search query string.

    Returns
    -------
    SearchSuggestionsResponse
        Search suggestions grouped by type (books, authors, tags, series).

    Raises
    ------
    HTTPException
        If no active library is configured (404).
    """
    if current_user is not None:
        permission_helper.check_read_permission(current_user)

    if not q or not q.strip():
        return SearchSuggestionsResponse()

    results = book_service.search_suggestions(
        query=q,
        book_limit=5,
        author_limit=5,
        tag_limit=5,
        series_limit=5,
    )

    return SearchSuggestionsResponse(
        books=[
            SearchSuggestionItem(id=int(item["id"]), name=str(item["name"]))
            for item in results["books"]
        ],
        authors=[
            SearchSuggestionItem(id=int(item["id"]), name=str(item["name"]))
            for item in results["authors"]
        ],
        tags=[
            SearchSuggestionItem(id=int(item["id"]), name=str(item["name"]))
            for item in results["tags"]
        ],
        series=[
            SearchSuggestionItem(id=int(item["id"]), name=str(item["name"]))
            for item in results["series"]
        ],
    )


@router.get("/filter/suggestions", response_model=FilterSuggestionsResponse)
def filter_suggestions(
    current_user: OptionalUserDep,
    q: str,
    filter_type: str,
    book_service: LibAwareBookServiceDep,
    permission_helper: PermissionHelperDep,
    limit: int = 10,
) -> FilterSuggestionsResponse:
    """Get filter suggestions for a specific filter type.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    q : str
        Search query string.
    filter_type : str
        Type of filter: 'author', 'title', 'genre', 'publisher',
        'identifier', 'series', 'format', 'rating', 'language'.
    limit : int
        Maximum number of suggestions to return (default: 10).

    Returns
    -------
    FilterSuggestionsResponse
        Filter suggestions for the specified type.

    Raises
    ------
    HTTPException
        If no active library is configured (404).
    """
    if current_user is not None:
        permission_helper.check_read_permission(current_user)

    if not q or not q.strip():
        return FilterSuggestionsResponse()

    results = book_service.filter_suggestions(
        query=q,
        filter_type=filter_type,
        limit=limit,
    )

    return FilterSuggestionsResponse(
        suggestions=[
            SearchSuggestionItem(id=int(item["id"]), name=str(item["name"]))
            for item in results
        ]
    )


@router.get("/tags/by-name", response_model=TagLookupResponse)
def lookup_tags_by_name(
    current_user: OptionalUserDep,
    book_service: LibAwareBookServiceDep,
    permission_helper: PermissionHelperDep,
    names: str = Query(..., description="Comma-separated list of tag names to lookup"),
) -> TagLookupResponse:
    """Lookup tag IDs by tag names (case-insensitive).

    Parameters
    ----------
    current_user : CurrentUserDep
        Current authenticated user.
    book_service : BookServiceDep
        Book service instance.
    permission_helper : PermissionHelperDep
        Permission helper instance.
    names : str
        Comma-separated list of tag names to lookup.

    Returns
    -------
    TagLookupResponse
        List of matching tags with IDs.

    Raises
    ------
    HTTPException
        If permission denied (403).
    """
    if current_user is not None:
        permission_helper.check_read_permission(current_user)

    # Parse comma-separated names
    tag_names = [name.strip() for name in names.split(",") if name.strip()]

    if not tag_names:
        return TagLookupResponse(tags=[])

    results = book_service.lookup_tags_by_names(tag_names=tag_names)

    return TagLookupResponse(
        tags=[
            TagLookupItem(id=int(item["id"]), name=str(item["name"]))
            for item in results
        ]
    )


@router.post("/filter", response_model=BookListResponse)
def filter_books(
    current_user: OptionalUserDep,
    filter_request: BookFilterRequest,
    book_service: BookServiceDep,
    permission_helper: PermissionHelperDep,
    response_builder: ResponseBuilderDep,
    session: SessionDep,
    library_id: ActiveLibraryIdDep,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    full: bool = False,
    include: Annotated[
        str | None,
        Query(
            description="Comma-separated list of optional includes (e.g., 'reading_summary')"
        ),
    ] = None,
    requested_library_id: Annotated[
        int | None,
        Query(
            alias="library_id",
            description="Optional library ID to filter books from a specific library",
        ),
    ] = None,
) -> BookListResponse:
    """Filter books with multiple criteria using OR conditions.

    Each filter type uses OR conditions (e.g., multiple authors = OR).
    Different filter types are combined with AND conditions.

    When *requested_library_id* is supplied (via ``?library_id=``), the
    endpoint validates that the current user has access to that library
    and returns filtered books from it instead of the user's active library.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    filter_request : BookFilterRequest
        Filter criteria.
    page : int
        Page number (1-indexed, default: 1).
    page_size : int
        Number of items per page (default: 20, max: 100).
    sort_by : str
        Field to sort by: 'timestamp', 'pubdate', 'title', 'author_sort',
        'series_index' (default: 'timestamp').
    sort_order : str
        Sort order: 'asc' or 'desc' (default: 'desc').
    full : bool
        If True, return full book details with all metadata (default: False).
    requested_library_id : int | None
        Optional explicit library ID to filter books from.

    Returns
    -------
    BookListResponse
        Paginated list of filtered books.

    Raises
    ------
    HTTPException
        If no active library is configured (404) or permission denied (403).
    """
    if current_user is not None:
        permission_helper.check_read_permission(current_user)

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    filter_kwargs: dict = {
        "author_ids": filter_request.author_ids,
        "title_ids": filter_request.title_ids,
        "genre_ids": filter_request.genre_ids,
        "publisher_ids": filter_request.publisher_ids,
        "identifier_ids": filter_request.identifier_ids,
        "series_ids": filter_request.series_ids,
        "formats": filter_request.formats,
        "rating_ids": filter_request.rating_ids,
        "language_ids": filter_request.language_ids,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "full": full,
    }

    effective_library_id: int | None = library_id

    if requested_library_id is not None and requested_library_id != library_id:
        eff_svc, eff_builder, effective_library_id = _resolve_requested_library(
            session, current_user, requested_library_id
        )
        books, total = eff_svc.list_books_with_filters(
            page=page,
            page_size=page_size,
            **filter_kwargs,
        )
        book_reads = eff_builder.build_book_read_list(books, full=full)
    elif (
        requested_library_id is None
        and current_user is not None
        and (ctx := _build_multi_library_context(session, current_user)) is not None
    ):
        services, libraries = ctx
        multi_svc = MultiLibraryBookService(libraries)
        multi_builder = MultiLibraryResponseBuilder(services)
        books, total = multi_svc.list_books_with_filters(
            page=page,
            page_size=page_size,
            **filter_kwargs,
        )
        book_reads = multi_builder.build_book_read_list(books, full=full)
        effective_library_id = None
    else:
        books, total = book_service.list_books_with_filters(
            page=page,
            page_size=page_size,
            **filter_kwargs,
        )
        book_reads = response_builder.build_book_read_list(books, full=full)

    read_model_service = BookReadModelService(session)
    read_model_service.apply_includes(
        book_reads=book_reads,
        include=include,
        user_id=current_user.id if current_user is not None else None,
        library_id=effective_library_id,
    )
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    return BookListResponse(
        items=book_reads,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/upload",
    response_model=BookUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_book(
    request: Request,
    current_user: CurrentUserDep,
    file: UploadFile,
    permission_helper: PermissionHelperDep,
    session: SessionDep,
    library_id: ActiveLibraryIdDep,
) -> BookUploadResponse:
    """Upload a book file to the active library (asynchronous).

    Accepts a book file, saves it temporarily, and creates a background task
    to add it to the Calibre database. Returns the task ID for tracking.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    file : UploadFile
        Book file to upload.

    Returns
    -------
    BookUploadResponse
        Response containing the task ID for tracking the upload.

    Raises
    ------
    HTTPException
        If no active library is configured (404), file is invalid (400),
        permission denied (403), or task runner unavailable (503).
    """
    permission_helper.check_create_permission(current_user)

    # Get task runner
    if (
        not hasattr(request.app.state, "task_runner")
        or request.app.state.task_runner is None
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task runner not available",
        )
    task_runner = request.app.state.task_runner

    # Validate file extension
    file_ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if not file_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_extension_required",
        )

    # Validate file format against allowed formats
    file_handling_service = FileHandlingConfigService(session)
    if not file_handling_service.is_format_allowed(file_ext):
        allowed_formats = file_handling_service.get_allowed_upload_formats()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File format '{file_ext}' is not allowed. Allowed formats: {', '.join(allowed_formats)}",
        )

    # Save file to temporary location
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=f".{file_ext}",
        prefix="calibre_upload_",
    ) as temp_file:
        temp_path = Path(temp_file.name)
        try:
            # Read and write file content
            content = file.file.read()
            temp_path.write_bytes(content)
        except Exception as exc:
            temp_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"failed_to_save_file: {exc!s}",
            ) from exc

        # Extract title from filename if possible
        filename = file.filename or "Unknown"
        title = Path(filename).stem if filename else None

    # Create upload task
    # Enqueue task with file path in payload
    # Task record will be created by the runner
    task_id = task_runner.enqueue(
        task_type=TaskType.BOOK_UPLOAD,
        payload={
            "file_path": str(temp_path),
            "filename": filename,
            "file_format": file_ext,
            "title": title,
        },
        user_id=current_user.id or 0,
        metadata={
            "task_type": TaskType.BOOK_UPLOAD,
            "filename": filename,
            "file_format": file_ext,
            "library_id": library_id,
        },
    )

    return BookUploadResponse(task_id=task_id)


@router.post(
    "/{book_id}/formats",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
)
def add_format(
    book_id: int,
    current_user: CurrentUserDep,
    book_service: LibAwareBookServiceDep,
    permission_helper: PermissionHelperDep,
    response_builder: ResponseBuilderDep,
    file: Annotated[UploadFile, File(...)],
    replace: bool = False,
) -> BookRead:
    """Add a new file format to an existing book.

    Parameters
    ----------
    book_id : int
        Book ID.
    current_user : CurrentUserDep
        Current authenticated user.
    book_service : BookServiceDep
        Book service instance.
    permission_helper : PermissionHelperDep
        Permission helper instance.
    response_builder : ResponseBuilderDep
        Response builder instance.
    file : UploadFile
        File to upload.
    replace : bool
        Whether to replace existing format.

    Returns
    -------
    BookRead
        Updated book data.

    Raises
    ------
    HTTPException
        If book not found (404), file exists (409), invalid file (400),
        or permission denied (403).
    """
    # Verify book exists
    existing_book = book_service.get_book_full(book_id)
    if existing_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    permission_helper.check_write_permission(current_user, existing_book)

    try:
        content = file.file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed_to_read_file: {exc!s}",
        ) from exc

    try:
        book_service.add_format_from_content(
            book_id=book_id,
            file_content=content,
            filename=file.filename or "",
            replace=replace,
        )
    except FileExistsError as exc:
        # 409 Conflict for existing format
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        if "book_not_found" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="book_not_found",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed_to_add_format: {exc!s}",
        ) from exc

    # Return updated book
    updated_book = book_service.get_book_full(book_id)
    if updated_book is None:
        # Should not happen if add_format succeeded
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    return response_builder.build_book_read(updated_book, full=True)


@router.get(
    "/{book_id}/formats/{file_format}/metadata",
    response_model=FormatMetadataResponse,
)
def get_format_metadata(
    book_id: int,
    file_format: str,
    current_user: OptionalUserDep,
    permission_helper: PermissionHelperDep,
    book_service: LibAwareBookServiceDep,
) -> FormatMetadataResponse:
    """Get detailed metadata for a specific format.

    Parameters
    ----------
    book_id : int
        Book ID.
    file_format : str
        Format extension (e.g. 'epub').
    current_user : CurrentUserDep
        Current authenticated user.
    session : SessionDep
        Database session.
    permission_helper : PermissionHelperDep
        Permission helper instance.
    book_service : BookServiceDep
        Book service instance.

    Returns
    -------
    FormatMetadataResponse
        Detailed format metadata.

    Raises
    ------
    HTTPException
        If book not found, format not found, or permission denied.
    """
    # Verify book exists
    existing_book = book_service.get_book_full(book_id)
    if existing_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    if current_user is not None:
        permission_helper.check_read_permission(current_user, existing_book)

    # Use the repository from the book service to initialize the metadata service
    # This accesses the private _book_repo, which is generally discouraged but necessary
    # here as we are in the API layer wiring things up. Ideally BookService would expose this.
    # Alternatively, we could inject CalibreBookRepository directly if we had a dependency for it.
    # Given the current structure, accessing _book_repo is the most straightforward path.
    # pylint: disable=protected-access
    metadata_service = FormatMetadataService(book_service._book_repo)  # noqa: SLF001

    try:
        return metadata_service.get_format_metadata(book_id, file_format)
    except ValueError as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed_to_get_metadata: {exc!s}",
        ) from exc


@router.delete(
    "/{book_id}/formats/{file_format}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_format(
    book_id: int,
    file_format: str,
    current_user: CurrentUserDep,
    book_service: LibAwareBookServiceDep,
    permission_helper: PermissionHelperDep,
) -> None:
    """Delete a format from an existing book.

    Parameters
    ----------
    book_id : int
        Book ID.
    file_format : str
        Format extension (e.g. 'epub').
    current_user : CurrentUserDep
        Current authenticated user.
    book_service : BookServiceDep
        Book service instance.
    permission_helper : PermissionHelperDep
        Permission helper instance.

    Raises
    ------
    HTTPException
        If book not found (404), format not found (404),
        or permission denied (403).
    """
    # Verify book exists
    existing_book = book_service.get_book_full(book_id)
    if existing_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    permission_helper.check_write_permission(current_user, existing_book)

    try:
        book_service.delete_format(
            book_id=book_id,
            file_format=file_format,
            delete_file_from_drive=True,
        )
    except ValueError as exc:
        if "book_not_found" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="book_not_found",
            ) from exc
        if "not found" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed_to_delete_format: {exc!s}",
        ) from exc


def _get_task_runner(request: Request) -> "TaskRunner":
    """Get and validate task runner from request app state.

    Parameters
    ----------
    request : Request
        FastAPI request object.

    Returns
    -------
    object
        Task runner instance.

    Raises
    ------
    HTTPException
        If task runner is not available.
    """
    if (
        not hasattr(request.app.state, "task_runner")
        or request.app.state.task_runner is None
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task runner not available",
        )
    return request.app.state.task_runner


def _validate_files(files: list[UploadFile]) -> None:
    """Validate that files list is not empty.

    Parameters
    ----------
    files : list[UploadFile]
        List of files to validate.

    Raises
    ------
    HTTPException
        If files list is empty.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided",
        )


### End of File


def _save_file_to_temp(
    file: UploadFile,
    temp_paths: list[Path],
    session: Session,
) -> dict[str, str | None]:
    """Save a single file to temporary location.

    Parameters
    ----------
    file : UploadFile
        File to save.
    temp_paths : list[Path]
        List of temporary paths (mutated to add new path).

    Returns
    -------
    dict[str, str | None]
        File info dictionary with file_path, filename, file_format, title.

    Raises
    ------
    HTTPException
        If file extension is missing or file save fails.
    """
    # Validate file extension
    file_ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if not file_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"file_extension_required: {file.filename}",
        )

    # Validate file format against allowed formats
    file_handling_service = FileHandlingConfigService(session)
    if not file_handling_service.is_format_allowed(file_ext):
        allowed_formats = file_handling_service.get_allowed_upload_formats()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File format '{file_ext}' is not allowed for file '{file.filename}'. Allowed formats: {', '.join(allowed_formats)}",
        )

    # Save file to temporary location
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=f".{file_ext}",
        prefix="calibre_upload_",
    ) as temp_file:
        temp_path = Path(temp_file.name)
        try:
            content = file.file.read()
            temp_path.write_bytes(content)
            temp_paths.append(temp_path)

            filename = file.filename or "Unknown"
            title = Path(filename).stem if filename else None

            return {
                "file_path": str(temp_path),
                "filename": filename,
                "file_format": file_ext,
                "title": title,
            }
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"failed_to_save_file: {exc!s}",
            ) from exc


def _save_files_to_temp(
    files: list[UploadFile],
    session: Session,
) -> tuple[list[dict[str, str | None]], list[Path]]:
    """Save all files to temporary locations.

    Parameters
    ----------
    files : list[UploadFile]
        List of files to save.

    Returns
    -------
    tuple[list[dict[str, str | None]], list[Path]]
        Tuple of (file_infos, temp_paths).

    Raises
    ------
    HTTPException
        If any file save fails.
    """
    file_infos = []
    temp_paths = []

    try:
        for file in files:
            file_info = _save_file_to_temp(file, temp_paths, session)
            file_infos.append(file_info)
    except HTTPException:
        # Clean up already saved files
        for path in temp_paths:
            path.unlink(missing_ok=True)
        raise
    else:
        return file_infos, temp_paths


def _enqueue_batch_upload_task(
    task_runner: "TaskRunner",
    file_infos: list[dict[str, str | None]],
    user_id: int,
    library_id: int | None = None,
) -> int:
    """Enqueue batch upload task.

    Parameters
    ----------
    task_runner : TaskRunner
        Task runner instance.
    file_infos : list[dict[str, str | None]]
        List of file info dictionaries.
    user_id : int
        User ID for the task.
    library_id : int | None
        Target library ID for the upload.

    Returns
    -------
    int
        Task ID.
    """
    metadata: dict[str, object] = {
        "task_type": TaskType.MULTI_BOOK_UPLOAD,
        "total_files": len(file_infos),
    }
    if library_id is not None:
        metadata["library_id"] = library_id

    task_id = task_runner.enqueue(
        task_type=TaskType.MULTI_BOOK_UPLOAD,
        payload={"files": file_infos},
        user_id=user_id,
        metadata=metadata,
    )
    return task_id  # noqa: RET504


@router.post(
    "/upload/batch",
    response_model=BookBatchUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_books_batch(
    request: Request,
    current_user: CurrentUserDep,
    permission_helper: PermissionHelperDep,
    session: SessionDep,
    library_id: ActiveLibraryIdDep,
    files: Annotated[list[UploadFile], File(...)],
) -> BookBatchUploadResponse:
    """Upload multiple book files to the active library (asynchronous).

    Accepts multiple book files, saves them temporarily, and creates a
    background task to add them to the Calibre database. Returns the task ID
    for tracking.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    library_id : ActiveLibraryIdDep
        Active library ID (resolved automatically).
    files : list[UploadFile]
        List of book files to upload.

    Returns
    -------
    BookBatchUploadResponse
        Response containing the task ID and total file count.

    Raises
    ------
    HTTPException
        If no active library is configured (404), files are invalid (400),
        permission denied (403), or task runner unavailable (503).
    """
    permission_helper.check_create_permission(current_user)

    task_runner = _get_task_runner(request)
    _validate_files(files)

    temp_paths: list[Path] = []
    try:
        file_infos, temp_paths = _save_files_to_temp(files, session)
        task_id = _enqueue_batch_upload_task(
            task_runner, file_infos, current_user.id or 0, library_id=library_id
        )
        return BookBatchUploadResponse(task_id=task_id, total_files=len(file_infos))
    except HTTPException:
        raise
    except Exception as exc:
        # Clean up on unexpected error
        for path in temp_paths:
            path.unlink(missing_ok=True)
        error_msg = f"failed_to_process_upload: {exc!s}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from exc


@router.post(
    "/merge/recommend",
    response_model=dict[str, object],
    dependencies=[Depends(get_current_user)],
)
def recommend_merge_book(
    request_body: BookMergeRecommendRequest,
    current_user: CurrentUserDep,
    book_service: BookServiceDep,
    merge_service: BookMergeServiceDep,
    permission_helper: PermissionHelperDep,
) -> dict[str, object]:
    """Recommend which book to keep when merging.

    Parameters
    ----------
    request_body : BookMergeRecommendRequest
        Request with list of book IDs to merge.
    current_user : CurrentUserDep
        Current authenticated user.
    book_service : BookServiceDep
        Book service instance.
    merge_service : BookMergeServiceDep
        Book merge service instance.
    permission_helper : PermissionHelperDep
        Permission helper instance.

    Returns
    -------
    dict[str, object]
        Dictionary with recommended keep book ID and book details.

    Raises
    ------
    HTTPException
        If validation fails, books not found, or permission denied.
    """
    # Check write permission for all books being merged
    for book_id in request_body.book_ids:
        book = book_service.get_book_full(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book not found: {book_id}",
            )
        permission_helper.check_write_permission(current_user, book)

    try:
        return merge_service.recommend_keep_book(request_body.book_ids)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/merge",
    response_model=dict[str, object],
    dependencies=[Depends(get_current_user)],
)
def merge_books(
    request_body: BookMergeRequest,
    current_user: CurrentUserDep,
    book_service: BookServiceDep,
    merge_service: BookMergeServiceDep,
    permission_helper: PermissionHelperDep,
) -> dict[str, object]:
    """Merge multiple books into one.

    Parameters
    ----------
    request_body : BookMergeRequest
        Request with list of book IDs and keep book ID.
    current_user : CurrentUserDep
        Current authenticated user.
    book_service : BookServiceDep
        Book service instance.
    merge_service : BookMergeServiceDep
        Book merge service instance.
    permission_helper : PermissionHelperDep
        Permission helper instance.

    Returns
    -------
    dict[str, object]
        Dictionary with merged book details.

    Raises
    ------
    HTTPException
        If validation fails, books not found, merge fails, or permission denied.
    """
    # Check write permission for all books being merged
    for book_id in request_body.book_ids:
        book = book_service.get_book_full(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book not found: {book_id}",
            )
        permission_helper.check_write_permission(current_user, book)

    try:
        return merge_service.merge_books(
            request_body.book_ids,
            request_body.keep_book_id,
        )
    except (ValueError, BookMergeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

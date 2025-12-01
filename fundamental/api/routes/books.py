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

import math
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from fundamental.services.book_conversion_orchestration_service import (
    BookConversionOrchestrationService,
)
from fundamental.services.metadata_enforcement_trigger_service import (
    MetadataEnforcementTriggerService,
)

if TYPE_CHECKING:
    from fundamental.services.tasks.base import TaskRunner

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

from fundamental.api.deps import get_current_user, get_db_session
from fundamental.api.schemas import (
    BookBatchUploadResponse,
    BookBulkSendRequest,
    BookConversionListResponse,
    BookConversionRead,
    BookConvertRequest,
    BookConvertResponse,
    BookDeleteRequest,
    BookFilterRequest,
    BookListResponse,
    BookRead,
    BookSendRequest,
    BookUpdate,
    BookUploadResponse,
    CoverFromUrlRequest,
    CoverFromUrlResponse,
    FilterSuggestionsResponse,
    SearchSuggestionItem,
    SearchSuggestionsResponse,
    TagLookupItem,
    TagLookupResponse,
)
from fundamental.models.auth import User
from fundamental.models.tasks import TaskType
from fundamental.repositories.config_repository import LibraryRepository
from fundamental.services.book_cover_service import BookCoverService
from fundamental.services.book_exception_mapper import BookExceptionMapper
from fundamental.services.book_permission_helper import BookPermissionHelper
from fundamental.services.book_response_builder import BookResponseBuilder
from fundamental.services.book_service import BookService
from fundamental.services.config_service import (
    FileHandlingConfigService,
    LibraryService,
)
from fundamental.services.email_config_service import EmailConfigService
from fundamental.services.metadata_export_service import MetadataExportService
from fundamental.services.metadata_import_service import MetadataImportService
from fundamental.services.security import DataEncryptor

if TYPE_CHECKING:
    from fundamental.services.tasks.base import TaskRunner

router = APIRouter(prefix="/books", tags=["books"])

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]

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


def _get_file_name(
    format_data: dict[str, str | int],
    book_id: int,
    file_format: str,
) -> str:
    """Get filename for the book file.

    Parameters
    ----------
    format_data : dict[str, str | int]
        Format data dictionary, may contain 'name' field.
    book_id : int
        Book ID for fallback naming.
    file_format : str
        File format extension.

    Returns
    -------
    str
        Filename for the book file.
    """
    file_name = format_data.get("name", "")
    if not file_name or not isinstance(file_name, str):
        # Calibre standard naming: {book_id}.{format_lower}
        return f"{book_id}.{file_format.lower()}"

    # Ensure filename has the correct extension
    expected_suffix = f".{file_format.lower()}"
    if not file_name.lower().endswith(expected_suffix):
        return f"{file_name}{expected_suffix}"
    return file_name


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
) -> BookService:
    """Get book service for the active library.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    BookService
        Book service instance.

    Raises
    ------
    HTTPException
        If no active library is configured (404).
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    library = library_service.get_active_library()

    if library is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    return BookService(library, session=session)


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


BookServiceDep = Annotated[BookService, Depends(_get_active_library_service)]
PermissionHelperDep = Annotated[
    BookPermissionHelper,
    Depends(_get_permission_helper),
]


def _get_conversion_orchestration_service(
    request: Request,
    session: SessionDep,
    book_service: BookServiceDep,
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

    # Get active library
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    library = library_service.get_active_library()
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
ResponseBuilderDep = Annotated[
    BookResponseBuilder,
    Depends(_get_response_builder),
]
CoverServiceDep = Annotated[
    BookCoverService,
    Depends(_get_cover_service),
]


@router.get("", response_model=BookListResponse)
def list_books(
    current_user: CurrentUserDep,
    book_service: BookServiceDep,
    permission_helper: PermissionHelperDep,
    response_builder: ResponseBuilderDep,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    author_id: int | None = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    full: bool = False,
    pubdate_month: int | None = None,
    pubdate_day: int | None = None,
) -> BookListResponse:
    """List books with pagination and optional search.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    book_service : BookServiceDep
        Book service instance.
    permission_helper : PermissionHelperDep
        Permission helper instance.
    response_builder : ResponseBuilderDep
        Response builder instance.
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

    Returns
    -------
    BookListResponse
        Paginated list of books.

    Raises
    ------
    HTTPException
        If no active library is configured (404) or permission denied (403).
    """
    permission_helper.check_read_permission(current_user)

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

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
    current_user: CurrentUserDep,
    book_id: int,
    book_service: BookServiceDep,
    permission_helper: PermissionHelperDep,
    response_builder: ResponseBuilderDep,
    full: bool = False,
) -> BookRead:
    """Get a book by ID.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    book_id : int
        Calibre book ID.
    book_service : BookServiceDep
        Book service instance.
    permission_helper : PermissionHelperDep
        Permission helper instance.
    response_builder : ResponseBuilderDep
        Response builder instance.
    full : bool
        If True, return full book details with all metadata (default: False).

    Returns
    -------
    BookRead
        Book data.

    Raises
    ------
    HTTPException
        If book not found (404), no active library (404), or permission denied (403).
    """
    if full:
        book_with_rels = book_service.get_book_full(book_id)
    else:
        book_with_rels = book_service.get_book(book_id)

    if book_with_rels is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    permission_helper.check_read_permission(current_user, book_with_rels)

    try:
        return response_builder.build_book_read(book_with_rels, full=full)
    except ValueError as exc:
        raise BookExceptionMapper.map_value_error_to_http_exception(exc) from exc


@router.put("/{book_id}", response_model=BookRead)
def update_book(
    current_user: CurrentUserDep,
    book_id: int,
    update: BookUpdate,
    book_service: BookServiceDep,
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

    updated_book = book_service.update_book(
        book_id=book_id,
        title=update.title,
        pubdate=update.pubdate,
        author_names=update.author_names,
        series_name=update.series_name,
        series_id=update.series_id,
        series_index=update.series_index,
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
    book_service: BookServiceDep,
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
    current_user: CurrentUserDep,
    book_id: int,
    book_service: BookServiceDep,
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

    permission_helper.check_read_permission(current_user, book_with_rels)

    cover_path = book_service.get_thumbnail_path(book_with_rels)
    book_id_for_filename = book_with_rels.book.id
    if cover_path is None or not cover_path.exists():
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return FileResponse(
        path=str(cover_path),
        media_type="image/jpeg",
        filename=f"cover_{book_id_for_filename}.jpg",
    )


@router.get("/{book_id}/download/{file_format}", response_model=None)
def download_book_file(
    current_user: CurrentUserDep,
    book_id: int,
    file_format: str,
    book_service: BookServiceDep,
    permission_helper: PermissionHelperDep,
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

    permission_helper.check_read_permission(current_user, book_with_rels)

    book = book_with_rels.book
    if book.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="book_missing_id",
        )

    # Find the format in the book's formats
    format_upper = file_format.upper()
    format_data, available_formats = _find_format_data(
        book_with_rels.formats, file_format
    )

    if format_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"format_not_found: requested '{format_upper}', available: {available_formats}",
        )

    # Construct file path: library_root / book.path / file_name
    # Prefer explicit library_root from config when provided
    lib_root = getattr(book_service._library, "library_root", None)  # type: ignore[attr-defined]  # noqa: SLF001
    if lib_root:
        library_path = Path(lib_root)
    else:
        # Determine library root robustly from configured calibre_db_path
        library_db_path = book_service._library.calibre_db_path  # type: ignore[attr-defined]  # noqa: SLF001
        library_db_path_obj = Path(library_db_path)
        # If calibre_db_path points to a directory, use it directly.
        # If it points to a file (e.g., metadata.db), use its parent directory.
        if library_db_path_obj.is_dir():
            library_path = library_db_path_obj
        else:
            library_path = library_db_path_obj.parent
    book_path = library_path / book.path
    file_name = _get_file_name(format_data, book_id, file_format)
    file_path = book_path / file_name

    if not file_path.exists():
        # Try alternative: just the format extension
        alt_file_name = f"{book_id}.{file_format.lower()}"
        alt_file_path = book_path / alt_file_name
        if alt_file_path.exists():
            file_path = alt_file_path
            file_name = alt_file_name
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"file_not_found: tried {file_path} and {alt_file_path}",
            )

    # Determine media type based on format
    media_type = _get_media_type(format_upper)

    # Sanitize author name(s)
    authors_str = ", ".join(book_with_rels.authors) if book_with_rels.authors else ""
    safe_author = "".join(
        c for c in authors_str if c.isalnum() or c in (" ", "-", "_", ",")
    ).strip()
    if not safe_author:
        safe_author = "Unknown"

    # Use book title for filename, sanitized
    safe_title = "".join(
        c for c in book.title if c.isalnum() or c in (" ", "-", "_")
    ).strip()
    if not safe_title:
        safe_title = f"book_{book_id}"
    filename = f"{safe_author} - {safe_title}.{file_format.lower()}"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )


@router.get("/{book_id}/metadata", response_model=None)
def download_book_metadata(
    current_user: CurrentUserDep,
    book_id: int,
    format: str,  # noqa: A002
    book_service: BookServiceDep,
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

    permission_helper.check_send_permission(
        current_user, existing_book, book_id, session
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


@router.get(
    "/{book_id}/conversions",
    response_model=BookConversionListResponse,
)
def get_book_conversions(
    book_id: int,
    current_user: CurrentUserDep,
    book_service: BookServiceDep,
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
    book_service: BookServiceDep,
    permission_helper: PermissionHelperDep,
    cover_service: CoverServiceDep,
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
    current_user: CurrentUserDep,
    q: str,
    book_service: BookServiceDep,
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
    current_user: CurrentUserDep,
    q: str,
    filter_type: str,
    book_service: BookServiceDep,
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
    current_user: CurrentUserDep,
    book_service: BookServiceDep,
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
    current_user: CurrentUserDep,
    filter_request: BookFilterRequest,
    book_service: BookServiceDep,
    permission_helper: PermissionHelperDep,
    response_builder: ResponseBuilderDep,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    full: bool = False,
) -> BookListResponse:
    """Filter books with multiple criteria using OR conditions.

    Each filter type uses OR conditions (e.g., multiple authors = OR).
    Different filter types are combined with AND conditions.

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

    Returns
    -------
    BookListResponse
        Paginated list of filtered books.

    Raises
    ------
    HTTPException
        If no active library is configured (404) or permission denied (403).
    """
    permission_helper.check_read_permission(current_user)

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    books, total = book_service.list_books_with_filters(
        page=page,
        page_size=page_size,
        author_ids=filter_request.author_ids,
        title_ids=filter_request.title_ids,
        genre_ids=filter_request.genre_ids,
        publisher_ids=filter_request.publisher_ids,
        identifier_ids=filter_request.identifier_ids,
        series_ids=filter_request.series_ids,
        formats=filter_request.formats,
        rating_ids=filter_request.rating_ids,
        language_ids=filter_request.language_ids,
        sort_by=sort_by,
        sort_order=sort_order,
        full=full,
    )

    book_reads = response_builder.build_book_read_list(books, full=full)
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
        },
    )

    return BookUploadResponse(task_id=task_id)


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
) -> int:
    """Enqueue batch upload task.

    Parameters
    ----------
    task_runner : object
        Task runner instance.
    file_infos : list[dict[str, str | None]]
        List of file info dictionaries.
    user_id : int
        User ID for the task.

    Returns
    -------
    str
        Task ID.
    """
    task_id = task_runner.enqueue(
        task_type=TaskType.MULTI_BOOK_UPLOAD,
        payload={"files": file_infos},
        user_id=user_id,
        metadata={
            "task_type": TaskType.MULTI_BOOK_UPLOAD,
            "total_files": len(file_infos),
        },
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
    files: list[UploadFile] = File(...),  # noqa: B008
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
            task_runner, file_infos, current_user.id or 0
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

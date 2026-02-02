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

"""Book management and search API schemas."""

from __future__ import annotations

from datetime import (
    datetime,  # noqa: TC003 Pydantic needs datetime at runtime for validation
)

from pydantic import BaseModel, ConfigDict, Field


class BookReadingSummary(BaseModel):
    """Denormalized reading summary for book list UIs.

    Attributes
    ----------
    read_status : str | None
        Current read status: 'not_read', 'reading', 'read', or None when no status exists.
    max_progress : float | None
        Highest progress recorded for the book (0.0 to 1.0) across formats/devices.
    status_updated_at : datetime | None
        Timestamp when read status was last updated.
    progress_updated_at : datetime | None
        Timestamp of the most recently updated progress record for the book.
    """

    read_status: str | None = Field(
        default=None,
        description="Read status: 'not_read', 'reading', 'read', or null when missing",
    )
    max_progress: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Highest progress recorded for the book (0.0 to 1.0)",
    )
    status_updated_at: datetime | None = Field(
        default=None, description="Timestamp when read status was last updated"
    )
    progress_updated_at: datetime | None = Field(
        default=None, description="Timestamp when reading progress was last updated"
    )


class BookRead(BaseModel):
    """Book representation for API responses.

    Attributes
    ----------
    id : int
        Calibre book ID.
    title : str
        Book title.
    authors : list[str]
        List of author names.
    author_ids : list[int]
        List of author IDs corresponding to ``authors`` (same order when available).
    author_sort : str | None
        Sortable author name.
    title_sort : str | None
        Sortable title (with articles removed).
    pubdate : datetime | None
        Publication date.
    timestamp : datetime | None
        Date book was added to library.
    series : str | None
        Series name if part of a series.
    series_id : int | None
        Series ID if part of a series.
    series_index : float | None
        Position in series.
    isbn : str | None
        ISBN identifier.
    uuid : str
        Unique identifier for the book.
    thumbnail_url : str | None
        URL to book cover thumbnail.
    has_cover : bool
        Whether the book has a cover image.
    tags : list[str]
        List of tag names.
    tag_ids : list[int]
        List of tag IDs corresponding to ``tags`` (same order when available).
    identifiers : list[dict[str, str]]
        List of identifiers, each with 'type' and 'val' keys.
    description : str | None
        Book description/comment text.
    publisher : str | None
        Publisher name.
    publisher_id : int | None
        Publisher ID.
    languages : list[str]
        List of language codes.
    language_ids : list[int]
        List of language IDs.
    rating : int | None
        Rating value (0-5).
    rating_id : int | None
        Rating ID.
    formats : list[dict[str, str | int]]
        List of file formats, each with 'format' and 'size' keys.
    reading_summary : BookReadingSummary | None
        Optional denormalized reading summary (status + max progress) for list UIs.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    authors: list[str] = Field(default_factory=list)
    author_ids: list[int] = Field(
        default_factory=list,
        description="List of author IDs corresponding to authors (same order when available)",
    )
    author_sort: str | None = None
    title_sort: str | None = None
    pubdate: datetime | None = None
    timestamp: datetime | None = None
    series: str | None = None
    series_id: int | None = None
    series_index: float | None = None
    isbn: str | None = None
    uuid: str
    thumbnail_url: str | None = None
    has_cover: bool = False
    tags: list[str] = Field(default_factory=list)
    tag_ids: list[int] = Field(
        default_factory=list,
        description="List of tag IDs corresponding to tags (same order when available)",
    )
    identifiers: list[dict[str, str]] = Field(default_factory=list)
    description: str | None = None
    publisher: str | None = None
    publisher_id: int | None = None
    languages: list[str] = Field(default_factory=list)
    language_ids: list[int] = Field(default_factory=list)
    rating: int | None = None
    rating_id: int | None = None
    formats: list[dict[str, str | int]] = Field(default_factory=list)
    reading_summary: BookReadingSummary | None = None
    tracking_status: str | None = Field(
        default=None,
        description="Tracking status for virtual books (e.g., 'wanted', 'downloading')",
    )
    is_virtual: bool = Field(
        default=False,
        description="Whether this is a virtual book (tracked but not in library)",
    )
    tracking_id: int | None = Field(
        default=None,
        description="ID of the tracked book record if this is a virtual book",
    )


class BookUpdate(BaseModel):
    """Book metadata update request.

    Attributes
    ----------
    title : str | None
        Book title to update.
    pubdate : datetime | None
        Publication date to update.
    author_names : list[str] | None
        List of author names to set (replaces existing).
    series_name : str | None
        Series name to set (creates if doesn't exist).
    series_id : int | None
        Series ID to set (if provided, series_name is ignored).
    series_index : float | None
        Series index to update.
    isbn : str | None
        ISBN identifier to set (first-class field).
    tag_names : list[str] | None
        List of tag names to set (replaces existing).
    identifiers : list[dict[str, str]] | None
        List of identifiers with 'type' and 'val' keys (replaces existing).
    description : str | None
        Book description/comment to set.
    publisher_name : str | None
        Publisher name to set (creates if doesn't exist).
    publisher_id : int | None
        Publisher ID to set (if provided, publisher_name is ignored).
    language_codes : list[str] | None
        List of language codes to set (creates if doesn't exist). Replaces existing languages.
    language_ids : list[int] | None
        List of language IDs to set (if provided, language_codes is ignored). Replaces existing languages.
    rating_value : int | None
        Rating value to set (creates if doesn't exist).
    rating_id : int | None
        Rating ID to set (if provided, rating_value is ignored).
    author_sort : str | None
        Author sort value to set.
    title_sort : str | None
        Title sort value to set.
    """

    title: str | None = None
    pubdate: datetime | None = None
    author_names: list[str] | None = None
    series_name: str | None = None
    series_id: int | None = None
    series_index: float | None = None
    isbn: str | None = None
    tag_names: list[str] | None = None
    identifiers: list[dict[str, str]] | None = None
    description: str | None = None
    publisher_name: str | None = None
    publisher_id: int | None = None
    language_codes: list[str] | None = None
    language_ids: list[int] | None = None
    rating_value: int | None = None
    rating_id: int | None = None
    author_sort: str | None = None
    title_sort: str | None = None


class BookListResponse(BaseModel):
    """Paginated book list response.

    Attributes
    ----------
    items : list[BookRead]
        List of books for current page.
    total : int
        Total number of books matching the query.
    page : int
        Current page number (1-indexed).
    page_size : int
        Number of items per page.
    total_pages : int
        Total number of pages.
    """

    items: list[BookRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class SearchSuggestionItem(BaseModel):
    """Single search suggestion item.

    Attributes
    ----------
    id : int
        Identifier for the item (book ID, author ID, tag ID, etc.).
    name : str
        Display name for the suggestion.
    """

    id: int
    name: str


class SearchSuggestionsResponse(BaseModel):
    """Search suggestions response.

    Attributes
    ----------
    books : list[SearchSuggestionItem]
        List of book title matches.
    authors : list[SearchSuggestionItem]
        List of author name matches.
    tags : list[SearchSuggestionItem]
        List of tag matches.
    series : list[SearchSuggestionItem]
        List of series matches.
    """

    books: list[SearchSuggestionItem] = Field(default_factory=list)
    authors: list[SearchSuggestionItem] = Field(default_factory=list)
    tags: list[SearchSuggestionItem] = Field(default_factory=list)
    series: list[SearchSuggestionItem] = Field(default_factory=list)


class FilterSuggestionsResponse(BaseModel):
    """Filter suggestions response.

    Attributes
    ----------
    suggestions : list[SearchSuggestionItem]
        List of filter suggestions for the specified filter type.
    """

    suggestions: list[SearchSuggestionItem] = Field(default_factory=list)


class TagLookupItem(BaseModel):
    """Tag lookup item.

    Attributes
    ----------
    id : int
        Tag ID.
    name : str
        Tag name.
    """

    id: int
    name: str


class TagLookupResponse(BaseModel):
    """Tag lookup response.

    Attributes
    ----------
    tags : list[TagLookupItem]
        List of matching tags.
    """

    tags: list[TagLookupItem] = Field(default_factory=list)


class BookFilterRequest(BaseModel):
    """Book filter request.

    Attributes
    ----------
    author_ids : list[int] | None
        List of author IDs to filter by (OR condition).
    title_ids : list[int] | None
        List of book IDs to filter by (OR condition).
    genre_ids : list[int] | None
        List of tag IDs to filter by (OR condition).
    publisher_ids : list[int] | None
        List of publisher IDs to filter by (OR condition).
    identifier_ids : list[int] | None
        List of identifier IDs to filter by (OR condition).
    series_ids : list[int] | None
        List of series IDs to filter by (OR condition).
    formats : list[str] | None
        List of format strings to filter by (OR condition).
    rating_ids : list[int] | None
        List of rating IDs to filter by (OR condition).
    language_ids : list[int] | None
        List of language IDs to filter by (OR condition).
    """

    author_ids: list[int] | None = Field(default=None)
    title_ids: list[int] | None = Field(default=None)
    genre_ids: list[int] | None = Field(default=None)
    publisher_ids: list[int] | None = Field(default=None)
    identifier_ids: list[int] | None = Field(default=None)
    series_ids: list[int] | None = Field(default=None)
    formats: list[str] | None = Field(default=None)
    rating_ids: list[int] | None = Field(default=None)
    language_ids: list[int] | None = Field(default=None)


class CoverFromUrlRequest(BaseModel):
    """Request to download cover image from URL.

    Attributes
    ----------
    url : str
        URL of the cover image to download.
    """

    url: str = Field(..., description="URL of the cover image to download")


class CoverFromUrlResponse(BaseModel):
    """Response containing temporary cover image URL.

    Attributes
    ----------
    temp_url : str
        Temporary URL to access the downloaded cover image.
    """

    temp_url: str = Field(
        ..., description="Temporary URL to access the downloaded cover image"
    )


class BookUploadResponse(BaseModel):
    """Response for book upload.

    Attributes
    ----------
    book_ids : list[int] | None
        IDs of uploaded books. Single book upload returns [book_id], multi-book returns [book_id1, book_id2, ...].
    task_id : int | None
        ID of upload task (for asynchronous uploads).
    """

    book_ids: list[int] | None = None
    task_id: int | None = None


class BookBatchUploadResponse(BaseModel):
    """Response for batch book upload.

    Attributes
    ----------
    task_id : int
        ID of the batch upload task.
    total_files : int
        Total number of files being uploaded.
    """

    task_id: int
    total_files: int


class BookDeleteRequest(BaseModel):
    """Request to delete a book.

    Attributes
    ----------
    delete_files_from_drive : bool
        If True, also delete files from filesystem (default: False).
    """

    delete_files_from_drive: bool = Field(
        default=False,
        description="If True, also delete files from filesystem",
    )


class BookSendRequest(BaseModel):
    """Request to send a book via email.

    Attributes
    ----------
    to_email : str | None
        Email address to send to. If not provided, sends to user's default device.
    file_format : str | None
        Optional file format to send (e.g., 'EPUB', 'MOBI').
        If not provided, uses device's preferred format or first available format.
    """

    to_email: str | None = Field(
        default=None,
        description="Email address to send to. If not provided, sends to user's default device",
    )
    file_format: str | None = Field(
        default=None,
        description="Optional file format to send (e.g., 'EPUB', 'MOBI')",
    )


class BookBulkSendRequest(BaseModel):
    """Request to send multiple books via email.

    Attributes
    ----------
    book_ids : list[int]
        List of book IDs to send.
    to_email : str | None
        Email address to send to. If not provided, sends to user's default device.
    file_format : str | None
        Optional file format to send (e.g., 'EPUB', 'MOBI').
        If not provided, uses device's preferred format or first available format.
    """

    book_ids: list[int] = Field(
        ...,
        description="List of book IDs to send",
        min_length=1,
    )
    to_email: str | None = Field(
        default=None,
        description="Email address to send to. If not provided, sends to user's default device",
    )
    file_format: str | None = Field(
        default=None,
        description="Optional file format to send (e.g., 'EPUB', 'MOBI')",
    )


class BookConvertRequest(BaseModel):
    """Request to convert a book format.

    Attributes
    ----------
    source_format : str
        Source format to convert from (e.g., 'MOBI', 'AZW3').
    target_format : str
        Target format to convert to (e.g., 'EPUB', 'KEPUB').
    """

    source_format: str = Field(
        description="Source format to convert from (e.g., 'MOBI', 'AZW3')"
    )
    target_format: str = Field(
        description="Target format to convert to (e.g., 'EPUB', 'KEPUB')"
    )


class BookConvertResponse(BaseModel):
    """Response for book conversion request.

    Attributes
    ----------
    task_id : int
        Task ID for tracking the conversion.
    message : str | None
        Optional message (e.g., if conversion already exists).
    existing_conversion_id : int | None
        ID of existing conversion if one was found.
    """

    task_id: int = Field(description="Task ID for tracking the conversion")
    message: str | None = Field(
        default=None,
        description="Optional message (e.g., if conversion already exists)",
    )
    existing_conversion_id: int | None = Field(
        default=None, description="ID of existing conversion if one was found"
    )


class BookStripDrmResponse(BaseModel):
    """Response for book DRM stripping request.

    Attributes
    ----------
    task_id : int
        Task ID for tracking the DRM stripping operation.
    message : str | None
        Optional message (e.g., if no suitable format was found).
    """

    task_id: int = Field(description="Task ID for tracking the DRM stripping operation")
    message: str | None = Field(
        default=None,
        description="Optional message about the result (e.g., if request is a no-op)",
    )


class BookFixEpubResponse(BaseModel):
    """Response for book EPUB fix request.

    Attributes
    ----------
    task_id : int
        Task ID for tracking the EPUB fix operation.
    message : str | None
        Optional message.
    """

    task_id: int = Field(description="Task ID for tracking the EPUB fix operation")
    message: str | None = Field(
        default=None,
        description="Optional message about the result",
    )


class FormatMetadataResponse(BaseModel):
    """Detailed metadata for a specific book format.

    Attributes
    ----------
    format : str
        Format extension (e.g. 'epub').
    size : int
        File size in bytes.
    path : str
        Relative path to the file in the library.
    created_at : datetime | None
        File creation timestamp.
    modified_at : datetime | None
        File modification timestamp.
    version : str | None
        Format version (e.g. '2.0', '3.0').
    page_count : int | None
        Number of pages (if applicable).
    encryption : str | None
        Encryption/DRM status.
    validation_status : str | None
        Validation status (valid, invalid, unknown).
    validation_issues : list[str]
        List of validation issues or warnings.
    mime_type : str | None
        MIME type.
    """

    format: str
    size: int
    path: str
    created_at: datetime | None = None
    modified_at: datetime | None = None
    version: str | None = None
    page_count: int | None = None
    encryption: str | None = None
    validation_status: str | None = None
    validation_issues: list[str] = Field(default_factory=list)
    mime_type: str | None = None


class BookMergeRecommendRequest(BaseModel):
    """Request model for book merge recommendation.

    Attributes
    ----------
    book_ids : list[int]
        List of book IDs to merge.
    """

    book_ids: list[int] = Field(..., min_length=2, description="Book IDs to merge")


class BookMergeRequest(BaseModel):
    """Request model for book merge operation.

    Attributes
    ----------
    book_ids : list[int]
        List of book IDs to merge.
    keep_book_id : int
        Book ID to keep (others will be merged into this one).
    """

    book_ids: list[int] = Field(..., min_length=2, description="Book IDs to merge")
    keep_book_id: int = Field(..., description="Book ID to keep")

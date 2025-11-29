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

"""OPDS feed API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OpdsFeedRequest(BaseModel):
    """Request parameters for OPDS feed generation.

    Attributes
    ----------
    offset : int
        Pagination offset (OPDS standard).
    page_size : int
        Number of items per page.
    """

    offset: int = Field(default=0, ge=0, description="Pagination offset")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Number of items per page"
    )


class OpdsFeedResponse(BaseModel):
    """Response from OPDS feed generation.

    Attributes
    ----------
    xml_content : str
        Generated OPDS XML content.
    content_type : str
        HTTP content type (default: 'application/atom+xml;profile=opds-catalog').
    """

    xml_content: str = Field(description="Generated OPDS XML content")
    content_type: str = Field(
        default="application/atom+xml;profile=opds-catalog",
        description="HTTP content type",
    )


class OpdsLink(BaseModel):
    """Represents a link in OPDS feed.

    Attributes
    ----------
    href : str
        Link URL.
    rel : str
        Link relation type.
    type : str | None
        MIME type of linked resource.
    title : str | None
        Optional link title.
    """

    href: str = Field(description="Link URL")
    rel: str = Field(description="Link relation type")
    type: str | None = Field(default=None, description="MIME type of linked resource")
    title: str | None = Field(default=None, description="Optional link title")


class OpdsEntry(BaseModel):
    """Represents a book entry in OPDS feed.

    Attributes
    ----------
    id : str
        Entry ID (book UUID or URI).
    title : str
        Book title.
    authors : list[str]
        List of author names.
    updated : str
        Last update timestamp (ISO 8601).
    summary : str | None
        Book description/summary.
    links : list[OpdsLink] | None
        List of links (download, cover, etc.).
    published : str | None
        Publication date (ISO 8601).
    language : str | None
        Language code.
    publisher : str | None
        Publisher name.
    identifier : str | None
        ISBN or other identifier.
    series : str | None
        Series name.
    series_index : float | None
        Position in series.
    """

    id: str = Field(description="Entry ID (book UUID or URI)")
    title: str = Field(description="Book title")
    authors: list[str] = Field(default_factory=list, description="List of author names")
    updated: str = Field(description="Last update timestamp (ISO 8601)")
    summary: str | None = Field(default=None, description="Book description/summary")
    links: list[OpdsLink] | None = Field(
        default=None, description="List of links (download, cover, etc.)"
    )
    published: str | None = Field(
        default=None, description="Publication date (ISO 8601)"
    )
    language: str | None = Field(default=None, description="Language code")
    publisher: str | None = Field(default=None, description="Publisher name")
    identifier: str | None = Field(default=None, description="ISBN or other identifier")
    series: str | None = Field(default=None, description="Series name")
    series_index: float | None = Field(default=None, description="Position in series")

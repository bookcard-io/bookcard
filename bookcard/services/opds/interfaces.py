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

"""Interfaces for OPDS feed services.

This module defines abstract interfaces following the Interface Segregation
Principle (ISP) and Dependency Inversion Principle (DIP).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Request

    from bookcard.api.schemas.opds import (
        OpdsEntry,
        OpdsFeedRequest,
        OpdsFeedResponse,
    )
    from bookcard.models.auth import User
    from bookcard.repositories.models import BookWithRelations


class IOpdsFeedService(ABC):
    """Interface for generating OPDS feeds."""

    @abstractmethod
    def generate_catalog_feed(self, request: Request) -> OpdsFeedResponse:
        """Generate main catalog feed.

        Parameters
        ----------
        request : Request
            FastAPI request object.

        Returns
        -------
        OpdsFeedResponse
            Generated feed response.
        """
        ...

    @abstractmethod
    def generate_books_feed(
        self, request: Request, user: User | None, feed_request: OpdsFeedRequest
    ) -> OpdsFeedResponse:
        """Generate books listing feed.

        Parameters
        ----------
        request : Request
            FastAPI request object.
        user : User | None
            Authenticated user or None.
        feed_request : OpdsFeedRequest
            Feed request parameters.

        Returns
        -------
        OpdsFeedResponse
            Generated feed response.
        """
        ...

    @abstractmethod
    def generate_new_feed(
        self, request: Request, user: User | None, feed_request: OpdsFeedRequest
    ) -> OpdsFeedResponse:
        """Generate recently added books feed.

        Parameters
        ----------
        request : Request
            FastAPI request object.
        user : User | None
            Authenticated user or None.
        feed_request : OpdsFeedRequest
            Feed request parameters.

        Returns
        -------
        OpdsFeedResponse
            Generated feed response.
        """
        ...

    @abstractmethod
    def generate_discover_feed(
        self, request: Request, user: User | None, feed_request: OpdsFeedRequest
    ) -> OpdsFeedResponse:
        """Generate random book discovery feed.

        Parameters
        ----------
        request : Request
            FastAPI request object.
        user : User | None
            Authenticated user or None.
        feed_request : OpdsFeedRequest
            Feed request parameters.

        Returns
        -------
        OpdsFeedResponse
            Generated feed response.
        """
        ...

    @abstractmethod
    def generate_search_feed(
        self,
        request: Request,
        user: User | None,
        query: str,
        feed_request: OpdsFeedRequest,
    ) -> OpdsFeedResponse:
        """Generate search results feed.

        Parameters
        ----------
        request : Request
            FastAPI request object.
        user : User | None
            Authenticated user or None.
        query : str
            Search query string.
        feed_request : OpdsFeedRequest
            Feed request parameters.

        Returns
        -------
        OpdsFeedResponse
            Generated feed response.
        """
        ...

    @abstractmethod
    def generate_opensearch_description(self, request: Request) -> OpdsFeedResponse:
        """Generate OpenSearch description XML.

        Parameters
        ----------
        request : Request
            FastAPI request object.

        Returns
        -------
        OpdsFeedResponse
            OpenSearch description XML.
        """
        ...


class IOpdsXmlBuilder(ABC):
    """Interface for building OPDS XML documents."""

    @abstractmethod
    def build_feed(
        self,
        title: str,
        feed_id: str,
        updated: str,
        entries: list[OpdsEntry],
        links: list[dict[str, str]] | None = None,
    ) -> str:
        """Build OPDS feed XML.

        Parameters
        ----------
        title : str
            Feed title.
        feed_id : str
            Feed ID (URI).
        updated : str
            Feed update timestamp (ISO 8601).
        entries : list[OpdsEntry]
            List of feed entries.
        links : list[dict[str, str]] | None
            Optional list of feed links.

        Returns
        -------
        str
            XML content as string.
        """
        ...

    @abstractmethod
    def build_entry(self, entry: OpdsEntry) -> object:
        """Build OPDS entry element.

        Parameters
        ----------
        entry : OpdsEntry
            Entry data model.

        Returns
        -------
        object
            XML element (lxml.etree._Element).
        """
        ...


class IOpdsBookQueryService(ABC):
    """Interface for querying books with permission filtering."""

    @abstractmethod
    def get_books(
        self,
        user: User | None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
    ) -> tuple[list[BookWithRelations], int]:
        """Get books with pagination and permission filtering.

        Parameters
        ----------
        user : User | None
            Authenticated user or None.
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.
        sort_by : str
            Field to sort by.
        sort_order : str
            Sort order: 'asc' or 'desc'.

        Returns
        -------
        tuple[list[BookWithRelations], int]
            Tuple of (books list, total count).
        """
        ...

    @abstractmethod
    def get_recent_books(
        self,
        user: User | None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[BookWithRelations], int]:
        """Get recently added books with permission filtering.

        Parameters
        ----------
        user : User | None
            Authenticated user or None.
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.

        Returns
        -------
        tuple[list[BookWithRelations], int]
            Tuple of (books list, total count).
        """
        ...

    @abstractmethod
    def get_random_books(
        self,
        user: User | None,
        limit: int = 20,
    ) -> list[BookWithRelations]:
        """Get random books with permission filtering.

        Parameters
        ----------
        user : User | None
            Authenticated user or None.
        limit : int
            Maximum number of books to return.

        Returns
        -------
        list[BookWithRelations]
            List of random books.
        """
        ...

    @abstractmethod
    def search_books(
        self,
        user: User | None,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[BookWithRelations], int]:
        """Search books with permission filtering.

        Parameters
        ----------
        user : User | None
            Authenticated user or None.
        query : str
            Search query string.
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.

        Returns
        -------
        tuple[list[BookWithRelations], int]
            Tuple of (books list, total count).
        """
        ...


class IOpdsAuthProvider(ABC):
    """Interface for OPDS authentication."""

    @abstractmethod
    def authenticate_request(self, request: Request) -> User | None:
        """Authenticate request via HTTP Basic Auth or JWT.

        Parameters
        ----------
        request : Request
            FastAPI request object.

        Returns
        -------
        User | None
            Authenticated user or None if authentication fails.
        """
        ...

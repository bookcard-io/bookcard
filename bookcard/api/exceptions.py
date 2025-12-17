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

"""Exception handlers for domain-specific exceptions.

Uses a registry pattern to allow easy addition of new exception handlers
without modifying the registration function.
"""

from collections.abc import Callable

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from starlette.requests import Request

from bookcard.services.author_exceptions import NoActiveLibraryError
from bookcard.services.ingest.exceptions import (
    IngestHistoryCreationError,
    IngestHistoryNotFoundError,
)

# Registry mapping exception types to HTTP status codes
EXCEPTION_HANDLERS: dict[type[Exception], int] = {
    IngestHistoryNotFoundError: status.HTTP_404_NOT_FOUND,
    NoActiveLibraryError: status.HTTP_400_BAD_REQUEST,
    IngestHistoryCreationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI application.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    """
    for exc_type, status_code in EXCEPTION_HANDLERS.items():
        # Create handler function with captured status_code
        def create_handler(sc: int) -> Callable[[Request, Exception], JSONResponse]:
            """Create an exception handler for a specific status code.

            Parameters
            ----------
            sc : int
                HTTP status code to return.

            Returns
            -------
            Callable[[Request, Exception], JSONResponse]
                Handler function.
            """

            def handler(_request: Request, exc: Exception) -> JSONResponse:
                """Handle domain-specific exceptions.

                Parameters
                ----------
                _request : Request
                    FastAPI request object (unused).
                exc : Exception
                    Exception instance to handle.

                Returns
                -------
                JSONResponse
                    JSON response with error detail.
                """
                return JSONResponse(
                    status_code=sc,
                    content={"detail": str(exc)},
                )

            return handler

        # Create handler with captured status_code
        handler_func = create_handler(status_code)

        # Register handler with captured exc_type
        def register_handler(
            exc_class: type[Exception],
            handler: Callable[[Request, Exception], JSONResponse],
        ) -> None:
            """Register an exception handler.

            Parameters
            ----------
            exc_class : type[Exception]
                Exception class to handle.
            handler : type
                Handler function.
            """

            @app.exception_handler(exc_class)
            def registered_handler(request: Request, exc: Exception) -> JSONResponse:
                """Handle registered exception."""
                return handler(request, exc)

        register_handler(exc_type, handler_func)

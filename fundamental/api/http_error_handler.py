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

"""Centralized HTTP error handler for structured error responses.

This module provides a centralized way to raise HTTPExceptions with
structured error details, removing implementation details from route handlers.
"""

from typing import Any, NoReturn

from fastapi import HTTPException, status

from fundamental.services.calibre_plugin_service import CalibreNotFoundError

# Registry mapping exception types to error configuration
# Each entry maps to: (error_type, status_code, message_type)
_EXCEPTION_ERROR_CONFIG: dict[type[Exception], tuple[str, int, str]] = {
    CalibreNotFoundError: (
        "calibre_not_found",
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "warning",
    ),
}


class HTTPErrorHandler:
    """Centralized handler for raising structured HTTP exceptions.

    Follows DRY by centralizing error response structure.
    Separates HTTP concerns from business logic (SOC).
    Uses dependency injection pattern (IOC) for extensibility.
    """

    @staticmethod
    def raise_for_exception(exception: Exception) -> NoReturn:
        """Raise HTTPException for a given exception.

        Maps domain exceptions to structured HTTP error responses.
        If the exception type is registered, uses the configured
        error type, status code, and message type. Otherwise,
        raises a generic 500 error.

        Parameters
        ----------
        exception : Exception
            The exception to convert to HTTPException.

        Raises
        ------
        HTTPException
            Structured HTTP exception with error details.
        """
        exc_type = type(exception)

        if exc_type in _EXCEPTION_ERROR_CONFIG:
            error_type, status_code, message_type = _EXCEPTION_ERROR_CONFIG[exc_type]
            HTTPErrorHandler.raise_structured_error(
                error_type=error_type,
                message=str(exception),
                status_code=status_code,
                message_type=message_type,
            )

        # Fallback for unregistered exceptions
        HTTPErrorHandler.raise_structured_error(
            error_type="internal_error",
            message=str(exception),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message_type="error",
        )

    @staticmethod
    def raise_structured_error(
        error_type: str,
        message: str,
        status_code: int,
        message_type: str = "error",
        additional_fields: dict[str, Any] | None = None,
    ) -> NoReturn:
        """Raise HTTPException with structured error details.

        Parameters
        ----------
        error_type : str
            Type identifier for the error (e.g., "calibre_not_found").
        message : str
            Human-readable error message.
        status_code : int
            HTTP status code to return.
        message_type : str, optional
            Type of message (e.g., "error", "warning", "info").
            Defaults to "error".
        additional_fields : dict[str, Any] | None, optional
            Additional fields to include in the error detail.
            Defaults to None.

        Raises
        ------
        HTTPException
            Structured HTTP exception with error details.
        """
        detail: dict[str, Any] = {
            "error_type": error_type,
            "message": message,
            "message_type": message_type,
        }
        if additional_fields:
            detail.update(additional_fields)

        raise HTTPException(
            status_code=status_code,
            detail=detail,
        )

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

"""Exception mapper for book operations.

Centralizes ValueError to HTTPException mapping following DRY principle.
Separates HTTP concerns from business logic.
"""

from fastapi import HTTPException, status


class BookExceptionMapper:
    """Maps business exceptions to HTTP exceptions for book operations.

    Follows DRY by centralizing error handling logic.
    Separates HTTP concerns from business logic.
    """

    @staticmethod
    def map_value_error_to_http_exception(error: ValueError) -> HTTPException:
        """Map ValueError to appropriate HTTPException.

        Parameters
        ----------
        error : ValueError
            Business logic exception.

        Returns
        -------
        HTTPException
            Appropriate HTTP exception with status code and detail.
        """
        error_msg = str(error)

        if "not found" in error_msg.lower() or error_msg == "book_not_found":
            return HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        if "no_active_library" in error_msg.lower():
            return HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="no_active_library",
            )

        if any(
            phrase in error_msg
            for phrase in [
                "format_not_found",
                "file_not_found",
                "Unsupported format",
                "file_extension_required",
                "url_required",
                "invalid_url_format",
            ]
        ):
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        if "email_server_not_configured" in error_msg.lower():
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        if "Task runner not available" in error_msg:
            return HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=error_msg,
            )

        # Default to 500 for unexpected errors
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )

    @staticmethod
    def map_cover_error_to_http_exception(
        error: ValueError | Exception,
    ) -> HTTPException:
        """Map cover-related errors to appropriate HTTPException.

        Parameters
        ----------
        error : ValueError | Exception
            Cover operation exception.

        Returns
        -------
        HTTPException
            Appropriate HTTP exception with status code and detail.
        """
        msg = str(error)

        if "not found" in msg.lower():
            return HTTPException(status_code=404, detail=msg)

        if msg in {
            "url_not_an_image",
            "invalid_image_format",
            "url_required",
            "invalid_url_format",
        }:
            return HTTPException(status_code=400, detail=msg)

        if msg.startswith(("failed_to_download_image", "failed_to_save_file")):
            return HTTPException(status_code=500, detail=msg)

        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg,
        )

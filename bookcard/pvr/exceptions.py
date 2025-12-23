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

"""PVR provider exception classes.

This module contains all exception classes used by the PVR system,
following SOC by separating exception definitions from business logic.
"""


class PVRProviderError(Exception):
    """Base exception for PVR provider errors."""


class PVRProviderNetworkError(PVRProviderError):
    """Exception raised when network requests fail."""


class PVRProviderParseError(PVRProviderError):
    """Exception raised when parsing response data fails."""


class PVRProviderTimeoutError(PVRProviderError):
    """Exception raised when requests timeout."""


class PVRProviderAuthenticationError(PVRProviderError):
    """Exception raised when authentication fails."""


class PVRProviderInvalidUrlError(PVRProviderError):
    """Exception raised when download URL format is invalid."""

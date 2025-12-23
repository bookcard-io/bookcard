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

"""Authentication utility functions for PVR system.

This module provides shared authentication utilities following DRY principles
by centralizing duplicate authentication logic.
"""

import base64


def build_basic_auth_header(username: str | None, password: str | None) -> str | None:
    """Build Basic Auth header if credentials are provided.

    Parameters
    ----------
    username : str | None
        Username for authentication.
    password : str | None
        Password for authentication.

    Returns
    -------
    str | None
        Basic Auth header value (e.g., "Basic <base64>") or None if credentials missing.

    Examples
    --------
    >>> build_basic_auth_header(
    ...     "user", "pass"
    ... )
    'Basic dXNlcjpwYXNz'
    >>> build_basic_auth_header(
    ...     None, "pass"
    ... )
    None
    """
    if username and password:
        credentials = f"{username}:{password}"
        auth_bytes = base64.b64encode(credentials.encode("utf-8"))
        return f"Basic {auth_bytes.decode('utf-8')}"
    return None

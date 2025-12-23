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

"""HTTP client abstractions for PVR system.

This module provides HTTP client protocols and implementations following
DIP by allowing HTTP clients to be injected and swapped.
"""

from bookcard.pvr.http.client import HttpClient, HttpxClient
from bookcard.pvr.http.protocol import HttpClientProtocol

__all__ = ["HttpClient", "HttpClientProtocol", "HttpxClient"]

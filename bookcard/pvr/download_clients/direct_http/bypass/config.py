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

"""Configuration classes for bypass client."""

from dataclasses import dataclass

from bookcard.pvr.download_clients.direct_http.bypass.constants import BypassConstants


@dataclass(frozen=True)
class FlareSolverrConfig:
    """Configuration for FlareSolverr bypass strategy."""

    url: str = BypassConstants.DEFAULT_FLARESOLVERR_URL
    path: str = BypassConstants.DEFAULT_FLARESOLVERR_PATH
    timeout: int = BypassConstants.DEFAULT_FLARESOLVERR_TIMEOUT


@dataclass(frozen=True)
class SeleniumBaseConfig:
    """Configuration for SeleniumBase bypass strategy."""

    page_load_timeout: int = BypassConstants.DEFAULT_PAGE_LOAD_TIMEOUT
    reconnect_time: float = BypassConstants.DEFAULT_RECONNECT_TIME
    # DDoS-Guard / Turnstile flows often fail in true headless mode.
    # We run with a virtual X display in Docker, so non-headless is safe there.
    headless: bool = False
    incognito: bool = True
    locale: str = "en"
    ad_block: bool = True


@dataclass(frozen=True)
class BypassConfig:
    """Configuration for bypass client."""

    flaresolverr: FlareSolverrConfig | None = None
    seleniumbase: SeleniumBaseConfig | None = None
    use_seleniumbase: bool = False

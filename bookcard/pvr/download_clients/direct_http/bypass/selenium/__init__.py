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

"""Selenium bypass client for Direct HTTP download client."""

from bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_engine import (
    BypassEngine,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods import (
    DEFAULT_BYPASS_METHODS,
    BypassMethod,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.challenge_detector import (
    ChallengeDetectionService,
    ChallengeDetector,
    CloudflareDetector,
    DdosGuardDetector,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.cookie_store import (
    CookieStore,
    ThreadSafeCookieStore,
    ThreadSafeUserAgentStore,
    UserAgentStore,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.display_manager import (
    DisplayManager,
    VirtualDisplayManager,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.driver_factory import (
    DriverFactory,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.driver_manager import (
    DriverManager,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.process_manager import (
    DockerProcessManager,
    ProcessManager,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.success_checker import (
    SuccessChecker,
)

__all__ = [
    "DEFAULT_BYPASS_METHODS",
    "BypassEngine",
    "BypassMethod",
    "ChallengeDetectionService",
    "ChallengeDetector",
    "CloudflareDetector",
    "CookieStore",
    "DdosGuardDetector",
    "DisplayManager",
    "DockerProcessManager",
    "DriverFactory",
    "DriverManager",
    "ProcessManager",
    "SuccessChecker",
    "ThreadSafeCookieStore",
    "ThreadSafeUserAgentStore",
    "UserAgentStore",
    "VirtualDisplayManager",
]

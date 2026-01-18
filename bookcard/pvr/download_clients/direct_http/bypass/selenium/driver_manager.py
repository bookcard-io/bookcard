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

"""Driver lifecycle management for Chrome drivers."""

import gc
import logging
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from seleniumbase import Driver

    from bookcard.pvr.download_clients.direct_http.bypass.selenium.process_manager import (
        ProcessManager,
    )

logger = logging.getLogger(__name__)


class DriverManager:
    """Manages Chrome driver lifecycle and cleanup."""

    def __init__(self, process_manager: "ProcessManager") -> None:
        """Initialize driver manager.

        Parameters
        ----------
        process_manager : ProcessManager
            Process manager for cleaning up orphan processes.
        """
        self._process_manager = process_manager

    def _stop_cdp_browser(self, driver: "Driver") -> None:  # type: ignore[invalid-type-form]
        """Stop CDP browser if in CDP mode (closes websocket connections).

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.
        """
        try:
            if hasattr(driver, "cdp") and driver.cdp and hasattr(driver.cdp, "driver"):
                driver.cdp.driver.stop()
                logger.debug("Stopped CDP browser (closed websocket)")
                time.sleep(0.3)
        except (AttributeError, RuntimeError) as e:
            logger.debug("CDP stop: %s", e)

    def _close_cdp_sockets(self) -> int:
        """Find and close any sockets connected to CDP port 9222.

        This is a workaround for SeleniumBase not properly closing websocket
        connections when using activate_cdp_mode(). Returns count of closed sockets.

        Returns
        -------
        int
            Number of sockets closed.
        """
        closed = 0
        pid = os.getpid()

        try:
            fd_path = Path(f"/proc/{pid}/fd")
            for fd_item in fd_path.iterdir():
                try:
                    fd = int(fd_item.name)
                    link = fd_item.readlink()
                    link_str = str(link)
                    if "socket:" not in link_str:
                        continue

                    # Check if this socket is connected to port 9222 (CDP)
                    # by reading /proc/net/tcp and matching inode
                    inode = link_str.split("[")[1].rstrip("]")

                    tcp_file = Path("/proc/net/tcp")
                    with tcp_file.open() as f:
                        for line in f:
                            parts = line.split()
                            if len(parts) < 10:
                                continue
                            # Check if this is our socket and connects to port 9222 (0x2406)
                            if parts[9] == inode:
                                remote = parts[2]
                                remote_port = int(remote.split(":")[1], 16)
                                if remote_port == 9222:
                                    logger.debug(
                                        "Closing CDP socket fd=%d inode=%s", fd, inode
                                    )
                                    os.close(fd)
                                    closed += 1
                                    break
                except (ValueError, OSError, IndexError):
                    continue
        except (OSError, PermissionError) as e:
            logger.debug("Error scanning for CDP sockets: %s", e)

        return closed

    def _safe_reconnect(self, driver: "Driver") -> None:  # type: ignore[invalid-type-form]
        """Safely attempt to reconnect WebDriver after CDP mode.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.
        """
        try:
            driver.reconnect()
        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.debug("Reconnect failed: %s", e)

    def quit(self, driver: "Driver | None") -> None:  # type: ignore[invalid-type-form]
        """Quit Chrome driver and clean up resources.

        Proper cleanup sequence for SeleniumBase CDP mode:
        1. Stop CDP browser (closes websocket connections)
        2. Reconnect WebDriver
        3. Close window
        4. Quit driver
        5. Force-kill any lingering processes

        The CDP websocket connection must be explicitly closed before Chrome is killed,
        otherwise the sockets end up in CLOSE_WAIT state causing gevent to busy-loop.

        Parameters
        ----------
        driver : Driver | None
            SeleniumBase driver instance to quit.
        """
        if driver is None:
            return

        logger.debug("Quitting Chrome driver...")

        # Strategy 1: Stop CDP browser if in CDP mode (closes websocket connections)
        self._stop_cdp_browser(driver)

        # Strategy 2: Reconnect to re-establish WebDriver control before quitting
        try:
            driver.reconnect()
            time.sleep(0.2)
        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.debug("Reconnect: %s", e)

        # Strategy 3: Close the current window/tab
        try:
            driver.close()
            time.sleep(0.2)
        except (AttributeError, RuntimeError) as e:
            logger.debug("Close window: %s", e)

        # Strategy 4: Fallback - explicitly close any remaining CDP sockets
        closed = self._close_cdp_sockets()
        if closed:
            logger.debug("Closed %d remaining CDP socket(s)", closed)

        # Strategy 5: Standard quit
        try:
            driver.quit()
        except (AttributeError, RuntimeError) as e:
            logger.debug("Quit: %s", e)

        # Strategy 6: Force garbage collection
        gc.collect()

        # Strategy 7: Force-kill any lingering Chrome/chromedriver processes
        self._process_manager.force_kill_chrome()

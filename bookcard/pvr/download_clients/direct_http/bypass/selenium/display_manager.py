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

"""Virtual display management for headless browser operations."""

import logging
import os
import threading
import time
from pathlib import Path
from typing import Protocol

from sbvirtualdisplay import Display

logger = logging.getLogger(__name__)


class DisplayManager(Protocol):
    """Protocol for display management."""

    def ensure_initialized(
        self, screen_width: int, screen_height: int, headless: bool
    ) -> None:
        """Ensure virtual display is initialized if needed.

        Parameters
        ----------
        screen_width : int
            Screen width in pixels.
        screen_height : int
            Screen height in pixels.
        headless : bool
            Whether running in headless mode.
        """
        ...

    def cleanup(self) -> None:
        """Clean up virtual display resources."""
        ...


class VirtualDisplayManager:
    """Manages virtual X display for headless browser operations."""

    def __init__(self, reconnect_time: float = 0.5) -> None:
        """Initialize display manager.

        Parameters
        ----------
        reconnect_time : float
            Time to wait after display initialization.
        """
        self._display: Display | None = None
        self._lock = threading.Lock()
        self._reconnect_time = reconnect_time

    def _is_docker_environment(self) -> bool:
        """Check if running in Docker environment.

        Returns
        -------
        bool
            True if in Docker environment.
        """
        return Path("/.dockerenv").exists() or os.environ.get("DOCKERMODE") == "true"

    def ensure_initialized(
        self, screen_width: int, screen_height: int, headless: bool
    ) -> None:
        """Ensure virtual display is initialized if needed.

        Parameters
        ----------
        screen_width : int
            Screen width in pixels.
        screen_height : int
            Screen height in pixels.
        headless : bool
            Whether running in headless mode.
        """
        with self._lock:
            if self._display is not None:
                return

            # Check if we need a virtual display
            is_docker = self._is_docker_environment()
            # We need a virtual display when:
            # - running in Docker (often no host X server)
            # - running in headless mode (some stacks still require Xvfb)
            # - running non-headless but no DISPLAY is available (common on servers/CI)
            has_display = bool(os.environ.get("DISPLAY"))
            needs_display = is_docker or headless or not has_display

            if not needs_display:
                self._reset_pyautogui_display_state()
                return

            # Add padding for browser chrome (title bar, borders, etc.)
            from bookcard.pvr.download_clients.direct_http.bypass.selenium.constants import (
                DISPLAY_HEIGHT_PADDING,
                DISPLAY_WIDTH_PADDING,
            )

            display_width = screen_width + DISPLAY_WIDTH_PADDING
            display_height = screen_height + DISPLAY_HEIGHT_PADDING

            self._display = Display(visible=False, size=(display_width, display_height))
            self._display.start()
            logger.info("Virtual display started: %sx%s", display_width, display_height)
            time.sleep(self._reconnect_time)
            self._reset_pyautogui_display_state()

    def _reset_pyautogui_display_state(self) -> None:
        """Reset pyautogui display state after virtual display initialization."""
        try:
            import pyautogui
            import Xlib.display

            # Access private members for display state reset (required for pyautogui)
            pyautogui_x11 = getattr(pyautogui, "_pyautogui_x11", None)
            if pyautogui_x11 is not None:
                # Unconditionally update the display object with the new DISPLAY env var
                pyautogui_x11._display = Xlib.display.Display(os.environ["DISPLAY"])  # noqa: SLF001
        except (ImportError, AttributeError, KeyError, OSError) as e:
            logger.warning("Error resetting pyautogui display state: %s", e)

    def cleanup(self) -> None:
        """Clean up virtual display resources."""
        with self._lock:
            if self._display is not None:
                try:
                    self._display.stop()
                    logger.debug("Virtual display stopped")
                except (AttributeError, RuntimeError) as e:
                    logger.debug("Error stopping display: %s", e)
                finally:
                    self._display = None

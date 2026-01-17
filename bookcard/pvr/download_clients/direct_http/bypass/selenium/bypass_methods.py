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

"""Bypass method implementations for different protection systems."""

import logging
import random
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from bookcard.pvr.download_clients.direct_http.bypass.selenium.constants import (
    CAPTCHA_WAIT_MAX,
    CAPTCHA_WAIT_MIN,
    CDP_CLICK_SELECTORS,
    CDP_DELAY_MAX,
    CDP_DELAY_MIN,
    CDP_GUI_CLICK_SELECTORS,
    HUMAN_DELAY_MAX,
    HUMAN_DELAY_MIN,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.success_checker import (
    SuccessChecker,
)

if TYPE_CHECKING:
    from seleniumbase import Driver

logger = logging.getLogger(__name__)

# Use SystemRandom for non-cryptographic randomness (satisfies S311)
_sys_random = random.SystemRandom()


class BypassMethod(ABC):
    """Abstract base class for bypass methods."""

    @abstractmethod
    def attempt(self, driver: "Driver") -> bool:  # type: ignore[invalid-type-form]
        """Attempt to bypass protection.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.

        Returns
        -------
        bool
            True if bypass successful.
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Get method name.

        Returns
        -------
        str
            Method name.
        """
        ...


def _simulate_human_behavior(sb: "Driver") -> None:  # type: ignore[invalid-type-form]
    """Simulate human-like behavior before bypass attempt.

    Parameters
    ----------
    sb : Driver
        SeleniumBase driver instance.
    """
    try:
        time.sleep(_sys_random.uniform(HUMAN_DELAY_MIN, HUMAN_DELAY_MAX))

        if _sys_random.random() < 0.3:
            sb.scroll_down(_sys_random.randint(20, 50))
            time.sleep(_sys_random.uniform(0.2, 0.5))
            sb.scroll_up(_sys_random.randint(10, 30))
            time.sleep(_sys_random.uniform(0.2, 0.4))

        try:
            import pyautogui

            x, y = pyautogui.position()
            pyautogui.moveTo(
                x + _sys_random.randint(-10, 10),
                y + _sys_random.randint(-10, 10),
                duration=_sys_random.uniform(0.05, 0.15),
            )
        except (ImportError, AttributeError, RuntimeError) as e:
            logger.debug("Mouse jiggle failed: %s", e)
    except (AttributeError, RuntimeError) as e:
        logger.debug("Human simulation failed: %s", e)


def _safe_reconnect(driver: "Driver") -> None:  # type: ignore[invalid-type-form]
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


# Global success checker instance for methods to use
_success_checker = SuccessChecker()


def _is_bypassed(driver: "Driver", escape_emojis: bool = True) -> bool:  # type: ignore[invalid-type-form]
    """Check if the protection has been bypassed.

    Parameters
    ----------
    driver : Driver
        SeleniumBase driver instance.
    escape_emojis : bool
        Whether to check for emojis as bypass indicator.

    Returns
    -------
    bool
        True if bypassed.
    """
    return _success_checker.is_bypassed(driver, escape_emojis)


class CdpSolveMethod(BypassMethod):
    """CDP Mode with solve_captcha() - WebDriver disconnected, no PyAutoGUI."""

    def attempt(self, driver: "Driver") -> bool:  # type: ignore[invalid-type-form]
        """Attempt bypass using CDP solve_captcha.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.

        Returns
        -------
        bool
            True if bypass successful.
        """
        try:
            logger.debug("Attempting bypass: CDP Mode solve_captcha")
            driver.activate_cdp_mode(driver.get_current_url())
            time.sleep(_sys_random.uniform(CDP_DELAY_MIN, CDP_DELAY_MAX))

            try:
                driver.cdp.solve_captcha()
                time.sleep(_sys_random.uniform(CAPTCHA_WAIT_MIN, CAPTCHA_WAIT_MAX))
                driver.reconnect()
                time.sleep(_sys_random.uniform(1, 2))
                result = _is_bypassed(driver)
            except (AttributeError, RuntimeError, TimeoutError) as e:
                logger.debug("CDP solve_captcha failed: %s", e)
                _safe_reconnect(driver)
                return False
            else:
                return result
        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.debug("CDP Mode solve failed: %s", e)
            _safe_reconnect(driver)
            return False

    def get_name(self) -> str:
        """Get method name.

        Returns
        -------
        str
            "cdp_solve"
        """
        return "cdp_solve"


class CdpClickMethod(BypassMethod):
    """CDP Mode with native clicking - no PyAutoGUI dependency."""

    def attempt(self, driver: "Driver") -> bool:  # type: ignore[invalid-type-form]
        """Attempt bypass using CDP native click.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.

        Returns
        -------
        bool
            True if bypass successful.
        """
        try:
            logger.debug("Attempting bypass: CDP Mode native click")
            driver.activate_cdp_mode(driver.get_current_url())
            time.sleep(_sys_random.uniform(CDP_DELAY_MIN, CDP_DELAY_MAX))

            for selector in CDP_CLICK_SELECTORS:
                try:
                    if not driver.cdp.is_element_visible(selector):
                        continue

                    logger.debug("CDP clicking: %s", selector)
                    driver.cdp.click(selector)
                    time.sleep(_sys_random.uniform(2, 4))

                    driver.reconnect()
                    time.sleep(_sys_random.uniform(1, 2))

                    if _is_bypassed(driver):
                        return True

                    driver.activate_cdp_mode(driver.get_current_url())
                    time.sleep(_sys_random.uniform(0.5, 1))
                except (AttributeError, RuntimeError, TimeoutError) as e:
                    logger.debug("CDP click on '%s' failed: %s", selector, e)

            _safe_reconnect(driver)
            result = _is_bypassed(driver)
        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.debug("CDP Mode click failed: %s", e)
            _safe_reconnect(driver)
            return False
        else:
            return result

    def get_name(self) -> str:
        """Get method name.

        Returns
        -------
        str
            "cdp_click"
        """
        return "cdp_click"


class CdpGuiClickMethod(BypassMethod):
    """CDP Mode with PyAutoGUI-based clicking - uses actual mouse movement."""

    def attempt(self, driver: "Driver") -> bool:  # type: ignore[invalid-type-form]
        """Attempt bypass using CDP GUI click.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.

        Returns
        -------
        bool
            True if bypass successful.
        """
        try:
            logger.debug("Attempting bypass: CDP Mode gui_click (mouse-based)")
            driver.activate_cdp_mode(driver.get_current_url())
            time.sleep(_sys_random.uniform(CDP_DELAY_MIN, CDP_DELAY_MAX))

            try:
                logger.debug("Trying cdp.gui_click_captcha()")
                driver.cdp.gui_click_captcha()
                time.sleep(_sys_random.uniform(CAPTCHA_WAIT_MIN, CAPTCHA_WAIT_MAX))

                driver.reconnect()
                time.sleep(_sys_random.uniform(1, 2))

                if _is_bypassed(driver):
                    return True

                driver.activate_cdp_mode(driver.get_current_url())
                time.sleep(_sys_random.uniform(0.5, 1))
            except (AttributeError, RuntimeError, TimeoutError) as e:
                logger.debug("cdp.gui_click_captcha() failed: %s", e)

            for selector in CDP_GUI_CLICK_SELECTORS:
                try:
                    if not driver.cdp.is_element_visible(selector):
                        continue

                    logger.debug("CDP gui_click_element: %s", selector)
                    driver.cdp.gui_click_element(selector)
                    time.sleep(_sys_random.uniform(CAPTCHA_WAIT_MIN, CAPTCHA_WAIT_MAX))

                    driver.reconnect()
                    time.sleep(_sys_random.uniform(1, 2))

                    if _is_bypassed(driver):
                        return True

                    driver.activate_cdp_mode(driver.get_current_url())
                    time.sleep(_sys_random.uniform(0.5, 1))
                except (AttributeError, RuntimeError, TimeoutError) as e:
                    logger.debug("CDP gui_click on '%s' failed: %s", selector, e)

            _safe_reconnect(driver)
            result = _is_bypassed(driver)
        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.debug("CDP Mode gui_click failed: %s", e)
            _safe_reconnect(driver)
            return False
        else:
            return result

    def get_name(self) -> str:
        """Get method name.

        Returns
        -------
        str
            "cdp_gui_click"
        """
        return "cdp_gui_click"


class HandleCaptchaMethod(BypassMethod):
    """Use uc_gui_handle_captcha() - TAB+SPACEBAR approach, stealthier than click."""

    def attempt(self, driver: "Driver") -> bool:  # type: ignore[invalid-type-form]
        """Attempt bypass using uc_gui_handle_captcha.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.

        Returns
        -------
        bool
            True if bypass successful.
        """
        try:
            logger.debug("Attempting bypass: uc_gui_handle_captcha (TAB+SPACEBAR)")
            _simulate_human_behavior(driver)
            driver.uc_gui_handle_captcha()
            time.sleep(_sys_random.uniform(CAPTCHA_WAIT_MIN, CAPTCHA_WAIT_MAX))
            result = _is_bypassed(driver)
        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.debug("uc_gui_handle_captcha failed: %s", e)
            return False
        else:
            return result

    def get_name(self) -> str:
        """Get method name.

        Returns
        -------
        str
            "handle_captcha"
        """
        return "handle_captcha"


class ClickCaptchaMethod(BypassMethod):
    """Use uc_gui_click_captcha() - direct click via PyAutoGUI."""

    def attempt(self, driver: "Driver") -> bool:  # type: ignore[invalid-type-form]
        """Attempt bypass using uc_gui_click_captcha.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.

        Returns
        -------
        bool
            True if bypass successful.
        """
        try:
            logger.debug("Attempting bypass: uc_gui_click_captcha (direct click)")
            _simulate_human_behavior(driver)
            driver.uc_gui_click_captcha()
            time.sleep(_sys_random.uniform(CAPTCHA_WAIT_MIN, CAPTCHA_WAIT_MAX))

            if _is_bypassed(driver):
                return True

            # Retry once with longer wait
            logger.debug("First click attempt failed, retrying...")
            time.sleep(_sys_random.uniform(4, 6))
            driver.uc_gui_click_captcha()
            time.sleep(_sys_random.uniform(CAPTCHA_WAIT_MIN, CAPTCHA_WAIT_MAX))
            result = _is_bypassed(driver)
        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.debug("uc_gui_click_captcha failed: %s", e)
            return False
        else:
            return result

    def get_name(self) -> str:
        """Get method name.

        Returns
        -------
        str
            "click_captcha"
        """
        return "click_captcha"


class HumanlikeMethod(BypassMethod):
    """Human-like behavior with scroll, wait, and reload."""

    def attempt(self, driver: "Driver") -> bool:  # type: ignore[invalid-type-form]
        """Attempt bypass using human-like interaction.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.

        Returns
        -------
        bool
            True if bypass successful.
        """
        try:
            logger.debug("Attempting bypass: human-like interaction")
            time.sleep(_sys_random.uniform(6, 10))

            try:
                driver.scroll_to_bottom()
                time.sleep(_sys_random.uniform(1, 2))
                driver.scroll_to_top()
                time.sleep(_sys_random.uniform(2, 3))
            except (AttributeError, RuntimeError) as e:
                logger.debug("Scroll behavior failed: %s", e)

            if _is_bypassed(driver):
                return True

            logger.debug("Trying page refresh...")
            driver.refresh()
            time.sleep(_sys_random.uniform(5, 8))

            if _is_bypassed(driver):
                return True

            try:
                driver.uc_gui_click_captcha()
                time.sleep(_sys_random.uniform(CAPTCHA_WAIT_MIN, CAPTCHA_WAIT_MAX))
            except (AttributeError, RuntimeError, TimeoutError) as e:
                logger.debug("Final captcha click failed: %s", e)

            result = _is_bypassed(driver)
        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.debug("Human-like method failed: %s", e)
            return False
        else:
            return result

    def get_name(self) -> str:
        """Get method name.

        Returns
        -------
        str
            "humanlike"
        """
        return "humanlike"


# Default bypass methods
DEFAULT_BYPASS_METHODS = [
    CdpSolveMethod(),
    CdpClickMethod(),
    CdpGuiClickMethod(),
    HandleCaptchaMethod(),
    ClickCaptchaMethod(),
    HumanlikeMethod(),
]

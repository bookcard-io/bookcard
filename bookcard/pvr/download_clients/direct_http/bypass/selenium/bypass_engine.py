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

"""Bypass engine for orchestrating bypass attempts."""

import logging
import random
import time
from threading import Event
from typing import TYPE_CHECKING

from bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods import (
    BypassMethod,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.challenge_detector import (
    ChallengeDetectionService,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.constants import (
    DEFAULT_MAX_BYPASS_RETRIES,
    MAX_CONSECUTIVE_SAME_CHALLENGE,
    NO_CHALLENGE_WAIT_MAX,
    NO_CHALLENGE_WAIT_MIN,
    RETRY_WAIT_MAX,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.success_checker import (
    SuccessChecker,
)

if TYPE_CHECKING:
    from seleniumbase import Driver

logger = logging.getLogger(__name__)

# Use SystemRandom for non-cryptographic randomness (satisfies S311)
_sys_random = random.SystemRandom()


class BypassEngine:
    """Orchestrates bypass attempts using multiple methods."""

    def __init__(
        self,
        methods: list[BypassMethod],
        challenge_detector: ChallengeDetectionService | None = None,
        success_checker: SuccessChecker | None = None,
    ) -> None:
        """Initialize bypass engine.

        Parameters
        ----------
        methods : list[BypassMethod]
            List of bypass methods to try.
        challenge_detector : ChallengeDetectionService | None
            Service for detecting challenge types. Defaults to new instance.
        success_checker : SuccessChecker | None
            Checker for verifying bypass success. Defaults to new instance.
        """
        self._methods = methods
        self._challenge_detector = challenge_detector or ChallengeDetectionService()
        self._success_checker = success_checker or SuccessChecker()

    def _handle_no_challenge(
        self,
        driver: "Driver",  # type: ignore[invalid-type-form, misc]
        cancel_flag: Event | None,
    ) -> bool | None:
        """Handle case when no challenge is detected.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.
        cancel_flag : Event | None
            Cancellation flag to check.

        Returns
        -------
        bool | None
            True if bypassed, False if cancelled, None if should continue.
        """
        if cancel_flag and cancel_flag.is_set():
            logger.info("Bypass cancelled by user")
            return False

        logger.info("No challenge detected, waiting for page to settle...")
        time.sleep(_sys_random.uniform(NO_CHALLENGE_WAIT_MIN, NO_CHALLENGE_WAIT_MAX))
        if self._success_checker.is_bypassed(driver):
            return True
        # Try a simple reconnect instead of captcha methods
        try:
            driver.reconnect()
            time.sleep(_sys_random.uniform(1, 2))
            if self._success_checker.is_bypassed(driver):
                logger.info("Bypass successful after reconnect")
                return True
        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.debug("Reconnect during no-challenge wait failed: %s", e)
        return None

    def _check_challenge_tracking(
        self,
        challenge_type: str,
        last_challenge_type: str | None,
        consecutive_same_challenge: int,
    ) -> tuple[bool, int]:
        """Check if we should abort due to consecutive same challenges.

        Parameters
        ----------
        challenge_type : str
            Current challenge type.
        last_challenge_type : str | None
            Previous challenge type.
        consecutive_same_challenge : int
            Count of consecutive same challenges.

        Returns
        -------
        tuple[bool, int]
            (should_abort, new_consecutive_count)
        """
        if challenge_type == last_challenge_type:
            consecutive_same_challenge += 1
            if consecutive_same_challenge >= MAX_CONSECUTIVE_SAME_CHALLENGE:
                logger.warning(
                    "Same challenge (%s) detected %d times - aborting",
                    challenge_type,
                    consecutive_same_challenge,
                )
                return True, consecutive_same_challenge
        else:
            consecutive_same_challenge = 1
        return False, consecutive_same_challenge

    def _wait_before_retry(self, try_count: int, cancel_flag: Event | None) -> bool:
        """Wait before retrying bypass method.

        Parameters
        ----------
        try_count : int
            Current attempt number.
        cancel_flag : Event | None
            Cancellation flag to check.

        Returns
        -------
        bool
            True if cancelled, False otherwise.
        """
        if try_count > 0:
            wait_time = min(_sys_random.uniform(2, 4) * try_count, RETRY_WAIT_MAX)
            logger.info("Waiting %.1fs before trying...", wait_time)
            for _ in range(int(wait_time)):
                if cancel_flag and cancel_flag.is_set():
                    logger.info("Bypass cancelled during wait")
                    return True
                time.sleep(1)
            time.sleep(wait_time - int(wait_time))
        return False

    def _try_bypass_method(
        self,
        method: BypassMethod,
        driver: "Driver",  # type: ignore[invalid-type-form]
    ) -> bool:
        """Try a bypass method and check if it succeeded.

        Parameters
        ----------
        method : BypassMethod
            Bypass method to try.
        driver : Driver
            SeleniumBase driver instance.

        Returns
        -------
        bool
            True if bypass successful.
        """
        try:
            if method.attempt(driver):
                logger.info("Bypass successful using %s", method.get_name())
                return True
        except (AttributeError, RuntimeError, TimeoutError) as e:
            logger.warning("Exception in %s: %s", method.get_name(), e)
        return False

    def attempt_bypass(
        self,
        driver: "Driver",  # type: ignore[invalid-type-form]
        max_retries: int | None = None,
        cancel_flag: Event | None = None,
    ) -> bool:
        """Attempt to bypass Cloudflare/DDOS-Guard protection using multiple methods.

        Parameters
        ----------
        driver : Driver
            SeleniumBase driver instance.
        max_retries : int | None
            Maximum number of retry attempts. Defaults to DEFAULT_MAX_BYPASS_RETRIES.
        cancel_flag : Event | None
            Cancellation flag to check during bypass.

        Returns
        -------
        bool
            True if bypass successful.
        """
        max_retries = (
            max_retries if max_retries is not None else DEFAULT_MAX_BYPASS_RETRIES
        )

        last_challenge_type = None
        consecutive_same_challenge = 0

        for try_count in range(max_retries):
            if cancel_flag and cancel_flag.is_set():
                logger.info("Bypass cancelled by user")
                return False

            if self._success_checker.is_bypassed(driver):
                if try_count == 0:
                    logger.info("Page already bypassed")
                return True

            challenge_type = self._challenge_detector.detect(driver)
            logger.debug("Challenge detected: %s", challenge_type)

            # No challenge detected but page doesn't look bypassed - wait and retry
            if challenge_type == "none":
                result = self._handle_no_challenge(driver, cancel_flag)
                if result is not None:
                    return result
                continue

            should_abort, consecutive_same_challenge = self._check_challenge_tracking(
                challenge_type, last_challenge_type, consecutive_same_challenge
            )
            if should_abort:
                return False
            last_challenge_type = challenge_type

            method = self._methods[try_count % len(self._methods)]
            logger.info(
                "Bypass attempt %d/%d using %s",
                try_count + 1,
                max_retries,
                method.get_name(),
            )

            if self._wait_before_retry(try_count, cancel_flag):
                return False

            if self._try_bypass_method(method, driver):
                return True

            logger.info("Bypass method %s failed.", method.get_name())

        logger.warning("Exceeded maximum retries. Bypass failed.")
        return False

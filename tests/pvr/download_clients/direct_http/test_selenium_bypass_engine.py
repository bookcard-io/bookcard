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

"""Tests for selenium bypass engine module."""

from threading import Event
from unittest.mock import MagicMock, patch

from bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_engine import (
    BypassEngine,
)
from bookcard.pvr.download_clients.direct_http.bypass.selenium.constants import (
    MAX_CONSECUTIVE_SAME_CHALLENGE,
)


class TestBypassEngine:
    """Test BypassEngine class."""

    def test_init(self) -> None:
        """Test initialization."""
        methods = [MagicMock(), MagicMock()]
        engine = BypassEngine(methods)
        assert engine._methods == methods
        assert engine._challenge_detector is not None
        assert engine._success_checker is not None

    def test_init_with_dependencies(
        self,
        mock_challenge_detector: MagicMock,
        mock_success_checker: MagicMock,
    ) -> None:
        """Test initialization with injected dependencies."""
        methods = [MagicMock()]
        engine = BypassEngine(
            methods,
            challenge_detector=mock_challenge_detector,
            success_checker=mock_success_checker,
        )
        assert engine._challenge_detector == mock_challenge_detector
        assert engine._success_checker == mock_success_checker

    def test_handle_no_challenge_cancelled(
        self, mock_driver: MagicMock, cancel_flag: Event
    ) -> None:
        """Test _handle_no_challenge when cancelled."""
        cancel_flag.set()
        engine = BypassEngine([])
        result = engine._handle_no_challenge(mock_driver, cancel_flag)
        assert result is False

    def test_handle_no_challenge_success(
        self, mock_driver: MagicMock, mock_success_checker: MagicMock
    ) -> None:
        """Test _handle_no_challenge when already bypassed."""
        mock_success_checker.is_bypassed.return_value = True
        engine = BypassEngine([], success_checker=mock_success_checker)
        with patch("time.sleep"):
            result = engine._handle_no_challenge(mock_driver, None)
            assert result is True

    def test_handle_no_challenge_reconnect_success(
        self, mock_driver: MagicMock, mock_success_checker: MagicMock
    ) -> None:
        """Test _handle_no_challenge with successful reconnect."""
        mock_success_checker.is_bypassed.side_effect = [False, True]
        engine = BypassEngine([], success_checker=mock_success_checker)
        with patch("time.sleep"):
            result = engine._handle_no_challenge(mock_driver, None)
            assert result is True

    def test_check_challenge_tracking_same_challenge(
        self,
    ) -> None:
        """Test _check_challenge_tracking with same challenge."""
        engine = BypassEngine([])
        should_abort, count = engine._check_challenge_tracking(
            "cloudflare", "cloudflare", MAX_CONSECUTIVE_SAME_CHALLENGE - 1
        )
        assert should_abort is True
        assert count == MAX_CONSECUTIVE_SAME_CHALLENGE

    def test_check_challenge_tracking_different_challenge(
        self,
    ) -> None:
        """Test _check_challenge_tracking with different challenge."""
        engine = BypassEngine([])
        should_abort, count = engine._check_challenge_tracking(
            "cloudflare", "ddos_guard", 5
        )
        assert should_abort is False
        assert count == 1

    def test_wait_before_retry_first_attempt(self, cancel_flag: Event) -> None:
        """Test _wait_before_retry on first attempt."""
        engine = BypassEngine([])
        cancelled = engine._wait_before_retry(0, cancel_flag)
        assert cancelled is False

    def test_wait_before_retry_cancelled(self, cancel_flag: Event) -> None:
        """Test _wait_before_retry when cancelled."""
        cancel_flag.set()
        engine = BypassEngine([])
        with patch("time.sleep"):
            cancelled = engine._wait_before_retry(1, cancel_flag)
            assert cancelled is True

    def test_try_bypass_method_success(
        self, mock_driver: MagicMock, mock_bypass_method: MagicMock
    ) -> None:
        """Test _try_bypass_method with success."""
        mock_bypass_method.attempt.return_value = True
        engine = BypassEngine([])
        result = engine._try_bypass_method(mock_bypass_method, mock_driver)
        assert result is True

    def test_try_bypass_method_failure(
        self, mock_driver: MagicMock, mock_bypass_method: MagicMock
    ) -> None:
        """Test _try_bypass_method with failure."""
        mock_bypass_method.attempt.return_value = False
        engine = BypassEngine([])
        result = engine._try_bypass_method(mock_bypass_method, mock_driver)
        assert result is False

    def test_try_bypass_method_exception(
        self, mock_driver: MagicMock, mock_bypass_method: MagicMock
    ) -> None:
        """Test _try_bypass_method with exception."""
        mock_bypass_method.attempt.side_effect = RuntimeError("Error")
        engine = BypassEngine([])
        result = engine._try_bypass_method(mock_bypass_method, mock_driver)
        assert result is False

    def test_attempt_bypass_already_bypassed(
        self,
        mock_driver: MagicMock,
        mock_success_checker: MagicMock,
    ) -> None:
        """Test attempt_bypass when already bypassed."""
        mock_success_checker.is_bypassed.return_value = True
        engine = BypassEngine([], success_checker=mock_success_checker)
        result = engine.attempt_bypass(mock_driver)
        assert result is True

    def test_attempt_bypass_success(
        self,
        mock_driver: MagicMock,
        mock_challenge_detector: MagicMock,
        mock_success_checker: MagicMock,
        mock_bypass_method: MagicMock,
    ) -> None:
        """Test attempt_bypass with successful bypass."""
        mock_challenge_detector.detect.return_value = "cloudflare"
        mock_success_checker.is_bypassed.side_effect = [False, True]
        mock_bypass_method.attempt.return_value = True

        engine = BypassEngine(
            [mock_bypass_method],
            challenge_detector=mock_challenge_detector,
            success_checker=mock_success_checker,
        )

        with patch("time.sleep"):
            result = engine.attempt_bypass(mock_driver)
            assert result is True

    def test_attempt_bypass_no_challenge(
        self,
        mock_driver: MagicMock,
        mock_challenge_detector: MagicMock,
        mock_success_checker: MagicMock,
    ) -> None:
        """Test attempt_bypass with no challenge."""
        mock_challenge_detector.detect.return_value = "none"
        mock_success_checker.is_bypassed.return_value = True

        engine = BypassEngine(
            [],
            challenge_detector=mock_challenge_detector,
            success_checker=mock_success_checker,
        )

        with patch("time.sleep"):
            result = engine.attempt_bypass(mock_driver)
            assert result is True

    def test_attempt_bypass_max_retries(
        self,
        mock_driver: MagicMock,
        mock_challenge_detector: MagicMock,
        mock_success_checker: MagicMock,
        mock_bypass_method: MagicMock,
    ) -> None:
        """Test attempt_bypass exceeding max retries."""
        mock_challenge_detector.detect.return_value = "cloudflare"
        mock_success_checker.is_bypassed.return_value = False
        mock_bypass_method.attempt.return_value = False

        engine = BypassEngine(
            [mock_bypass_method],
            challenge_detector=mock_challenge_detector,
            success_checker=mock_success_checker,
        )

        with patch("time.sleep"):
            result = engine.attempt_bypass(mock_driver, max_retries=2)
            assert result is False

    def test_attempt_bypass_cancelled(
        self,
        mock_driver: MagicMock,
        cancel_flag: Event,
    ) -> None:
        """Test attempt_bypass when cancelled."""
        cancel_flag.set()
        engine = BypassEngine([])
        result = engine.attempt_bypass(mock_driver, cancel_flag=cancel_flag)
        assert result is False

    def test_attempt_bypass_cycles_methods(
        self,
        mock_driver: MagicMock,
        mock_challenge_detector: MagicMock,
        mock_success_checker: MagicMock,
    ) -> None:
        """Test that attempt_bypass cycles through methods."""
        mock_challenge_detector.detect.return_value = "cloudflare"
        mock_success_checker.is_bypassed.return_value = False

        method1 = MagicMock()
        method1.attempt.return_value = False
        method1.get_name.return_value = "method1"
        method2 = MagicMock()
        method2.attempt.return_value = False
        method2.get_name.return_value = "method2"

        engine = BypassEngine(
            [method1, method2],
            challenge_detector=mock_challenge_detector,
            success_checker=mock_success_checker,
        )

        with patch("time.sleep"):
            engine.attempt_bypass(mock_driver, max_retries=3)
            # Should have tried both methods
            assert method1.attempt.call_count >= 1
            assert method2.attempt.call_count >= 1

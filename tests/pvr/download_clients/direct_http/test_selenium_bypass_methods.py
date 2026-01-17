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

"""Tests for selenium bypass methods module."""

from unittest.mock import MagicMock, patch

import pytest

from bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods import (
    BypassMethod,
    CdpClickMethod,
    CdpGuiClickMethod,
    CdpSolveMethod,
    ClickCaptchaMethod,
    HandleCaptchaMethod,
    HumanlikeMethod,
    cdp_mode,
)


class TestCdpModeContextManager:
    """Test cdp_mode context manager."""

    def test_cdp_mode_activates_and_reconnects(self, mock_driver: MagicMock) -> None:
        """Test that cdp_mode activates CDP and reconnects on exit."""
        with cdp_mode(mock_driver):
            pass

        mock_driver.activate_cdp_mode.assert_called_once()
        mock_driver.reconnect.assert_called()

    def test_cdp_mode_reconnects_on_exception(self, mock_driver: MagicMock) -> None:
        """Test that cdp_mode reconnects even when exception occurs."""
        mock_driver.activate_cdp_mode.side_effect = RuntimeError("Error")
        with pytest.raises(RuntimeError), cdp_mode(mock_driver):
            pass

        # Should still attempt reconnect (finally block always executes)
        mock_driver.reconnect.assert_called()


class TestCdpSolveMethod:
    """Test CdpSolveMethod class."""

    def test_get_name(self) -> None:
        """Test get_name method."""
        method = CdpSolveMethod()
        assert method.get_name() == "cdp_solve"

    def test_attempt_success(self, mock_driver: MagicMock) -> None:
        """Test successful bypass attempt."""
        method = CdpSolveMethod()
        mock_driver.cdp.solve_captcha = MagicMock()

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                return_value=True,
            ),
            patch("time.sleep"),
        ):
            result = method.attempt(mock_driver)
            assert result is True
            mock_driver.cdp.solve_captcha.assert_called_once()

    def test_attempt_failure(self, mock_driver: MagicMock) -> None:
        """Test failed bypass attempt."""
        method = CdpSolveMethod()
        mock_driver.cdp.solve_captcha.side_effect = RuntimeError("Error")

        with patch("time.sleep"):
            result = method.attempt(mock_driver)
            assert result is False

    def test_attempt_uses_context_manager(self, mock_driver: MagicMock) -> None:
        """Test that attempt uses cdp_mode context manager."""
        method = CdpSolveMethod()
        mock_driver.cdp.solve_captcha = MagicMock()

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                return_value=True,
            ),
            patch("time.sleep"),
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods.cdp_mode"
            ) as mock_cdp_mode,
        ):
            mock_cdp_mode.return_value.__enter__ = MagicMock(return_value=mock_driver)
            mock_cdp_mode.return_value.__exit__ = MagicMock(return_value=False)
            method.attempt(mock_driver)
            mock_cdp_mode.assert_called_once_with(mock_driver)


class TestCdpClickMethod:
    """Test CdpClickMethod class."""

    def test_get_name(self) -> None:
        """Test get_name method."""
        method = CdpClickMethod()
        assert method.get_name() == "cdp_click"

    def test_attempt_success(self, mock_driver: MagicMock) -> None:
        """Test successful bypass attempt."""
        method = CdpClickMethod()
        mock_driver.cdp.is_element_visible.return_value = True
        mock_driver.cdp.click = MagicMock()

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                return_value=True,
            ),
            patch("time.sleep"),
        ):
            result = method.attempt(mock_driver)
            assert result is True

    def test_attempt_no_visible_elements(self, mock_driver: MagicMock) -> None:
        """Test attempt when no elements are visible."""
        method = CdpClickMethod()
        mock_driver.cdp.is_element_visible.return_value = False

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                return_value=False,
            ),
            patch("time.sleep"),
        ):
            result = method.attempt(mock_driver)
            assert result is False

    def test_attempt_uses_context_manager(self, mock_driver: MagicMock) -> None:
        """Test that attempt uses cdp_mode context manager."""
        method = CdpClickMethod()
        mock_driver.cdp.is_element_visible.return_value = True
        mock_driver.cdp.click = MagicMock()

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                return_value=True,
            ),
            patch("time.sleep"),
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods.cdp_mode"
            ) as mock_cdp_mode,
        ):
            mock_cdp_mode.return_value.__enter__ = MagicMock(return_value=mock_driver)
            mock_cdp_mode.return_value.__exit__ = MagicMock(return_value=False)
            method.attempt(mock_driver)
            # Should be called for each selector attempt
            assert mock_cdp_mode.called


class TestCdpGuiClickMethod:
    """Test CdpGuiClickMethod class."""

    def test_get_name(self) -> None:
        """Test get_name method."""
        method = CdpGuiClickMethod()
        assert method.get_name() == "cdp_gui_click"

    def test_attempt_success_gui_click_captcha(self, mock_driver: MagicMock) -> None:
        """Test successful bypass with gui_click_captcha."""
        method = CdpGuiClickMethod()
        mock_driver.cdp.gui_click_captcha = MagicMock()

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                return_value=True,
            ),
            patch("time.sleep"),
        ):
            result = method.attempt(mock_driver)
            assert result is True

    def test_attempt_success_gui_click_element(self, mock_driver: MagicMock) -> None:
        """Test successful bypass with gui_click_element."""
        method = CdpGuiClickMethod()
        mock_driver.cdp.gui_click_captcha.side_effect = RuntimeError("Error")
        mock_driver.cdp.is_element_visible.return_value = True
        mock_driver.cdp.gui_click_element = MagicMock()

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                side_effect=[False, True],
            ),
            patch("time.sleep"),
        ):
            result = method.attempt(mock_driver)
            assert result is True

    def test_attempt_uses_context_manager(self, mock_driver: MagicMock) -> None:
        """Test that attempt uses cdp_mode context manager."""
        method = CdpGuiClickMethod()
        mock_driver.cdp.gui_click_captcha = MagicMock()

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                return_value=True,
            ),
            patch("time.sleep"),
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods.cdp_mode"
            ) as mock_cdp_mode,
        ):
            mock_cdp_mode.return_value.__enter__ = MagicMock(return_value=mock_driver)
            mock_cdp_mode.return_value.__exit__ = MagicMock(return_value=False)
            method.attempt(mock_driver)
            assert mock_cdp_mode.called


class TestHandleCaptchaMethod:
    """Test HandleCaptchaMethod class."""

    def test_get_name(self) -> None:
        """Test get_name method."""
        method = HandleCaptchaMethod()
        assert method.get_name() == "handle_captcha"

    def test_attempt_success(self, mock_driver: MagicMock) -> None:
        """Test successful bypass attempt."""
        method = HandleCaptchaMethod()
        mock_driver.uc_gui_handle_captcha = MagicMock()

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                return_value=True,
            ),
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._simulate_human_behavior"
            ),
            patch("time.sleep"),
        ):
            result = method.attempt(mock_driver)
            assert result is True

    def test_attempt_failure(self, mock_driver: MagicMock) -> None:
        """Test failed bypass attempt."""
        method = HandleCaptchaMethod()
        mock_driver.uc_gui_handle_captcha.side_effect = RuntimeError("Error")

        with patch(
            "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._simulate_human_behavior"
        ):
            result = method.attempt(mock_driver)
            assert result is False


class TestClickCaptchaMethod:
    """Test ClickCaptchaMethod class."""

    def test_get_name(self) -> None:
        """Test get_name method."""
        method = ClickCaptchaMethod()
        assert method.get_name() == "click_captcha"

    def test_attempt_success_first_attempt(self, mock_driver: MagicMock) -> None:
        """Test successful bypass on first attempt."""
        method = ClickCaptchaMethod()
        mock_driver.uc_gui_click_captcha = MagicMock()

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                return_value=True,
            ),
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._simulate_human_behavior"
            ),
            patch("time.sleep"),
        ):
            result = method.attempt(mock_driver)
            assert result is True

    def test_attempt_success_retry(self, mock_driver: MagicMock) -> None:
        """Test successful bypass on retry."""
        method = ClickCaptchaMethod()
        mock_driver.uc_gui_click_captcha = MagicMock()

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                side_effect=[False, True],
            ),
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._simulate_human_behavior"
            ),
            patch("time.sleep"),
        ):
            result = method.attempt(mock_driver)
            assert result is True
            assert mock_driver.uc_gui_click_captcha.call_count == 2

    def test_attempt_failure(self, mock_driver: MagicMock) -> None:
        """Test failed bypass attempt."""
        method = ClickCaptchaMethod()
        mock_driver.uc_gui_click_captcha.side_effect = RuntimeError("Error")

        with patch(
            "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._simulate_human_behavior"
        ):
            result = method.attempt(mock_driver)
            assert result is False


class TestHumanlikeMethod:
    """Test HumanlikeMethod class."""

    def test_get_name(self) -> None:
        """Test get_name method."""
        method = HumanlikeMethod()
        assert method.get_name() == "humanlike"

    def test_attempt_success_after_scroll(self, mock_driver: MagicMock) -> None:
        """Test successful bypass after scroll."""
        method = HumanlikeMethod()
        mock_driver.scroll_to_bottom = MagicMock()
        mock_driver.scroll_to_top = MagicMock()

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                return_value=True,
            ),
            patch("time.sleep"),
        ):
            result = method.attempt(mock_driver)
            assert result is True

    def test_attempt_success_after_refresh(self, mock_driver: MagicMock) -> None:
        """Test successful bypass after refresh."""
        method = HumanlikeMethod()
        mock_driver.scroll_to_bottom = MagicMock()
        mock_driver.scroll_to_top = MagicMock()
        mock_driver.refresh = MagicMock()

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                side_effect=[False, True],
            ),
            patch("time.sleep"),
        ):
            result = method.attempt(mock_driver)
            assert result is True

    def test_attempt_uses_js_fallback(self, mock_driver: MagicMock) -> None:
        """Test that attempt uses JS fallback when scroll helpers unavailable."""
        method = HumanlikeMethod()
        # Don't provide scroll_to_bottom/scroll_to_top
        mock_driver.scroll_to_bottom = None
        mock_driver.scroll_to_top = None
        mock_driver.execute_script = MagicMock()

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                return_value=True,
            ),
            patch("time.sleep"),
        ):
            method.attempt(mock_driver)
            assert mock_driver.execute_script.called

    def test_attempt_failure(self, mock_driver: MagicMock) -> None:
        """Test failed bypass attempt."""
        method = HumanlikeMethod()
        mock_driver.scroll_to_bottom.side_effect = RuntimeError("Error")

        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.selenium.bypass_methods._is_bypassed",
                return_value=False,
            ),
            patch("time.sleep"),
        ):
            result = method.attempt(mock_driver)
            assert result is False


class TestBypassMethod:
    """Test BypassMethod abstract class."""

    def test_cannot_instantiate(self) -> None:
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            BypassMethod()  # type: ignore[abstract]

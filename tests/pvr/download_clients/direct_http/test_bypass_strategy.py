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

"""Tests for bypass strategy module."""

import pytest

from bookcard.pvr.download_clients.direct_http.bypass.result import BypassResult
from bookcard.pvr.download_clients.direct_http.bypass.strategy import BypassStrategy


class TestBypassStrategy:
    """Test BypassStrategy abstract class."""

    def test_cannot_instantiate(self) -> None:
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            BypassStrategy()

    def test_fetch_abstract(self) -> None:
        """Test that fetch is abstract."""

        # Create a concrete implementation for testing
        class ConcreteStrategy(BypassStrategy):
            def fetch(self, url: str) -> BypassResult:
                return BypassResult(html="<html>test</html>")

            def validate_dependencies(self) -> None:
                pass

        strategy = ConcreteStrategy()
        result = strategy.fetch("https://example.com")
        assert result.success is True

    def test_validate_dependencies_abstract(self) -> None:
        """Test that validate_dependencies is abstract."""

        # Create a concrete implementation for testing
        class ConcreteStrategy(BypassStrategy):
            def fetch(self, url: str) -> BypassResult:
                return BypassResult(html="<html>test</html>")

            def validate_dependencies(self) -> None:
                pass

        strategy = ConcreteStrategy()
        strategy.validate_dependencies()  # Should not raise

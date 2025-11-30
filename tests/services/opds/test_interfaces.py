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

from __future__ import annotations

import pytest

from fundamental.services.opds.interfaces import (
    IOpdsAuthProvider,
    IOpdsBookQueryService,
    IOpdsFeedService,
    IOpdsXmlBuilder,
)


class TestInterfaces:
    def test_interfaces_are_abstract(self) -> None:
        """Test that interfaces cannot be instantiated."""
        with pytest.raises(TypeError):
            IOpdsFeedService()

        with pytest.raises(TypeError):
            IOpdsXmlBuilder()

        with pytest.raises(TypeError):
            IOpdsBookQueryService()

        with pytest.raises(TypeError):
            IOpdsAuthProvider()

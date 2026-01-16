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

"""Mirror rotation strategy for Anna's Archive."""

import logging
import urllib.parse

logger = logging.getLogger(__name__)


class MirrorRotator:
    """Handles mirror selection and rotation."""

    def __init__(self, mirrors: list[str]) -> None:
        self._mirrors = list(mirrors)

    def get_mirrors(self, current_url: str) -> list[str]:
        """Get list of mirrors to try, starting with the current one if applicable."""
        mirrors = list(self._mirrors)

        parsed_url = urllib.parse.urlparse(current_url)
        current_base = f"{parsed_url.scheme}://{parsed_url.netloc}"

        if current_base in mirrors:
            mirrors.remove(current_base)
            mirrors.insert(0, current_base)
        elif not any(m in current_base for m in mirrors):
            # If current URL uses a mirror not in our list, add it first
            mirrors.insert(0, current_base)

        return mirrors

    def get_next_url(self, current_url: str, mirror_base: str) -> str:
        """Construct URL for the next mirror."""
        path = urllib.parse.urlparse(current_url).path
        return urllib.parse.urljoin(mirror_base, path)

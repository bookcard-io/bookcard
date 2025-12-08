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

"""KCC locator for discovering KCC executable.

Handles discovery and validation of KCC CLI executable,
following SRP by focusing solely on KCC location.
"""

import shutil
from pathlib import Path


class KCCLocator:
    """Locates and validates KCC executable.

    Discovers KCC kcc-c2e.py script by checking Docker
    installation path and system PATH.

    Methods
    -------
    find_kcc() -> Path | None
        Find the KCC executable.
    """

    def find_kcc(self) -> Path | None:
        """Get path to KCC kcc-c2e.py script.

        Checks Docker installation path first, then falls back
        to PATH lookup.

        Returns
        -------
        Path | None
            Path to KCC executable if found, None otherwise.
        """
        # First check Docker installation path
        docker_path = Path("/opt/kcc/kcc-c2e.py")
        if docker_path.exists():
            return docker_path

        # Fallback to PATH lookup
        kcc = shutil.which("kcc-c2e") or shutil.which("c2e")
        if kcc:
            return Path(kcc)

        # Also check for kcc-c2e.py directly
        kcc_py = shutil.which("kcc-c2e.py")
        if kcc_py:
            return Path(kcc_py)

        return None

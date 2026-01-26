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

"""Library scan task package.

This package contains the library scan task adapter and its collaborators
(publisher, state repository, monitor, orchestrator).

The goal is to keep each module small and focused (SRP), while allowing
dependencies to be injected via narrow protocols (DIP/IoC).
"""

from bookcard.services.tasks.library_scan.task import LibraryScanTask

__all__ = ["LibraryScanTask"]

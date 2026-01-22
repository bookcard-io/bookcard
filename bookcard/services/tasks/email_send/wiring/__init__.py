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

"""Composition root for the email-send task.

This package contains default wiring helpers. It intentionally depends on
concrete implementations, keeping `dependencies.py` focused on abstractions.
"""

from bookcard.services.tasks.email_send.wiring.defaults import (
    create_default_email_send_dependencies,
)

__all__ = [
    "create_default_email_send_dependencies",
]

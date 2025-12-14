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

"""Calibre helper scripts executed via ``calibre-debug``."""

from __future__ import annotations

LIST_USER_PLUGINS_AS_JSON = r"""
import json
from pathlib import Path

from calibre.utils.config import config_dir
import calibre.customize.ui as u

u.initialize_plugins()

plugins_dir = Path(config_dir) / "plugins"
user_names = {p.stem for p in plugins_dir.glob("*.zip")} if plugins_dir.exists() else set()

res = []
for name in sorted(user_names):
    p = u.find_plugin(name)
    if p is None:
        continue

    author = getattr(p, "author", "") or ""
    description = getattr(p, "description", "") or ""
    version = getattr(p, "version", None)
    if isinstance(version, tuple):
        version_str = ", ".join(str(x) for x in version)
    else:
        version_str = str(version) if version is not None else ""

    res.append(
        {
            "name": getattr(p, "name", name) or name,
            "version": version_str,
            "author": author or "Unknown",
            "description": description,
        }
    )

print(json.dumps(res))
"""

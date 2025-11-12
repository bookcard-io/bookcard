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

"""Filesystem suggestion endpoints.

Provides directory autocomplete suggestions for absolute paths that the
backend process can read/execute. Meant for assisting path entry in the
admin UI.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Query, status

if TYPE_CHECKING:
    from collections.abc import Iterable

router = APIRouter(prefix="/fs", tags=["fs"])


# Screaming-case exclusion list of root-level directories to ignore. These are
# considered system or container paths that are rarely useful for media
# libraries and often large or protected.
EXCLUDED_FS_DIR_PREFIXES: tuple[str, ...] = (
    "/app",
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/lib",
    "/lib64",
    "/proc",
    "/run",
    "/sbin",
    "/snap",
    "/srv",
    "/sys",
    "/tmp",  # noqa: S108
    "/usr",
    "/var",
    "/opt",
    "/overlay",
    "/root",
)


def _is_under_excluded(path: Path) -> bool:
    """Return True if ``path`` is under an excluded root prefix.

    Parameters
    ----------
    path : Path
        Filesystem path to check.

    Returns
    -------
    bool
        Whether the path is under any of the excluded prefixes.
    """
    p = path.resolve(strict=False)
    as_posix = p.as_posix()
    return any(
        as_posix == prefix or as_posix.startswith(prefix + "/")
        for prefix in EXCLUDED_FS_DIR_PREFIXES
    )


def _list_subdirectories(base: Path) -> Iterable[Path]:
    """Yield immediate subdirectories of ``base`` safely.

    Parameters
    ----------
    base : Path
        Directory to list.

    Yields
    ------
    Path
        Paths of immediate child directories.
    """
    # Require read and execute permissions on the base directory
    if not os.access(base, os.R_OK | os.X_OK):
        return
    try:
        with os.scandir(base) as it:  # type: ignore[arg-type]
            for entry in it:
                try:
                    if not entry.is_dir(follow_symlinks=True):
                        continue
                except OSError:
                    # Skip entries we cannot stat
                    continue
                child = Path(entry.path)
                if _is_under_excluded(child):
                    continue
                if not os.access(child, os.R_OK | os.X_OK):
                    continue
                yield child
    except (FileNotFoundError, NotADirectoryError, PermissionError, OSError):
        return


def _normalize_query(q: str) -> str:
    """Normalize raw query text into an absolute path-like string.

    Parameters
    ----------
    q : str
        Raw query string from the client.

    Returns
    -------
    str
        Normalized absolute-path-like string.
    """
    query = (q or "").strip()
    if query.startswith("~"):
        query = str(Path(query).expanduser())
    if query and not query.startswith("/"):
        query = "/" + query
    return query


def _resolve_base_and_needle(candidate: Path) -> tuple[Path, str]:
    """Resolve the base directory to list and the filter needle.

    Parameters
    ----------
    candidate : Path
        Candidate path from the normalized query.

    Returns
    -------
    tuple[Path, str]
        The base directory to list and the final-segment needle.

    Raises
    ------
    HTTPException
        If the candidate path cannot be inspected.
    """
    try:
        if candidate.is_dir():
            base_dir = candidate
            needle = ""
        else:
            base_dir = (
                candidate.parent if candidate.parent.as_posix() != "" else Path("/")
            )
            needle = candidate.name
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    else:
        return base_dir, needle


def _list_children_filtered(base_dir: Path) -> list[Path]:
    """List immediate child directories with root-level exclusions applied."""
    if base_dir == Path("/"):
        return [
            p
            for p in _list_subdirectories(base_dir)
            if not any(
                p.as_posix().startswith(prefix + "/") or p.as_posix() == prefix
                for prefix in EXCLUDED_FS_DIR_PREFIXES
            )
        ]
    return list(_list_subdirectories(base_dir))


def _build_suggestions(children: Iterable[Path], needle: str, limit: int) -> list[str]:
    """Build a sorted list of suggestion strings respecting limit and needle."""
    suggestions: list[str] = []
    if needle:
        for child in children:
            if child.name.startswith(needle):
                suggestions.append(child.as_posix())
                if len(suggestions) >= limit:
                    break
    else:
        for child in children:
            suggestions.append(child.as_posix())
            if len(suggestions) >= limit:
                break
    suggestions.sort()
    return suggestions[:limit]


@router.get("/suggest_dirs")
def suggest_dirs(
    q: str = Query(default="", description="Absolute path or prefix for suggestions."),
    limit: int = Query(
        default=50, ge=1, le=200, description="Maximum number of suggestions to return."
    ),
) -> dict[str, list[str]]:
    """Suggest accessible directories for a given absolute path prefix.

    The endpoint performs a shallow listing of the candidate parent directory
    and filters results by the final path segment prefix. This allows recursive
    exploration through successive requests without scanning the entire
    filesystem at once.

    Parameters
    ----------
    q : str, optional
        Absolute path prefix typed by the user. ``~`` is expanded. When empty,
        suggestions are produced from the filesystem root ``/`` (excluding
        obvious system directories defined in ``EXCLUDED_FS_DIR_PREFIXES``).
    limit : int, optional
        Maximum number of directory suggestions to return, by default 50.

    Returns
    -------
    dict[str, list[str]]
        JSON object with a ``suggestions`` list of absolute directory paths.

    Raises
    ------
    HTTPException
        If the input path attempts path traversal outside the filesystem root
        context or is otherwise invalid.
    """
    query = _normalize_query(q)
    # Base directory and needle prefix
    candidate = Path(query) if query else Path("/")

    # If the candidate is excluded outright, return no suggestions
    if _is_under_excluded(candidate):
        return {"suggestions": []}

    base_dir, needle = _resolve_base_and_needle(candidate)
    # If the parent/base itself is excluded, do not list
    if _is_under_excluded(base_dir):
        return {"suggestions": []}

    # Root-level exclusions: if we're at '/', filter by excluded prefixes
    children = _list_children_filtered(base_dir)
    suggestions = _build_suggestions(children, needle, limit)
    return {"suggestions": suggestions}

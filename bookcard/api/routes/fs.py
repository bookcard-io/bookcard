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

Provides directory and file autocomplete suggestions for absolute paths that the
backend process can read/execute. Meant for assisting path entry in the
admin UI.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, status

from bookcard.api.deps import get_admin_user

if TYPE_CHECKING:
    from collections.abc import Iterable

router = APIRouter(prefix="/fs", tags=["fs"])


# Screaming-case exclusion list of root-level directories to ignore. These are
# considered system or container paths that are rarely useful for media
# libraries and often large or protected.
EXCLUDED_FS_DIR_PREFIXES: tuple[str, ...] = (
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
    # Check original path first (handles symlinks like /etc -> /private/etc on macOS)
    original_posix = path.as_posix()
    if any(
        original_posix == prefix or original_posix.startswith(prefix + "/")
        for prefix in EXCLUDED_FS_DIR_PREFIXES
    ):
        return True

    # Check resolved path
    p = path.resolve(strict=False)
    resolved_posix = p.as_posix()
    # On macOS, /etc and /var are symlinks to /private/etc and /private/var
    # Normalize by removing /private prefix if present
    normalized_posix = resolved_posix.removeprefix("/private")
    return any(
        normalized_posix == prefix or normalized_posix.startswith(prefix + "/")
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


def _list_files(base: Path) -> Iterable[Path]:
    """Yield immediate files in ``base`` safely.

    Parameters
    ----------
    base : Path
        Directory to list.

    Yields
    ------
    Path
        Paths of immediate child files.
    """
    # Require read and execute permissions on the base directory
    if not os.access(base, os.R_OK | os.X_OK):
        return
    try:
        with os.scandir(base) as it:  # type: ignore[arg-type]
            for entry in it:
                try:
                    if not entry.is_file(follow_symlinks=True):
                        continue
                except OSError:
                    # Skip entries we cannot stat
                    continue
                child = Path(entry.path)
                if _is_under_excluded(child):
                    continue
                if not os.access(child, os.R_OK):
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


def _list_children_with_files_filtered(base_dir: Path) -> list[Path]:
    """List immediate child directories and files with root-level exclusions applied."""
    children: list[Path] = []
    if base_dir == Path("/"):
        children.extend(
            p
            for p in _list_subdirectories(base_dir)
            if not any(
                p.as_posix().startswith(prefix + "/") or p.as_posix() == prefix
                for prefix in EXCLUDED_FS_DIR_PREFIXES
            )
        )
        # Don't list files at root level
    else:
        children.extend(_list_subdirectories(base_dir))
        children.extend(_list_files(base_dir))
    return children


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


@router.get(
    "/suggest_dirs",
    dependencies=[Depends(get_admin_user)],
)
def suggest_dirs(
    q: str = Query(default="", description="Absolute path or prefix for suggestions."),
    limit: int = Query(
        default=50, ge=1, le=200, description="Maximum number of suggestions to return."
    ),
    include_files: bool = Query(
        default=False,
        description="Whether to include files in suggestions (default: False, directories only).",
    ),
) -> dict[str, list[str]]:
    """Suggest accessible directories (and optionally files) for a given absolute path prefix.

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
        Maximum number of suggestions to return, by default 50.
    include_files : bool, optional
        Whether to include files in suggestions, by default False (directories only).

    Returns
    -------
    dict[str, list[str]]
        JSON object with a ``suggestions`` list of absolute paths (directories and/or files).

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

    # List children (directories and optionally files)
    if include_files:
        children = _list_children_with_files_filtered(base_dir)
    else:
        children = _list_children_filtered(base_dir)
    suggestions = _build_suggestions(children, needle, limit)
    return {"suggestions": suggestions}

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

"""Filesystem suggestion endpoints tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

if TYPE_CHECKING:
    from collections.abc import Iterator

from fundamental.api.routes.fs import (
    EXCLUDED_FS_DIR_PREFIXES,
    _build_suggestions,
    _is_under_excluded,
    _list_children_filtered,
    _list_subdirectories,
    _normalize_query,
    _resolve_base_and_needle,
    suggest_dirs,
)


@pytest.fixture
def temp_dir() -> Iterator[Path]:  # type: ignore[type-arg]
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ==================== _is_under_excluded Tests ====================


@pytest.mark.parametrize(
    ("path_str", "expected"),
    [
        ("/bin", True),
        ("/usr", True),
        ("/usr/local", True),
        ("/etc/config", True),
        ("/home", False),
        ("/home/user", False),
        ("/media", False),
        ("/mnt", False),
        ("/opt/custom", True),
        ("/var/log", True),
        ("/root", True),
        ("/root/.ssh", True),
    ],
)
def test_is_under_excluded(path_str: str, expected: bool) -> None:
    """Test _is_under_excluded identifies excluded paths (lines 83-88)."""
    path = Path(path_str)
    result = _is_under_excluded(path)
    assert result == expected


def test_is_under_excluded_exact_match() -> None:
    """Test _is_under_excluded matches exact excluded prefix."""
    for prefix in EXCLUDED_FS_DIR_PREFIXES:
        path = Path(prefix)
        assert _is_under_excluded(path) is True


def test_is_under_excluded_subdirectory() -> None:
    """Test _is_under_excluded matches subdirectories of excluded prefixes."""
    for prefix in EXCLUDED_FS_DIR_PREFIXES:
        subpath = Path(f"{prefix}/subdir")
        assert _is_under_excluded(subpath) is True


# ==================== _list_subdirectories Tests ====================


def test_list_subdirectories_returns_directories(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _list_subdirectories lists accessible subdirectories (lines 104-121)."""
    # Create subdirectories
    (temp_dir / "dir1").mkdir()
    (temp_dir / "dir2").mkdir()
    (temp_dir / "file.txt").write_text("content")

    # Patch _is_under_excluded to return False for temp directories
    # (temp dirs resolve to /tmp/... which is excluded)
    with patch("fundamental.api.routes.fs._is_under_excluded", return_value=False):
        result = list(_list_subdirectories(temp_dir))
        assert len(result) == 2
        assert any(p.name == "dir1" for p in result)
        assert any(p.name == "dir2" for p in result)


def test_list_subdirectories_no_permissions(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _list_subdirectories returns empty when no read/execute permissions (lines 105-106)."""
    with patch("os.access", return_value=False):
        result = list(_list_subdirectories(temp_dir))
        assert len(result) == 0


def test_list_subdirectories_skips_files(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _list_subdirectories skips files (lines 110-112)."""
    (temp_dir / "file.txt").write_text("content")
    (temp_dir / "dir").mkdir()

    with patch("fundamental.api.routes.fs._is_under_excluded", return_value=False):
        result = list(_list_subdirectories(temp_dir))
        assert len(result) == 1
        assert result[0].name == "dir"


def test_list_subdirectories_skips_excluded(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _list_subdirectories skips excluded directories (lines 117-118)."""
    (temp_dir / "dir1").mkdir()
    (temp_dir / "dir2").mkdir()

    # Mock _is_under_excluded to exclude dir2
    def mock_is_under_excluded(path: Path) -> bool:
        return path.name == "dir2"

    with patch(
        "fundamental.api.routes.fs._is_under_excluded",
        side_effect=mock_is_under_excluded,
    ):
        result = list(_list_subdirectories(temp_dir))
        assert len(result) == 1
        assert result[0].name == "dir1"


def test_list_subdirectories_skips_no_permission_child(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _list_subdirectories skips children without read/execute permissions (lines 119-120)."""
    (temp_dir / "dir1").mkdir()
    (temp_dir / "dir2").mkdir()

    call_count = 0

    def mock_access(path: Path | str, mode: int) -> bool:
        nonlocal call_count
        call_count += 1
        # First call is for base dir (should pass), subsequent calls are for children
        if call_count == 1:
            return True
        # Only dir1 has permissions - convert to Path if needed to check name
        path_obj = Path(path) if isinstance(path, str) else path
        return path_obj.name == "dir1"

    with (
        patch("os.access", side_effect=mock_access),
        patch("fundamental.api.routes.fs._is_under_excluded", return_value=False),
    ):
        result = list(_list_subdirectories(temp_dir))
        assert len(result) == 1
        assert result[0].name == "dir1"


def test_list_subdirectories_handles_oserror_on_stat(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _list_subdirectories handles OSError when statting entries (lines 113-115)."""
    mock_entry = MagicMock()
    mock_entry.is_dir.side_effect = OSError("Permission denied")
    mock_entry.path = "/some/path"

    # Create a context manager mock that returns an iterator
    mock_scandir_result = MagicMock()
    mock_scandir_result.__enter__ = MagicMock(return_value=iter([mock_entry]))
    mock_scandir_result.__exit__ = MagicMock(return_value=False)

    with patch("os.scandir", return_value=mock_scandir_result):
        result = list(_list_subdirectories(temp_dir))
        assert len(result) == 0


def test_list_subdirectories_handles_scandir_exceptions(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _list_subdirectories handles scandir exceptions (lines 122-123)."""
    with patch("os.scandir", side_effect=FileNotFoundError("Not found")):
        result = list(_list_subdirectories(temp_dir))
        assert len(result) == 0

    with patch("os.scandir", side_effect=PermissionError("Permission denied")):
        result = list(_list_subdirectories(temp_dir))
        assert len(result) == 0

    with patch("os.scandir", side_effect=NotADirectoryError("Not a directory")):
        result = list(_list_subdirectories(temp_dir))
        assert len(result) == 0

    with patch("os.scandir", side_effect=OSError("Other error")):
        result = list(_list_subdirectories(temp_dir))
        assert len(result) == 0


# ==================== _normalize_query Tests ====================


@pytest.mark.parametrize(
    ("input_query", "expected"),
    [
        ("", ""),  # Empty string returns empty (caller handles default to "/")
        ("/", "/"),
        ("/home", "/home"),
        ("/home/user", "/home/user"),
        ("home", "/home"),
        ("~", str(Path("~").expanduser())),
        ("~/books", str(Path("~/books").expanduser())),
        ("  /home  ", "/home"),
        ("  ", ""),  # Whitespace-only returns empty (caller handles default to "/")
    ],
)
def test_normalize_query(input_query: str, expected: str) -> None:
    """Test _normalize_query normalizes various input formats (lines 139-144)."""
    result = _normalize_query(input_query)
    assert result == expected


def test_normalize_query_strips_whitespace() -> None:
    """Test _normalize_query strips whitespace (line 139)."""
    assert _normalize_query("  /path  ") == "/path"
    assert (
        _normalize_query("  ") == ""
    )  # Whitespace-only returns empty (caller handles default)


def test_normalize_query_expands_tilde() -> None:
    """Test _normalize_query expands tilde (lines 140-141)."""
    result = _normalize_query("~/books")
    assert result.startswith(("/", str(Path("~").expanduser())))


def test_normalize_query_prepends_slash() -> None:
    """Test _normalize_query prepends slash to relative paths (lines 142-143)."""
    assert _normalize_query("home") == "/home"
    assert _normalize_query("books/albums") == "/books/albums"


# ==================== _resolve_base_and_needle Tests ====================


def test_resolve_base_and_needle_directory(temp_dir: Path) -> None:
    """Test _resolve_base_and_needle when candidate is a directory (lines 166-168)."""
    base_dir, needle = _resolve_base_and_needle(temp_dir)
    assert base_dir == temp_dir
    assert needle == ""


def test_resolve_base_and_needle_file(temp_dir: Path) -> None:
    """Test _resolve_base_and_needle when candidate is a file (lines 169-173)."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("content")

    base_dir, needle = _resolve_base_and_needle(test_file)
    assert base_dir == temp_dir
    assert needle == "test.txt"


def test_resolve_base_and_needle_root_parent() -> None:
    """Test _resolve_base_and_needle handles root parent (line 171)."""
    path = Path("/file")
    base_dir, needle = _resolve_base_and_needle(path)
    assert base_dir == Path("/")
    assert needle == "file"


def test_resolve_base_and_needle_handles_oserror(temp_dir: Path) -> None:
    """Test _resolve_base_and_needle handles OSError (lines 174-177)."""
    # Create a path that will raise OSError when checked
    with patch("pathlib.Path.is_dir", side_effect=OSError("Permission denied")):
        with pytest.raises(HTTPException) as exc_info:
            _resolve_base_and_needle(Path("/nonexistent"))
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400


# ==================== _list_children_filtered Tests ====================


def test_list_children_filtered_root(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _list_children_filtered filters at root (lines 184-192)."""
    root_dir = Path("/")

    # Mock _list_subdirectories to return some directories
    mock_dirs = [
        Path("/bin"),
        Path("/home"),
        Path("/usr"),
        Path("/media"),
    ]

    with patch(
        "fundamental.api.routes.fs._list_subdirectories", return_value=mock_dirs
    ):
        result = _list_children_filtered(root_dir)
        # Should exclude /bin and /usr, keep /home and /media
        assert len(result) == 2
        assert any(p.name == "home" for p in result)
        assert any(p.name == "media" for p in result)


def test_list_children_filtered_non_root(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _list_children_filtered does not filter at non-root (lines 184-193)."""
    (temp_dir / "dir1").mkdir()
    (temp_dir / "dir2").mkdir()

    # Patch _is_under_excluded to return False for temp directories
    with patch("fundamental.api.routes.fs._is_under_excluded", return_value=False):
        result = _list_children_filtered(temp_dir)
        assert len(result) == 2


def test_list_children_filtered_root_excludes_exact_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _list_children_filtered excludes exact matches at root (lines 188-190)."""
    root_dir = Path("/")
    mock_dirs = [Path("/bin"), Path("/usr")]

    with patch(
        "fundamental.api.routes.fs._list_subdirectories", return_value=mock_dirs
    ):
        result = _list_children_filtered(root_dir)
        assert len(result) == 0


def test_list_children_filtered_root_excludes_prefixes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _list_children_filtered excludes subdirectories of excluded prefixes (line 189)."""
    root_dir = Path("/")
    mock_dirs = [Path("/usr/local"), Path("/bin/bash")]

    with patch(
        "fundamental.api.routes.fs._list_subdirectories", return_value=mock_dirs
    ):
        result = _list_children_filtered(root_dir)
        assert len(result) == 0


# ==================== _build_suggestions Tests ====================


def test_build_suggestions_with_needle(temp_dir: Path) -> None:
    """Test _build_suggestions filters by needle prefix (lines 199-204)."""
    children = [
        temp_dir / "alpha",
        temp_dir / "beta",
        temp_dir / "alphabet",
    ]

    result = _build_suggestions(children, "alp", limit=10)
    assert len(result) == 2
    assert any("alpha" in s for s in result)
    assert any("alphabet" in s for s in result)


def test_build_suggestions_without_needle(temp_dir: Path) -> None:
    """Test _build_suggestions returns all when no needle (lines 205-209)."""
    children = [
        temp_dir / "dir1",
        temp_dir / "dir2",
        temp_dir / "dir3",
    ]

    result = _build_suggestions(children, "", limit=10)
    assert len(result) == 3


def test_build_suggestions_respects_limit(temp_dir: Path) -> None:
    """Test _build_suggestions respects limit parameter (lines 203, 208)."""
    children = [temp_dir / f"dir{i}" for i in range(10)]

    result = _build_suggestions(children, "", limit=5)
    assert len(result) == 5


def test_build_suggestions_sorts_results(temp_dir: Path) -> None:
    """Test _build_suggestions sorts results alphabetically (line 210)."""
    children = [
        temp_dir / "zebra",
        temp_dir / "alpha",
        temp_dir / "beta",
    ]

    result = _build_suggestions(children, "", limit=10)
    assert len(result) == 3
    # Check that results are sorted
    paths = [Path(s).name for s in result]
    assert paths == sorted(paths)


def test_build_suggestions_needle_no_matches(temp_dir: Path) -> None:
    """Test _build_suggestions returns empty when no matches (lines 199-204)."""
    children = [temp_dir / "alpha", temp_dir / "beta"]

    result = _build_suggestions(children, "xyz", limit=10)
    assert len(result) == 0


def test_build_suggestions_needle_respects_limit_break(
    temp_dir: Path,
) -> None:
    """Test _build_suggestions breaks when limit reached with needle (line 204)."""
    children = [temp_dir / f"alpha{i}" for i in range(10)]

    result = _build_suggestions(children, "alpha", limit=3)
    assert len(result) == 3
    # Should stop after finding 3 matches, not continue
    assert all("alpha" in s for s in result)


# ==================== suggest_dirs Endpoint Tests ====================


def test_suggest_dirs_empty_query(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test suggest_dirs with empty query returns root suggestions (lines 248-264)."""
    mock_dirs = [Path("/home"), Path("/media")]

    with patch(
        "fundamental.api.routes.fs._list_children_filtered", return_value=mock_dirs
    ):
        result = suggest_dirs(q="", limit=50)
        assert "suggestions" in result
        assert isinstance(result["suggestions"], list)


def test_suggest_dirs_with_query(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test suggest_dirs with query parameter (lines 248-264)."""
    test_dir = temp_dir / "books"
    test_dir.mkdir()

    with patch(
        "fundamental.api.routes.fs._list_children_filtered", return_value=[test_dir]
    ):
        result = suggest_dirs(q=str(temp_dir), limit=50)
        assert "suggestions" in result
        assert isinstance(result["suggestions"], list)


def test_suggest_dirs_excluded_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test suggest_dirs returns empty when candidate is excluded (lines 252-254)."""
    with patch("fundamental.api.routes.fs._is_under_excluded", return_value=True):
        result = suggest_dirs(q="/bin", limit=50)
        assert result["suggestions"] == []


def test_suggest_dirs_excluded_base_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test suggest_dirs returns empty when base_dir is excluded (lines 257-259)."""
    with (
        patch(
            "fundamental.api.routes.fs._is_under_excluded",
            side_effect=lambda p: p.name == "bin",
        ),
        patch(
            "fundamental.api.routes.fs._resolve_base_and_needle",
            return_value=(Path("/bin"), ""),
        ),
    ):
        result = suggest_dirs(q="/bin/subdir", limit=50)
        assert result["suggestions"] == []


def test_suggest_dirs_respects_limit(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test suggest_dirs respects limit parameter."""
    mock_dirs = [temp_dir / f"dir{i}" for i in range(20)]

    with patch(
        "fundamental.api.routes.fs._list_children_filtered", return_value=mock_dirs
    ):
        result = suggest_dirs(q=str(temp_dir), limit=5)
        assert len(result["suggestions"]) <= 5


def test_suggest_dirs_with_tilde(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test suggest_dirs expands tilde in query (lines 248-264)."""
    expanded = str(Path("~/books").expanduser())
    mock_dir = Path(expanded)

    with (
        patch("fundamental.api.routes.fs._is_under_excluded", return_value=False),
        patch(
            "fundamental.api.routes.fs._resolve_base_and_needle",
            return_value=(mock_dir.parent, "books"),
        ),
        patch(
            "fundamental.api.routes.fs._list_children_filtered", return_value=[mock_dir]
        ),
    ):
        result = suggest_dirs(q="~/books", limit=50)
        assert "suggestions" in result


def test_suggest_dirs_with_relative_path(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test suggest_dirs handles relative paths (lines 248-264)."""
    test_dir = temp_dir / "books"
    test_dir.mkdir()

    with (
        patch("fundamental.api.routes.fs._is_under_excluded", return_value=False),
        patch(
            "fundamental.api.routes.fs._resolve_base_and_needle",
            return_value=(temp_dir, "books"),
        ),
        patch(
            "fundamental.api.routes.fs._list_children_filtered", return_value=[test_dir]
        ),
    ):
        result = suggest_dirs(q="books", limit=50)
        assert "suggestions" in result


def test_suggest_dirs_handles_oserror(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test suggest_dirs handles OSError from _resolve_base_and_needle."""
    with (
        patch("fundamental.api.routes.fs._is_under_excluded", return_value=False),
        patch(
            "fundamental.api.routes.fs._resolve_base_and_needle",
            side_effect=HTTPException(status_code=400, detail="Permission denied"),
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            suggest_dirs(q="/invalid/path", limit=50)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400

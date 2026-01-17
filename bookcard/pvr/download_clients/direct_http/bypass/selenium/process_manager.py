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

"""Process management for cleaning up orphan browser processes."""

import logging
import os
import shutil
import subprocess  # noqa: S404
import time
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)


class ProcessManager(Protocol):
    """Protocol for process management."""

    def cleanup_orphans(self) -> int:
        """Clean up orphan processes.

        Returns
        -------
        int
            Number of processes killed.
        """
        ...

    def force_kill_chrome(self) -> None:
        """Force kill Chrome/chromedriver processes."""
        ...


class DockerProcessManager:
    """Process manager for Docker environments."""

    def __init__(self) -> None:
        """Initialize process manager."""
        self._processes_to_kill = ["chrome", "chromedriver", "Xvfb", "ffmpeg"]

    def _is_docker_environment(self) -> bool:
        """Check if running in Docker environment.

        Returns
        -------
        bool
            True if in Docker environment.
        """
        return Path("/.dockerenv").exists() or os.environ.get("DOCKERMODE") == "true"

    def cleanup_orphans(self) -> int:
        """Kill orphan Chrome/Xvfb processes. Only runs in Docker mode.

        Returns
        -------
        int
            Number of processes killed.
        """
        if not self._is_docker_environment():
            return 0

        total_killed = 0

        # Resolve absolute paths for security (S607)
        pgrep_path = shutil.which("pgrep")
        pkill_path = shutil.which("pkill")
        if not pgrep_path or not pkill_path:
            logger.warning("pgrep or pkill not found in PATH")
            return 0

        logger.debug("Checking for orphan processes...")

        for proc_name in self._processes_to_kill:
            try:
                # S603: proc_name is from hardcoded list, pgrep_path is from shutil.which()
                result = subprocess.run(  # noqa: S603
                    [pgrep_path, "-f", proc_name],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if result.returncode != 0 or not result.stdout.strip():
                    continue

                pids = result.stdout.strip().split("\n")
                count = len(pids)
                logger.info(
                    "Found %d orphan %s process(es), killing...", count, proc_name
                )

                # S603: proc_name is from hardcoded list, pkill_path is from shutil.which()
                kill_result = subprocess.run(  # noqa: S603
                    [pkill_path, "-9", "-f", proc_name],
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
                if kill_result.returncode == 0:
                    total_killed += count
                else:
                    logger.warning(
                        "pkill for %s returned %d", proc_name, kill_result.returncode
                    )

            except subprocess.TimeoutExpired:
                logger.warning("Timeout while checking for %s processes", proc_name)
            except (OSError, ValueError, subprocess.SubprocessError) as e:
                logger.debug("Error checking for %s processes: %s", proc_name, e)

        if total_killed > 0:
            time.sleep(1)
            logger.info("Cleaned up %d orphan process(es)", total_killed)
        else:
            logger.debug("No orphan processes found")

        return total_killed

    def force_kill_chrome(self) -> None:
        """Force-kill any lingering Chrome/chromedriver processes in Docker.

        Only runs in Docker environments.
        """
        if not self._is_docker_environment():
            return

        time.sleep(0.3)
        try:
            pkill_path = shutil.which("pkill")
            if pkill_path:
                # S603: "chrom" is hardcoded, pkill_path is from shutil.which()
                subprocess.run(  # noqa: S603
                    [pkill_path, "-9", "-f", "chrom"],
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
        except (OSError, subprocess.SubprocessError) as e:
            logger.debug("pkill chrome: %s", e)

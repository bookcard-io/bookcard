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

"""Command executor for executing commands with automatic undo on failure."""

from contextlib import suppress

from bookcard.repositories.delete_commands import DeleteCommand


class CommandExecutor:
    """Executes commands with automatic undo on failure.

    Follows Command pattern executor with compensating transaction support.
    If any command fails, all previously executed commands are undone.
    """

    def __init__(self) -> None:
        self._executed_commands: list[DeleteCommand] = []

    def execute(self, command: DeleteCommand) -> None:
        """Execute a command and track it for potential undo.

        Parameters
        ----------
        command : DeleteCommand
            Command to execute.

        Raises
        ------
        Exception
            If command execution fails. All previous commands are undone.
        """
        try:
            command.execute()
            self._executed_commands.append(command)
        except Exception:
            # Undo all previously executed commands in reverse order
            self._undo_all()
            raise

    def _undo_all(self) -> None:
        """Undo all executed commands in reverse order."""
        for command in reversed(self._executed_commands):
            with suppress(Exception):
                command.undo()
        self._executed_commands.clear()

    def clear(self) -> None:
        """Clear executed commands (after successful completion)."""
        self._executed_commands.clear()

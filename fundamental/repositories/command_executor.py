# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


"""Command executor for executing commands with automatic undo on failure."""

from contextlib import suppress

from fundamental.repositories.delete_commands import DeleteCommand


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

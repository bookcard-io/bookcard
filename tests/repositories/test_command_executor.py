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

"""Tests for command executor."""

from __future__ import annotations

import pytest

from bookcard.repositories.command_executor import CommandExecutor
from bookcard.repositories.delete_commands import DeleteCommand


class MockDeleteCommand(DeleteCommand):
    """Mock delete command for testing."""

    def __init__(
        self,
        execute_raises: Exception | None = None,
        undo_raises: Exception | None = None,
    ) -> None:
        """Initialize mock command.

        Parameters
        ----------
        execute_raises : Exception | None
            Exception to raise during execute, if any.
        undo_raises : Exception | None
            Exception to raise during undo, if any.
        """
        self._execute_raises = execute_raises
        self._undo_raises = undo_raises
        self._executed = False
        self._undone = False

    def execute(self) -> None:
        """Execute the command."""
        self._executed = True
        if self._execute_raises:
            raise self._execute_raises

    def undo(self) -> None:
        """Undo the command."""
        self._undone = True
        if self._undo_raises:
            raise self._undo_raises


@pytest.fixture
def executor() -> CommandExecutor:
    """Create a CommandExecutor instance."""
    return CommandExecutor()


def test_init_creates_empty_executed_commands(executor: CommandExecutor) -> None:
    """Test __init__ creates empty executed commands list."""
    assert executor._executed_commands == []


def test_execute_success_adds_command(executor: CommandExecutor) -> None:
    """Test execute successfully adds command to executed list."""
    command = MockDeleteCommand()
    executor.execute(command)
    assert command._executed is True
    assert len(executor._executed_commands) == 1
    assert executor._executed_commands[0] is command


def test_execute_failure_undoes_previous_commands(executor: CommandExecutor) -> None:
    """Test execute failure undoes all previous commands."""
    command1 = MockDeleteCommand()
    command2 = MockDeleteCommand()
    failing_command = MockDeleteCommand(execute_raises=ValueError("test error"))

    executor.execute(command1)
    executor.execute(command2)
    assert len(executor._executed_commands) == 2

    with pytest.raises(ValueError, match="test error"):
        executor.execute(failing_command)

    # Both previous commands should be undone
    assert command1._undone is True
    assert command2._undone is True
    # Executed commands list should be cleared
    assert len(executor._executed_commands) == 0


def test_execute_failure_undo_suppresses_exceptions(executor: CommandExecutor) -> None:
    """Test execute failure suppresses exceptions during undo."""
    command1 = MockDeleteCommand(undo_raises=RuntimeError("undo error"))
    failing_command = MockDeleteCommand(execute_raises=ValueError("execute error"))

    executor.execute(command1)
    # Should raise the execute error, not the undo error
    with pytest.raises(ValueError, match="execute error"):
        executor.execute(failing_command)
    # Undo should have been called despite raising
    assert command1._undone is True


def test_undo_all_reverses_order(executor: CommandExecutor) -> None:
    """Test _undo_all undoes commands in reverse order."""
    undo_order: list[int] = []

    class OrderTrackingCommand(DeleteCommand):
        def __init__(self, order_id: int) -> None:
            self._order_id = order_id

        def execute(self) -> None:
            pass

        def undo(self) -> None:
            undo_order.append(self._order_id)

    command1 = OrderTrackingCommand(1)
    command2 = OrderTrackingCommand(2)
    command3 = OrderTrackingCommand(3)

    executor.execute(command1)
    executor.execute(command2)
    executor.execute(command3)

    executor._undo_all()

    assert undo_order == [3, 2, 1]
    assert len(executor._executed_commands) == 0


def test_undo_all_clears_executed_commands(executor: CommandExecutor) -> None:
    """Test _undo_all clears executed commands list."""
    command1 = MockDeleteCommand()
    command2 = MockDeleteCommand()

    executor.execute(command1)
    executor.execute(command2)
    assert len(executor._executed_commands) == 2

    executor._undo_all()
    assert len(executor._executed_commands) == 0


def test_clear_clears_executed_commands(executor: CommandExecutor) -> None:
    """Test clear removes all executed commands."""
    command1 = MockDeleteCommand()
    command2 = MockDeleteCommand()

    executor.execute(command1)
    executor.execute(command2)
    assert len(executor._executed_commands) == 2

    executor.clear()
    assert len(executor._executed_commands) == 0

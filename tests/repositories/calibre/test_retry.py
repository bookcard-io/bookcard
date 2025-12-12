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

"""Tests for retry module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError
from sqlmodel import Session

from fundamental.repositories.calibre.retry import SQLiteRetryPolicy


def _create_operational_error(msg: str) -> OperationalError:
    """Create an OperationalError for testing."""
    return OperationalError(msg, None, Exception(msg))


class TestSQLiteRetryPolicy:
    """Test suite for SQLiteRetryPolicy."""

    def test_is_lock_error_database_locked(self) -> None:
        """Test is_lock_error detects 'database is locked'."""
        policy = SQLiteRetryPolicy()
        error = _create_operational_error("database is locked")
        assert policy.is_lock_error(error) is True

    def test_is_lock_error_database_busy(self) -> None:
        """Test is_lock_error detects 'database is busy'."""
        policy = SQLiteRetryPolicy()
        error = _create_operational_error("database is busy")
        assert policy.is_lock_error(error) is True

    def test_is_lock_error_case_insensitive(self) -> None:
        """Test is_lock_error is case insensitive."""
        policy = SQLiteRetryPolicy()
        error = _create_operational_error("DATABASE IS LOCKED")
        assert policy.is_lock_error(error) is True

    def test_is_lock_error_other_error(self) -> None:
        """Test is_lock_error returns False for other errors."""
        policy = SQLiteRetryPolicy()
        error = _create_operational_error("syntax error")
        assert policy.is_lock_error(error) is False

    @patch("time.sleep")
    def test_sleep_with_backoff(self, mock_sleep: MagicMock) -> None:
        """Test sleep_with_backoff uses exponential backoff."""
        policy = SQLiteRetryPolicy()
        policy.sleep_with_backoff(1)
        mock_sleep.assert_called_once()
        # Check that delay is reasonable (0.1 * 2^0 + jitter)
        call_args = mock_sleep.call_args[0][0]
        assert 0.1 <= call_args <= 0.15

    @patch("time.sleep")
    def test_sleep_with_backoff_multiple_attempts(self, mock_sleep: MagicMock) -> None:
        """Test sleep_with_backoff increases delay with attempts."""
        policy = SQLiteRetryPolicy()
        delays = []
        for attempt in [1, 2, 3]:
            policy.sleep_with_backoff(attempt)
            delays.append(mock_sleep.call_args[0][0])
            mock_sleep.reset_mock()

        # Each attempt should have longer delay
        assert delays[0] < delays[1] < delays[2]

    def test_run_read_succeeds_on_first_attempt(self) -> None:
        """Test run_read succeeds without retries."""
        policy = SQLiteRetryPolicy(max_retries=3)
        session = MagicMock(spec=Session)
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None

        operation = MagicMock(return_value="result")
        result = policy.run_read(session_factory, operation, operation_name="test")
        assert result == "result"
        operation.assert_called_once_with(session)

    @patch("time.sleep")
    def test_run_read_retries_on_lock_error(self, mock_sleep: MagicMock) -> None:
        """Test run_read retries on lock error."""
        policy = SQLiteRetryPolicy(max_retries=3)
        session = MagicMock(spec=Session)
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None

        lock_error = OperationalError(
            "database is locked", None, Exception("database is locked")
        )
        operation = MagicMock(side_effect=[lock_error, lock_error, "result"])

        result = policy.run_read(session_factory, operation, operation_name="test")
        assert result == "result"
        assert operation.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between retries

    @patch("time.sleep")
    def test_run_read_exhausts_retries(self, mock_sleep: MagicMock) -> None:
        """Test run_read raises after exhausting retries."""
        policy = SQLiteRetryPolicy(max_retries=2)
        session = MagicMock(spec=Session)
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None

        lock_error = OperationalError(
            "database is locked", None, Exception("database is locked")
        )
        operation = MagicMock(side_effect=lock_error)

        with pytest.raises(OperationalError):
            policy.run_read(session_factory, operation, operation_name="test")
        assert operation.call_count == 2
        assert mock_sleep.call_count == 1

    def test_run_read_raises_non_lock_error(self) -> None:
        """Test run_read raises non-lock errors immediately."""
        policy = SQLiteRetryPolicy(max_retries=3)
        session = MagicMock(spec=Session)
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None

        other_error = OperationalError("syntax error", None, Exception("syntax error"))
        operation = MagicMock(side_effect=other_error)

        with pytest.raises(OperationalError):
            policy.run_read(session_factory, operation, operation_name="test")
        operation.assert_called_once()

    def test_commit_succeeds_on_first_attempt(self) -> None:
        """Test commit succeeds without retries."""
        policy = SQLiteRetryPolicy(max_retries=3)
        session = MagicMock(spec=Session)
        policy.commit(session)
        assert session.commit.call_count == 1

    @patch("time.sleep")
    def test_commit_retries_on_lock_error(self, mock_sleep: MagicMock) -> None:
        """Test commit retries on lock error."""
        policy = SQLiteRetryPolicy(max_retries=3)
        session = MagicMock(spec=Session)
        lock_error = OperationalError(
            "database is locked", None, Exception("database is locked")
        )
        session.commit.side_effect = [lock_error, lock_error, None]

        policy.commit(session)
        assert session.commit.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("time.sleep")
    def test_commit_exhausts_retries(self, mock_sleep: MagicMock) -> None:
        """Test commit raises after exhausting retries."""
        policy = SQLiteRetryPolicy(max_retries=2)
        session = MagicMock(spec=Session)
        lock_error = OperationalError(
            "database is locked", None, Exception("database is locked")
        )
        session.commit.side_effect = lock_error

        with pytest.raises(OperationalError):
            policy.commit(session)
        assert session.commit.call_count == 2
        assert mock_sleep.call_count == 1

    def test_commit_raises_non_lock_error(self) -> None:
        """Test commit raises non-lock errors immediately."""
        policy = SQLiteRetryPolicy(max_retries=3)
        session = MagicMock(spec=Session)
        other_error = OperationalError("syntax error", None, Exception("syntax error"))
        session.commit.side_effect = other_error

        with pytest.raises(OperationalError):
            policy.commit(session)
        assert session.commit.call_count == 1

    def test_flush_succeeds_on_first_attempt(self) -> None:
        """Test flush succeeds without retries."""
        policy = SQLiteRetryPolicy(max_retries=3)
        session = MagicMock(spec=Session)
        policy.flush(session)
        assert session.flush.call_count == 1

    @patch("time.sleep")
    def test_flush_retries_on_lock_error(self, mock_sleep: MagicMock) -> None:
        """Test flush retries on lock error."""
        policy = SQLiteRetryPolicy(max_retries=3)
        session = MagicMock(spec=Session)
        lock_error = OperationalError(
            "database is locked", None, Exception("database is locked")
        )
        session.flush.side_effect = [lock_error, lock_error, None]

        policy.flush(session)
        assert session.flush.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("time.sleep")
    def test_flush_exhausts_retries(self, mock_sleep: MagicMock) -> None:
        """Test flush raises after exhausting retries."""
        policy = SQLiteRetryPolicy(max_retries=2)
        session = MagicMock(spec=Session)
        lock_error = OperationalError(
            "database is locked", None, Exception("database is locked")
        )
        session.flush.side_effect = lock_error

        with pytest.raises(OperationalError):
            policy.flush(session)
        assert session.flush.call_count == 2
        assert mock_sleep.call_count == 1

    def test_flush_raises_non_lock_error(self) -> None:
        """Test flush raises non-lock errors immediately."""
        policy = SQLiteRetryPolicy(max_retries=3)
        session = MagicMock(spec=Session)
        other_error = OperationalError("syntax error", None, Exception("syntax error"))
        session.flush.side_effect = other_error

        with pytest.raises(OperationalError):
            policy.flush(session)
        assert session.flush.call_count == 1

    def test_run_read_with_custom_max_retries(self) -> None:
        """Test run_read respects custom max_retries parameter."""
        policy = SQLiteRetryPolicy(max_retries=3)
        session = MagicMock(spec=Session)
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None

        operation = MagicMock(return_value="result")
        result = policy.run_read(
            session_factory, operation, operation_name="test", max_retries=5
        )
        assert result == "result"
        operation.assert_called_once()

    @pytest.mark.parametrize(
        ("error_msg", "is_lock"),
        [
            ("database is locked", True),
            ("database is busy", True),
            ("DATABASE IS LOCKED", True),
            ("DATABASE IS BUSY", True),
            ("syntax error", False),
            ("table not found", False),
            ("", False),
        ],
    )
    def test_is_lock_error_parametrized(self, error_msg: str, is_lock: bool) -> None:
        """Test is_lock_error with various error messages (parametrized)."""
        policy = SQLiteRetryPolicy()
        error = _create_operational_error(error_msg)
        assert policy.is_lock_error(error) == is_lock

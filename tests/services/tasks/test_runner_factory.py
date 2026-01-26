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

"""Tests for runner factory."""

from __future__ import annotations

from unittest.mock import ANY, MagicMock, patch

import pytest

from bookcard.config import AppConfig
from bookcard.services.tasks.runner_factory import create_task_runner


@pytest.fixture
def mock_engine() -> MagicMock:
    """Return mock SQLAlchemy engine."""
    return MagicMock()


@pytest.fixture
def mock_task_factory() -> MagicMock:
    """Return mock task factory function."""
    return MagicMock()


@pytest.mark.parametrize(
    ("runner_type", "expected_class_name"),
    [
        ("thread", "ThreadTaskRunner"),
        ("dramatiq", "DramatiqTaskRunner"),
        ("celery", "CeleryTaskRunner"),
    ],
)
def test_create_task_runner_valid_types(
    mock_engine: MagicMock,
    runner_type: str,
    expected_class_name: str,
) -> None:
    """Test create_task_runner with valid runner types."""
    config = AppConfig(
        jwt_secret="secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=30,
        encryption_key="key",
        task_runner=runner_type,
    )

    with (
        patch("bookcard.services.tasks.runner_factory.ThreadTaskRunner") as mock_thread,
        patch(
            "bookcard.services.tasks.runner_factory.DramatiqTaskRunner"
        ) as mock_dramatiq,
        patch("bookcard.services.tasks.runner_factory.CeleryTaskRunner") as mock_celery,
        patch(
            "bookcard.services.tasks.runner_factory.RedisBroker"
        ) as mock_redis_broker,
        patch("bookcard.services.tasks.runner_factory.create_task") as mock_create_task,
    ):
        mock_redis_broker.return_value = MagicMock()
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        mock_dramatiq_instance = MagicMock()
        mock_dramatiq.return_value = mock_dramatiq_instance
        mock_celery_instance = MagicMock()
        mock_celery.return_value = mock_celery_instance

        result = create_task_runner(mock_engine, config)

        if runner_type == "thread":
            mock_thread.assert_called_once_with(mock_engine, mock_create_task, ANY)
            assert result == mock_thread_instance
        elif runner_type == "dramatiq":
            mock_dramatiq.assert_called_once()
            assert result == mock_dramatiq_instance
        elif runner_type == "celery":
            mock_celery.assert_called_once()
            assert result == mock_celery_instance


def test_create_task_runner_invalid_type(mock_engine: MagicMock) -> None:
    """Test create_task_runner raises ValueError for invalid type."""
    config = AppConfig(
        jwt_secret="secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=30,
        encryption_key="key",
        task_runner="invalid",
    )

    with pytest.raises(ValueError, match="Unknown task runner type"):
        create_task_runner(mock_engine, config)


def test_create_task_runner_default_thread(mock_engine: MagicMock) -> None:
    """Test create_task_runner defaults to thread runner."""
    config = AppConfig(
        jwt_secret="secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=30,
        encryption_key="key",
        task_runner="thread",
    )

    with (
        patch("bookcard.services.tasks.runner_factory.ThreadTaskRunner") as mock_thread,
        patch(
            "bookcard.services.tasks.runner_factory.RedisBroker"
        ) as mock_redis_broker,
        patch("bookcard.services.tasks.runner_factory.create_task") as mock_create_task,
    ):
        mock_redis_broker.return_value = MagicMock()
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        result = create_task_runner(mock_engine, config)

        mock_thread.assert_called_once_with(mock_engine, mock_create_task, ANY)
        assert result == mock_thread_instance

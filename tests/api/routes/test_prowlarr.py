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

"""Tests for prowlarr routes."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from cryptography.fernet import Fernet

import bookcard.api.routes.prowlarr as prowlarr
from bookcard.api.schemas.prowlarr import ProwlarrConfigUpdate
from bookcard.models.pvr import ProwlarrConfig
from bookcard.services.security import DataEncryptor

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def valid_fernet_key() -> str:
    """Generate a valid Fernet key."""
    return Fernet.generate_key().decode()


class TestGetProwlarrConfig:
    """Test get_prowlarr_config endpoint."""

    def test_get_prowlarr_config_decrypts_key(
        self, session: DummySession, valid_fernet_key: str
    ) -> None:
        """Test get_prowlarr_config decrypts the API key."""
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key
        encryptor = DataEncryptor(valid_fernet_key)

        # Setup existing encrypted config
        raw_key = "my-secret-key"
        encrypted_key = encryptor.encrypt(raw_key)
        config = ProwlarrConfig(id=1, api_key=encrypted_key, url="http://test")

        # Mock the database return
        session.set_exec_result([config])

        # Mock request state for get_data_encryptor
        request.app.state.config.encryption_key = valid_fernet_key

        result = prowlarr.get_prowlarr_config(session=session, request=request)

        assert result.api_key == raw_key


class TestUpdateProwlarrConfig:
    """Test update_prowlarr_config endpoint."""

    def test_update_prowlarr_config_encrypts_key(
        self, session: DummySession, valid_fernet_key: str
    ) -> None:
        """Test update_prowlarr_config encrypts the API key."""
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        # Setup existing config
        config = ProwlarrConfig(id=1, url="http://test")
        session.set_exec_result([config])

        update_data = ProwlarrConfigUpdate(api_key="new-secret-key")

        result = prowlarr.update_prowlarr_config(
            data=update_data, session=session, request=request
        )

        # The result object is the modified config object
        # Since we modified it in place, let's check what happened.
        # The function encrypts the key: config.api_key = encryptor.encrypt(data.api_key)
        # And returns it.

        assert result.api_key != "new-secret-key"

        # Verify decryption
        encryptor = DataEncryptor(valid_fernet_key)
        decrypted = encryptor.decrypt(result.api_key)
        assert decrypted == "new-secret-key"

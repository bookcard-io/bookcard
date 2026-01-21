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

"""DTOs for email server configuration updates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bookcard.models.config import EmailServerType


@dataclass(frozen=True, slots=True)
class EmailServerConfigUpdate:
    """Email server configuration update request.

    This is a service-layer DTO (not an API schema). It is intentionally permissive:
    fields are optional and only non-``None`` values are applied to the persisted config.

    Attributes
    ----------
    server_type : EmailServerType
        The email server type.
    smtp_host : str | None
        SMTP host.
    smtp_port : int | None
        SMTP port.
    smtp_username : str | None
        SMTP username. Empty string indicates clearing the username.
    smtp_password : str | None
        SMTP password. Empty string indicates clearing the password.
    smtp_use_tls : bool | None
        Whether to use TLS.
    smtp_use_ssl : bool | None
        Whether to use SSL.
    smtp_from_email : str | None
        Sender email.
    smtp_from_name : str | None
        Sender display name.
    max_email_size_mb : int | None
        Maximum email size.
    gmail_token : dict[str, object] | None
        Gmail OAuth token JSON.
    enabled : bool | None
        Enable/disable email sending.
    """

    server_type: EmailServerType

    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool | None = None
    smtp_use_ssl: bool | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str | None = None

    max_email_size_mb: int | None = None
    gmail_token: dict[str, object] | None = None
    enabled: bool | None = None

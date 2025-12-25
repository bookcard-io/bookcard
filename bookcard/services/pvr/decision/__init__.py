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

"""Download decision engine for evaluating releases.

Similar to Sonarr's decision engine, provides services for evaluating
releases against user preferences and making download decisions.
"""

from bookcard.models.pvr import DownloadRejectionReason, RejectionType
from bookcard.services.pvr.decision.models import (
    DownloadDecision,
    DownloadRejection,
)
from bookcard.services.pvr.decision.preferences import DownloadDecisionPreferences
from bookcard.services.pvr.decision.service import DownloadDecisionService

__all__ = [
    "DownloadDecision",
    "DownloadDecisionPreferences",
    "DownloadDecisionService",
    "DownloadRejection",
    "DownloadRejectionReason",
    "RejectionType",
]

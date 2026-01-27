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

"""Models for download decision evaluation.

Provides data structures for evaluating releases and making download decisions,
similar to Sonarr's decision engine.
"""

from dataclasses import dataclass, field

from bookcard.models.pvr import DownloadRejectionReason, RejectionType
from bookcard.pvr.models import ReleaseInfo


@dataclass
class DownloadRejection:
    """Rejection information for a download decision.

    Attributes
    ----------
    reason : DownloadRejectionReason
        Reason for rejection.
    message : str
        Human-readable rejection message.
    type : RejectionType
        Type of rejection (permanent or temporary).
    """

    reason: DownloadRejectionReason
    message: str
    type: RejectionType = RejectionType.PERMANENT


@dataclass
class DownloadDecision:
    """Decision result for evaluating a release.

    Attributes
    ----------
    release : ReleaseInfo
        The release being evaluated.
    approved : bool
        Whether the release is approved for download.
    rejections : list[DownloadRejection]
        List of rejection reasons if not approved.
    score : float
        Quality/relevance score (0.0-1.0, higher is better).
    """

    release: ReleaseInfo
    approved: bool = True
    rejections: list[DownloadRejection] = field(default_factory=list)
    score: float = 0.0

    @property
    def temporarily_rejected(self) -> bool:
        """Check if release is temporarily rejected.

        Returns
        -------
        bool
            True if rejected but only with temporary rejections.
        """
        return (
            not self.approved
            and bool(self.rejections)
            and all(r.type == RejectionType.TEMPORARY for r in self.rejections)
        )

    @property
    def permanently_rejected(self) -> bool:
        """Check if release is permanently rejected.

        Returns
        -------
        bool
            True if rejected with at least one permanent rejection.
        """
        return (
            not self.approved
            and bool(self.rejections)
            and any(r.type == RejectionType.PERMANENT for r in self.rejections)
        )

    def add_rejection(
        self,
        reason: DownloadRejectionReason,
        message: str,
        rejection_type: RejectionType = RejectionType.PERMANENT,
    ) -> None:
        """Add a rejection to this decision.

        Parameters
        ----------
        reason : DownloadRejectionReason
            Rejection reason.
        message : str
            Rejection message.
        rejection_type : RejectionType
            Type of rejection.
        """
        self.rejections.append(
            DownloadRejection(reason=reason, message=message, type=rejection_type)
        )
        self.approved = False

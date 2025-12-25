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

"""Tests for download decision models."""

import pytest

from bookcard.models.pvr import DownloadRejectionReason, RejectionType
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.decision.models import (
    DownloadDecision,
    DownloadRejection,
)


class TestDownloadRejection:
    """Test DownloadRejection dataclass."""

    def test_create_permanent_rejection(self) -> None:
        """Test creating a permanent rejection.

        Verifies that a permanent rejection is created correctly.
        """
        rejection = DownloadRejection(
            reason=DownloadRejectionReason.WRONG_FORMAT,
            message="Format not supported",
            type=RejectionType.PERMANENT,
        )

        assert rejection.reason == DownloadRejectionReason.WRONG_FORMAT
        assert rejection.message == "Format not supported"
        assert rejection.type == RejectionType.PERMANENT

    def test_create_temporary_rejection(self) -> None:
        """Test creating a temporary rejection.

        Verifies that a temporary rejection is created correctly.
        """
        rejection = DownloadRejection(
            reason=DownloadRejectionReason.INSUFFICIENT_SEEDERS,
            message="Too few seeders",
            type=RejectionType.TEMPORARY,
        )

        assert rejection.reason == DownloadRejectionReason.INSUFFICIENT_SEEDERS
        assert rejection.message == "Too few seeders"
        assert rejection.type == RejectionType.TEMPORARY

    def test_default_rejection_type(self) -> None:
        """Test default rejection type is permanent.

        Verifies that if type is not specified, it defaults to permanent.
        """
        rejection = DownloadRejection(
            reason=DownloadRejectionReason.WRONG_FORMAT,
            message="Test",
        )

        assert rejection.type == RejectionType.PERMANENT

    @pytest.mark.parametrize(
        ("reason", "expected_type"),
        [
            (DownloadRejectionReason.WRONG_FORMAT, RejectionType.PERMANENT),
            (DownloadRejectionReason.INSUFFICIENT_SEEDERS, RejectionType.TEMPORARY),
            (DownloadRejectionReason.TOO_NEW, RejectionType.TEMPORARY),
            (DownloadRejectionReason.BLOCKLISTED, RejectionType.PERMANENT),
        ],
    )
    def test_rejection_reasons(
        self, reason: DownloadRejectionReason, expected_type: RejectionType
    ) -> None:
        """Test various rejection reasons.

        Parameters
        ----------
        reason : DownloadRejectionReason
            Rejection reason to test.
        expected_type : RejectionType
            Expected rejection type.
        """
        rejection = DownloadRejection(
            reason=reason,
            message="Test message",
            type=expected_type,
        )

        assert rejection.reason == reason
        assert rejection.type == expected_type


class TestDownloadDecision:
    """Test DownloadDecision dataclass."""

    def test_create_approved_decision(self, sample_release: ReleaseInfo) -> None:
        """Test creating an approved decision.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release fixture.
        """
        decision = DownloadDecision(
            release=sample_release,
            approved=True,
            score=0.85,
        )

        assert decision.release == sample_release
        assert decision.approved is True
        assert decision.score == 0.85
        assert len(decision.rejections) == 0
        assert decision.temporarily_rejected is False
        assert decision.permanently_rejected is False

    def test_create_rejected_decision(self, sample_release: ReleaseInfo) -> None:
        """Test creating a rejected decision.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release fixture.
        """
        decision = DownloadDecision(
            release=sample_release,
            approved=False,
            score=0.3,
        )

        assert decision.approved is False
        assert decision.score == 0.3

    def test_add_rejection(self, sample_release: ReleaseInfo) -> None:
        """Test adding a rejection to a decision.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release fixture.
        """
        decision = DownloadDecision(release=sample_release, approved=True)

        decision.add_rejection(
            reason=DownloadRejectionReason.WRONG_FORMAT,
            message="Format not supported",
            rejection_type=RejectionType.PERMANENT,
        )

        assert decision.approved is False
        assert len(decision.rejections) == 1
        assert decision.rejections[0].reason == DownloadRejectionReason.WRONG_FORMAT
        assert decision.rejections[0].message == "Format not supported"
        assert decision.rejections[0].type == RejectionType.PERMANENT

    def test_add_multiple_rejections(self, sample_release: ReleaseInfo) -> None:
        """Test adding multiple rejections to a decision.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release fixture.
        """
        decision = DownloadDecision(release=sample_release, approved=True)

        decision.add_rejection(
            reason=DownloadRejectionReason.WRONG_FORMAT,
            message="Format issue",
        )
        decision.add_rejection(
            reason=DownloadRejectionReason.INSUFFICIENT_SEEDERS,
            message="Seeders issue",
            rejection_type=RejectionType.TEMPORARY,
        )

        assert decision.approved is False
        assert len(decision.rejections) == 2

    def test_temporarily_rejected_property(self, sample_release: ReleaseInfo) -> None:
        """Test temporarily_rejected property.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release fixture.
        """
        decision = DownloadDecision(release=sample_release, approved=True)

        # Only temporary rejections
        decision.add_rejection(
            reason=DownloadRejectionReason.INSUFFICIENT_SEEDERS,
            message="Low seeders",
            rejection_type=RejectionType.TEMPORARY,
        )

        assert decision.temporarily_rejected is True
        assert decision.permanently_rejected is False

    def test_permanently_rejected_property(self, sample_release: ReleaseInfo) -> None:
        """Test permanently_rejected property.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release fixture.
        """
        decision = DownloadDecision(release=sample_release, approved=True)

        # Permanent rejection
        decision.add_rejection(
            reason=DownloadRejectionReason.WRONG_FORMAT,
            message="Wrong format",
            rejection_type=RejectionType.PERMANENT,
        )

        assert decision.temporarily_rejected is False
        assert decision.permanently_rejected is True

    def test_mixed_rejections_property(self, sample_release: ReleaseInfo) -> None:
        """Test mixed temporary and permanent rejections.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release fixture.
        """
        decision = DownloadDecision(release=sample_release, approved=True)

        decision.add_rejection(
            reason=DownloadRejectionReason.INSUFFICIENT_SEEDERS,
            message="Low seeders",
            rejection_type=RejectionType.TEMPORARY,
        )
        decision.add_rejection(
            reason=DownloadRejectionReason.WRONG_FORMAT,
            message="Wrong format",
            rejection_type=RejectionType.PERMANENT,
        )

        # If any permanent rejection exists, it's permanently rejected
        assert decision.temporarily_rejected is False
        assert decision.permanently_rejected is True

    @pytest.mark.parametrize(
        ("score", "expected_valid"),
        [
            (0.0, True),
            (0.5, True),
            (1.0, True),
            (-0.1, True),  # Dataclass doesn't validate range
            (1.1, True),  # Dataclass doesn't validate range
        ],
    )
    def test_score_values(
        self, sample_release: ReleaseInfo, score: float, expected_valid: bool
    ) -> None:
        """Test decision with various score values.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release fixture.
        score : float
            Score value to test.
        expected_valid : bool
            Whether the score is expected to be valid.
        """
        decision = DownloadDecision(release=sample_release, score=score)
        assert decision.score == score

    def test_default_values(self, sample_release: ReleaseInfo) -> None:
        """Test decision default values.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release fixture.
        """
        decision = DownloadDecision(release=sample_release)

        assert decision.approved is True
        assert decision.score == 0.0
        assert len(decision.rejections) == 0

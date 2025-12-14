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

"""Tests for CompositeConversionStrategy to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.kcc_config import KCCConversionProfile
from fundamental.services.conversion.exceptions import ConversionError
from fundamental.services.conversion.strategies.composite import (
    CompositeConversionStrategy,
    is_comic_format,
)


@pytest.fixture
def mock_kcc_strategy() -> MagicMock:
    """Create a mock KCCConversionStrategy.

    Returns
    -------
    MagicMock
        Mock KCC strategy instance.
    """
    return MagicMock(spec=["supports", "convert", "kcc_path", "timeout"])


@pytest.fixture
def mock_calibre_strategy() -> MagicMock:
    """Create a mock CalibreConversionStrategy.

    Returns
    -------
    MagicMock
        Mock Calibre strategy instance.
    """
    return MagicMock(spec=["supports", "convert"])


@pytest.fixture
def composite_strategy(
    mock_kcc_strategy: MagicMock,
    mock_calibre_strategy: MagicMock,
) -> CompositeConversionStrategy:
    """Create CompositeConversionStrategy instance.

    Parameters
    ----------
    mock_kcc_strategy : MagicMock
        Mock KCC strategy.
    mock_calibre_strategy : MagicMock
        Mock Calibre strategy.

    Returns
    -------
    CompositeConversionStrategy
        Composite strategy instance.
    """
    return CompositeConversionStrategy(
        kcc_strategy=mock_kcc_strategy,
        calibre_strategy=mock_calibre_strategy,
    )


@pytest.fixture
def composite_strategy_no_kcc(
    mock_calibre_strategy: MagicMock,
) -> CompositeConversionStrategy:
    """Create CompositeConversionStrategy without KCC.

    Parameters
    ----------
    mock_calibre_strategy : MagicMock
        Mock Calibre strategy.

    Returns
    -------
    CompositeConversionStrategy
        Composite strategy instance without KCC.
    """
    return CompositeConversionStrategy(
        kcc_strategy=None,
        calibre_strategy=mock_calibre_strategy,
    )


@pytest.fixture
def input_path(tmp_path: Path) -> Path:
    """Create a mock input file.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory.

    Returns
    -------
    Path
        Path to input file.
    """
    input_file = tmp_path / "input.cbz"
    input_file.write_text("mock input content")
    return input_file


@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    """Create a mock output file path.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory.

    Returns
    -------
    Path
        Path to output file.
    """
    return tmp_path / "output.epub"


@pytest.fixture
def kcc_profile() -> KCCConversionProfile:
    """Create a KCC conversion profile.

    Returns
    -------
    KCCConversionProfile
        KCC profile instance.
    """
    return KCCConversionProfile(
        id=1,
        user_id=1,
        name="Test Profile",
        device_profile="KV",
        output_format="MOBI",
    )


class TestIsComicFormat:
    """Test is_comic_format function."""

    @pytest.mark.parametrize(
        ("format_name", "expected"),
        [
            ("CBZ", True),
            ("cbz", True),
            ("CBR", True),
            ("cbr", True),
            ("CB7", True),
            ("cb7", True),
            ("PDF", True),
            ("pdf", True),
            ("MOBI", False),
            ("EPUB", False),
            ("AZW3", False),
            ("", False),
        ],
    )
    def test_is_comic_format(
        self,
        format_name: str,
        expected: bool,
    ) -> None:
        """Test is_comic_format with various formats (covers line 56).

        Parameters
        ----------
        format_name : str
            Format name to test.
        expected : bool
            Expected result.
        """
        assert is_comic_format(format_name) == expected


class TestInit:
    """Test __init__ method."""

    def test_init(
        self,
        mock_kcc_strategy: MagicMock,
        mock_calibre_strategy: MagicMock,
    ) -> None:
        """Test initialization (covers lines 74-89).

        Parameters
        ----------
        mock_kcc_strategy : MagicMock
            Mock KCC strategy.
        mock_calibre_strategy : MagicMock
            Mock Calibre strategy.
        """
        strategy = CompositeConversionStrategy(
            kcc_strategy=mock_kcc_strategy,
            calibre_strategy=mock_calibre_strategy,
        )

        assert strategy._kcc_strategy == mock_kcc_strategy
        assert strategy._calibre_strategy == mock_calibre_strategy


class TestSupports:
    """Test supports method."""

    def test_supports_comic_format_with_kcc(
        self,
        composite_strategy: CompositeConversionStrategy,
        mock_kcc_strategy: MagicMock,
    ) -> None:
        """Test supports for comic format when KCC supports it (covers lines 111-116).

        Parameters
        ----------
        composite_strategy : CompositeConversionStrategy
            Composite strategy instance.
        mock_kcc_strategy : MagicMock
            Mock KCC strategy.
        """
        mock_kcc_strategy.supports.return_value = True

        result = composite_strategy.supports("CBZ", "MOBI")

        assert result is True
        mock_kcc_strategy.supports.assert_called_once_with("CBZ", "MOBI")

    def test_supports_comic_format_kcc_returns_false(
        self,
        composite_strategy: CompositeConversionStrategy,
        mock_kcc_strategy: MagicMock,
        mock_calibre_strategy: MagicMock,
    ) -> None:
        """Test supports for comic format when KCC doesn't support it (covers lines 117-120).

        Parameters
        ----------
        composite_strategy : CompositeConversionStrategy
            Composite strategy instance.
        mock_kcc_strategy : MagicMock
            Mock KCC strategy.
        mock_calibre_strategy : MagicMock
            Mock Calibre strategy.
        """
        mock_kcc_strategy.supports.return_value = False
        mock_calibre_strategy.supports.return_value = True

        result = composite_strategy.supports("CBZ", "MOBI")

        assert result is True
        mock_kcc_strategy.supports.assert_called_once_with("CBZ", "MOBI")
        mock_calibre_strategy.supports.assert_called_once_with("CBZ", "MOBI")

    def test_supports_comic_format_no_kcc_strategy(
        self,
        composite_strategy_no_kcc: CompositeConversionStrategy,
        mock_calibre_strategy: MagicMock,
    ) -> None:
        """Test supports for comic format when KCC strategy is None (covers lines 108-120).

        Parameters
        ----------
        composite_strategy_no_kcc : CompositeConversionStrategy
            Composite strategy without KCC.
        mock_calibre_strategy : MagicMock
            Mock Calibre strategy.
        """
        mock_calibre_strategy.supports.return_value = True

        result = composite_strategy_no_kcc.supports("CBZ", "MOBI")

        assert result is True
        mock_calibre_strategy.supports.assert_called_once_with("CBZ", "MOBI")

    def test_supports_non_comic_format(
        self,
        composite_strategy: CompositeConversionStrategy,
        mock_calibre_strategy: MagicMock,
    ) -> None:
        """Test supports for non-comic format (covers lines 108-120).

        Parameters
        ----------
        composite_strategy : CompositeConversionStrategy
            Composite strategy instance.
        mock_calibre_strategy : MagicMock
            Mock Calibre strategy.
        """
        mock_calibre_strategy.supports.return_value = True

        result = composite_strategy.supports("MOBI", "EPUB")

        assert result is True
        mock_calibre_strategy.supports.assert_called_once_with("MOBI", "EPUB")


class TestConvert:
    """Test convert method."""

    def test_convert_comic_format_with_kcc_success(
        self,
        composite_strategy: CompositeConversionStrategy,
        mock_kcc_strategy: MagicMock,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test convert for comic format with KCC success (covers lines 164-200).

        Parameters
        ----------
        composite_strategy : CompositeConversionStrategy
            Composite strategy instance.
        mock_kcc_strategy : MagicMock
            Mock KCC strategy.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        mock_kcc_strategy.supports.return_value = True
        mock_kcc_strategy.convert.return_value = output_path

        result = composite_strategy.convert(
            input_path=input_path,
            target_format="MOBI",
            output_path=output_path,
        )

        assert result == output_path
        mock_kcc_strategy.supports.assert_called_once_with("CBZ", "MOBI")
        mock_kcc_strategy.convert.assert_called_once_with(
            input_path,
            "MOBI",
            output_path,
        )

    def test_convert_comic_format_with_kcc_and_profile(
        self,
        composite_strategy: CompositeConversionStrategy,
        mock_kcc_strategy: MagicMock,
        input_path: Path,
        output_path: Path,
        kcc_profile: KCCConversionProfile,
    ) -> None:
        """Test convert for comic format with KCC and profile (covers lines 171-191).

        Parameters
        ----------
        composite_strategy : CompositeConversionStrategy
            Composite strategy instance.
        mock_kcc_strategy : MagicMock
            Mock KCC strategy.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        kcc_profile : KCCConversionProfile
            KCC conversion profile.
        """
        mock_kcc_strategy.supports.return_value = True
        mock_kcc_strategy.kcc_path = Path("/path/to/kcc")
        mock_kcc_strategy.timeout = 600

        def profile_getter() -> KCCConversionProfile:
            return kcc_profile

        with patch(
            "fundamental.services.conversion.strategies.kcc.KCCConversionStrategy"
        ) as mock_kcc_class:
            mock_new_strategy = MagicMock()
            mock_new_strategy.convert.return_value = output_path
            mock_kcc_class.return_value = mock_new_strategy

            result = composite_strategy.convert(
                input_path=input_path,
                target_format="MOBI",
                output_path=output_path,
                profile_getter=profile_getter,
            )

            assert result == output_path
            mock_kcc_class.assert_called_once_with(
                mock_kcc_strategy.kcc_path,
                profile=kcc_profile,
                timeout=mock_kcc_strategy.timeout,
            )
            mock_new_strategy.convert.assert_called_once_with(
                input_path,
                "MOBI",
                output_path,
            )

    def test_convert_comic_format_with_kcc_and_profile_getter_returns_none(
        self,
        composite_strategy: CompositeConversionStrategy,
        mock_kcc_strategy: MagicMock,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test convert with profile_getter returning None (covers lines 171-200).

        Parameters
        ----------
        composite_strategy : CompositeConversionStrategy
            Composite strategy instance.
        mock_kcc_strategy : MagicMock
            Mock KCC strategy.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        mock_kcc_strategy.supports.return_value = True
        mock_kcc_strategy.convert.return_value = output_path

        def profile_getter() -> None:
            return None

        result = composite_strategy.convert(
            input_path=input_path,
            target_format="MOBI",
            output_path=output_path,
            profile_getter=profile_getter,
        )

        assert result == output_path
        mock_kcc_strategy.convert.assert_called_once_with(
            input_path,
            "MOBI",
            output_path,
        )

    def test_convert_comic_format_with_kcc_failure_fallback_to_calibre(
        self,
        composite_strategy: CompositeConversionStrategy,
        mock_kcc_strategy: MagicMock,
        mock_calibre_strategy: MagicMock,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test convert for comic format with KCC failure, fallback to Calibre (covers lines 201-214).

        Parameters
        ----------
        composite_strategy : CompositeConversionStrategy
            Composite strategy instance.
        mock_kcc_strategy : MagicMock
            Mock KCC strategy.
        mock_calibre_strategy : MagicMock
            Mock Calibre strategy.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        mock_kcc_strategy.supports.return_value = True
        mock_kcc_strategy.convert.side_effect = ConversionError("KCC failed")
        mock_calibre_strategy.convert.return_value = output_path

        result = composite_strategy.convert(
            input_path=input_path,
            target_format="MOBI",
            output_path=output_path,
        )

        assert result == output_path
        mock_kcc_strategy.convert.assert_called_once()
        mock_calibre_strategy.convert.assert_called_once_with(
            input_path,
            "MOBI",
            output_path,
        )

    def test_convert_comic_format_no_kcc_strategy(
        self,
        composite_strategy_no_kcc: CompositeConversionStrategy,
        mock_calibre_strategy: MagicMock,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test convert for comic format when KCC strategy is None (covers lines 164-214).

        Parameters
        ----------
        composite_strategy_no_kcc : CompositeConversionStrategy
            Composite strategy without KCC.
        mock_calibre_strategy : MagicMock
            Mock Calibre strategy.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        mock_calibre_strategy.convert.return_value = output_path

        result = composite_strategy_no_kcc.convert(
            input_path=input_path,
            target_format="MOBI",
            output_path=output_path,
        )

        assert result == output_path
        mock_calibre_strategy.convert.assert_called_once_with(
            input_path,
            "MOBI",
            output_path,
        )

    def test_convert_comic_format_kcc_does_not_support(
        self,
        composite_strategy: CompositeConversionStrategy,
        mock_kcc_strategy: MagicMock,
        mock_calibre_strategy: MagicMock,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test convert for comic format when KCC doesn't support it (covers lines 164-214).

        Parameters
        ----------
        composite_strategy : CompositeConversionStrategy
            Composite strategy instance.
        mock_kcc_strategy : MagicMock
            Mock KCC strategy.
        mock_calibre_strategy : MagicMock
            Mock Calibre strategy.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        mock_kcc_strategy.supports.return_value = False
        mock_calibre_strategy.convert.return_value = output_path

        result = composite_strategy.convert(
            input_path=input_path,
            target_format="MOBI",
            output_path=output_path,
        )

        assert result == output_path
        mock_calibre_strategy.convert.assert_called_once_with(
            input_path,
            "MOBI",
            output_path,
        )

    def test_convert_non_comic_format(
        self,
        composite_strategy: CompositeConversionStrategy,
        mock_calibre_strategy: MagicMock,
        tmp_path: Path,
        output_path: Path,
    ) -> None:
        """Test convert for non-comic format (covers lines 156-214).

        Parameters
        ----------
        composite_strategy : CompositeConversionStrategy
            Composite strategy instance.
        mock_calibre_strategy : MagicMock
            Mock Calibre strategy.
        tmp_path : Path
            Temporary directory.
        output_path : Path
            Output file path.
        """
        input_path = tmp_path / "input.mobi"
        input_path.write_text("mock input content")
        mock_calibre_strategy.convert.return_value = output_path

        result = composite_strategy.convert(
            input_path=input_path,
            target_format="EPUB",
            output_path=output_path,
        )

        assert result == output_path
        mock_calibre_strategy.convert.assert_called_once_with(
            input_path,
            "EPUB",
            output_path,
        )

    def test_convert_no_extension_infer_from_stem(
        self,
        composite_strategy: CompositeConversionStrategy,
        mock_kcc_strategy: MagicMock,
        mock_calibre_strategy: MagicMock,
        tmp_path: Path,
        output_path: Path,
    ) -> None:
        """Test convert with no extension, infer from stem (covers lines 156-160).

        Parameters
        ----------
        composite_strategy : CompositeConversionStrategy
            Composite strategy instance.
        mock_kcc_strategy : MagicMock
            Mock KCC strategy.
        mock_calibre_strategy : MagicMock
            Mock Calibre strategy.
        tmp_path : Path
            Temporary directory.
        output_path : Path
            Output file path.
        """
        # File with no extension - format will be inferred from stem
        # Create a file named "input.mobi" where "mobi" is part of the stem, not extension
        # Actually, to test the no-extension case, we need a file with truly no extension
        # So we'll use a file like "input.mobi" but the code sees it as having .mobi extension
        # To test inference, we need a file with no extension at all
        input_path = tmp_path / "input"  # Truly no extension
        input_path.write_text("mock input content")
        # Ensure KCC doesn't support this to force Calibre path
        mock_kcc_strategy.supports.return_value = False
        mock_calibre_strategy.convert.return_value = output_path

        result = composite_strategy.convert(
            input_path=input_path,
            target_format="EPUB",
            output_path=output_path,
        )

        assert result == output_path
        mock_calibre_strategy.convert.assert_called_once_with(
            input_path,
            "EPUB",
            output_path,
        )

    def test_convert_no_extension_no_suffix(
        self,
        composite_strategy: CompositeConversionStrategy,
        mock_calibre_strategy: MagicMock,
        tmp_path: Path,
        output_path: Path,
    ) -> None:
        """Test convert with no extension and no suffix in stem (covers lines 156-160).

        Parameters
        ----------
        composite_strategy : CompositeConversionStrategy
            Composite strategy instance.
        mock_calibre_strategy : MagicMock
            Mock Calibre strategy.
        tmp_path : Path
            Temporary directory.
        output_path : Path
            Output file path.
        """
        input_path = tmp_path / "input"
        input_path.write_text("mock input content")
        mock_calibre_strategy.convert.return_value = output_path

        result = composite_strategy.convert(
            input_path=input_path,
            target_format="EPUB",
            output_path=output_path,
        )

        assert result == output_path
        mock_calibre_strategy.convert.assert_called_once_with(
            input_path,
            "EPUB",
            output_path,
        )

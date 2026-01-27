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

"""Tests for KCCConversionStrategy to achieve 100% coverage."""

from __future__ import annotations

import subprocess  # noqa: S404
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.kcc_config import KCCConversionProfile
from bookcard.services.conversion.exceptions import ConversionError
from bookcard.services.conversion.strategies.kcc import KCCConversionStrategy

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def kcc_path(tmp_path: Path) -> Path:
    """Create a mock KCC executable path.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory.

    Returns
    -------
    Path
        Path to mock KCC executable.
    """
    kcc = tmp_path / "kcc-c2e.py"
    kcc.write_text("#!/usr/bin/env python3\n# mock kcc")
    kcc.chmod(0o755)
    return kcc


@pytest.fixture
def kcc_path_with_venv(tmp_path: Path) -> Path:
    """Create a mock KCC path with venv.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory.

    Returns
    -------
    Path
        Path to mock KCC executable with venv.
    """
    kcc = tmp_path / "kcc-c2e.py"
    kcc.write_text("#!/usr/bin/env python3\n# mock kcc")
    kcc.chmod(0o755)
    venv_python = tmp_path / "venv" / "bin" / "python3"
    venv_python.parent.mkdir(parents=True, exist_ok=True)
    venv_python.write_text("#!/usr/bin/env python3\n# mock venv python")
    venv_python.chmod(0o755)
    return kcc


@pytest.fixture
def strategy(kcc_path: Path) -> KCCConversionStrategy:
    """Create KCCConversionStrategy instance.

    Parameters
    ----------
    kcc_path : Path
        Path to KCC executable.

    Returns
    -------
    KCCConversionStrategy
        Strategy instance.
    """
    return KCCConversionStrategy(kcc_path=kcc_path, timeout=600)


@pytest.fixture
def strategy_with_profile(
    kcc_path: Path,
) -> tuple[KCCConversionStrategy, KCCConversionProfile]:
    """Create KCCConversionStrategy with profile.

    Parameters
    ----------
    kcc_path : Path
        Path to KCC executable.

    Returns
    -------
    tuple[KCCConversionStrategy, KCCConversionProfile]
        Strategy instance and profile.
    """
    profile = KCCConversionProfile(
        id=1,
        user_id=1,
        name="Test Profile",
        device_profile="KPW5",
        output_format="MOBI",
        manga_style=True,
        hq=True,
        two_panel=True,
        webtoon=True,
        upscale=True,
        stretch=True,
        gamma=1.2,
        autolevel=True,
        autocontrast=False,
        colorautocontrast=True,
        cropping=1,
        cropping_power=1.5,
        preserve_margin=0.1,
        cropping_minimum=0.05,
        inter_panel_crop=1,
        black_borders=True,
        white_borders=True,
        force_color=True,
        force_png=True,
        mozjpeg=True,
        maximize_strips=True,
        splitter=1,
        target_size=200,
    )
    strategy = KCCConversionStrategy(kcc_path=kcc_path, profile=profile, timeout=600)
    return strategy, profile


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
    return tmp_path / "output.mobi"


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


class TestInit:
    """Test __init__ method."""

    def test_init_with_timeout(
        self,
        kcc_path: Path,
    ) -> None:
        """Test initialization with custom timeout (covers lines 65-84).

        Parameters
        ----------
        kcc_path : Path
            Path to KCC executable.
        """
        strategy = KCCConversionStrategy(kcc_path=kcc_path, timeout=300)

        assert strategy._kcc_path == kcc_path
        assert strategy._timeout == 300
        assert strategy._profile is None

    def test_init_with_profile(
        self,
        kcc_path: Path,
        kcc_profile: KCCConversionProfile,
    ) -> None:
        """Test initialization with profile (covers lines 65-84).

        Parameters
        ----------
        kcc_path : Path
            Path to KCC executable.
        kcc_profile : KCCConversionProfile
            KCC conversion profile.
        """
        strategy = KCCConversionStrategy(
            kcc_path=kcc_path,
            profile=kcc_profile,
            timeout=600,
        )

        assert strategy._kcc_path == kcc_path
        assert strategy._timeout == 600
        assert strategy._profile == kcc_profile

    def test_init_default_timeout(
        self,
        kcc_path: Path,
    ) -> None:
        """Test initialization with default timeout (covers lines 65-84).

        Parameters
        ----------
        kcc_path : Path
            Path to KCC executable.
        """
        strategy = KCCConversionStrategy(kcc_path=kcc_path)

        assert strategy._timeout == 600


class TestProperties:
    """Test property methods."""

    def test_kcc_path_property(
        self,
        strategy: KCCConversionStrategy,
        kcc_path: Path,
    ) -> None:
        """Test kcc_path property (covers lines 86-95).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        kcc_path : Path
            Expected KCC path.
        """
        assert strategy.kcc_path == kcc_path

    def test_timeout_property(
        self,
        strategy: KCCConversionStrategy,
    ) -> None:
        """Test timeout property (covers lines 97-106).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        """
        assert strategy.timeout == 600


class TestSupports:
    """Test supports method."""

    @pytest.mark.parametrize(
        ("source_format", "target_format", "expected"),
        [
            ("CBZ", "MOBI", True),
            ("CBR", "EPUB", True),
            ("CB7", "KEPUB", True),
            ("PDF", "AZW3", True),
            ("PDF", "CBZ", True),
            ("PDF", "PDF", True),
            ("PDF", "KFX", True),
            ("MOBI", "EPUB", False),
            ("EPUB", "MOBI", False),
            ("CBZ", "INVALID", False),
            ("INVALID", "MOBI", False),
        ],
    )
    def test_supports(
        self,
        strategy: KCCConversionStrategy,
        source_format: str,
        target_format: str,
        expected: bool,
    ) -> None:
        """Test supports method with various formats (covers lines 108-134).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        source_format : str
            Source format.
        target_format : str
            Target format.
        expected : bool
            Expected result.
        """
        assert strategy.supports(source_format, target_format) == expected


class TestConvert:
    """Test convert method."""

    def test_convert_success(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test successful conversion (covers lines 136-227).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # Create output file in input directory (KCC default behavior)
            kcc_output = input_path.parent / f"{input_path.stem}.mobi"
            kcc_output.write_text("converted content")

            result = strategy.convert(
                input_path=input_path,
                target_format="MOBI",
                output_path=output_path,
            )

            assert result == output_path
            assert output_path.exists()
            mock_run.assert_called_once()

    def test_convert_success_output_written_to_output_dir(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test successful conversion when KCC writes into output directory.

        This matches how BookCard calls KCC: ConversionService passes a pre-created
        temp file path, and KCC writes the real output into `output_path.parent` via `-o`.
        """
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # Simulate ConversionService temp file placeholder (0 bytes).
            output_path.write_text("")

            # Simulate KCC writing the real output into the output directory.
            kcc_output = output_path.parent / f"{input_path.stem}.mobi"
            kcc_output.write_text("converted content")

            result = strategy.convert(
                input_path=input_path,
                target_format="MOBI",
                output_path=output_path,
            )

            assert result == output_path
            assert output_path.read_text() == "converted content"
            mock_run.assert_called_once()

    def test_convert_success_output_already_at_target(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test successful conversion when output is already at target location (covers line 213).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        tmp_path : Path
            Temporary directory.
        """
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # Output path is in the same directory as input, matching KCC's default output location
            output_path = input_path.parent / f"{input_path.stem}.mobi"
            output_path.write_text("converted content")

            result = strategy.convert(
                input_path=input_path,
                target_format="MOBI",
                output_path=output_path,
            )

            assert result == output_path
            assert output_path.exists()
            mock_run.assert_called_once()

    def test_convert_failure_nonzero_returncode(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test conversion failure with nonzero returncode (covers lines 189-194).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "KCC error message"
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            with pytest.raises(ConversionError, match="KCC conversion failed"):
                strategy.convert(
                    input_path=input_path,
                    target_format="MOBI",
                    output_path=output_path,
                )

    def test_convert_failure_no_stderr(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test conversion failure with no stderr (covers lines 189-194).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = ""
            mock_result.stdout = "Error in stdout"
            mock_run.return_value = mock_result

            with pytest.raises(ConversionError, match="KCC conversion failed"):
                strategy.convert(
                    input_path=input_path,
                    target_format="MOBI",
                    output_path=output_path,
                )

    def test_convert_failure_no_output_file(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test conversion failure when output file not found (covers lines 202-204).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # Don't create output file

            with pytest.raises(ConversionError, match="output file not found"):
                strategy.convert(
                    input_path=input_path,
                    target_format="MOBI",
                    output_path=output_path,
                )

    def test_convert_timeout(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test conversion timeout (covers lines 214-216).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd=["python3", "kcc-c2e.py"],
                timeout=600,
            )

            with pytest.raises(ConversionError, match="timed out"):
                strategy.convert(
                    input_path=input_path,
                    target_format="MOBI",
                    output_path=output_path,
                )

    def test_convert_conversion_error_re_raises(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test that ConversionError is re-raised (covers lines 217-218).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = ConversionError("Already a conversion error")

            with pytest.raises(ConversionError, match="Already a conversion error"):
                strategy.convert(
                    input_path=input_path,
                    target_format="MOBI",
                    output_path=output_path,
                )

    def test_convert_general_exception(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test conversion with unexpected OS/process error.

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("python3 not found")

            with pytest.raises(ConversionError, match="KCC conversion failed"):
                strategy.convert(
                    input_path=input_path,
                    target_format="MOBI",
                    output_path=output_path,
                )

            # Verify output file cleanup attempt
            assert not output_path.exists()

    def test_convert_general_exception_output_exists(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test conversion with unexpected OS/process error when output exists.

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        output_path.write_text("partial output")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("python3 not found")

            with pytest.raises(ConversionError):
                strategy.convert(
                    input_path=input_path,
                    target_format="MOBI",
                    output_path=output_path,
                )

            # Output file should be cleaned up
            assert not output_path.exists()


class TestGetPythonCommand:
    """Test _get_python_command method."""

    def test_get_python_command_with_venv(
        self,
        kcc_path_with_venv: Path,
    ) -> None:
        """Test _get_python_command with venv (covers lines 229-243).

        Parameters
        ----------
        kcc_path_with_venv : Path
            KCC path with venv.
        """
        strategy = KCCConversionStrategy(kcc_path=kcc_path_with_venv)
        python_cmd = strategy._get_python_command()

        assert python_cmd == str(kcc_path_with_venv.parent / "venv" / "bin" / "python3")

    def test_get_python_command_without_venv(
        self,
        kcc_path: Path,
    ) -> None:
        """Test _get_python_command without venv (covers lines 229-243).

        Parameters
        ----------
        kcc_path : Path
            KCC path without venv.
        """
        strategy = KCCConversionStrategy(kcc_path=kcc_path)
        python_cmd = strategy._get_python_command()

        assert python_cmd == "python3"


class TestBuildKCCCommand:
    """Test _build_kcc_command method."""

    def test_build_kcc_command_without_profile(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test _build_kcc_command without profile (covers lines 245-290).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        cmd = strategy._build_kcc_command(input_path, "MOBI", output_path)

        assert "-p" in cmd
        assert "KV" in cmd  # Default device profile
        assert "-f" in cmd
        assert "MOBI" in cmd
        assert "-o" in cmd
        assert str(output_path.parent) in cmd
        assert str(input_path) in cmd
        assert cmd[-1] == str(input_path)  # Input file must be last

    def test_build_kcc_command_with_profile(
        self,
        strategy_with_profile: tuple[KCCConversionStrategy, KCCConversionProfile],
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test _build_kcc_command with profile (covers lines 245-290).

        Parameters
        ----------
        strategy_with_profile : tuple[KCCConversionStrategy, KCCConversionProfile]
            Strategy and profile.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        strategy, profile = strategy_with_profile
        cmd = strategy._build_kcc_command(input_path, "EPUB", output_path)

        assert "-p" in cmd
        assert profile.device_profile in cmd
        assert "-f" in cmd
        assert "EPUB" in cmd
        assert str(input_path) in cmd

    def test_build_kcc_command_azw3_format(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test _build_kcc_command with AZW3 format (covers lines 245-290).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        cmd = strategy._build_kcc_command(input_path, "AZW3", output_path)

        assert "-f" in cmd
        # AZW3 maps to MOBI in KCC_OUTPUT_FORMATS
        assert "MOBI" in cmd


class TestAddProfileOptions:
    """Test _add_profile_options method."""

    def test_add_profile_options(
        self,
        strategy_with_profile: tuple[KCCConversionStrategy, KCCConversionProfile],
    ) -> None:
        """Test _add_profile_options (covers lines 292-307).

        Parameters
        ----------
        strategy_with_profile : tuple[KCCConversionStrategy, KCCConversionProfile]
            Strategy and profile.
        """
        strategy, profile = strategy_with_profile
        cmd: list[str] = []

        strategy._add_profile_options(cmd, profile)

        # Should have added options from all sub-methods
        assert len(cmd) > 0


class TestAddBasicOptions:
    """Test _add_basic_options method."""

    @pytest.mark.parametrize(
        ("manga_style", "hq", "two_panel", "webtoon", "upscale", "stretch"),
        [
            (True, False, False, False, False, False),
            (False, True, False, False, False, False),
            (False, False, True, False, False, False),
            (False, False, False, True, False, False),
            (False, False, False, False, True, False),
            (False, False, False, False, False, True),
            (True, True, True, True, True, True),
        ],
    )
    def test_add_basic_options(
        self,
        strategy: KCCConversionStrategy,
        kcc_profile: KCCConversionProfile,
        manga_style: bool,
        hq: bool,
        two_panel: bool,
        webtoon: bool,
        upscale: bool,
        stretch: bool,
    ) -> None:
        """Test _add_basic_options with various flags (covers lines 309-330).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        kcc_profile : KCCConversionProfile
            KCC profile.
        manga_style : bool
            Manga style flag.
        hq : bool
            HQ flag.
        two_panel : bool
            Two panel flag.
        webtoon : bool
            Webtoon flag.
        upscale : bool
            Upscale flag.
        stretch : bool
            Stretch flag.
        """
        kcc_profile.manga_style = manga_style
        kcc_profile.hq = hq
        kcc_profile.two_panel = two_panel
        kcc_profile.webtoon = webtoon
        kcc_profile.upscale = upscale
        kcc_profile.stretch = stretch

        cmd: list[str] = []
        strategy._add_basic_options(cmd, kcc_profile)

        if manga_style:
            assert "-m" in cmd
        if hq:
            assert "-q" in cmd
        if two_panel:
            assert "-2" in cmd
        if webtoon:
            assert "-w" in cmd
        if upscale:
            assert "-u" in cmd
        if stretch:
            assert "-s" in cmd


class TestAddProcessingOptions:
    """Test _add_processing_options method."""

    def test_add_processing_options_with_gamma(
        self,
        strategy: KCCConversionStrategy,
        kcc_profile: KCCConversionProfile,
    ) -> None:
        """Test _add_processing_options with gamma (covers lines 332-351).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        kcc_profile : KCCConversionProfile
            KCC profile.
        """
        kcc_profile.gamma = 1.2
        kcc_profile.autolevel = True
        kcc_profile.autocontrast = False
        kcc_profile.colorautocontrast = True

        cmd: list[str] = []
        strategy._add_processing_options(cmd, kcc_profile)

        assert "-g" in cmd
        assert "1.2" in cmd
        assert "--autolevel" in cmd
        assert "--noautocontrast" in cmd
        assert "--colorautocontrast" in cmd

    def test_add_processing_options_without_gamma(
        self,
        strategy: KCCConversionStrategy,
        kcc_profile: KCCConversionProfile,
    ) -> None:
        """Test _add_processing_options without gamma (covers lines 332-351).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        kcc_profile : KCCConversionProfile
            KCC profile.
        """
        kcc_profile.gamma = None
        kcc_profile.autolevel = False
        kcc_profile.autocontrast = True
        kcc_profile.colorautocontrast = False

        cmd: list[str] = []
        strategy._add_processing_options(cmd, kcc_profile)

        assert "-g" not in cmd
        assert "--autolevel" not in cmd
        assert "--noautocontrast" not in cmd
        assert "--colorautocontrast" not in cmd


class TestAddCroppingOptions:
    """Test _add_cropping_options method."""

    def test_add_cropping_options_all(
        self,
        strategy: KCCConversionStrategy,
        kcc_profile: KCCConversionProfile,
    ) -> None:
        """Test _add_cropping_options with all options (covers lines 353-378).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        kcc_profile : KCCConversionProfile
            KCC profile.
        """
        kcc_profile.cropping = 1
        kcc_profile.cropping_power = 1.5
        kcc_profile.preserve_margin = 0.1
        kcc_profile.cropping_minimum = 0.05
        kcc_profile.inter_panel_crop = 1
        kcc_profile.black_borders = True
        kcc_profile.white_borders = True

        cmd: list[str] = []
        strategy._add_cropping_options(cmd, kcc_profile)

        assert "-c" in cmd
        assert "1" in cmd
        assert "--cp" in cmd
        assert "1.5" in cmd
        assert "--preservemargin" in cmd
        assert "0.1" in cmd
        assert "--cm" in cmd
        assert "0.05" in cmd
        assert "--ipc" in cmd
        assert "1" in cmd
        assert "--blackborders" in cmd
        assert "--whiteborders" in cmd

    def test_add_cropping_options_none(
        self,
        strategy: KCCConversionStrategy,
        kcc_profile: KCCConversionProfile,
    ) -> None:
        """Test _add_cropping_options with no options (covers lines 353-378).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        kcc_profile : KCCConversionProfile
            KCC profile.
        """
        kcc_profile.cropping = None  # ty:ignore[invalid-assignment]
        kcc_profile.cropping_power = None  # ty:ignore[invalid-assignment]
        kcc_profile.preserve_margin = None  # ty:ignore[invalid-assignment]
        kcc_profile.cropping_minimum = None  # ty:ignore[invalid-assignment]
        kcc_profile.inter_panel_crop = None  # ty:ignore[invalid-assignment]
        kcc_profile.black_borders = False
        kcc_profile.white_borders = False

        cmd: list[str] = []
        strategy._add_cropping_options(cmd, kcc_profile)

        assert "-c" not in cmd
        assert "--cp" not in cmd
        assert "--preservemargin" not in cmd
        assert "--cm" not in cmd
        assert "--ipc" not in cmd
        assert "--blackborders" not in cmd
        assert "--whiteborders" not in cmd


class TestAddOutputOptions:
    """Test _add_output_options method."""

    def test_add_output_options_all(
        self,
        strategy: KCCConversionStrategy,
        kcc_profile: KCCConversionProfile,
    ) -> None:
        """Test _add_output_options with all options (covers lines 380-403).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        kcc_profile : KCCConversionProfile
            KCC profile.
        """
        kcc_profile.force_color = True
        kcc_profile.force_png = True
        kcc_profile.mozjpeg = True
        kcc_profile.maximize_strips = True
        kcc_profile.splitter = 1
        kcc_profile.target_size = 200

        cmd: list[str] = []
        strategy._add_output_options(cmd, kcc_profile)

        assert "--forcecolor" in cmd
        assert "--forcepng" in cmd
        assert "--mozjpeg" in cmd
        assert "--maximizestrips" in cmd
        assert "-r" in cmd
        assert "1" in cmd
        assert "--ts" in cmd
        assert "200" in cmd

    def test_add_output_options_none(
        self,
        strategy: KCCConversionStrategy,
        kcc_profile: KCCConversionProfile,
    ) -> None:
        """Test _add_output_options with no options (covers lines 380-403).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        kcc_profile : KCCConversionProfile
            KCC profile.
        """
        kcc_profile.force_color = False
        kcc_profile.force_png = False
        kcc_profile.mozjpeg = False
        kcc_profile.maximize_strips = False
        kcc_profile.splitter = None  # ty:ignore[invalid-assignment]
        kcc_profile.target_size = None

        cmd: list[str] = []
        strategy._add_output_options(cmd, kcc_profile)

        assert "--forcecolor" not in cmd
        assert "--forcepng" not in cmd
        assert "--mozjpeg" not in cmd
        assert "--maximizestrips" not in cmd
        assert "-r" not in cmd
        assert "--ts" not in cmd


class TestFindKCCOutput:
    """Test _find_kcc_output method."""

    @pytest.mark.parametrize(
        ("target_format", "expected_ext"),
        [
            ("MOBI", "mobi"),
            ("AZW3", "mobi"),
            ("EPUB", "epub"),
            ("KEPUB", "kepub.epub"),
            ("CBZ", "cbz"),
            ("PDF", "pdf"),
            ("KFX", "kfx"),
        ],
    )
    def test_find_kcc_output(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
        target_format: str,
        expected_ext: str,
    ) -> None:
        """Test _find_kcc_output with various formats (covers lines 405-459).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        target_format : str
            Target format.
        expected_ext : str
            Expected extension.
        """
        # Create output file in input directory
        kcc_output = input_path.parent / f"{input_path.stem}.{expected_ext}"
        kcc_output.write_text("converted content")

        result = strategy._find_kcc_output(input_path, target_format, output_path)

        assert result == kcc_output
        assert result.exists()

    def test_find_kcc_output_not_found(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test _find_kcc_output when file not found (covers lines 405-459).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        # Don't create output file

        result = strategy._find_kcc_output(input_path, "MOBI", output_path)

        # Should return expected output path when not found
        assert result == output_path

    def test_find_kcc_output_with_different_naming(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test _find_kcc_output with different naming pattern (covers lines 405-459).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        # Create output with input filename pattern
        kcc_output = input_path.parent / f"{input_path.name}.mobi"
        kcc_output.write_text("converted content")

        result = strategy._find_kcc_output(input_path, "MOBI", output_path)

        assert result == kcc_output
        assert result.exists()

    def test_find_kcc_output_unknown_format(
        self,
        strategy: KCCConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test _find_kcc_output with unknown format (covers lines 405-459).

        Parameters
        ----------
        strategy : KCCConversionStrategy
            Strategy instance.
        input_path : Path
            Input file path.
        output_path : Path
            Output file path.
        """
        # Unknown format defaults to mobi
        kcc_output = input_path.parent / f"{input_path.stem}.mobi"
        kcc_output.write_text("converted content")

        result = strategy._find_kcc_output(input_path, "UNKNOWN", output_path)

        assert result == kcc_output

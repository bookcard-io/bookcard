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

"""Tests for CalibreConversionStrategy to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from bookcard.services.conversion.exceptions import ConversionError
from bookcard.services.conversion.strategies.calibre import (
    CalibreConversionStrategy,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def converter_path(tmp_path: Path) -> Path:
    """Create a mock converter path."""
    converter = tmp_path / "ebook-convert"
    converter.write_text("#!/bin/bash\necho 'mock converter'")
    converter.chmod(0o755)
    return converter


@pytest.fixture
def strategy(converter_path: Path) -> CalibreConversionStrategy:
    """Create CalibreConversionStrategy instance."""
    return CalibreConversionStrategy(converter_path=converter_path, timeout=300)


@pytest.fixture
def input_path(tmp_path: Path) -> Path:
    """Create a mock input file."""
    input_file = tmp_path / "input.mobi"
    input_file.write_text("mock input content")
    return input_file


@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    """Create a mock output file path."""
    return tmp_path / "output.epub"


class TestInit:
    """Test __init__ method."""

    def test_init_with_timeout(
        self,
        converter_path: Path,
    ) -> None:
        """Test initialization with custom timeout (covers lines 56-57)."""
        strategy = CalibreConversionStrategy(
            converter_path=converter_path,
            timeout=600,
        )

        assert strategy._converter_path == converter_path
        assert strategy._timeout == 600

    def test_init_default_timeout(
        self,
        converter_path: Path,
    ) -> None:
        """Test initialization with default timeout."""
        strategy = CalibreConversionStrategy(converter_path=converter_path)

        assert strategy._timeout == 300


class TestSupports:
    """Test supports method."""

    @pytest.mark.parametrize(
        ("source_format", "target_format"),
        [
            ("MOBI", "EPUB"),
            ("AZW3", "EPUB"),
            ("PDF", "EPUB"),
            ("EPUB", "MOBI"),
        ],
    )
    def test_supports_always_true(
        self,
        strategy: CalibreConversionStrategy,
        source_format: str,
        target_format: str,
    ) -> None:
        """Test supports always returns True (covers line 76)."""
        assert strategy.supports(source_format, target_format) is True


class TestConvert:
    """Test convert method."""

    def test_convert_success(
        self,
        strategy: CalibreConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test successful conversion (covers lines 110-137)."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # Create output file to simulate successful conversion
            output_path.write_text("converted content")

            result = strategy.convert(
                input_path=input_path,
                target_format="EPUB",
                output_path=output_path,
            )

            assert result == output_path
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0][0] == str(strategy._converter_path)
            assert mock_run.call_args[0][0][1] == str(input_path)
            assert mock_run.call_args[0][0][2] == str(output_path)

    def test_convert_failure_nonzero_returncode(
        self,
        strategy: CalibreConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test conversion failure with nonzero returncode (covers lines 127-130)."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Conversion error message"
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            with pytest.raises(ConversionError, match="Conversion failed"):
                strategy.convert(
                    input_path=input_path,
                    target_format="EPUB",
                    output_path=output_path,
                )

    def test_convert_failure_no_output_file(
        self,
        strategy: CalibreConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test conversion failure when output file not created (covers lines 132-134)."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # Don't create output file

            with pytest.raises(ConversionError, match="output file not found"):
                strategy.convert(
                    input_path=input_path,
                    target_format="EPUB",
                    output_path=output_path,
                )

    def test_convert_timeout(
        self,
        strategy: CalibreConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test conversion timeout (covers lines 138-140)."""
        with patch("subprocess.run") as mock_run:
            import subprocess  # noqa: S404

            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd=["ebook-convert"],
                timeout=300,
            )

            with pytest.raises(ConversionError, match="timed out"):
                strategy.convert(
                    input_path=input_path,
                    target_format="EPUB",
                    output_path=output_path,
                )

    def test_convert_general_exception(
        self,
        strategy: CalibreConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test conversion with general exception (covers lines 143-149)."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")

            with pytest.raises(ConversionError, match="Conversion failed"):
                strategy.convert(
                    input_path=input_path,
                    target_format="EPUB",
                    output_path=output_path,
                )

            # Verify output file cleanup attempt
            assert not output_path.exists()

    def test_convert_general_exception_output_exists(
        self,
        strategy: CalibreConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test conversion with general exception when output exists."""
        output_path.write_text("partial output")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")

            with pytest.raises(ConversionError):
                strategy.convert(
                    input_path=input_path,
                    target_format="EPUB",
                    output_path=output_path,
                )

            # Output file should be cleaned up
            assert not output_path.exists()

    def test_convert_conversion_error_re_raises(
        self,
        strategy: CalibreConversionStrategy,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Test that ConversionError is re-raised (covers lines 141-142)."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = ConversionError("Already a conversion error")

            with pytest.raises(ConversionError, match="Already a conversion error"):
                strategy.convert(
                    input_path=input_path,
                    target_format="EPUB",
                    output_path=output_path,
                )

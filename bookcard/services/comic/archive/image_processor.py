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

"""Image processing utilities used by the comic archive service."""

from __future__ import annotations

from io import BytesIO

from PIL import Image

from bookcard.services.comic.archive.exceptions import ImageProcessingError


class ImageProcessor:
    """Image processing component.

    This class is responsible only for basic image analysis needed by the
    comic reader backend (e.g., dimensions).
    """

    def get_dimensions(self, image_data: bytes) -> tuple[int, int]:
        """Get width and height from image bytes.

        Parameters
        ----------
        image_data : bytes
            Raw image bytes.

        Returns
        -------
        tuple[int, int]
            (width, height) in pixels.

        Raises
        ------
        ImageProcessingError
            If the image cannot be decoded.
        """
        try:
            img = Image.open(BytesIO(image_data))
        except OSError as e:
            msg = f"Failed to read image dimensions: {e}"
            raise ImageProcessingError(msg) from e
        else:
            return img.size

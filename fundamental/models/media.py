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

"""Media database models for Fundamental."""

from sqlmodel import Field, SQLModel


class Data(SQLModel, table=True):
    """Data model for book file formats.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    book : int
        Foreign key to book.
    format : str
        File format (e.g., 'EPUB', 'PDF', 'MOBI').
    uncompressed_size : int
        Uncompressed file size in bytes.
    name : str
        File name.
    """

    __tablename__ = "data"

    id: int | None = Field(default=None, primary_key=True)
    book: int = Field(foreign_key="books.id")
    format: str
    uncompressed_size: int
    name: str


class ConversionOptions(SQLModel, table=True):
    """Conversion options model for format conversion settings.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    format : str
        Target format for conversion.
    book : Optional[int]
        Foreign key to book (optional, can be None for global settings).
    data : bytes
        Binary data containing conversion options.
    """

    __tablename__ = "conversion_options"

    id: int | None = Field(default=None, primary_key=True)
    format: str
    book: int | None = Field(default=None, foreign_key="books.id")
    data: bytes

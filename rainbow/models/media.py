# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Media database models for Rainbow."""

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

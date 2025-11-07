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

"""Reading-related database models for Rainbow."""

from sqlmodel import Field, SQLModel


class Annotation(SQLModel, table=True):
    """Annotation model for book annotations (highlights, bookmarks, notes).

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    book : int
        Foreign key to book.
    format : str
        Book format this annotation applies to.
    user_type : str
        Type of user (e.g., 'local', 'remote').
    user : str
        User identifier.
    timestamp : float
        Timestamp when annotation was created.
    annot_id : str
        Unique annotation identifier.
    annot_type : str
        Type of annotation (e.g., 'highlight', 'bookmark', 'note').
    annot_data : str
        Annotation data (JSON or other format).
    searchable_text : str
        Searchable text content (default empty string).
    """

    __tablename__ = "annotations"

    id: int | None = Field(default=None, primary_key=True)
    book: int = Field(foreign_key="books.id")
    format: str
    user_type: str
    user: str
    timestamp: float
    annot_id: str
    annot_type: str
    annot_data: str
    searchable_text: str = ""


class AnnotationDirtied(SQLModel, table=True):
    """Annotation dirtied model for tracking modified annotations.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    book : int
        Foreign key to book.
    """

    __tablename__ = "annotations_dirtied"

    id: int | None = Field(default=None, primary_key=True)
    book: int = Field(foreign_key="books.id")


class LastReadPosition(SQLModel, table=True):
    """Last read position model for tracking reading progress.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    book : int
        Foreign key to book.
    format : str
        Book format.
    user : str
        User identifier.
    device : str
        Device identifier.
    cfi : str
        Canonical Fragment Identifier (CFI) for position.
    epoch : float
        Timestamp when position was saved.
    pos_frac : float
        Position fraction (default 0.0).
    """

    __tablename__ = "last_read_positions"

    id: int | None = Field(default=None, primary_key=True)
    book: int = Field(foreign_key="books.id")
    format: str
    user: str
    device: str
    cfi: str
    epoch: float
    pos_frac: float = 0.0

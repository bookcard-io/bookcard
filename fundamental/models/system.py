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
# IMPLIED, INCLUDING WITHOUT LIMITATION THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""System database models for Fundamental."""

from sqlmodel import Field, SQLModel


class Preference(SQLModel, table=True):
    """Preference model for application preferences.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    key : str
        Preference key.
    val : str
        Preference value.
    """

    __tablename__ = "preferences"

    id: int | None = Field(default=None, primary_key=True)
    key: str
    val: str


class LibraryId(SQLModel, table=True):
    """Library ID model for library UUID.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    uuid : str
        Unique library identifier.
    """

    __tablename__ = "library_id"

    id: int | None = Field(default=None, primary_key=True)
    uuid: str


class MetadataDirtied(SQLModel, table=True):
    """Metadata dirtied model for tracking modified book metadata.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    book : int
        Foreign key to book.
    """

    __tablename__ = "metadata_dirtied"

    id: int | None = Field(default=None, primary_key=True)
    book: int = Field(foreign_key="books.id")


class Feed(SQLModel, table=True):
    """Feed model for RSS/news feeds.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    title : str
        Feed title.
    script : str
        Feed script/configuration.
    """

    __tablename__ = "feeds"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    script: str


class CustomColumn(SQLModel, table=True):
    """Custom column model for user-defined metadata columns.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    label : str
        Display label for column.
    name : str
        Internal name for column.
    datatype : str
        Data type of column.
    mark_for_delete : bool
        Whether column is marked for deletion (default False).
    editable : bool
        Whether column is editable (default True).
    display : str
        Display configuration JSON (default '{}').
    is_multiple : bool
        Whether column supports multiple values (default False).
    normalized : Optional[bool]
        Whether column values are normalized.
    """

    __tablename__ = "custom_columns"

    id: int | None = Field(default=None, primary_key=True)
    label: str
    name: str
    datatype: str
    mark_for_delete: bool = False
    editable: bool = True
    display: str = "{}"
    is_multiple: bool = False
    normalized: bool | None = None


class BookPluginData(SQLModel, table=True):
    """Book plugin data model for plugin-specific book data.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    book : int
        Foreign key to book.
    name : str
        Plugin name.
    val : str
        Plugin data value.
    """

    __tablename__ = "books_plugin_data"

    id: int | None = Field(default=None, primary_key=True)
    book: int = Field(foreign_key="books.id")
    name: str
    val: str

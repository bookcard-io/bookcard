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

"""Database models for Fundamental."""

from fundamental.models.auth import (
    Permission,
    RefreshToken,
    Role,
    RolePermission,
    User,
    UserRole,
    UserSetting,
)
from fundamental.models.core import (
    Author,
    Book,
    BookAuthorLink,
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
    Comment,
    Identifier,
    Language,
    Publisher,
    Rating,
    Series,
    Tag,
)
from fundamental.models.media import ConversionOptions, Data
from fundamental.models.reading import (
    Annotation,
    AnnotationDirtied,
    LastReadPosition,
)
from fundamental.models.system import (
    BookPluginData,
    CustomColumn,
    Feed,
    LibraryId,
    MetadataDirtied,
    Preference,
)

__all__ = [
    "Annotation",
    "AnnotationDirtied",
    "Author",
    "Book",
    "BookAuthorLink",
    "BookLanguageLink",
    "BookPluginData",
    "BookPublisherLink",
    "BookRatingLink",
    "BookSeriesLink",
    "BookTagLink",
    "Comment",
    "ConversionOptions",
    "CustomColumn",
    "Data",
    "Feed",
    "Identifier",
    "Language",
    "LastReadPosition",
    "LibraryId",
    "MetadataDirtied",
    "Permission",
    "Preference",
    "Publisher",
    "Rating",
    "RefreshToken",
    "Role",
    "RolePermission",
    "Series",
    "Tag",
    "User",
    "UserRole",
    "UserSetting",
]

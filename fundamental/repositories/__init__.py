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

"""Repositories module for Fundamental."""

# Re-export all classes from calibre_book_repository for backward compatibility
from fundamental.repositories.calibre_book_repository import CalibreBookRepository
from fundamental.repositories.filters import (
    AuthorFilterStrategy,
    FilterBuilder,
    FilterStrategy,
    FormatFilterStrategy,
    GenreFilterStrategy,
    IdentifierFilterStrategy,
    LanguageFilterStrategy,
    PublisherFilterStrategy,
    RatingFilterStrategy,
    SeriesFilterStrategy,
    TitleFilterStrategy,
)
from fundamental.repositories.models import BookWithRelations, FilterContext
from fundamental.repositories.suggestions import (
    AuthorSuggestionStrategy,
    FilterSuggestionFactory,
    FilterSuggestionStrategy,
    FormatSuggestionStrategy,
    GenreSuggestionStrategy,
    IdentifierSuggestionStrategy,
    LanguageSuggestionStrategy,
    PublisherSuggestionStrategy,
    RatingSuggestionStrategy,
    SeriesSuggestionStrategy,
    TitleSuggestionStrategy,
)

__all__ = [
    "AuthorFilterStrategy",
    "AuthorSuggestionStrategy",
    # Models
    "BookWithRelations",
    # Main repository
    "CalibreBookRepository",
    "FilterBuilder",
    "FilterContext",
    # Filter strategies
    "FilterStrategy",
    "FilterSuggestionFactory",
    # Suggestion strategies
    "FilterSuggestionStrategy",
    "FormatFilterStrategy",
    "FormatSuggestionStrategy",
    "GenreFilterStrategy",
    "GenreSuggestionStrategy",
    "IdentifierFilterStrategy",
    "IdentifierSuggestionStrategy",
    "LanguageFilterStrategy",
    "LanguageSuggestionStrategy",
    "PublisherFilterStrategy",
    "PublisherSuggestionStrategy",
    "RatingFilterStrategy",
    "RatingSuggestionStrategy",
    "SeriesFilterStrategy",
    "SeriesSuggestionStrategy",
    "TitleFilterStrategy",
    "TitleSuggestionStrategy",
]

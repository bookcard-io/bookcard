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

"""Repositories module for Bookcard."""

# Re-export all classes from calibre_book_repository for backward compatibility
from bookcard.repositories.calibre_book_repository import CalibreBookRepository
from bookcard.repositories.epub_fixer_repository import (
    EPUBFixRepository,
    EPUBFixRunRepository,
)
from bookcard.repositories.filters import (
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
from bookcard.repositories.models import (
    BookWithFullRelations,
    BookWithRelations,
    FilterContext,
)
from bookcard.repositories.suggestions import (
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
    "BookWithFullRelations",
    # Models
    "BookWithRelations",
    # Main repository
    "CalibreBookRepository",
    "EPUBFixRepository",
    "EPUBFixRunRepository",
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

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

"""GraphQL queries for Hardcover API."""

# Search query that returns parsed book data
SEARCH_QUERY = (
    "query SearchBooks($query: String!) { "
    'search(query: $query, query_type: "Book", per_page: 50) { results } '
    "}"
)

# Edition query to fetch detailed book and edition information
EDITION_QUERY = (
    "query BookEditions($bookId: Int!) { "
    "books(where: {id: {_eq: $bookId}}) { "
    "  id slug description "
    "  book_series { position series { name } } "
    '  cached_tags(path: "Genre") '
    "  editions { "
    "    id title release_date isbn_13 isbn_10 reading_format_id "
    "    image { url } "
    "    language { code3 } "
    "    publisher { name } "
    "    contributions { author { name } } "
    "  } "
    "} }"
)

# Author search query using search endpoint
AUTHOR_SEARCH_QUERY = (
    "query SearchAuthors($query: String!) { "
    'search(query: $query, query_type: "Author", per_page: 50) { results } '
    "}"
)

# Author query to get author by ID with all fields
AUTHOR_BY_ID_QUERY = (
    "query GetAuthor($authorId: Int!) { "
    "authors(where: {id: {_eq: $authorId}}, limit: 1) { "
    "  id name slug "
    "  alternate_names bio "
    "  born_date born_year death_date death_year "
    "  books_count "
    "  cached_image "
    "  identifiers "
    "  is_bipoc is_lgbtq "
    "  contributions { "
    "    id contribution contributable_type "
    "    book { id title slug } "
    "  } "
    "} }"
)

# Operation names for each query
SEARCH_OPERATION_NAME = "SearchBooks"
EDITION_OPERATION_NAME = "BookEditions"
AUTHOR_SEARCH_OPERATION_NAME = "SearchAuthors"
AUTHOR_BY_ID_OPERATION_NAME = "GetAuthor"

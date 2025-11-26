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

# Operation names for each query
SEARCH_OPERATION_NAME = "SearchBooks"
EDITION_OPERATION_NAME = "BookEditions"

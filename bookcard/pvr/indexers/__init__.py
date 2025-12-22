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

"""PVR indexer implementations."""

from bookcard.pvr.indexers.newznab import NewznabIndexer
from bookcard.pvr.indexers.torrent_rss import TorrentRssIndexer
from bookcard.pvr.indexers.torznab import TorznabIndexer

__all__ = ["NewznabIndexer", "TorrentRssIndexer", "TorznabIndexer"]


# Auto-register built-in indexers
def _register_builtin_indexers() -> None:
    """Register built-in indexer implementations."""
    from bookcard.models.pvr import IndexerType
    from bookcard.pvr.factory import register_indexer

    register_indexer(IndexerType.TORZNAB, TorznabIndexer)
    register_indexer(IndexerType.NEWZNAB, NewznabIndexer)
    register_indexer(IndexerType.TORRENT_RSS, TorrentRssIndexer)


# Register on import
_register_builtin_indexers()

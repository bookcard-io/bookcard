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

"""XML parsing utilities for PVR indexers.

This module provides utilities for parsing XML elements, following DRY
principles by centralizing duplicate XML parsing logic.
"""

from contextlib import suppress
from datetime import datetime
from xml.etree.ElementTree import Element  # noqa: S405


def extract_publish_date_from_xml(item: Element) -> datetime | None:
    """Extract publish date from XML item element.

    Parameters
    ----------
    item : Element
        XML item element (from ElementTree).

    Returns
    -------
    datetime | None
        Parsed publish date or None if not found/invalid.

    Examples
    --------
    >>> from xml.etree.ElementTree import (
    ...     fromstring,
    ... )
    >>> item = fromstring(
    ...     "<item><pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate></item>"
    ... )
    >>> extract_publish_date_from_xml(
    ...     item
    ... )
    datetime.datetime(2024, 1, 1, 12, 0, 0)
    """
    pub_date_elem = item.find("pubDate")
    if pub_date_elem is not None and pub_date_elem.text:
        with suppress(ValueError, TypeError):
            from email.utils import parsedate_to_datetime

            return parsedate_to_datetime(pub_date_elem.text)
    return None

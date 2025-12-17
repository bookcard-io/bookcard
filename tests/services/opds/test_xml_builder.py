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

from __future__ import annotations

import pytest
from lxml import etree  # type: ignore[attr-defined]

from bookcard.api.schemas.opds import OpdsEntry, OpdsLink
from bookcard.services.opds.xml_builder import (
    NS_ATOM,
    NS_DC,
    NS_OPDS,
    OpdsXmlBuilder,
)


@pytest.fixture
def xml_builder() -> OpdsXmlBuilder:
    return OpdsXmlBuilder()


@pytest.fixture
def sample_entry() -> OpdsEntry:
    return OpdsEntry(
        id="urn:uuid:123",
        title="Test Book",
        authors=["Author One"],
        updated="2023-01-01T12:00:00Z",
        summary="A test book",
        published="2023-01-01",
        language="en",
        publisher="Test Publisher",
        identifier="1234567890",
        series="Test Series",
        series_index=1.0,
        links=[
            OpdsLink(href="/link1", rel="alternate", type="text/html", title="Link 1")
        ],
    )


class TestOpdsXmlBuilder:
    def test_build_feed(
        self, xml_builder: OpdsXmlBuilder, sample_entry: OpdsEntry
    ) -> None:
        """Test building a full feed."""
        links = [
            {"href": "/feed/self", "rel": "self", "type": "application/atom+xml"},
            {"href": "/feed/next", "rel": "next"},
        ]

        xml = xml_builder.build_feed(
            title="Test Feed",
            feed_id="urn:uuid:feed",
            updated="2023-01-01T12:00:00Z",
            entries=[sample_entry],
            links=links,
        )

        assert xml.startswith("<?xml")
        root = etree.fromstring(xml.encode("utf-8"))

        # Check namespaces
        assert root.nsmap[None] == NS_ATOM
        assert root.nsmap["opds"] == NS_OPDS

        # Check feed metadata
        assert root.find(f"{{{NS_ATOM}}}title").text == "Test Feed"
        assert root.find(f"{{{NS_ATOM}}}id").text == "urn:uuid:feed"
        assert root.find(f"{{{NS_ATOM}}}updated").text == "2023-01-01T12:00:00Z"

        # Check links
        feed_links = root.findall(f"{{{NS_ATOM}}}link")
        assert len(feed_links) == 2
        assert feed_links[0].get("href") == "/feed/self"

        # Check entry
        entry = root.find(f"{{{NS_ATOM}}}entry")
        assert entry is not None
        assert entry.find(f"{{{NS_ATOM}}}title").text == "Test Book"

    def test_build_entry(
        self, xml_builder: OpdsXmlBuilder, sample_entry: OpdsEntry
    ) -> None:
        """Test building a single entry."""
        elem = xml_builder.build_entry(sample_entry)

        # Elements are created without explicit namespace, but when added to feed
        # with default namespace, they'll be in that namespace
        # For testing, we can search without namespace or check tag names
        assert elem.tag == "entry"

        # Required Atom elements - search by tag name (namespace will be applied when added to feed)
        id_elem = elem.find("id")
        assert id_elem is not None
        assert id_elem.text == "urn:uuid:123"

        title_elem = elem.find("title")
        assert title_elem is not None
        assert title_elem.text == "Test Book"

        updated_elem = elem.find("updated")
        assert updated_elem is not None
        assert updated_elem.text == "2023-01-01T12:00:00Z"

        # Authors
        author = elem.find("author")
        assert author is not None
        name_elem = author.find("name")
        assert name_elem is not None
        assert name_elem.text == "Author One"

        # Optional metadata
        summary_elem = elem.find("summary")
        assert summary_elem is not None
        assert summary_elem.text == "A test book"

        published_elem = elem.find("published")
        assert published_elem is not None
        assert published_elem.text == "2023-01-01"

        # DC elements use namespace prefix
        language_elem = elem.find(f"{{{NS_DC}}}language")
        assert language_elem is not None
        assert language_elem.text == "en"

        publisher_elem = elem.find(f"{{{NS_DC}}}publisher")
        assert publisher_elem is not None
        assert publisher_elem.text == "Test Publisher"

        # ISBN identifier
        identifier = elem.find(f"{{{NS_DC}}}identifier")
        assert identifier is not None
        assert identifier.text == "1234567890"
        assert identifier.get("scheme") == "ISBN"

        # Links
        link = elem.find("link")
        assert link is not None
        assert link.get("href") == "/link1"
        assert link.get("rel") == "alternate"

    def test_build_entry_minimal(self, xml_builder: OpdsXmlBuilder) -> None:
        """Test building an entry with minimal fields."""
        entry = OpdsEntry(
            id="urn:uuid:min",
            title="Min Book",
            authors=[],
            updated="2023-01-01T00:00:00Z",
            links=[],
        )

        elem = xml_builder.build_entry(entry)

        # Search by tag name (namespace applied when added to feed)
        id_elem = elem.find("id")
        assert id_elem is not None
        assert id_elem.text == "urn:uuid:min"

        assert elem.find("summary") is None
        assert elem.find(f"{{{NS_DC}}}language") is None

    def test_build_feed_no_links(self, xml_builder: OpdsXmlBuilder) -> None:
        """Test building feed without links."""
        xml = xml_builder.build_feed(
            title="Title", feed_id="id", updated="time", entries=[]
        )
        root = etree.fromstring(xml.encode("utf-8"))
        assert len(root.findall(f"{{{NS_ATOM}}}link")) == 0

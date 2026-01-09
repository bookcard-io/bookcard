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

"""XML builder for OPDS feeds.

Builds OPDS 1.2/2.0 compliant XML documents using lxml.etree.
"""

from lxml import etree  # type: ignore[attr-defined]

from bookcard.api.schemas.opds import OpdsEntry
from bookcard.services.opds.interfaces import IOpdsXmlBuilder

# OPDS namespaces
NS_ATOM = "http://www.w3.org/2005/Atom"
NS_OPDS = "http://opds-spec.org/2010/catalog"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_DCTERMS = "http://purl.org/dc/terms/"


class OpdsXmlBuilder(IOpdsXmlBuilder):
    """Builder for OPDS XML documents.

    Follows SRP by focusing solely on OPDS XML generation logic.
    Uses lxml.etree consistent with existing OpfService pattern.
    """

    def build_feed(
        self,
        title: str,
        feed_id: str,
        updated: str,
        entries: list[OpdsEntry],
        links: list[dict[str, str]] | None = None,
    ) -> str:
        """Build OPDS feed XML.

        Parameters
        ----------
        title : str
            Feed title.
        feed_id : str
            Feed ID (URI).
        updated : str
            Feed update timestamp (ISO 8601).
        entries : list[OpdsEntry]
            List of feed entries.
        links : list[dict[str, str]] | None
            Optional list of feed links (with 'href', 'rel', 'type' keys).

        Returns
        -------
        str
            XML content as string.
        """
        # Create root feed element with namespaces
        feed = etree.Element(
            f"{{{NS_ATOM}}}feed",
            nsmap={
                None: NS_ATOM,
                "opds": NS_OPDS,
                "dc": NS_DC,
                "dcterms": NS_DCTERMS,
            },
        )

        # Add required Atom elements
        title_elem = etree.SubElement(feed, f"{{{NS_ATOM}}}title")
        title_elem.text = title

        id_elem = etree.SubElement(feed, f"{{{NS_ATOM}}}id")
        id_elem.text = feed_id

        updated_elem = etree.SubElement(feed, f"{{{NS_ATOM}}}updated")
        updated_elem.text = updated

        # Add author element (required by Atom)
        author_elem = etree.SubElement(feed, f"{{{NS_ATOM}}}author")
        name_elem = etree.SubElement(author_elem, f"{{{NS_ATOM}}}name")
        name_elem.text = "Calibre Bookcard"

        # Add links
        if links:
            for link_data in links:
                self._add_link(
                    feed,
                    link_data.get("href", ""),
                    link_data.get("rel", "alternate"),
                    mime_type=link_data.get("type"),
                    title=link_data.get("title"),
                )

        # Add entries
        for entry in entries:
            entry_elem = self.build_entry(entry)
            feed.append(entry_elem)

        # Generate XML string
        return etree.tostring(
            feed,
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=True,
        ).decode("utf-8")

    def build_entry(self, entry: OpdsEntry) -> etree._Element:
        """Build OPDS entry element.

        Parameters
        ----------
        entry : OpdsEntry
            Entry data model.

        Returns
        -------
        _Element
            XML element (lxml.etree._Element).
        """
        entry_elem = etree.Element(f"{{{NS_ATOM}}}entry")

        # Required Atom elements
        self._add_required_atom_elements(entry_elem, entry)
        self._add_authors(entry_elem, entry)
        self._add_optional_metadata(entry_elem, entry)
        self._add_links(entry_elem, entry)

        return entry_elem

    def _add_required_atom_elements(
        self, entry_elem: etree._Element, entry: OpdsEntry
    ) -> None:
        """Add required Atom elements to entry.

        Parameters
        ----------
        entry_elem : _Element
            Entry XML element.
        entry : OpdsEntry
            Entry data model.
        """
        id_elem = etree.SubElement(entry_elem, f"{{{NS_ATOM}}}id")
        id_elem.text = entry.id

        title_elem = etree.SubElement(entry_elem, f"{{{NS_ATOM}}}title")
        title_elem.text = entry.title

        updated_elem = etree.SubElement(entry_elem, f"{{{NS_ATOM}}}updated")
        updated_elem.text = entry.updated

    def _add_authors(self, entry_elem: etree._Element, entry: OpdsEntry) -> None:
        """Add authors to entry.

        Parameters
        ----------
        entry_elem : _Element
            Entry XML element.
        entry : OpdsEntry
            Entry data model.
        """
        for author in entry.authors:
            author_elem = etree.SubElement(entry_elem, f"{{{NS_ATOM}}}author")
            name_elem = etree.SubElement(author_elem, f"{{{NS_ATOM}}}name")
            name_elem.text = author

    def _add_optional_metadata(
        self, entry_elem: etree._Element, entry: OpdsEntry
    ) -> None:
        """Add optional metadata to entry.

        Parameters
        ----------
        entry_elem : _Element
            Entry XML element.
        entry : OpdsEntry
            Entry data model.
        """
        # Summary/description
        if entry.summary:
            summary_elem = etree.SubElement(entry_elem, f"{{{NS_ATOM}}}summary")
            summary_elem.text = entry.summary
            summary_elem.set("type", "text")

        # Published date
        if entry.published:
            published_elem = etree.SubElement(entry_elem, f"{{{NS_ATOM}}}published")
            published_elem.text = entry.published

        # DC metadata
        if entry.language:
            language_elem = etree.SubElement(entry_elem, f"{{{NS_DC}}}language")
            language_elem.text = entry.language

        if entry.publisher:
            publisher_elem = etree.SubElement(entry_elem, f"{{{NS_DC}}}publisher")
            publisher_elem.text = entry.publisher

        if entry.identifier:
            identifier_elem = etree.SubElement(entry_elem, f"{{{NS_DC}}}identifier")
            identifier_elem.text = entry.identifier
            # Assume ISBN if starts with digits
            if entry.identifier.replace("-", "").replace(" ", "").isdigit():
                identifier_elem.set("scheme", "ISBN")

        # Series information (OPDS extension)
        if entry.series:
            series_elem = etree.SubElement(
                entry_elem,
                f"{{{NS_DCTERMS}}}belongsTo",
            )
            series_elem.text = entry.series
            if entry.series_index is not None:
                series_elem.set("group-position", str(entry.series_index))

    def _add_links(self, entry_elem: etree._Element, entry: OpdsEntry) -> None:
        """Add links to entry.

        Parameters
        ----------
        entry_elem : _Element
            Entry XML element.
        entry : OpdsEntry
            Entry data model.
        """
        if entry.links:
            for link in entry.links:
                self._add_link(
                    entry_elem,
                    link.href,
                    link.rel,
                    mime_type=link.type,  # type is a field name from OpdsLink schema
                    title=link.title,
                )

    def _add_link(
        self,
        parent: etree._Element,
        href: str,
        rel: str,
        mime_type: str | None = None,
        title: str | None = None,
    ) -> None:
        """Add link element to parent.

        Parameters
        ----------
        parent : _Element
            Parent XML element.
        href : str
            Link URL.
        rel : str
            Link relation type.
        mime_type : str | None
            MIME type of linked resource.
        title : str | None
            Optional link title.
        """
        link_elem = etree.SubElement(parent, f"{{{NS_ATOM}}}link")
        link_elem.set("href", href)
        link_elem.set("rel", rel)

        if mime_type:
            link_elem.set("type", mime_type)

        if title:
            link_elem.set("title", title)

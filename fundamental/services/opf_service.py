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

"""Service for generating OPF (Open Packaging Format) metadata files.

This service encapsulates the business logic for converting book metadata
into OPF 3.0 XML format, following Calibre's standard metadata format.
"""

from __future__ import annotations

from dataclasses import dataclass

from lxml import etree  # type: ignore[attr-defined]

from fundamental.repositories.models import BookWithFullRelations  # noqa: TC001
from fundamental.services.metadata_builder import MetadataBuilder, StructuredMetadata
from fundamental.services.metadata_export_utils import FilenameGenerator

# OPF namespaces
NS_OPF = "http://www.idpf.org/2007/opf"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_DCTERMS = "http://purl.org/dc/terms/"


@dataclass
class OpfMetadataResult:
    """Result of OPF metadata generation.

    Attributes
    ----------
    xml_content : str
        Generated OPF XML content as string.
    filename : str
        Suggested filename for the OPF file.
    """

    xml_content: str
    filename: str


class OpfService:
    """Service for generating OPF metadata files from book data.

    Follows SRP by focusing solely on OPF XML generation logic.
    Uses IOC by accepting BookWithFullRelations as input, allowing
    the service to be tested independently of data source.
    """

    def generate_opf(self, book_with_rels: BookWithFullRelations) -> OpfMetadataResult:
        """Generate OPF 3.0 XML metadata from book data.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with all related metadata.

        Returns
        -------
        OpfMetadataResult
            Generated OPF XML content and suggested filename.

        Raises
        ------
        ValueError
            If book ID is missing.
        """
        # Use shared metadata builder to eliminate DRY violation
        structured_metadata = MetadataBuilder.build(book_with_rels)

        # Create root package element
        package = self._create_package_element()

        # Create metadata element
        metadata = etree.SubElement(package, "metadata")

        # Add all metadata fields from structured metadata
        self._add_identifier(metadata, structured_metadata)
        self._add_title(metadata, structured_metadata)
        self._add_authors(metadata, structured_metadata)
        self._add_publisher(metadata, structured_metadata)
        self._add_publication_date(metadata, structured_metadata)
        self._add_description(metadata, structured_metadata)
        self._add_languages(metadata, structured_metadata)
        self._add_identifiers(metadata, structured_metadata)
        self._add_series(metadata, structured_metadata)
        self._add_tags(metadata, structured_metadata)
        self._add_rating(metadata, structured_metadata)
        self._add_modified_date(metadata, structured_metadata)

        # Generate XML string
        xml_string = etree.tostring(
            package,
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=True,
        ).decode("utf-8")

        # Generate filename using shared utility
        filename = FilenameGenerator.generate(
            book_with_rels, book_with_rels.book, "opf"
        )

        return OpfMetadataResult(xml_content=xml_string, filename=filename)

    def _create_package_element(self) -> etree._Element:
        """Create the root package element with namespaces.

        Returns
        -------
        etree._Element
            Root package element.
        """
        return etree.Element(
            "package",
            version="3.0",
            unique_identifier="bookid",
            nsmap={
                None: NS_OPF,
                "dc": NS_DC,
                "dcterms": NS_DCTERMS,
            },
        )

    def _add_identifier(
        self, metadata: etree._Element, structured: StructuredMetadata
    ) -> None:
        """Add unique identifier to metadata.

        Parameters
        ----------
        metadata : etree._Element
            Metadata element to add identifier to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        identifier_elem = etree.SubElement(
            metadata,
            f"{{{NS_DC}}}identifier",
            attrib={"id": "bookid"},
        )
        identifier_elem.text = structured.uuid

    def _add_title(
        self, metadata: etree._Element, structured: StructuredMetadata
    ) -> None:
        """Add title to metadata.

        Parameters
        ----------
        metadata : etree._Element
            Metadata element to add title to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        if structured.title:
            title_elem = etree.SubElement(metadata, f"{{{NS_DC}}}title")
            title_elem.text = structured.title

    def _add_authors(
        self, metadata: etree._Element, structured: StructuredMetadata
    ) -> None:
        """Add authors to metadata.

        Parameters
        ----------
        metadata : etree._Element
            Metadata element to add authors to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        for author in structured.authors:
            creator_elem = etree.SubElement(metadata, f"{{{NS_DC}}}creator")
            creator_elem.text = author

    def _add_publisher(
        self, metadata: etree._Element, structured: StructuredMetadata
    ) -> None:
        """Add publisher to metadata.

        Parameters
        ----------
        metadata : etree._Element
            Metadata element to add publisher to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        if structured.publisher:
            publisher_elem = etree.SubElement(metadata, f"{{{NS_DC}}}publisher")
            publisher_elem.text = structured.publisher

    def _add_publication_date(
        self, metadata: etree._Element, structured: StructuredMetadata
    ) -> None:
        """Add publication date to metadata.

        Parameters
        ----------
        metadata : etree._Element
            Metadata element to add publication date to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        if structured.pubdate:
            date_elem = etree.SubElement(
                metadata,
                f"{{{NS_DCTERMS}}}date",
                attrib={"event": "publication"},
            )
            # Extract date part from ISO string (YYYY-MM-DD)
            date_elem.text = structured.pubdate.split("T")[0]

    def _add_description(
        self, metadata: etree._Element, structured: StructuredMetadata
    ) -> None:
        """Add description to metadata.

        Parameters
        ----------
        metadata : etree._Element
            Metadata element to add description to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        if structured.description:
            description_elem = etree.SubElement(metadata, f"{{{NS_DC}}}description")
            description_elem.text = structured.description

    def _add_languages(
        self, metadata: etree._Element, structured: StructuredMetadata
    ) -> None:
        """Add languages to metadata.

        Parameters
        ----------
        metadata : etree._Element
            Metadata element to add languages to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        for lang in structured.languages or []:
            language_elem = etree.SubElement(metadata, f"{{{NS_DC}}}language")
            language_elem.text = lang

    def _add_identifiers(
        self, metadata: etree._Element, structured: StructuredMetadata
    ) -> None:
        """Add identifiers (ISBN, etc.) to metadata.

        Parameters
        ----------
        metadata : etree._Element
            Metadata element to add identifiers to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        for identifier in structured.identifiers or []:
            id_type = identifier.get("type", "").lower()
            id_val = identifier.get("val", "")
            if id_val:
                id_elem = etree.SubElement(metadata, f"{{{NS_DC}}}identifier")
                if id_type == "isbn":
                    id_elem.set("scheme", "ISBN")
                id_elem.text = id_val

    def _add_series(
        self, metadata: etree._Element, structured: StructuredMetadata
    ) -> None:
        """Add series information to metadata.

        Parameters
        ----------
        metadata : etree._Element
            Metadata element to add series to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        if structured.series:
            series_elem = etree.SubElement(
                metadata,
                "meta",
                attrib={"id": "series", "property": "belongs-to-collection"},
            )
            series_elem.text = structured.series
            if structured.series_index is not None:
                series_index_elem = etree.SubElement(
                    metadata,
                    "meta",
                    attrib={"property": "group-position", "refines": "#series"},
                )
                series_index_elem.text = str(structured.series_index)

    def _add_tags(
        self, metadata: etree._Element, structured: StructuredMetadata
    ) -> None:
        """Add tags/subjects to metadata.

        Parameters
        ----------
        metadata : etree._Element
            Metadata element to add tags to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        for tag in structured.tags or []:
            subject_elem = etree.SubElement(metadata, f"{{{NS_DC}}}subject")
            subject_elem.text = tag

    def _add_rating(
        self, metadata: etree._Element, structured: StructuredMetadata
    ) -> None:
        """Add rating to metadata.

        Parameters
        ----------
        metadata : etree._Element
            Metadata element to add rating to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        if structured.rating is not None:
            rating_elem = etree.SubElement(
                metadata,
                "meta",
                attrib={"property": "calibre:rating"},
            )
            rating_elem.text = str(structured.rating)

    def _add_modified_date(
        self, metadata: etree._Element, structured: StructuredMetadata
    ) -> None:
        """Add modified date to metadata.

        Parameters
        ----------
        metadata : etree._Element
            Metadata element to add modified date to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        if structured.timestamp:
            modified_elem = etree.SubElement(
                metadata,
                "meta",
                attrib={"property": "dcterms:modified"},
            )
            # Extract and format timestamp (already in ISO format from builder)
            # OPF expects: YYYY-MM-DDTHH:MM:SSZ
            timestamp_str = structured.timestamp
            if "T" in timestamp_str and "Z" not in timestamp_str:
                # Ensure Z suffix for UTC
                if timestamp_str.endswith("+00:00"):
                    timestamp_str = timestamp_str.replace("+00:00", "Z")
                elif not timestamp_str.endswith("Z"):
                    timestamp_str = f"{timestamp_str}Z"
            modified_elem.text = timestamp_str

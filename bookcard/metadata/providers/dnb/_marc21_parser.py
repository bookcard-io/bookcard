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

"""MARC21 XML parser for DNB provider.

This module handles parsing MARC21-XML records from DNB SRU API,
following Single Responsibility Principle with separate extractors
for each field type.
"""

from __future__ import annotations

import datetime
import logging
import re
from contextlib import suppress
from typing import TYPE_CHECKING, ClassVar

import httpx

if TYPE_CHECKING:
    from lxml import etree  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


class MARC21Parser:
    """Parser for MARC21-XML records.

    This class is responsible solely for parsing MARC21-XML records
    and extracting book metadata into a structured dictionary format.
    Each field type has its own extraction method following SRP.

    Attributes
    ----------
    MARC21_NS : dict[str, str]
        MARC21 XML namespace mapping.
    """

    MARC21_NS: ClassVar[dict[str, str]] = {"marc21": "http://www.loc.gov/MARC21/slim"}

    # ISO 639-2/B to ISO 639-3 mapping
    ISO639_2B_TO_3: ClassVar[dict[str, str]] = {
        "ger": "deu",
        "fre": "fra",
        "dut": "nld",
        "chi": "zho",
        "cze": "ces",
        "gre": "ell",
        "ice": "isl",
        "rum": "ron",
    }

    def __init__(self) -> None:
        """Initialize MARC21 parser."""
        self._text_cleaner = None  # Will be set if needed for series guessing

    def parse(self, record: etree._Element) -> dict | None:
        """Parse MARC21 record into book data dictionary.

        Parameters
        ----------
        record : etree._Element
            MARC21 XML record element.

        Returns
        -------
        dict | None
            Book data dictionary, or None if record is invalid.
        """
        # Skip audio/video content
        if self._is_media_content(record):
            return None

        book: dict = {
            "series": None,
            "series_index": None,
            "pubdate": None,
            "languages": [],
            "title": None,
            "authors": [],
            "comments": None,
            "idn": None,
            "urn": None,
            "isbn": None,
            "tags": [],
            "publisher_name": None,
            "publisher_location": None,
        }

        # Extract IDN
        book["idn"] = self._extract_idn(record)

        # Extract title and series
        self._extract_title_and_series(record, book)

        # Extract authors
        self._extract_authors(record, book)

        # Extract publisher info
        self._extract_publisher_info(record, book)

        # Extract ISBN
        book["isbn"] = self._extract_isbn(record)

        # Extract subjects/tags
        self._extract_subjects(record, book)

        # Extract languages
        self._extract_languages(record, book)

        # Extract comments/description
        book["comments"] = self._extract_comments(record)

        return book

    def _is_media_content(self, record: etree._Element) -> bool:
        """Check if record represents audio/video content.

        Parameters
        ----------
        record : etree._Element
            MARC21 record element.

        Returns
        -------
        bool
            True if record is audio/video content.
        """
        # Check field 336 (Content Type)
        with suppress(IndexError, AttributeError):
            mediatype = (
                record
                .xpath(
                    "./marc21:datafield[@tag='336']/marc21:subfield[@code='a']",
                    namespaces=self.MARC21_NS,
                )[0]
                .text.strip()
                .lower()
            )
            if mediatype in ("gesprochenes wort",):
                return True

        # Check field 337 (Media Type)
        with suppress(IndexError, AttributeError):
            mediatype = (
                record
                .xpath(
                    "./marc21:datafield[@tag='337']/marc21:subfield[@code='a']",
                    namespaces=self.MARC21_NS,
                )[0]
                .text.strip()
                .lower()
            )
            if mediatype in ("audio", "video"):
                return True

        return False

    def _extract_idn(self, record: etree._Element) -> str | None:
        """Extract DNB IDN from field 016.

        Parameters
        ----------
        record : etree._Element
            MARC21 record element.

        Returns
        -------
        str | None
            IDN identifier, or None if not found.
        """
        with suppress(IndexError, AttributeError):
            return record.xpath(
                "./marc21:datafield[@tag='016']/marc21:subfield[@code='a']",
                namespaces=self.MARC21_NS,
            )[0].text.strip()
        return None

    def _extract_title_and_series(
        self,
        record: etree._Element,
        book: dict,
    ) -> None:
        """Extract title and series from field 245.

        Parameters
        ----------
        record : etree._Element
            MARC21 record element.
        book : dict
            Book data dictionary to update.
        """
        for field in record.xpath(
            "./marc21:datafield[@tag='245']", namespaces=self.MARC21_NS
        ):
            # Extract subfields
            code_a = self._extract_subfield_a(field)
            code_n = self._extract_subfield_n(field)
            code_p = self._extract_subfield_p(field)

            title_parts = code_a

            # Handle series extraction
            if code_a and code_n:
                title_parts, series_info = self._build_series_info(
                    code_a,
                    code_n,
                    code_p,
                )
                book["series"] = series_info["series"]
                book["series_index"] = series_info["series_index"]
                if code_p:
                    title_parts = [code_p[-1]]

            # Add subtitle (subfield b)
            self._add_subtitle(field, title_parts)

            if title_parts:
                book["title"] = " : ".join(title_parts)

    def _extract_subfield_a(self, field: etree._Element) -> list[str]:
        """Extract subfield a (main title).

        Parameters
        ----------
        field : etree._Element
            MARC21 field 245 element.

        Returns
        -------
        list[str]
            List of title parts.
        """
        return [
            i.text.strip()
            for i in field.xpath(
                "./marc21:subfield[@code='a']",
                namespaces=self.MARC21_NS,
            )
            if i.text
        ]

    def _extract_subfield_n(self, field: etree._Element) -> list[str]:
        """Extract subfield n (part numbers).

        Parameters
        ----------
        field : etree._Element
            MARC21 field 245 element.

        Returns
        -------
        list[str]
            List of part numbers.
        """
        code_n = []
        for i in field.xpath(
            "./marc21:subfield[@code='n']",
            namespaces=self.MARC21_NS,
        ):
            if i.text:
                match = re.search(r"(\d+([,\.]\d+)?)", i.text.strip())
                if match:
                    code_n.append(match.group(1))
        return code_n

    def _extract_subfield_p(self, field: etree._Element) -> list[str]:
        """Extract subfield p (part names).

        Parameters
        ----------
        field : etree._Element
            MARC21 field 245 element.

        Returns
        -------
        list[str]
            List of part names.
        """
        return [
            i.text.strip()
            for i in field.xpath(
                "./marc21:subfield[@code='p']",
                namespaces=self.MARC21_NS,
            )
            if i.text
        ]

    def _build_series_info(
        self,
        code_a: list[str],
        code_n: list[str],
        code_p: list[str],
    ) -> tuple[list[str], dict[str, str | None]]:
        """Build series information from title parts.

        Parameters
        ----------
        code_a : list[str]
            Main title parts.
        code_n : list[str]
            Part numbers.
        code_p : list[str]
            Part names.

        Returns
        -------
        tuple[list[str], dict[str, str | None]]
            Tuple of (title_parts, series_info).
        """
        series_parts = [code_a[0]]
        max_parts = min(len(code_p), len(code_n)) - 1
        for i in range(max_parts):
            if i < len(series_parts):
                series_parts[i] += " " + code_n[i]

        series_info = {
            "series": " - ".join(series_parts),
            "series_index": code_n[-1] if code_n else None,
        }
        return code_a, series_info

    def _add_subtitle(
        self,
        field: etree._Element,
        title_parts: list[str],
    ) -> None:
        """Add subtitle (subfield b) to title parts.

        Parameters
        ----------
        field : etree._Element
            MARC21 field 245 element.
        title_parts : list[str]
            List of title parts to update.
        """
        with suppress(IndexError, AttributeError):
            subtitle = field.xpath(
                "./marc21:subfield[@code='b']",
                namespaces=self.MARC21_NS,
            )[0].text.strip()
            title_parts.append(subtitle)

    def _extract_authors(self, record: etree._Element, book: dict) -> None:
        """Extract authors from fields 100 and 700.

        Parameters
        ----------
        record : etree._Element
            MARC21 record element.
        book : dict
            Book data dictionary to update.
        """
        # Primary authors (field 100) with role 'aut'
        for i in record.xpath(
            "./marc21:datafield[@tag='100']/marc21:subfield[@code='4' and text()='aut']/../marc21:subfield[@code='a']",
            namespaces=self.MARC21_NS,
        ):
            if i.text:
                name = re.sub(r" \[.*\]$", "", i.text.strip())
                book["authors"].append(name)

        # Secondary authors (field 700) with role 'aut'
        for i in record.xpath(
            "./marc21:datafield[@tag='700']/marc21:subfield[@code='4' and text()='aut']/../marc21:subfield[@code='a']",
            namespaces=self.MARC21_NS,
        ):
            if i.text:
                name = re.sub(r" \[.*\]$", "", i.text.strip())
                book["authors"].append(name)

        # If no authors found, use all involved persons
        if not book["authors"]:
            for i in record.xpath(
                "./marc21:datafield[@tag='700']/marc21:subfield[@code='a']",
                namespaces=self.MARC21_NS,
            ):
                if i.text:
                    name = re.sub(r" \[.*\]$", "", i.text.strip())
                    book["authors"].append(name)

    def _extract_publisher_info(
        self,
        record: etree._Element,
        book: dict,
    ) -> None:
        """Extract publisher information from field 264.

        Parameters
        ----------
        record : etree._Element
            MARC21 record element.
        book : dict
            Book data dictionary to update.
        """
        for field in record.xpath(
            "./marc21:datafield[@tag='264']", namespaces=self.MARC21_NS
        ):
            # Publisher location (subfield a)
            if not book["publisher_location"]:
                location_parts = [
                    i.text.strip()
                    for i in field.xpath(
                        "./marc21:subfield[@code='a']",
                        namespaces=self.MARC21_NS,
                    )
                    if i.text
                ]
                if location_parts:
                    book["publisher_location"] = " ".join(location_parts).strip("[]")

            # Publisher name (subfield b)
            if not book["publisher_name"]:
                with suppress(IndexError, AttributeError):
                    book["publisher_name"] = field.xpath(
                        "./marc21:subfield[@code='b']",
                        namespaces=self.MARC21_NS,
                    )[0].text.strip()

            # Publication date (subfield c)
            if not book["pubdate"]:
                with suppress(IndexError, AttributeError):
                    pubdate = field.xpath(
                        "./marc21:subfield[@code='c']",
                        namespaces=self.MARC21_NS,
                    )[0].text.strip()
                    match = re.search(r"(\d{4})", pubdate)
                    if match:
                        year = int(match.group(1))
                        book["pubdate"] = datetime.datetime(
                            year,
                            1,
                            1,
                            12,
                            30,
                            0,
                            tzinfo=datetime.UTC,
                        )

    def _extract_isbn(self, record: etree._Element) -> str | None:
        """Extract ISBN from field 020.

        Parameters
        ----------
        record : etree._Element
            MARC21 record element.

        Returns
        -------
        str | None
            ISBN, or None if not found.
        """
        for i in record.xpath(
            "./marc21:datafield[@tag='020']/marc21:subfield[@code='a']",
            namespaces=self.MARC21_NS,
        ):
            if i.text:
                isbn_regex = (
                    r"(?:ISBN(?:-1[03])?:? )?(?=[-0-9 ]{17}|[-0-9X ]{13}|[0-9X]{10})"
                    r"(?:97[89][- ]?)?[0-9]{1,5}[- ]?(?:[0-9]+[- ]?){2}[0-9X]"
                )
                match = re.search(isbn_regex, i.text.strip())
                if match:
                    isbn = match.group()
                    # Remove ISBN prefix, dashes, and spaces
                    isbn = re.sub(
                        r"^ISBN(?:-1[03])?:?\s*", "", isbn, flags=re.IGNORECASE
                    )
                    return isbn.replace("-", "").replace(" ", "")
        return None

    def _extract_subjects(self, record: etree._Element, book: dict) -> None:
        """Extract subjects/tags from various MARC21 fields.

        Parameters
        ----------
        record : etree._Element
            MARC21 record element.
        book : dict
            Book data dictionary to update.
        """
        tags: list[str] = []

        # GND subjects from field 689
        tags.extend(self._extract_gnd_subjects_689(record))

        # GND subjects from fields 600-655
        tags.extend(self._extract_gnd_subjects_600_655(record))

        # Non-GND subjects from fields 600-655
        tags.extend(self._extract_non_gnd_subjects(record))

        book["tags"] = list(dict.fromkeys(tags))  # Remove duplicates, preserve order

    def _extract_gnd_subjects_689(self, record: etree._Element) -> list[str]:
        """Extract GND subjects from field 689.

        Parameters
        ----------
        record : etree._Element
            MARC21 record element.

        Returns
        -------
        list[str]
            List of GND subjects.
        """
        return [
            i.text.strip()
            for i in record.xpath(
                "./marc21:datafield[@tag='689']/marc21:subfield[@code='a']",
                namespaces=self.MARC21_NS,
            )
            if i.text
        ]

    def _extract_gnd_subjects_600_655(self, record: etree._Element) -> list[str]:
        """Extract GND subjects from fields 600-655.

        Parameters
        ----------
        record : etree._Element
            MARC21 record element.

        Returns
        -------
        list[str]
            List of GND subjects.
        """
        return [
            i.text.strip()
            for field_tag in range(600, 656)
            for i in record.xpath(
                f"./marc21:datafield[@tag='{field_tag}']/"
                f"marc21:subfield[@code='2' and text()='gnd']/../marc21:subfield[@code='a']",
                namespaces=self.MARC21_NS,
            )
            if i.text and not i.text.startswith("(")
        ]

    def _extract_non_gnd_subjects(self, record: etree._Element) -> list[str]:
        """Extract non-GND subjects from fields 600-655.

        Parameters
        ----------
        record : etree._Element
            MARC21 record element.

        Returns
        -------
        list[str]
            List of non-GND subjects.
        """
        tags: list[str] = []
        for field_tag in range(600, 656):
            for i in record.xpath(
                f"./marc21:datafield[@tag='{field_tag}']/marc21:subfield[@code='a']",
                namespaces=self.MARC21_NS,
            ):
                if i.text and not i.text.startswith("(") and len(i.text) >= 2:
                    # Split on comma or semicolon
                    subjects = re.split(r"[,;]", i.text)
                    tags.extend(
                        subject.strip() for subject in subjects if subject.strip()
                    )
        return tags

    def _extract_languages(self, record: etree._Element, book: dict) -> None:
        """Extract languages from field 041.

        Parameters
        ----------
        record : etree._Element
            MARC21 record element.
        book : dict
            Book data dictionary to update.
        """
        languages: list[str] = []
        for i in record.xpath(
            "./marc21:datafield[@tag='041']/marc21:subfield[@code='a']",
            namespaces=self.MARC21_NS,
        ):
            if i.text:
                lang_code = i.text.strip()
                # Convert ISO 639-2/B to ISO 639-3
                lang_code = self.ISO639_2B_TO_3.get(lang_code.lower(), lang_code)
                languages.append(lang_code)

        book["languages"] = languages

    def _extract_comments(self, record: etree._Element) -> str | None:
        """Extract comments/description from field 856.

        Fetches description from DNB deposit URLs if available.

        Parameters
        ----------
        record : etree._Element
            MARC21 record element.

        Returns
        -------
        str | None
            Description text, or None if not available.
        """
        for url_elem in record.xpath(
            "./marc21:datafield[@tag='856']/marc21:subfield[@code='u']",
            namespaces=self.MARC21_NS,
        ):
            if url_elem.text:
                url = url_elem.text.strip()
                if url.startswith((
                    "http://deposit.dnb.de/",
                    "https://deposit.dnb.de/",
                )):
                    try:
                        response = httpx.get(url, timeout=15, follow_redirects=True)
                        response.raise_for_status()

                        comments_text = response.text
                        if "Zugriff derzeit nicht möglich" in comments_text:
                            continue

                        # Clean up comments
                        comments_text = re.sub(
                            r"(\s|<br>|<p>|\n)*Angaben aus der Verlagsmeldung"
                            r"(\s|<br>|<p>|\n)*(<h3>.*?</h3>)*(\s|<br>|<p>|\n)*",
                            "",
                            comments_text,
                            flags=re.IGNORECASE,
                        )
                        return comments_text.strip()

                    except (
                        httpx.RequestError,
                        httpx.HTTPStatusError,
                        ValueError,
                        AttributeError,
                    ) as e:
                        logger.debug("Failed to fetch DNB comments from %s: %s", url, e)
                        continue

        return None

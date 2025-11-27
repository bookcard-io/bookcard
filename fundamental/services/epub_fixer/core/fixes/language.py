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

"""Language tag fix implementation.

Fixes invalid or missing language tags in EPUB OPF metadata.
"""

from contextlib import suppress
from xml.parsers.expat import ExpatError

from defusedxml import minidom

from fundamental.models.epub_fixer import EPUBFixType
from fundamental.services.epub_fixer.core.epub import EPUBContents, FixResult
from fundamental.services.epub_fixer.core.fixes.base import EPUBFix
from fundamental.services.epub_fixer.utils.opf_locator import OPFLocator


class LanguageFix(EPUBFix):
    """Fix for invalid or missing language tags.

    Based on Amazon KDP language requirements:
    https://kdp.amazon.com/en_US/help/topic/G200673300
    """

    # Allowed languages from KDP requirements
    ALLOWED_LANGUAGES = frozenset([
        # ISO 639-1
        "af",
        "gsw",
        "ar",
        "eu",
        "nb",
        "br",
        "ca",
        "zh",
        "kw",
        "co",
        "da",
        "nl",
        "stq",
        "en",
        "fi",
        "fr",
        "fy",
        "gl",
        "de",
        "gu",
        "hi",
        "is",
        "ga",
        "it",
        "ja",
        "lb",
        "mr",
        "ml",
        "gv",
        "frr",
        "nn",
        "pl",
        "pt",
        "oc",
        "rm",
        "sco",
        "gd",
        "es",
        "sv",
        "ta",
        "cy",
        # ISO 639-2
        "afr",
        "ara",
        "eus",
        "baq",
        "nob",
        "bre",
        "cat",
        "zho",
        "chi",
        "cor",
        "cos",
        "dan",
        "nld",
        "dut",
        "eng",
        "fin",
        "fra",
        "fre",
        "fry",
        "glg",
        "deu",
        "ger",
        "guj",
        "hin",
        "isl",
        "ice",
        "gle",
        "ita",
        "jpn",
        "ltz",
        "mar",
        "mal",
        "glv",
        "nor",
        "nno",
        "por",
        "oci",
        "roh",
        "gla",
        "spa",
        "swe",
        "tam",
        "cym",
        "wel",
    ])

    def __init__(self, default_language: str = "en") -> None:
        """Initialize language fix.

        Parameters
        ----------
        default_language : str
            Default language to use if language is missing or invalid (default: 'en').
        """
        self._default_language = default_language

    @property
    def fix_type(self) -> EPUBFixType:
        """Return fix type.

        Returns
        -------
        EPUBFixType
            LANGUAGE_TAG fix type.
        """
        return EPUBFixType.LANGUAGE_TAG

    def apply(self, contents: EPUBContents) -> list[FixResult]:
        """Fix language field not defined or not available.

        Parameters
        ----------
        contents : EPUBContents
            EPUB contents to fix (modified in place).

        Returns
        -------
        list[FixResult]
            List of fixes applied.
        """
        results: list[FixResult] = []

        # Find OPF file
        opf_filename = OPFLocator.find_opf_path(contents.files)
        if not opf_filename or opf_filename not in contents.files:
            return results

        with suppress(ExpatError, ValueError, IndexError):
            opf = minidom.parseString(contents.files[opf_filename])
            language_tags = opf.getElementsByTagName("dc:language")
            language = self._default_language
            original_language = "undefined"

            if not language_tags or not language_tags[0].firstChild:
                # Use default language if no language tag exists or tag is empty
                results.append(
                    FixResult(
                        fix_type=self.fix_type,
                        description=f"No language tag found. Setting to default: {self._default_language}",
                        file_name=opf_filename,
                        original_value=original_language,
                        fixed_value=self._default_language,
                    )
                )
            else:
                language = language_tags[0].firstChild.nodeValue
                original_language = language

            simplified_lang = language.split("-")[0].lower()
            if simplified_lang not in self.ALLOWED_LANGUAGES:
                # If language is not supported, use default
                language = self._default_language
                results.append(
                    FixResult(
                        fix_type=self.fix_type,
                        description=f"Unsupported language {original_language}. Changed to {self._default_language}",
                        file_name=opf_filename,
                        original_value=original_language,
                        fixed_value=self._default_language,
                    )
                )

            # Update or create language tag
            if not language_tags:
                language_tag = opf.createElement("dc:language")
                text_node = opf.createTextNode(language)
                language_tag.appendChild(text_node)
                metadata = opf.getElementsByTagName("metadata")[0]
                metadata.appendChild(language_tag)
            else:
                if language_tags[0].firstChild:
                    language_tags[0].firstChild.nodeValue = language
                else:
                    text_node = opf.createTextNode(language)
                    language_tags[0].appendChild(text_node)

            if language != original_language:
                contents.files[opf_filename] = opf.toxml()
                if not results:
                    # Only add result if we didn't already add one above
                    results.append(
                        FixResult(
                            fix_type=self.fix_type,
                            description=f"Changed document language from {original_language} to {language}",
                            file_name=opf_filename,
                            original_value=original_language,
                            fixed_value=language,
                        )
                    )

        return results

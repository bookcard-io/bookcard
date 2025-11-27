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

"""EPUB fix implementations.

Each fix class follows Single Responsibility Principle and implements
the EPUBFix interface for extensibility (Open/Closed Principle).
"""

from fundamental.services.epub_fixer.core.fixes.base import EPUBFix
from fundamental.services.epub_fixer.core.fixes.body_id_link import BodyIdLinkFix
from fundamental.services.epub_fixer.core.fixes.encoding import EncodingFix
from fundamental.services.epub_fixer.core.fixes.language import LanguageFix
from fundamental.services.epub_fixer.core.fixes.stray_img import StrayImageFix

__all__ = [
    "BodyIdLinkFix",
    "EPUBFix",
    "EncodingFix",
    "LanguageFix",
    "StrayImageFix",
]

// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import { SHELF_IMPORTER } from "./shelfConstants";

export interface FileImportStrategy {
  accept: string;
  label: string;
  importerType: string;
  parse(file: File): Promise<{ name?: string; description?: string }>;
}

export const comicRackImportStrategy: FileImportStrategy = {
  accept: ".cbl",
  label: "ComicRack .cbl",
  importerType: SHELF_IMPORTER.COMICRACK,
  parse: async (file: File) => {
    const text = await file.text();
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(text, "text/xml");

    const parserError = xmlDoc.querySelector("parsererror");
    if (parserError) {
      throw new Error("Invalid XML file");
    }

    const name = xmlDoc
      .querySelector("ReadingList > Name")
      ?.textContent?.trim();
    const description = xmlDoc
      .querySelector("ReadingList > Description")
      ?.textContent?.trim();

    return { name, description: description || undefined };
  },
};

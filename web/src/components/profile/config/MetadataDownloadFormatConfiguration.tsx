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

"use client";

import { useSetting } from "@/hooks/useSetting";
import { RadioGroup } from "../RadioGroup";
import { METADATA_DOWNLOAD_FORMAT_OPTIONS } from "./configurationConstants";

const SETTING_KEY = "metadata_download_format";
const DEFAULT_VALUE = "opf";

/**
 * Metadata download format configuration component.
 *
 * Manages the preferred format for downloading book metadata.
 * Follows SRP by handling only metadata download format preference.
 * Follows IOC by using useSetting hook for persistence.
 */
export function MetadataDownloadFormatConfiguration() {
  const { value, setValue } = useSetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });

  return (
    <RadioGroup
      label="Metadata Download Format"
      options={[...METADATA_DOWNLOAD_FORMAT_OPTIONS]}
      value={value}
      onChange={setValue}
      name="metadata-download-format"
    />
  );
}

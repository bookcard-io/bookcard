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

import type { DownloadClientCreate } from "@/types/downloadClient";
import type { DownloadClientFormDataRelaxed as DownloadClientFormData } from "./types";

export function buildDownloadClientPayload(
  formData: DownloadClientFormData,
): DownloadClientCreate {
  const {
    url_base,
    api_key,
    rpc_path,
    secret_token,
    app_id,
    app_token,
    api_url,
    tags,
    destination,
    nzb_folder,
    strm_folder,
    torrent_folder,
    watch_folder,
    save_magnet_files,
    magnet_file_extension,
    directory,
    path_mappings,
    ...baseData
  } = formData;

  const additional_settings: Record<string, unknown> = {};

  // Helper to add if value exists
  const addIf = (key: string, value: string | number | boolean | undefined) => {
    if (value !== undefined && value !== "") {
      additional_settings[key] = value;
    }
  };

  addIf("url_base", url_base);
  addIf("api_key", api_key);
  addIf("rpc_path", rpc_path);
  addIf("secret_token", secret_token);
  addIf("app_id", app_id);
  addIf("app_token", app_token);
  addIf("api_url", api_url);
  addIf("tags", tags);
  addIf("destination", destination);
  addIf("nzb_folder", nzb_folder);
  addIf("strm_folder", strm_folder);
  addIf("torrent_folder", torrent_folder);
  addIf("watch_folder", watch_folder);
  addIf("magnet_file_extension", magnet_file_extension);
  addIf("directory", directory);

  // Boolean fields might be false, so check undefined
  if (save_magnet_files !== undefined) {
    additional_settings.save_magnet_files = save_magnet_files;
  }

  if (path_mappings && path_mappings.length > 0) {
    additional_settings.path_mappings = path_mappings;
  }

  // Ensure baseData satisfies DownloadClientCreate
  // We need to provide defaults for optional fields if they are missing
  return {
    ...baseData,
    name: baseData.name || baseData.client_type,
    host: baseData.host || "localhost",
    port: baseData.port || 0,
    use_ssl: baseData.use_ssl || false,
    priority: baseData.priority || 0,
    timeout_seconds: baseData.timeout_seconds || 30,
    enabled: baseData.enabled ?? true,
    additional_settings,
    download_path: directory || destination || formData.download_path,
  };
}

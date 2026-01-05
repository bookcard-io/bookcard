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

import { useCallback, useEffect, useState } from "react";
import {
  type DownloadClient,
  type DownloadClientCreate,
  DownloadClientType,
} from "@/types/downloadClient";
import { useDownloadClientConfig } from "./DownloadClientConfigContext";
import { buildDownloadClientPayload } from "./DownloadClientPayloadBuilder";
import type {
  DownloadClientFormDataRelaxed as DownloadClientFormData,
  PathMapping,
} from "./types";

// Re-export for consumers
export type { DownloadClientFormData };

const DEFAULT_FORM_DATA: DownloadClientFormData = {
  name: "",
  client_type: DownloadClientType.QBITTORRENT,
  host: "localhost",
  port: 8080,
  username: "",
  password: "",
  use_ssl: false,
  priority: 0,
  timeout_seconds: 30,
  enabled: true,
  category: "bookcard",
  url_base: "",
  api_key: "",
  rpc_path: "",
  secret_token: "",
  app_id: "",
  app_token: "",
  api_url: "",
  destination: "",
  nzb_folder: "",
  strm_folder: "",
  torrent_folder: "",
  watch_folder: "",
  save_magnet_files: false,
  magnet_file_extension: "",
  directory: "",
  download_path: "",
  path_mappings: [],
};

export function useDownloadClientForm(initialData?: DownloadClient) {
  const { configs } = useDownloadClientConfig();
  const [formData, setFormData] =
    useState<DownloadClientFormData>(DEFAULT_FORM_DATA);

  useEffect(() => {
    if (initialData) {
      const additional = initialData.additional_settings || {};
      setFormData({
        name: initialData.name,
        client_type: initialData.client_type,
        host: initialData.host,
        port: initialData.port,
        username: initialData.username || "",
        password: "", // Password always empty on edit for security
        use_ssl: initialData.use_ssl ?? false,
        priority: initialData.priority,
        timeout_seconds: initialData.timeout_seconds,
        enabled: initialData.enabled,
        category: initialData.category || "bookcard",
        download_path: initialData.download_path || "",

        // Map additional settings back to form fields
        url_base: (additional.url_base as string) || "",
        api_key: (additional.api_key as string) || "",
        rpc_path: (additional.rpc_path as string) || "",
        secret_token: (additional.secret_token as string) || "",
        app_id: (additional.app_id as string) || "",
        app_token: (additional.app_token as string) || "",
        api_url: (additional.api_url as string) || "",
        tags: (additional.tags as string) || "",
        destination: (additional.destination as string) || "",
        nzb_folder: (additional.nzb_folder as string) || "",
        strm_folder: (additional.strm_folder as string) || "",
        torrent_folder: (additional.torrent_folder as string) || "",
        watch_folder: (additional.watch_folder as string) || "",
        save_magnet_files: (additional.save_magnet_files as boolean) ?? false,
        magnet_file_extension:
          (additional.magnet_file_extension as string) || "",
        directory: (additional.directory as string) || "",
        path_mappings: (additional.path_mappings as PathMapping[]) || [],
      });
    } else {
      // Reset to defaults when opening fresh or when client type changes if needed
      // But initially just set defaults based on current type if not edit
      const type = formData.client_type;
      const config = configs[type];
      setFormData((prev) => ({
        ...prev,
        port: config.defaultPort,
        url_base: config.defaultUrlBase || "",
        rpc_path: config.defaultRpcPath || "",
        path_mappings: [],
      }));
    }
  }, [initialData, configs, formData.client_type]); // Depend on initialData and configs

  const handleChange = useCallback(
    (field: keyof DownloadClientFormData, value: unknown) => {
      setFormData((prev) => {
        const updates: Partial<DownloadClientFormData> = { [field]: value };

        // If client type changes, set default port and fields
        if (field === "client_type") {
          const newType = value as DownloadClientType;
          const config = configs[newType];
          if (config) {
            updates.port = config.defaultPort;
            updates.url_base = config.defaultUrlBase || "";
            updates.rpc_path = config.defaultRpcPath || "";
          }
        }
        return { ...prev, ...updates };
      });
    },
    [configs],
  );

  const getPayload = useCallback((): DownloadClientCreate => {
    return buildDownloadClientPayload(formData);
  }, [formData]);

  return { formData, handleChange, getPayload, setFormData };
}

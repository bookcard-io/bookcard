import { DownloadClientType } from "@/types/downloadClient";

export type ClientField =
  | "host"
  | "port"
  | "use_ssl"
  | "url_base"
  | "api_key"
  | "username"
  | "password"
  | "category"
  | "directory"
  | "destination"
  | "rpc_path"
  | "secret_token"
  | "app_id"
  | "app_token"
  | "api_url"
  | "tags"
  | "nzb_folder"
  | "strm_folder"
  | "torrent_folder"
  | "watch_folder"
  | "save_magnet_files"
  | "magnet_file_extension"
  | "priority";

export interface ClientConfig {
  defaultPort: number;
  fields: ClientField[];
  advancedFields?: ClientField[];
  defaultUrlBase?: string;
  defaultRpcPath?: string;
}

export const CLIENT_CONFIGS: Record<DownloadClientType, ClientConfig> = {
  [DownloadClientType.QBITTORRENT]: {
    defaultPort: 8080,
    fields: [
      "host",
      "port",
      "use_ssl",
      "username",
      "password",
      "category",
      "priority",
    ],
    advancedFields: ["url_base"],
  },
  [DownloadClientType.TRANSMISSION]: {
    defaultPort: 9091,
    defaultUrlBase: "/transmission/",
    fields: [
      "host",
      "port",
      "use_ssl",
      "username",
      "password",
      "category",
      "priority",
    ],
    advancedFields: ["url_base", "directory"],
  },
  [DownloadClientType.DELUGE]: {
    defaultPort: 8112,
    fields: ["host", "port", "use_ssl", "password", "category", "priority"],
    advancedFields: ["url_base", "directory"],
  },
  [DownloadClientType.RTORRENT]: {
    defaultPort: 8080,
    defaultUrlBase: "RPC2",
    fields: [
      "host",
      "port",
      "use_ssl",
      "username",
      "password",
      "url_base",
      "category",
      "priority",
    ],
    advancedFields: ["directory"],
  },
  [DownloadClientType.UTORRENT]: {
    defaultPort: 8080,
    defaultUrlBase: "gui",
    fields: [
      "host",
      "port",
      "use_ssl",
      "username",
      "password",
      "category",
      "priority",
    ],
    advancedFields: ["url_base"],
  },
  [DownloadClientType.VUZE]: {
    defaultPort: 65335,
    fields: [
      "host",
      "port",
      "use_ssl",
      "username",
      "password",
      "category",
      "priority",
    ],
  },
  [DownloadClientType.ARIA2]: {
    defaultPort: 6800,
    defaultRpcPath: "/jsonrpc",
    fields: [
      "host",
      "port",
      "use_ssl",
      "rpc_path",
      "secret_token",
      "directory",
      "priority",
    ],
  },
  [DownloadClientType.FLOOD]: {
    defaultPort: 3000,
    fields: [
      "host",
      "port",
      "use_ssl",
      "username",
      "password",
      "url_base",
      "destination",
      "priority",
    ],
  },
  [DownloadClientType.HADOUKEN]: {
    defaultPort: 7070,
    fields: [
      "host",
      "port",
      "use_ssl",
      "username",
      "password",
      "category",
      "priority",
    ],
    advancedFields: ["url_base"],
  },
  [DownloadClientType.FREEBOX_DOWNLOAD]: {
    defaultPort: 443,
    fields: [
      "host",
      "port",
      "use_ssl",
      "app_id",
      "app_token",
      "category",
      "priority",
    ],
    advancedFields: ["api_url", "destination"],
  },
  [DownloadClientType.DOWNLOAD_STATION]: {
    defaultPort: 5000,
    fields: [
      "host",
      "port",
      "use_ssl",
      "username",
      "password",
      "category",
      "directory",
      "priority",
    ],
  },
  [DownloadClientType.SABNZBD]: {
    defaultPort: 8080,
    defaultUrlBase: "sabnzbd",
    fields: [
      "host",
      "port",
      "use_ssl",
      "username",
      "password",
      "api_key",
      "category",
      "priority",
    ],
    advancedFields: ["url_base"],
  },
  [DownloadClientType.NZBGET]: {
    defaultPort: 6789,
    defaultUrlBase: "nzbget",
    fields: [
      "host",
      "port",
      "use_ssl",
      "username",
      "password",
      "category",
      "priority",
    ],
    advancedFields: ["url_base"],
  },
  [DownloadClientType.NZBVORTEX]: {
    defaultPort: 4321,
    fields: ["host", "port", "use_ssl", "api_key", "category", "priority"],
    advancedFields: ["url_base"],
  },
  [DownloadClientType.PNEUMATIC]: {
    defaultPort: 0,
    fields: ["nzb_folder", "strm_folder", "priority"],
  },
  [DownloadClientType.TORRENT_BLACKHOLE]: {
    defaultPort: 0,
    fields: [
      "torrent_folder",
      "watch_folder",
      "save_magnet_files",
      "magnet_file_extension",
      "priority",
    ],
  },
  [DownloadClientType.USENET_BLACKHOLE]: {
    defaultPort: 0,
    fields: ["nzb_folder", "watch_folder", "priority"],
  },
};

export const FIELD_DEFINITIONS: Record<
  ClientField,
  { label: string; type: string; placeholder?: string }
> = {
  host: { label: "Host", type: "text" },
  port: { label: "Port", type: "number" },
  use_ssl: { label: "Use SSL", type: "checkbox" },
  url_base: {
    label: "URL Base",
    type: "text",
    placeholder: "e.g. /transmission/ or RPC2",
  },
  api_key: { label: "API Key", type: "password" },
  username: { label: "Username", type: "text" },
  password: { label: "Password", type: "password" },
  category: { label: "Category", type: "text", placeholder: "bookcard" },
  directory: { label: "Directory", type: "text" },
  destination: { label: "Destination", type: "text" },
  rpc_path: { label: "RPC Path", type: "text", placeholder: "/jsonrpc" },
  secret_token: { label: "Secret Token", type: "password" },
  app_id: { label: "App ID", type: "text" },
  app_token: { label: "App Token", type: "password" },
  api_url: { label: "API URL", type: "text", placeholder: "/api/v1/" },
  tags: { label: "Tags", type: "text" },
  nzb_folder: { label: "NZB Folder", type: "text" },
  strm_folder: { label: "STRM Folder", type: "text" },
  torrent_folder: { label: "Torrent Folder", type: "text" },
  watch_folder: { label: "Watch Folder", type: "text" },
  save_magnet_files: { label: "Save Magnet Files", type: "checkbox" },
  magnet_file_extension: {
    label: "Magnet File Extension",
    type: "text",
    placeholder: ".magnet",
  },
  priority: { label: "Priority", type: "number" },
};

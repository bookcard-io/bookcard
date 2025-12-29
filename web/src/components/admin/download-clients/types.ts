import type { DownloadClientType } from "@/types/downloadClient";

export interface BaseClientFormData {
  name: string;
  client_type: DownloadClientType;
  priority: number;
  timeout_seconds: number;
  enabled: boolean;

  // These might be common enough or could be specific
  host?: string;
  port?: number;
  use_ssl?: boolean;
}

export interface AuthenticatedClientFormData extends BaseClientFormData {
  username?: string;
  password?: string;
}

// Specific Client Types
export interface QBittorrentFormData extends AuthenticatedClientFormData {
  client_type: DownloadClientType.QBITTORRENT;
  category: string;
  url_base?: string;
}

export interface TransmissionFormData extends AuthenticatedClientFormData {
  client_type: DownloadClientType.TRANSMISSION;
  category: string;
  url_base?: string;
  directory?: string;
}

export interface DelugeFormData extends BaseClientFormData {
  client_type: DownloadClientType.DELUGE;
  password?: string;
  category: string;
  url_base?: string;
  directory?: string;
}

export interface RTorrentFormData extends AuthenticatedClientFormData {
  client_type: DownloadClientType.RTORRENT;
  category: string;
  url_base?: string;
  directory?: string;
}

export interface UTorrentFormData extends AuthenticatedClientFormData {
  client_type: DownloadClientType.UTORRENT;
  category: string;
  url_base?: string;
}

export interface VuzeFormData extends AuthenticatedClientFormData {
  client_type: DownloadClientType.VUZE;
  category: string;
}

export interface Aria2FormData extends BaseClientFormData {
  client_type: DownloadClientType.ARIA2;
  rpc_path?: string;
  secret_token?: string;
  directory?: string;
}

export interface FloodFormData extends AuthenticatedClientFormData {
  client_type: DownloadClientType.FLOOD;
  url_base?: string;
  destination?: string;
}

export interface HadoukenFormData extends AuthenticatedClientFormData {
  client_type: DownloadClientType.HADOUKEN;
  category: string;
  url_base?: string;
}

export interface FreeboxFormData extends BaseClientFormData {
  client_type: DownloadClientType.FREEBOX_DOWNLOAD;
  app_id?: string;
  app_token?: string;
  category: string;
  api_url?: string;
  destination?: string;
}

export interface DownloadStationFormData extends AuthenticatedClientFormData {
  client_type: DownloadClientType.DOWNLOAD_STATION;
  category: string;
  directory?: string;
}

export interface SabnzbdFormData extends AuthenticatedClientFormData {
  client_type: DownloadClientType.SABNZBD;
  api_key?: string;
  category: string;
  url_base?: string;
}

export interface NzbgetFormData extends AuthenticatedClientFormData {
  client_type: DownloadClientType.NZBGET;
  category: string;
  url_base?: string;
}

export interface NzbvortexFormData extends BaseClientFormData {
  client_type: DownloadClientType.NZBVORTEX;
  api_key?: string;
  category: string;
  use_ssl?: boolean;
  url_base?: string;
}

export interface PneumaticFormData extends BaseClientFormData {
  client_type: DownloadClientType.PNEUMATIC;
  nzb_folder?: string;
  strm_folder?: string;

  // These shouldn't be here for Pneumatic but simplifying Base
  host?: never;
  port?: never;
  use_ssl?: never;
}

export interface TorrentBlackholeFormData extends BaseClientFormData {
  client_type: DownloadClientType.TORRENT_BLACKHOLE;
  torrent_folder?: string;
  watch_folder?: string;
  save_magnet_files?: boolean;
  magnet_file_extension?: string;

  // These shouldn't be here for Blackhole
  host?: never;
  port?: never;
  use_ssl?: never;
}

export interface UsenetBlackholeFormData extends BaseClientFormData {
  client_type: DownloadClientType.USENET_BLACKHOLE;
  nzb_folder?: string;
  watch_folder?: string;

  // These shouldn't be here for Blackhole
  host?: never;
  port?: never;
  use_ssl?: never;
}

export type DownloadClientFormDataUnion =
  | QBittorrentFormData
  | TransmissionFormData
  | DelugeFormData
  | RTorrentFormData
  | UTorrentFormData
  | VuzeFormData
  | Aria2FormData
  | FloodFormData
  | HadoukenFormData
  | FreeboxFormData
  | DownloadStationFormData
  | SabnzbdFormData
  | NzbgetFormData
  | NzbvortexFormData
  | PneumaticFormData
  | TorrentBlackholeFormData
  | UsenetBlackholeFormData;

// Helper to access fields safely with indexing, although Typescript might complain with union
// We can use a relaxed type for form handling that includes all fields optional
// but the main benefit is validation or specific logic per type.

export interface DownloadClientFormDataRelaxed {
  name: string;
  client_type: DownloadClientType;
  priority: number;
  timeout_seconds: number;
  enabled: boolean;

  host?: string;
  port?: number;
  use_ssl?: boolean;
  username?: string;
  password?: string;
  category?: string;
  url_base?: string;
  api_key?: string;
  rpc_path?: string;
  secret_token?: string;
  app_id?: string;
  app_token?: string;
  api_url?: string;
  tags?: string;
  destination?: string;
  nzb_folder?: string;
  strm_folder?: string;
  torrent_folder?: string;
  watch_folder?: string;
  save_magnet_files?: boolean;
  magnet_file_extension?: string;
  directory?: string;
  download_path?: string;
}

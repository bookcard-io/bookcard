export enum DownloadClientType {
  QBITTORRENT = "qbittorrent",
  TRANSMISSION = "transmission",
  DELUGE = "deluge",
  RTORRENT = "rtorrent",
  UTORRENT = "utorrent",
  VUZE = "vuze",
  ARIA2 = "aria2",
  FLOOD = "flood",
  HADOUKEN = "hadouken",
  FREEBOX_DOWNLOAD = "freebox_download",
  DOWNLOAD_STATION = "download_station",
  SABNZBD = "sabnzbd",
  NZBGET = "nzbget",
  NZBVORTEX = "nzbvortex",
  PNEUMATIC = "pneumatic",
  TORRENT_BLACKHOLE = "torrent_blackhole",
  USENET_BLACKHOLE = "usenet_blackhole",
  DIRECT_HTTP = "direct_http",
}

export enum DownloadClientStatus {
  HEALTHY = "healthy",
  DEGRADED = "degraded",
  UNHEALTHY = "unhealthy",
  DISABLED = "disabled",
}

export interface DownloadClient {
  id: number;
  name: string;
  client_type: DownloadClientType;
  host: string;
  port: number;
  username: string | null;
  use_ssl: boolean;
  enabled: boolean;
  priority: number;
  timeout_seconds: number;
  category: string | null;
  download_path: string | null;
  additional_settings: Record<string, unknown> | null;
  status: DownloadClientStatus;
  last_checked_at: string | null;
  last_successful_connection_at: string | null;
  error_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface DownloadClientCreate {
  name: string;
  client_type: DownloadClientType;
  host: string;
  port: number;
  username?: string;
  password?: string;
  use_ssl: boolean;
  enabled: boolean;
  priority: number;
  timeout_seconds: number;
  category?: string;
  download_path?: string;
  additional_settings?: Record<string, unknown>;
}

export interface DownloadClientUpdate {
  name?: string;
  host?: string;
  port?: number;
  username?: string;
  password?: string;
  use_ssl?: boolean;
  enabled?: boolean;
  priority?: number;
  timeout_seconds?: number;
  category?: string;
  download_path?: string;
  additional_settings?: Record<string, unknown>;
}

export interface DownloadClientListResponse {
  items: DownloadClient[];
  total: number;
}

export interface DownloadClientTestResponse {
  success: boolean;
  message: string;
}

export interface DownloadClientStatusResponse {
  id: number;
  status: DownloadClientStatus;
  last_checked_at: string | null;
  last_successful_connection_at: string | null;
  error_count: number;
  error_message: string | null;
}

export interface DownloadItemResponse {
  client_item_id: string;
  title: string;
  status: string;
  progress: number;
  size_bytes: number | null;
  downloaded_bytes: number | null;
  download_speed_bytes_per_sec: number | null;
  eta_seconds: number | null;
  file_path: string | null;
}

export interface DownloadItemsResponse {
  items: DownloadItemResponse[];
  total: number;
}

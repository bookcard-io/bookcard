export enum IndexerProtocol {
  TORRENT = "torrent",
  USENET = "usenet",
}

export enum IndexerType {
  TORZNAB = "torznab",
  NEWZNAB = "newznab",
  TORRENT_RSS = "torrent_rss",
  USENET_RSS = "usenet_rss",
  CUSTOM = "custom",
}

export enum IndexerStatus {
  HEALTHY = "healthy",
  DEGRADED = "degraded",
  UNHEALTHY = "unhealthy",
  DISABLED = "disabled",
  UNKNOWN = "unknown",
}

export interface Indexer {
  id: number;
  name: string;
  indexer_type: IndexerType;
  protocol: IndexerProtocol;
  base_url: string;
  api_key?: string | null;
  enabled: boolean;
  priority: number;
  timeout_seconds: number;
  retry_count: number;
  categories?: number[] | null;
  additional_settings?: Record<string, unknown> | null;
  status: IndexerStatus;
  last_checked_at?: string | null;
  last_successful_query_at?: string | null;
  error_count: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface IndexerCreate {
  name: string;
  indexer_type: IndexerType;
  protocol: IndexerProtocol;
  base_url: string;
  api_key?: string;
  enabled?: boolean;
  priority?: number;
  timeout_seconds?: number;
  retry_count?: number;
  categories?: number[];
  additional_settings?: Record<string, unknown>;
}

export interface IndexerUpdate {
  name?: string;
  base_url?: string;
  api_key?: string;
  enabled?: boolean;
  priority?: number;
  timeout_seconds?: number;
  retry_count?: number;
  categories?: number[];
  additional_settings?: Record<string, unknown>;
}

export interface IndexerTestResponse {
  success: boolean;
  message: string;
  latency_ms?: number;
}

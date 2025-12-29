export interface ProwlarrConfig {
  id: number | null;
  url: string;
  api_key: string | null;
  enabled: boolean;
  sync_categories: string[] | null;
  sync_app_profiles: number[] | null;
  sync_interval_minutes: number;
  created_at: string;
  updated_at: string;
}

export interface ProwlarrConfigUpdate {
  url: string;
  api_key?: string | null;
  enabled: boolean;
  sync_categories?: string[] | null;
  sync_app_profiles?: number[] | null;
  sync_interval_minutes: number;
}

export interface ProwlarrSyncResult {
  added: number;
  updated: number;
  removed: number;
  failed: number;
  total: number;
}

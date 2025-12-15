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

import { useCallback, useEffect, useRef, useState } from "react";
import type {
  PluginInfo,
  PluginInstallRequest,
  PluginListResult,
} from "@/services/pluginService";
import {
  installPluginGit,
  installPluginUpload,
  installPluginUrl,
  listPlugins,
  removePlugin,
  syncDeDRM,
} from "@/services/pluginService";
import {
  getPluginStatusFromError,
  type PluginStatus,
  type PluginStatusType,
} from "@/utils/plugins/errorHandling";
import { isAbortError } from "@/utils/plugins/isAbortError";

export interface PluginService {
  listPlugins: (signal?: AbortSignal) => Promise<PluginListResult>;
  installPluginUpload: (file: File) => Promise<void>;
  installPluginGit: (request: PluginInstallRequest) => Promise<void>;
  installPluginUrl: (url: string) => Promise<void>;
  removePlugin: (pluginName: string) => Promise<void>;
  syncDeDRM: () => Promise<{ message: string }>;
}

const defaultPluginService: PluginService = {
  listPlugins,
  installPluginUpload,
  installPluginGit,
  installPluginUrl,
  removePlugin,
  syncDeDRM,
};

export interface UsePluginsOptions {
  /**Override the concrete plugin service (useful for testing). */
  service?: PluginService;
  /**Callback invoked when listing plugins fails (non-abort). */
  onListError?: (error: unknown) => void;
}

export interface UsePluginsResult {
  plugins: PluginInfo[];
  statusMessage: string | null;
  statusType: PluginStatusType;
  dismissStatus: () => void;

  loading: boolean;
  refreshing: boolean;
  installing: boolean;
  syncing: boolean;

  refresh: (signal?: AbortSignal) => Promise<void>;
  installFromUpload: (file: File) => Promise<boolean>;
  installFromGit: (request: PluginInstallRequest) => Promise<boolean>;
  installFromUrl: (url: string) => Promise<boolean>;
  removeInstalledPlugin: (pluginName: string) => Promise<boolean>;
  syncDeDRMKeys: () => Promise<string>;
}

/**
 * Plugin state + operations for the admin Plugins tab.
 *
 * This hook centralizes plugin list management and mutation operations
 * (upload install, git install, removal, DeDRM sync), and normalizes
 * typed backend errors into a status banner.
 */
export function usePlugins(options: UsePluginsOptions = {}): UsePluginsResult {
  const service = options.service ?? defaultPluginService;
  const onListError = options.onListError;

  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [statusType, setStatusType] = useState<PluginStatusType>("neutral");

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [installing, setInstalling] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const hasLoadedOnceRef = useRef(false);

  const applyStatus = useCallback((status: PluginStatus | null) => {
    if (!status) return;
    setStatusMessage(status.message);
    setStatusType(status.type);
  }, []);

  const refresh = useCallback(
    async (signal?: AbortSignal) => {
      const isInitialLoad = !hasLoadedOnceRef.current;

      try {
        if (isInitialLoad) {
          setLoading(true);
        } else {
          setRefreshing(true);
        }

        const result = await service.listPlugins(signal);
        if (signal?.aborted) return;

        setPlugins(result.plugins);
        setStatusMessage(result.statusMessage || null);
        setStatusType(result.statusType || "neutral");
      } catch (error) {
        if (isAbortError(error)) {
          return;
        }
        onListError?.(error);
      } finally {
        if (!signal?.aborted) {
          if (isInitialLoad) {
            setLoading(false);
            hasLoadedOnceRef.current = true;
          } else {
            setRefreshing(false);
          }
        }
      }
    },
    [onListError, service],
  );

  useEffect(() => {
    const controller = new AbortController();
    refresh(controller.signal);
    return () => controller.abort();
  }, [refresh]);

  const installFromUpload = useCallback(
    async (file: File) => {
      try {
        setInstalling(true);
        await service.installPluginUpload(file);
        await refresh();
        return true;
      } catch (error) {
        const status = getPluginStatusFromError(error);
        if (status) {
          applyStatus(status);
          return false;
        }
        throw error;
      } finally {
        setInstalling(false);
      }
    },
    [applyStatus, refresh, service],
  );

  const installFromGit = useCallback(
    async (request: PluginInstallRequest) => {
      try {
        setInstalling(true);
        await service.installPluginGit(request);
        await refresh();
        return true;
      } catch (error) {
        const status = getPluginStatusFromError(error);
        if (status) {
          applyStatus(status);
          return false;
        }
        throw error;
      } finally {
        setInstalling(false);
      }
    },
    [applyStatus, refresh, service],
  );

  const installFromUrl = useCallback(
    async (url: string) => {
      try {
        setInstalling(true);
        await service.installPluginUrl(url);
        await refresh();
        return true;
      } catch (error) {
        const status = getPluginStatusFromError(error);
        if (status) {
          applyStatus(status);
          return false;
        }
        throw error;
      } finally {
        setInstalling(false);
      }
    },
    [applyStatus, refresh, service],
  );

  const removeInstalledPlugin = useCallback(
    async (pluginName: string) => {
      try {
        setInstalling(true);
        await service.removePlugin(pluginName);
        await refresh();
        return true;
      } finally {
        setInstalling(false);
      }
    },
    [refresh, service],
  );

  const syncDeDRMKeys = useCallback(async () => {
    try {
      setSyncing(true);
      const res = await service.syncDeDRM();
      return res.message;
    } finally {
      setSyncing(false);
    }
  }, [service]);

  const dismissStatus = useCallback(() => {
    setStatusMessage(null);
  }, []);

  return {
    plugins,
    statusMessage,
    statusType,
    dismissStatus,

    loading,
    refreshing,
    installing,
    syncing,

    refresh,
    installFromUpload,
    installFromGit,
    installFromUrl,
    removeInstalledPlugin,
    syncDeDRMKeys,
  };
}

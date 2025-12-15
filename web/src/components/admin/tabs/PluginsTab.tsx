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

import { useCallback } from "react";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { usePlugins } from "@/hooks/plugins/usePlugins";
import { PluginInstallSection } from "./plugins/PluginInstallSection";
import { PluginList } from "./plugins/PluginList";
import { StatusBanner } from "./plugins/StatusBanner";

export function PluginsTab() {
  const { showDanger, showSuccess, showWarning } = useGlobalMessages();
  const handleListError = useCallback(
    (error: unknown) => {
      console.error("Failed to fetch plugins", error);
      showDanger("Failed to fetch plugins.");
    },
    [showDanger],
  );

  const {
    plugins,
    statusMessage,
    statusType,
    dismissStatus,
    loading,
    refreshing,
    installing,
    syncing,
    installFromUpload,
    installFromUrl,
    removeInstalledPlugin,
    syncDeDRMKeys,
  } = usePlugins({
    onListError: handleListError,
  });

  const handleRemoveRequested = useCallback(
    (pluginName: string) => {
      removeInstalledPlugin(pluginName)
        .then((ok) => {
          if (ok) {
            showSuccess("Plugin removed successfully!");
          }
        })
        .catch((error) => {
          console.error("Failed to remove plugin", error);
          showDanger(
            `Failed to remove plugin: ${error instanceof Error ? error.message : "Unknown error"}`,
          );
        });
    },
    [removeInstalledPlugin, showDanger, showSuccess],
  );

  const handleSyncDeDRMRequested = useCallback(() => {
    syncDeDRMKeys()
      .then((message) => {
        showSuccess(message);
      })
      .catch((error) => {
        console.error("Failed to sync DeDRM", error);
        showDanger(
          `Failed to sync DeDRM: ${error instanceof Error ? error.message : "Unknown error"}`,
        );
      });
  }, [showDanger, showSuccess, syncDeDRMKeys]);

  return (
    <div className="flex flex-col gap-6">
      {statusMessage && (
        <StatusBanner
          message={statusMessage}
          type={statusType}
          onDismiss={dismissStatus}
        />
      )}

      <PluginInstallSection
        installing={installing}
        installFromUpload={installFromUpload}
        installFromUrl={installFromUrl}
        showSuccess={showSuccess}
        showWarning={showWarning}
        showDanger={showDanger}
      />

      <PluginList
        plugins={plugins}
        loading={loading}
        refreshing={refreshing}
        installing={installing}
        syncingDeDRM={syncing}
        onRemoveRequested={handleRemoveRequested}
        onSyncDeDRMRequested={handleSyncDeDRMRequested}
      />
    </div>
  );
}

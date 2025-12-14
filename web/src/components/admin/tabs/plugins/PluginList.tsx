import { FaSpinner } from "react-icons/fa";
import type { PluginInfo } from "@/services/pluginService";
import { PluginCard } from "./PluginCard";
import { getPluginActions } from "./pluginActions";

export interface PluginListProps {
  plugins: PluginInfo[];
  loading: boolean;
  refreshing: boolean;
  installing: boolean;
  syncingDeDRM: boolean;
  onRemoveRequested: (pluginName: string) => void;
  onSyncDeDRMRequested: () => void;
}

export function PluginList({
  plugins,
  loading,
  refreshing,
  installing,
  syncingDeDRM,
  onRemoveRequested,
  onSyncDeDRMRequested,
}: PluginListProps): React.ReactElement {
  const handleRemove = (pluginName: string) => {
    if (!confirm(`Are you sure you want to remove ${pluginName}?`)) {
      return;
    }
    onRemoveRequested(pluginName);
  };

  return (
    <div className="rounded-lg border border-[var(--color-surface-a20)] bg-[var(--color-surface-tonal-a0)] p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-semibold text-[var(--color-text-a0)] text-xl">
          Installed Plugins
        </h2>
        {refreshing && (
          <div className="flex items-center gap-2 text-[var(--color-text-a30)] text-sm">
            <FaSpinner className="animate-spin" />
            Refreshing...
          </div>
        )}
      </div>

      {loading && plugins.length === 0 ? (
        <div className="text-[var(--color-text-a30)]">Loading plugins...</div>
      ) : plugins.length === 0 ? (
        <div className="text-[var(--color-text-a30)] italic">
          No plugins installed.
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {plugins.map((plugin) => {
            const pluginActions = getPluginActions(plugin, {
              syncingDeDRM,
              onSyncDeDRM: onSyncDeDRMRequested,
            });

            return (
              <PluginCard
                key={plugin.name}
                plugin={plugin}
                installing={installing}
                primaryAction={pluginActions.primary}
                overflowActions={pluginActions.overflow}
                onRemove={handleRemove}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}

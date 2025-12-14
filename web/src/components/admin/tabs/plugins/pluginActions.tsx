import { FaSpinner, FaSync } from "react-icons/fa";
import type { PluginInfo } from "@/services/pluginService";

export interface PluginActionContext {
  syncingDeDRM: boolean;
  onSyncDeDRM: () => void;
}

export interface PluginPrimaryAction {
  label: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
}

export interface PluginOverflowAction {
  label: string;
  icon?: React.ReactNode | string;
  onClick: () => void;
  disabled?: boolean;
  tone?: "default" | "danger";
}

export interface PluginActions {
  /** At most one visible primary action to keep cards scannable. */
  primary?: PluginPrimaryAction;
  /** Additional non-primary actions that should appear in the overflow menu. */
  overflow: PluginOverflowAction[];
}

type PluginActionResolver = (
  plugin: PluginInfo,
  ctx: PluginActionContext,
) => PluginActions;

const pluginActionResolvers: Record<string, PluginActionResolver> = {
  DeDRM: (_plugin, ctx) => ({
    primary: {
      onClick: ctx.onSyncDeDRM,
      disabled: ctx.syncingDeDRM,
      label: ctx.syncingDeDRM ? (
        <>
          <FaSpinner className="animate-spin" />
          Syncing...
        </>
      ) : (
        <>
          <FaSync />
          Sync DeDRM Keys
        </>
      ),
    },
    overflow: [],
  }),
};

/**
 * Resolve plugin-specific actions for a plugin card.
 *
 * Adding new plugin-specific actions should only require updating this registry.
 */
export function getPluginActions(
  plugin: PluginInfo,
  ctx: PluginActionContext,
): PluginActions {
  return pluginActionResolvers[plugin.name]?.(plugin, ctx) ?? { overflow: [] };
}

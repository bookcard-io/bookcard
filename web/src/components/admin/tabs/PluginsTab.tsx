"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { FaGithub, FaSpinner, FaSync, FaTrash, FaUpload } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { TextInput } from "@/components/forms/TextInput";
import {
  installPluginGit,
  installPluginUpload,
  listPlugins,
  type PluginInfo,
  removePlugin,
  syncDeDRM,
} from "@/services/pluginService";

export function PluginsTab() {
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [installing, setInstalling] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [gitUrl, setGitUrl] = useState("");
  const [branch, setBranch] = useState("");
  const [subpath, setSubpath] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchPlugins = useCallback(async () => {
    try {
      setLoading(true);
      const data = await listPlugins();
      setPlugins(data);
    } catch (error) {
      console.error("Failed to fetch plugins", error);
      alert("Failed to fetch plugins.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPlugins();
  }, [fetchPlugins]);

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".zip")) {
      alert("Only ZIP files are supported.");
      return;
    }

    try {
      setInstalling(true);
      await installPluginUpload(file);
      alert("Plugin installed successfully!");
      fetchPlugins();
    } catch (error) {
      console.error("Failed to install plugin", error);
      alert(
        `Failed to install plugin: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    } finally {
      setInstalling(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleGitInstall = async () => {
    if (!gitUrl) {
      alert("Please enter a Git repository URL.");
      return;
    }

    try {
      setInstalling(true);
      await installPluginGit({
        repo_url: gitUrl,
        branch: branch || undefined,
        plugin_path: subpath || undefined,
      });
      alert("Plugin installed successfully!");
      setGitUrl("");
      setBranch("");
      setSubpath("");
      fetchPlugins();
    } catch (error) {
      console.error("Failed to install plugin from Git", error);
      alert(
        `Failed to install plugin: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    } finally {
      setInstalling(false);
    }
  };

  const handleRemove = async (pluginName: string) => {
    if (!confirm(`Are you sure you want to remove ${pluginName}?`)) {
      return;
    }

    try {
      setInstalling(true);
      await removePlugin(pluginName);
      alert("Plugin removed successfully!");
      fetchPlugins();
    } catch (error) {
      console.error("Failed to remove plugin", error);
      alert(
        `Failed to remove plugin: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    } finally {
      setInstalling(false);
    }
  };

  const handleSyncDeDRM = async () => {
    try {
      setSyncing(true);
      const res = await syncDeDRM();
      alert(res.message);
    } catch (error) {
      console.error("Failed to sync DeDRM", error);
      alert(
        `Failed to sync DeDRM: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Installation Section */}
      <div className="rounded-lg border border-[var(--color-surface-a20)] bg-[var(--color-surface-tonal-a0)] p-6">
        <h2 className="mb-4 font-semibold text-[var(--color-text-a0)] text-xl">
          Install Plugin
        </h2>

        <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
          {/* Upload */}
          <div className="flex flex-col gap-4">
            <h3 className="font-medium text-[var(--color-text-a10)]">
              Upload ZIP
            </h3>
            <p className="text-[var(--color-text-a30)] text-sm">
              Upload a plugin ZIP file directly from your computer.
            </p>
            <div className="flex items-center gap-2">
              <input
                type="file"
                ref={fileInputRef}
                accept=".zip"
                className="hidden"
                onChange={handleFileUpload}
              />
              <Button
                variant="primary"
                onClick={() => fileInputRef.current?.click()}
                disabled={installing}
              >
                {installing ? (
                  <>
                    <FaSpinner className="animate-spin" />
                    Installing...
                  </>
                ) : (
                  <>
                    <FaUpload />
                    Select File
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Git Install */}
          <div className="flex flex-col gap-4 border-[var(--color-surface-a20)] border-t pt-6 md:border-t-0 md:border-l md:pt-0 md:pl-8">
            <h3 className="font-medium text-[var(--color-text-a10)]">
              From Git Repository
            </h3>
            <p className="text-[var(--color-text-a30)] text-sm">
              Install directly from a Git repository (e.g. GitHub).
            </p>
            <div className="flex flex-col gap-3">
              <TextInput
                label="Repository URL"
                value={gitUrl}
                onChange={(e) => setGitUrl(e.target.value)}
                placeholder="https://github.com/user/repo"
              />
              <div className="flex gap-3">
                <div className="flex-1">
                  <TextInput
                    label="Branch/Tag (Optional)"
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    placeholder="main"
                  />
                </div>
                <div className="flex-1">
                  <TextInput
                    label="Subpath (Optional)"
                    value={subpath}
                    onChange={(e) => setSubpath(e.target.value)}
                    placeholder="DeDRM_plugin"
                  />
                </div>
              </div>
              <Button
                variant="secondary"
                onClick={handleGitInstall}
                disabled={installing || !gitUrl}
              >
                {installing ? (
                  <>
                    <FaSpinner className="animate-spin" />
                    Installing...
                  </>
                ) : (
                  <>
                    <FaGithub />
                    Install from Git
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Installed Plugins List */}
      <div className="rounded-lg border border-[var(--color-surface-a20)] bg-[var(--color-surface-tonal-a0)] p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-semibold text-[var(--color-text-a0)] text-xl">
            Installed Plugins
          </h2>
          <Button
            variant="secondary"
            size="small"
            onClick={handleSyncDeDRM}
            disabled={syncing}
          >
            {syncing ? (
              <>
                <FaSpinner className="animate-spin" />
                Syncing...
              </>
            ) : (
              <>
                <FaSync />
                Sync DeDRM Keys
              </>
            )}
          </Button>
        </div>

        {loading ? (
          <div className="text-[var(--color-text-a30)]">Loading plugins...</div>
        ) : plugins.length === 0 ? (
          <div className="text-[var(--color-text-a30)] italic">
            No plugins installed.
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {plugins.map((plugin) => (
              <div
                key={plugin.name}
                className="flex items-start justify-between rounded-md border border-[var(--color-surface-a10)] bg-[var(--color-surface-a0)] p-4"
              >
                <div>
                  <div className="flex items-baseline gap-2">
                    <h3 className="font-bold text-[var(--color-text-a0)]">
                      {plugin.name}
                    </h3>
                    <span className="text-[var(--color-text-a40)] text-xs">
                      v{plugin.version}
                    </span>
                  </div>
                  <div className="mb-1 text-[var(--color-text-a20)] text-sm">
                    by {plugin.author}
                  </div>
                  <p className="text-[var(--color-text-a30)] text-sm">
                    {plugin.description}
                  </p>
                </div>
                <Button
                  variant="danger"
                  size="small"
                  onClick={() => handleRemove(plugin.name)}
                  disabled={installing}
                  aria-label={`Remove ${plugin.name}`}
                >
                  <FaTrash />
                  Remove
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

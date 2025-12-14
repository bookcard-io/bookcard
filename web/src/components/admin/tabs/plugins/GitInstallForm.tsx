import { useState } from "react";
import { FaGithub, FaSpinner } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { TextInput } from "@/components/forms/TextInput";
import type { PluginInstallRequest } from "@/services/pluginService";
import { validateGitRepoUrl } from "@/utils/plugins/validation";

export interface GitInstallFormProps {
  installing: boolean;
  installFromGit: (request: PluginInstallRequest) => Promise<boolean>;
  showSuccess: (message: string) => void;
  showWarning: (message: string) => void;
  showDanger: (message: string) => void;
}

export function GitInstallForm({
  installing,
  installFromGit,
  showSuccess,
  showWarning,
  showDanger,
}: GitInstallFormProps): React.ReactElement {
  const [gitUrl, setGitUrl] = useState("");
  const [branch, setBranch] = useState("");
  const [subpath, setSubpath] = useState("");

  const handleGitInstall = async () => {
    const validationError = validateGitRepoUrl(gitUrl);
    if (validationError) {
      showWarning(validationError);
      return;
    }

    try {
      const ok = await installFromGit({
        repo_url: gitUrl.trim(),
        branch: branch.trim() || undefined,
        plugin_path: subpath.trim() || undefined,
      });

      if (ok) {
        showSuccess("Plugin installed successfully!");
        setGitUrl("");
        setBranch("");
        setSubpath("");
      }
    } catch (error) {
      console.error("Failed to install plugin from Git", error);
      showDanger(
        `Failed to install plugin: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    }
  };

  return (
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
              placeholder="e.g., master"
              helperText="The branch or tag to install the plugin from. If not provided, the default branch will be used."
            />
          </div>
          <div className="flex-1">
            <TextInput
              label="Subpath (Optional)"
              value={subpath}
              onChange={(e) => setSubpath(e.target.value)}
              placeholder="e.g., DeDRM_plugin"
              helperText="The folder on the repository containing the plugin. Omit to install from repository root."
            />
          </div>
        </div>
        <Button
          variant="secondary"
          onClick={handleGitInstall}
          disabled={installing || !gitUrl.trim()}
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
  );
}

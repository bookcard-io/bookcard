import type { PluginInstallRequest } from "@/services/pluginService";
import { GitInstallForm } from "./GitInstallForm";
import { PluginUploadForm } from "./PluginUploadForm";

export interface PluginInstallSectionProps {
  installing: boolean;
  installFromUpload: (file: File) => Promise<boolean>;
  installFromGit: (request: PluginInstallRequest) => Promise<boolean>;
  showSuccess: (message: string) => void;
  showWarning: (message: string) => void;
  showDanger: (message: string) => void;
}

export function PluginInstallSection({
  installing,
  installFromUpload,
  installFromGit,
  showSuccess,
  showWarning,
  showDanger,
}: PluginInstallSectionProps): React.ReactElement {
  return (
    <div className="rounded-lg border border-[var(--color-surface-a20)] bg-[var(--color-surface-tonal-a0)] p-6">
      <h2 className="mb-4 font-semibold text-[var(--color-text-a0)] text-xl">
        Install Plugin
      </h2>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        <PluginUploadForm
          installing={installing}
          installFromUpload={installFromUpload}
          showSuccess={showSuccess}
          showWarning={showWarning}
          showDanger={showDanger}
        />

        <GitInstallForm
          installing={installing}
          installFromGit={installFromGit}
          showSuccess={showSuccess}
          showWarning={showWarning}
          showDanger={showDanger}
        />
      </div>
    </div>
  );
}

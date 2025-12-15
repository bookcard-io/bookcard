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

import { PluginUploadForm } from "./PluginUploadForm";
import { UrlInstallForm } from "./UrlInstallForm";

export interface PluginInstallSectionProps {
  installing: boolean;
  installFromUpload: (file: File) => Promise<boolean>;
  installFromUrl: (url: string) => Promise<boolean>;
  showSuccess: (message: string) => void;
  showWarning: (message: string) => void;
  showDanger: (message: string) => void;
}

export function PluginInstallSection({
  installing,
  installFromUpload,
  installFromUrl,
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

        <UrlInstallForm
          installing={installing}
          installFromUrl={installFromUrl}
          showSuccess={showSuccess}
          showWarning={showWarning}
          showDanger={showDanger}
        />
      </div>
    </div>
  );
}

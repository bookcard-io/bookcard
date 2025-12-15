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

import { useState } from "react";
import { FaDownload, FaSpinner } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { TextInput } from "@/components/forms/TextInput";

export interface UrlInstallFormProps {
  installing: boolean;
  installFromUrl: (url: string) => Promise<boolean>;
  showSuccess: (message: string) => void;
  showWarning: (message: string) => void;
  showDanger: (message: string) => void;
}

export function UrlInstallForm({
  installing,
  installFromUrl,
  showSuccess,
  showWarning,
  showDanger,
}: UrlInstallFormProps): React.ReactElement {
  const [url, setUrl] = useState("");

  const handleUrlInstall = async () => {
    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      showWarning("Please enter a URL");
      return;
    }

    // Basic URL validation - just check if it looks like a URL
    try {
      new URL(trimmedUrl);
    } catch {
      showWarning("Please enter a valid URL");
      return;
    }

    try {
      const ok = await installFromUrl(trimmedUrl);

      if (ok) {
        showSuccess("Plugin installed successfully!");
        setUrl("");
      }
    } catch (error) {
      console.error("Failed to install plugin from URL", error);
      showDanger(
        `Failed to install plugin: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    }
  };

  return (
    <div className="flex flex-col gap-4 border-[var(--color-surface-a20)] border-t pt-6 md:border-t-0 md:border-l md:pt-0 md:pl-8">
      <h3 className="font-medium text-[var(--color-text-a10)]">From URL</h3>
      <p className="text-[var(--color-text-a30)] text-sm">
        Install a plugin by downloading a ZIP file from a URL.
      </p>
      <div className="flex flex-col gap-3">
        <TextInput
          label="ZIP File URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/plugin.zip"
          helperText="Enter the URL of a ZIP file containing the plugin."
        />
        <Button
          variant="secondary"
          onClick={handleUrlInstall}
          disabled={installing || !url.trim()}
        >
          {installing ? (
            <>
              <FaSpinner className="animate-spin" />
              Installing...
            </>
          ) : (
            <>
              <FaDownload />
              Install from URL
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

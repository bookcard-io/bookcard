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

import { useCallback, useState } from "react";
import type { FileImportStrategy } from "@/utils/importStrategies";

interface UseShelfImportProps {
  strategy: FileImportStrategy;
  onParseSuccess?: (data: { name?: string; description?: string }) => void;
  onError?: (error: unknown) => void;
  enabled?: boolean;
}

export const useShelfImport = ({
  strategy,
  onParseSuccess,
  onError,
  enabled = true,
}: UseShelfImportProps) => {
  const [importFile, setImportFile] = useState<File | null>(null);

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0] || null;
      setImportFile(selectedFile);

      if (!selectedFile) {
        return;
      }

      // If parsing is disabled (e.g. edit mode), we just set the file and return
      if (!enabled) {
        return;
      }

      try {
        const data = await strategy.parse(selectedFile);
        onParseSuccess?.(data);
      } catch (error) {
        setImportFile(null);
        onError?.(error);
      }
    },
    [strategy, onParseSuccess, onError, enabled],
  );

  const resetImport = useCallback(() => {
    setImportFile(null);
  }, []);

  return {
    importFile,
    setImportFile,
    handleFileChange,
    resetImport,
  };
};

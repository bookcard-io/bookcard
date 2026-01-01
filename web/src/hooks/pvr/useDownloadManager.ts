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
import { pvrSearchService } from "@/services/pvrSearchService";

export function useDownloadManager(trackedBookId: number, onClose: () => void) {
  const [downloadingIndex, setDownloadingIndex] = useState<number | null>(null);

  const handleDownload = async (index: number) => {
    setDownloadingIndex(index);
    try {
      await pvrSearchService.download(trackedBookId, { release_index: index });
      onClose();
    } catch (err) {
      console.error(err);
      // Ideally show a toast
    } finally {
      setDownloadingIndex(null);
    }
  };

  return { downloadingIndex, handleDownload };
}

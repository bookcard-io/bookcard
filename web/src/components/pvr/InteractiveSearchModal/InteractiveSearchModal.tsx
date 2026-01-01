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

import { useDownloadManager } from "@/hooks/pvr/useDownloadManager";
import { useSearchResults } from "@/hooks/pvr/useSearchResults";
import { useTableSort } from "@/hooks/pvr/useTableSort";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { renderModalPortal } from "@/utils/modal";
import { SearchModalView } from "./SearchModalView";

interface InteractiveSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  trackedBookId: number;
  bookTitle: string;
  bookYear?: string;
}

export function InteractiveSearchModal({
  isOpen,
  onClose,
  trackedBookId,
  bookTitle,
  bookYear,
}: InteractiveSearchModalProps) {
  useModal(isOpen);
  const { handleOverlayClick, handleModalClick, handleOverlayKeyDown } =
    useModalInteractions({ onClose });

  const { results, isLoading, error, refetch } = useSearchResults(
    trackedBookId,
    isOpen,
  );
  const { sortedResults, sortConfig, handleSort } = useTableSort(results);
  const { handleDownload, downloadingIndex } = useDownloadManager(
    trackedBookId,
    onClose,
  );

  if (!isOpen) return null;

  return renderModalPortal(
    <SearchModalView
      onClose={onClose}
      bookTitle={bookTitle}
      bookYear={bookYear}
      isLoading={isLoading}
      resultsCount={results.length}
      error={error}
      onRetry={() => refetch(true)}
      sortedResults={sortedResults}
      sortConfig={sortConfig}
      onSort={handleSort}
      onDownload={handleDownload}
      downloadingIndex={downloadingIndex}
      onOverlayClick={handleOverlayClick}
      onOverlayKeyDown={handleOverlayKeyDown}
      onModalClick={handleModalClick}
    />,
  );
}

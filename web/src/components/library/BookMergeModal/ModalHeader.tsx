// Copyright (C) 2026 knguyen and others
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

export function ModalHeader({ onClose }: { onClose: () => void }) {
  return (
    <div className="flex items-center justify-between border-surface-a20 border-b p-6">
      <h2
        id="merge-modal-title"
        className="m-0 font-semibold text-[var(--color-text-a0)] text-xl"
      >
        Merge Books
      </h2>
      <button
        type="button"
        onClick={onClose}
        className="flex h-8 w-8 items-center justify-center rounded-md text-text-a30 transition-colors hover:bg-surface-a10 hover:text-text-a0 focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2"
        aria-label="Close"
      >
        <i className="pi pi-times" aria-hidden="true" />
      </button>
    </div>
  );
}

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

"use client";

import { useState } from "react";
import { Button } from "@/components/forms/Button";
import { useShelves } from "@/hooks/useShelves";
import type { ShelfCreate, ShelfUpdate } from "@/types/shelf";
import { ShelfCard } from "./ShelfCard";
import { ShelfEditModal } from "./ShelfEditModal";

/**
 * Shelf list component.
 *
 * Displays a list of shelves with the ability to create new ones.
 */
export function ShelfList() {
  const { shelves, isLoading, error, createShelf, updateShelf } = useShelves();
  const [editingShelf, setEditingShelf] = useState<number | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const handleCreate = async (data: ShelfCreate | ShelfUpdate) => {
    await createShelf(data as ShelfCreate);
    setShowCreateModal(false);
  };

  const handleEdit = async (data: ShelfCreate | ShelfUpdate) => {
    if (editingShelf !== null) {
      await updateShelf(editingShelf, data as ShelfUpdate);
      setEditingShelf(null);
    }
  };

  if (isLoading) {
    return <div className="p-4">Loading shelves...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-600">Error: {error}</div>;
  }

  return (
    <div className="p-4">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="font-bold text-2xl">Shelves</h1>
        <Button onClick={() => setShowCreateModal(true)}>Create Shelf</Button>
      </div>

      {shelves.length === 0 ? (
        <p className="text-gray-600">
          No shelves yet. Create one to get started!
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {shelves.map((shelf) => (
            <ShelfCard key={shelf.id} shelf={shelf} />
          ))}
        </div>
      )}

      {showCreateModal && (
        <ShelfEditModal
          shelf={null}
          onClose={() => setShowCreateModal(false)}
          onSave={handleCreate}
        />
      )}

      {editingShelf !== null && (
        <ShelfEditModal
          shelf={shelves.find((s) => s.id === editingShelf) ?? null}
          onClose={() => setEditingShelf(null)}
          onSave={handleEdit}
        />
      )}
    </div>
  );
}

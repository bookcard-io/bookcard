import { useState } from "react";

export function useBookCardModals() {
  const [showAddToShelfModal, setShowAddToShelfModal] = useState(false);

  const openAddToShelf = () => setShowAddToShelfModal(true);
  const closeAddToShelf = () => setShowAddToShelfModal(false);

  return {
    showAddToShelfModal,
    openAddToShelf,
    closeAddToShelf,
  };
}

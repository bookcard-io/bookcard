import { ConversionModal } from "@/components/books/ConversionModal";
import { DeleteBookConfirmationModal } from "@/components/books/DeleteBookConfirmationModal";
import { AddToShelfModal } from "@/components/library/AddToShelfModal";
import { ShelfEditModal } from "@/components/shelves/ShelfEditModal";
import type { CreateShelfOptions } from "@/services/shelfService";
import type { Book } from "@/types/book";
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";

interface DeleteState {
  isOpen: boolean;
  dontShowAgain: boolean;
  deleteFilesFromDrive: boolean;
  close: () => void;
  toggleDontShowAgain: () => void;
  toggleDeleteFilesFromDrive: () => void;
  confirm: () => void;
  isDeleting: boolean;
  error: string | null;
}

interface ShelfState {
  showCreateModal: boolean;
  closeCreateModal: () => void;
  handleCreateShelf: (
    data: ShelfCreate | ShelfUpdate,
    options?: CreateShelfOptions,
  ) => Promise<Shelf>;
}

interface AddToShelfState {
  show: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface ConversionState {
  isOpen: boolean;
  close: () => void;
}

export interface BookCardModalsProps {
  book: Book;
  deleteState: DeleteState;
  shelfState: ShelfState;
  addToShelfState: AddToShelfState;
  conversionState: ConversionState;
}

export function BookCardModals({
  book,
  deleteState,
  shelfState,
  addToShelfState,
  conversionState,
}: BookCardModalsProps) {
  return (
    <>
      <DeleteBookConfirmationModal
        isOpen={deleteState.isOpen}
        dontShowAgain={deleteState.dontShowAgain}
        deleteFilesFromDrive={deleteState.deleteFilesFromDrive}
        onClose={deleteState.close}
        onToggleDontShowAgain={deleteState.toggleDontShowAgain}
        onToggleDeleteFilesFromDrive={deleteState.toggleDeleteFilesFromDrive}
        onConfirm={deleteState.confirm}
        bookTitle={book.title}
        book={book}
        isDeleting={deleteState.isDeleting}
        error={deleteState.error}
      />
      {shelfState.showCreateModal && (
        <ShelfEditModal
          shelf={null}
          onClose={shelfState.closeCreateModal}
          onSave={shelfState.handleCreateShelf}
        />
      )}
      {addToShelfState.show && (
        <AddToShelfModal
          books={[book]}
          onClose={addToShelfState.onClose}
          onSuccess={addToShelfState.onSuccess}
        />
      )}
      <ConversionModal
        book={book}
        isOpen={conversionState.isOpen}
        onClose={conversionState.close}
      />
    </>
  );
}

import type { Book } from "@/types/book";
import { BookCardCheckbox } from "./BookCardCheckbox";
import { BookCardEditButton } from "./BookCardEditButton";
import {
  BookCardMenuButton,
  type BookCardMenuButtonProps,
} from "./BookCardMenuButton";

export interface BookCardActionsProps {
  book: Book;
  allBooks: Book[];
  selected: boolean;
  showSelection: boolean;
  onEdit?: (bookId: number) => void;
  menuProps: BookCardMenuButtonProps;
  variant?: "desktop" | "mobile";
  showMenu?: boolean;
}

export function BookCardActions({
  variant = "desktop",
  ...props
}: BookCardActionsProps) {
  return (
    <>
      {props.showSelection && (
        <BookCardCheckbox
          book={props.book}
          allBooks={props.allBooks}
          selected={props.selected}
          variant={variant === "mobile" ? "mobile" : undefined}
        />
      )}
      {props.onEdit && (
        <BookCardEditButton
          bookTitle={props.book.title}
          onEdit={() => props.onEdit?.(props.book.id)}
          variant={variant === "mobile" ? "mobile" : undefined}
        />
      )}
      {props.showMenu !== false && (
        <BookCardMenuButton
          {...props.menuProps}
          variant={variant === "mobile" ? "mobile" : undefined}
        />
      )}
    </>
  );
}

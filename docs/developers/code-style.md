# Code Style Guidelines

## Python

### PEP 8 Compliance

Follow [PEP 8](https://pep8.org/) style guidelines for Python code.

**Key points:**
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 88 characters (Black default)
- Use meaningful variable and function names
- Import statements should be organized (standard library, third-party, local)

**Example:**

```python
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from bookcard.models.core import Book
from bookcard.repositories.book_repository import BookRepository


def get_book_by_id(
    book_id: int,
    repository: BookRepository = Depends(),
) -> Optional[Book]:
    """
    Retrieve a book by its ID.

    Parameters
    ----------
    book_id : int
        The unique identifier of the book.
    repository : BookRepository, optional
        The book repository instance, by default Depends().

    Returns
    -------
    Optional[Book]
        The book if found, None otherwise.
    """
    return repository.get_by_id(book_id)
```

### Docstrings

Use numpy-style docstrings for all public methods and classes.

**Example:**

```python
class BookService:
    """
    Service for managing book operations.

    This service provides high-level operations for book management,
    including creation, retrieval, and updates.
    """

    def create_book(
        self,
        title: str,
        author: str,
        isbn: Optional[str] = None,
    ) -> Book:
        """
        Create a new book record.

        Parameters
        ----------
        title : str
            The title of the book.
        author : str
            The author of the book.
        isbn : Optional[str], optional
            The ISBN of the book, by default None.

        Returns
        -------
        Book
            The newly created book instance.

        Raises
        ------
        ValueError
            If title or author is empty.
        """
        if not title or not author:
            raise ValueError("Title and author are required")
        # ... implementation
```

### Type Hints

Type hints are required for all public APIs.

**Example:**

```python
from typing import List, Optional, Dict, Any

def process_books(
    books: List[Book],
    filters: Optional[Dict[str, Any]] = None,
) -> List[Book]:
    """
    Process a list of books with optional filters.

    Parameters
    ----------
    books : List[Book]
        List of books to process.
    filters : Optional[Dict[str, Any]], optional
        Optional filters to apply, by default None.

    Returns
    -------
    List[Book]
        Processed list of books.
    """
    # ... implementation
```

### Exception Handling

- Do not catch blind exceptions
- Always analyze underlying calls for specific exceptions
- Use `contextlib.suppress` for `try...except...pass` patterns

**Example:**

```python
from contextlib import suppress
import os

# Good: Using suppress for specific exceptions
with suppress(FileNotFoundError):
    os.remove("temp_file.txt")

# Good: Catching specific exceptions
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
except KeyError as e:
    logger.error(f"Missing key: {e}")
    raise

# Bad: Catching all exceptions
try:
    result = risky_operation()
except:  # noqa: E722
    pass
```

### Code Formatting

Run `ruff` for linting and formatting:

```bash
make formatpy  # Format Python code
```

## TypeScript/JavaScript

### General Guidelines

- Follow project ESLint rules
- Use TypeScript for new code
- Prefer functional components in React
- Use meaningful variable and function names

**Example:**

```typescript
interface Book {
  id: number;
  title: string;
  author: string;
  isbn?: string;
}

async function fetchBookById(id: number): Promise<Book | null> {
  try {
    const response = await fetch(`/api/books/${id}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch book: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching book:", error);
    return null;
  }
}
```

### React Components

**Example:**

```typescript
import { useState, useEffect } from "react";

interface BookCardProps {
  book: Book;
  onSelect?: (book: Book) => void;
}

export function BookCard({ book, onSelect }: BookCardProps) {
  const [isSelected, setIsSelected] = useState(false);

  useEffect(() => {
    // Component initialization logic
  }, []);

  const handleClick = () => {
    setIsSelected(!isSelected);
    onSelect?.(book);
  };

  return (
    <div onClick={handleClick} className={isSelected ? "selected" : ""}>
      <h3>{book.title}</h3>
      <p>{book.author}</p>
    </div>
  );
}
```

### Code Formatting

Run linting and formatting:

```bash
make formatjs  # Format JS/TS code
```

Or manually in the `web/` directory:

```bash
cd web
npm run lint:fix
npm run check:types
```

## Design Principles

When implementing new methods, always adhere to:

- **DRY (Don't Repeat Yourself)**: Avoid code duplication
- **SRP (Single Responsibility Principle)**: Each function/class should have one responsibility
- **SOC (Separation of Concerns)**: Separate different aspects of the application
- **IOC (Inversion of Control)**: Use dependency injection
- **KISS (Keep It Simple, Stupid)**: Prefer simple solutions over complex ones

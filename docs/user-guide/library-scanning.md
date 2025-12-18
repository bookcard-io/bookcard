# Library Scanning

Library Scanning is an advanced background process in Bookcard that enriches your library by linking your local content to authoritative external databases.

## What is it?

While "Fetching Metadata" works on a per-book basis to update title, cover, and description, **Library Scanning** works at a library-wide level. It focuses on establishing permanent links between your authors/books and their corresponding records in a global book database.

## Data Providers

Bookcard currently supports the following providers for library scanning:

-   **Hardcover:** A privacy-focused, community-driven book database. This is the primary provider for high-quality author and series data.
-   **Open Library:** An open, editable library catalog.

## How to Use

1.  Navigate to **Settings** > **Admin** > **Libraries**.
2.  Find the library you want to scan in the library list.
3.  Click the **Scan** button next to the library name.

This will trigger the background scanning process. You can view the progress and status in the **Tasks** section of the admin dashboard.

> **Note:** Library scanning is a resource-intensive process, especially for large libraries. It runs in the background to avoid blocking the user interface.

## How it Works

The scanning process runs in a pipeline with several stages:

1.  **Crawl:** The scanner reads your local library to identify authors and books.
2.  **Match:** It searches the external provider (e.g., Hardcover) to find matching records. It uses fuzzy matching algorithms to handle slight spelling variations or formatting differences (e.g., "J.R.R. Tolkien" vs "J. R. R. Tolkien").
3.  **Link:** When a confident match is found, Bookcard creates a "linkage." This connects your local author ID to the external provider's Author ID (e.g., Hardcover ID).
4.  **Enrich:** Once linked, Bookcard can pull in rich metadata that might be missing from your files, such as:
    -   Author birth and death dates
    -   Author biographies
    -   Complete series lists and correct reading orders
    -   Official book summaries

## Benefits

-   **Unified Authors:** If you have books by "Stephen King" and "Steve King," linking them both to the same external ID allows Bookcard to treat them as the same person in certain views.
-   **Better Metadata:** Get access to high-quality data that isn't typically stored in ebook files, like author photos and biographies.
-   **Future-Proofing:** These links enable advanced features like reading challenges, social sharing, and recommendations based on verified book data.

# Fetching Metadata

Bookcard allows you to enrich your library by fetching high-quality metadata and covers from external providers.

## How It Works

![Fetch Metadata Screen](../screenshots/fetch_metadata_screen.png){ width="400" }

When editing a book, you can click the **Fetch metadata** button in the header. This opens a modal where you can:

1.  **Search:** Bookcard automatically searches using the book's title and author, but you can refine the query manually.
2.  **Review Results:** Results from configured providers (e.g., Google Books, Open Library) are displayed in real-time.
3.  **Import:** Click on a result to expand it. You can then selectively choose which fields to import (e.g., Title, Author, Description, Publisher, Tags, Cover) using checkboxes.

## Providers

Metadata providers are external services that Bookcard queries to find information about your books.

### Managing Providers

You can configure which providers to use in your user profile settings under **Metadata Providers**.

-   **Preferred Providers:** Select your favorite sources. Bookcard will prioritize results from these providers.
-   **Enabled/Disabled:** You can enable or disable specific providers if you find their results irrelevant or if you don't have an API key (for providers that require one).

Common supported providers include:

-   **Google Books:** Extensive database for general books.
-   **Open Library:** Open, editable library catalog.
-   **Comic Vine:** Specialized for comics and graphic novels (requires API key).
-   **Amazon:** Good for covers and commercial metadata.
-   **Hardcover:** Community-driven book database.
-   **Google Scholar:** Academic publications and papers.
-   **Douban:** Popular Chinese book database.
-   **Lubimyczytac:** Popular Polish book database.

By tailoring your provider list, you can ensure the search results are relevant to the types of books in your library.

# Ingestion Configuration

This section explains how to configure automatic book ingestion. These settings control how Bookcard monitors a folder for new books and processes them into your library.

Navigate to **Settings > Admin > Configuration > Ingestion Configuration**.

## Basic Settings

-   **Watch Directory:** The absolute path on the server where Bookcard should look for new files. Any supported book files dropped into this folder (or its subfolders) will be automatically processed.
-   **Enable Ingest:** Master switch to turn the automatic ingestion process on or off.

## Metadata Settings

-   **Enable Metadata Fetch:** When enabled, Bookcard will attempt to fetch metadata (title, author, cover, description) from external providers for each ingested book.
-   **Merge Strategy:** Controls how new metadata is combined with existing metadata or multiple results.
        -   **Merge Best:** Smartly combines data, prioritizing longer descriptions and higher-resolution covers.
        -   **First Wins:** Uses the first result found; ignores others.
        -   **Last Wins:** Uses the last result found; overwrites previous ones.
        -   **Merge All:** Combines all data (e.g., appends all found tags).
-   **Metadata Providers:** Select which external services to query during ingestion (e.g., Google Books, Open Library). Deselecting providers can speed up ingestion if you don't need them.

## Retry Settings

These settings control how the background worker handles failures (e.g., network issues during metadata fetch).

-   **Max Retry Attempts:** How many times to retry a failed task before giving up.
-   **Backoff Seconds:** How long to wait between retries (increases exponentially).
-   **Process Timeout:** Maximum time (in seconds) allowed for processing a single book before it's considered "stuck" and cancelled.

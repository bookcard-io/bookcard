# Book Card Interface

The Book Card is the primary way you interact with books in your library. It provides a quick overview of the book and access to common actions.

![Book Card Interface](../screenshots/book_card_item.png){ width="300" }

## Reading Status

The top-right corner of the book card serves as a reading status indicator and control:

-   **Ribbon:** A "READ" ribbon indicates the book has been marked as finished.
-   **Bookmark:** A bookmark icon with a percentage shows your current reading progress (if you've started reading).
-   **Toggle:** Hovering over this area on an unread book allows you to quickly mark it as read by clicking the bookmark icon.

## Context Menu

Clicking the **More options** (three dots) button on a book card opens a menu with several actions:

### Book Info
Opens the detailed view of the book, showing metadata, description, and file information.

### Send to...
Allows you to send the book file to your e-reader device via email.

-   **Default Device:** If configured, your default device appears at the top for one-click sending.
-   **Other Devices:** Lists other configured devices from your profile.
-   **Send to Email:** Allows manually entering an email address to send the book to.

### Move to Library (Admin)
Allows administrators to move the book to a different library managed by Bookcard.

### Add to...
Manage the book's shelf assignments.

-   **Add to shelf...:** Opens a dialog to select or create shelves.
-   **Recent Shelves:** Quickly add the book to shelves you've recently used.

### Convert Format
Convert the book's file format (e.g., from EPUB to AZW3). This is useful for compatibility with certain e-readers.

### Delete
Permanently removes the book and its files from the library.

### More...
Contains advanced or less common actions:

-   **Strip DRM if present:** triggers a background task to attempt removing DRM from the book file (requires the DeDRM plugin to be configured).

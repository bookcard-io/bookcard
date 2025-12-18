# Managing Devices

You can manage your e-reader devices (like Kindles, Kobos, Nooks) in your user profile. This provides two key features: sending books via email and automated DRM removal.

## Sending to Email

If your device supports receiving books via email (e.g., "Send to Kindle"), you can add your device's email address here.

1.  Go to your **Profile**.
2.  Scroll down to the **My Devices** section.
3.  Click **Add Device**.
4.  Enter a name (e.g., "My Kindle") and the device's email address (e.g., `kindle_name@kindle.com`).

Once added, you will see a "Send to Device" option when viewing book details.

> **Note:** An administrator must first configure the email server settings in **Settings > Admin > Email** for this feature to work.

## DeDRM Integration

If you use the [DeDRM plugin](https://github.com/noDRM/DeDRM_tools) to remove DRM from your legally purchased ebooks, Bookcard can automatically sync your device serial numbers to the plugin configuration.

### How to Use

1.  When adding or editing a device in Bookcard, enter your device's **Serial Number**.
2.  Bookcard will automatically sync this serial number to the `dedrm.json` configuration file used by the backend.
3.  When you import a book that is locked to that device's serial number, the DeDRM plugin will use the synced configuration to unlock it automatically.

### Installation & Configuration

For this to work, the DeDRM plugin must be installed and accessible:

1.  **Install Plugin:** Administrators can install the plugin via **Settings > Admin > Plugins**. You can upload the plugin file directly or install from a URL. The file must be a zip file.

    ![Plugin Install Screen](../screenshots/plugin_install_screen.png){ width="600" }

2.  **Configuration Path:** The backend needs access to the Calibre configuration directory. This is typically configured via Docker volume mounts:
    -   **Docker Volume:** `/path/to/calibre/config:/home/appuser/.config/calibre`
    -   **File Location:** The synced configuration will be stored at `.../plugins/dedrm.json`.

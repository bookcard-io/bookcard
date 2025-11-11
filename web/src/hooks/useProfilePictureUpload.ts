import { useFileDropzone } from "./useFileDropzone";

export interface ProfilePictureUploadOptions {
  /**
   * Callback function called when a profile picture is selected.
   * Currently a no-op - backend not wired to accept profile picture uploads.
   */
  onPictureSelect?: (file: File) => void;
}

/**
 * Custom hook for profile picture upload functionality.
 *
 * Wraps useFileDropzone with profile picture-specific configuration.
 * Follows SRP by handling only profile picture upload concerns.
 * Follows IOC by accepting callback for file processing.
 *
 * Parameters
 * ----------
 * options : ProfilePictureUploadOptions
 *     Configuration options for profile picture upload.
 *
 * Returns
 * -------
 * ReturnType<typeof useFileDropzone>
 *     File dropzone hook return value with profile picture configuration.
 */
export function useProfilePictureUpload(
  options: ProfilePictureUploadOptions = {},
) {
  const { onPictureSelect } = options;

  const handleFileSelect = (file: File) => {
    // TODO: Wire profile picture upload to frontend and backend
    // - Validate file type and size
    // - Upload to backend API endpoint
    // - Update user profile with new picture path
    // - Refresh profile data
    console.log("Profile picture selected:", file.name);

    if (onPictureSelect) {
      onPictureSelect(file);
    }
  };

  return useFileDropzone({
    onFileSelect: handleFileSelect,
    accept: "image/jpeg,image/jpg,image/png,image/gif,image/webp,image/svg+xml",
    filterImages: true,
  });
}

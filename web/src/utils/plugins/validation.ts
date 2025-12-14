/**
 * Validate a plugin ZIP file selected by the user.
 *
 * Parameters
 * ----------
 * file : File
 *     File selected in the file picker.
 *
 * Returns
 * -------
 * string | null
 *     Validation error message if invalid; otherwise null.
 */
export function validatePluginZipFile(file: File): string | null {
  if (!file.name.toLowerCase().endsWith(".zip")) {
    return "Only ZIP files are supported.";
  }

  return null;
}

/**
 * Validate a git repository URL.
 *
 * Parameters
 * ----------
 * repoUrl : string
 *     Repository URL input.
 *
 * Returns
 * -------
 * string | null
 *     Validation error message if invalid; otherwise null.
 */
export function validateGitRepoUrl(repoUrl: string): string | null {
  const trimmed = repoUrl.trim();
  if (!trimmed) {
    return "Please enter a Git repository URL.";
  }

  try {
    // Accept any valid absolute URL; backend will do deeper validation.
    // eslint-disable-next-line no-new
    new URL(trimmed);
  } catch {
    return "Please enter a valid repository URL.";
  }

  return null;
}

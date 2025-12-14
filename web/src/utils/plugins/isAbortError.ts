/**
 * Check whether an error represents an aborted request.
 *
 * Parameters
 * ----------
 * error : unknown
 *     Error value thrown by an async operation.
 *
 * Returns
 * -------
 * bool
 *     True if the error indicates an abort/cancellation.
 */
export function isAbortError(error: unknown): boolean {
  if (error instanceof DOMException) {
    return error.name === "AbortError";
  }

  if (error instanceof Error) {
    return error.name === "AbortError";
  }

  return false;
}

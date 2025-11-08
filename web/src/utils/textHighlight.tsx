import type React from "react";

/**
 * Highlight matching text in a string (case-insensitive).
 *
 * Parameters
 * ----------
 * text : str
 *     The text to highlight.
 * query : str
 *     The search query to highlight.
 * highlightClassName : str | undefined
 *     CSS class name for the highlight span (optional).
 *
 * Returns
 * -------
 * React.ReactNode
 *     JSX with highlighted text.
 */
export function highlightText(
  text: string,
  query: string,
  highlightClassName?: string,
): React.ReactNode {
  if (!query.trim()) {
    return text;
  }

  const queryLower = query.toLowerCase();
  const textLower = text.toLowerCase();
  const index = textLower.indexOf(queryLower);

  if (index === -1) {
    return text;
  }

  // Use the original text for the match to preserve case
  const before = text.slice(0, index);
  const match = text.slice(index, index + query.length);
  const after = text.slice(index + query.length);

  return (
    <>
      {before}
      <span className={highlightClassName || ""}>{match}</span>
      {after}
    </>
  );
}

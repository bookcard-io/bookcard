import { useEffect, useState } from "react";

export function usePathSuggestions(query: string) {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [show, setShow] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setSuggestions([]);
      setShow(false);
      setSelectedIndex(-1);
      return;
    }
    let active = true;
    const controller = new AbortController();
    const id = window.setTimeout(async () => {
      try {
        const response = await fetch(
          `/api/fs/suggest_dirs?q=${encodeURIComponent(q)}&limit=50`,
          { cache: "no-store", signal: controller.signal },
        );
        if (!response.ok) return;
        const data = (await response.json()) as { suggestions?: string[] };
        if (active) {
          const suggestionsList = Array.isArray(data?.suggestions)
            ? data.suggestions
            : [];
          setSuggestions(suggestionsList);
          setShow(suggestionsList.length > 0);
          setSelectedIndex(-1);
        }
      } catch {
        // Ignore suggest errors
      }
    }, 300);
    return () => {
      active = false;
      controller.abort();
      window.clearTimeout(id);
    };
  }, [query]);

  return {
    suggestions,
    show,
    setShow,
    selectedIndex,
    setSelectedIndex,
  } as const;
}

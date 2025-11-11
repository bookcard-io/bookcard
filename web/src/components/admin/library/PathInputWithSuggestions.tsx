"use client";

import { useCallback, useEffect, useState } from "react";
import { cn } from "@/libs/utils";

type Props = {
  value: string;
  onChange: (val: string) => void;
  onSubmit: () => void;
  busy?: boolean;
};

export function PathInputWithSuggestions({
  value,
  onChange,
  onSubmit,
  busy,
}: Props) {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [show, setShow] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const [hoveredIndex, setHoveredIndex] = useState<number>(-1);

  useEffect(() => {
    const q = value.trim();
    if (q.length < 2) {
      setSuggestions([]);
      setShow(false);
      setSelectedIndex(-1);
      setHoveredIndex(-1);
      return;
    }

    let active = true;
    const controller = new AbortController();
    const id = window.setTimeout(async () => {
      try {
        const response = await fetch(
          `/api/fs/suggest_dirs?q=${encodeURIComponent(q)}&limit=50`,
          {
            cache: "no-store",
            signal: controller.signal,
          },
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
          setHoveredIndex(-1);
        }
      } catch {
        // ignore suggest errors
      }
    }, 300);

    return () => {
      active = false;
      controller.abort();
      window.clearTimeout(id);
    };
  }, [value]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        if (show && suggestions.length > 0 && selectedIndex >= 0) {
          e.preventDefault();
          const chosen = suggestions[selectedIndex] ?? value;
          onChange(chosen);
          setShow(false);
        } else {
          onSubmit();
        }
      } else if (e.key === "Tab" && show && suggestions.length > 0) {
        e.preventDefault();
        const chosen =
          (selectedIndex >= 0 ? suggestions[selectedIndex] : suggestions[0]) ??
          value;
        onChange(chosen);
        setShow(false);
      } else if (
        (e.key === "ArrowDown" || e.key === "Down") &&
        show &&
        suggestions.length > 0
      ) {
        e.preventDefault();
        setSelectedIndex((prev) => {
          const count = suggestions.length;
          const next = prev < 0 ? 0 : (prev + 1) % count;
          return next;
        });
      } else if (
        (e.key === "ArrowUp" || e.key === "Up") &&
        show &&
        suggestions.length > 0
      ) {
        e.preventDefault();
        setSelectedIndex((prev) => {
          const count = suggestions.length;
          if (prev < 0) return count - 1;
          return prev === 0 ? count - 1 : prev - 1;
        });
      }
    },
    [onSubmit, onChange, selectedIndex, show, suggestions, value],
  );

  return (
    <div className="relative min-w-0 flex-1">
      <input
        type="text"
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setSelectedIndex(-1);
        }}
        placeholder="Enter path, e.g. /home/user/Calibre Library"
        onKeyDown={handleKeyDown}
        onFocus={() => setShow(suggestions.length > 0)}
        onBlur={() => setShow(false)}
        disabled={!!busy}
        className={cn(
          "w-full bg-surface-a10 px-3 py-2.5 text-sm text-text-a0",
          "rounded-md border border-[var(--color-surface-a20)]",
          "transition-colors duration-200",
          "focus:border-[var(--color-primary-a0)] focus:outline-none",
          "disabled:cursor-not-allowed disabled:opacity-70",
        )}
      />
      {show && suggestions.length > 0 && (
        <div
          className={cn(
            "absolute top-[calc(100%+4px)] right-0 left-0 z-10",
            "max-h-[240px] overflow-y-auto",
            "rounded-md border border-[var(--color-surface-a20)] bg-surface-a0",
            "shadow-[0_4px_16px_rgba(0,0,0,0.3)]",
          )}
        >
          {suggestions.map((s, idx) => (
            <button
              key={s}
              type="button"
              onMouseDown={(e) => {
                e.preventDefault();
                onChange(s);
                setShow(false);
              }}
              onMouseEnter={() => setHoveredIndex(idx)}
              onMouseLeave={() => setHoveredIndex(-1)}
              className={cn(
                "block w-full bg-transparent px-3 py-2 text-text-a0",
                "border-0 border-[var(--color-surface-a20)] border-b",
                "cursor-pointer select-none text-left text-sm",
                "transition-colors duration-150",
                (idx === hoveredIndex || idx === selectedIndex) &&
                  "bg-surface-tonal-a0",
                idx === suggestions.length - 1 && "border-b-0",
              )}
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

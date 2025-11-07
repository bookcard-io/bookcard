"use client";

import type React from "react";
import { Search } from "@/icons/Search";
import styles from "./SearchInput.module.scss";

export interface SearchInputProps {
  /**
   * Placeholder text for the search input.
   */
  placeholder?: string;
  /**
   * Current search value.
   */
  value?: string;
  /**
   * Callback fired when the search value changes.
   */
  onChange?: (value: string) => void;
  /**
   * Callback fired when the search input is submitted.
   */
  onSubmit?: (value: string) => void;
}

/**
 * Search input component with integrated search icon.
 *
 * Provides a text input field for searching books, tags, and genres.
 */
export function SearchInput({
  placeholder = "Search books, tags & genres",
  value = "",
  onChange,
  onSubmit,
}: SearchInputProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange?.(e.target.value);
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSubmit?.(value);
  };

  return (
    <form className={styles.searchForm} onSubmit={handleSubmit}>
      <div className={styles.searchContainer}>
        <Search className={styles.searchIcon} aria-hidden="true" />
        <input
          type="text"
          className={styles.searchInput}
          placeholder={placeholder}
          value={value}
          onChange={handleChange}
          aria-label="Search books, tags & genres"
        />
      </div>
    </form>
  );
}

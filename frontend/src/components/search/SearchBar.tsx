/**
 * SearchBar — the main input for product descriptions.
 *
 * A simple search input with a submit button. The user types a product
 * description (e.g., "cotton t-shirts from China") and hits Enter or
 * clicks the search icon.
 *
 * This component is "controlled" — the parent (SearchPage) owns the
 * input value and handles submission via callbacks.
 */

import { Search, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
  placeholder?: string;
}

export function SearchBar({
  value,
  onChange,
  onSubmit,
  isLoading,
  placeholder = "Describe a product (e.g., 'cotton knitted t-shirts from China')",
}: SearchBarProps) {
  function handleKeyDown(e: React.KeyboardEvent) {
    // Submit on Enter (but not Shift+Enter, in case we add multiline later)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !isLoading) onSubmit();
    }
  }

  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={isLoading}
        className={cn(
          "w-full rounded-xl border bg-background px-4 py-3 pr-12",
          "text-base placeholder:text-muted-foreground",
          "focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "transition-shadow"
        )}
        data-testid="search-input"
      />

      {/* Search / Loading button (positioned inside the input, right side) */}
      <button
        onClick={onSubmit}
        disabled={!value.trim() || isLoading}
        className={cn(
          "absolute right-2 top-1/2 -translate-y-1/2",
          "p-2 rounded-lg",
          "text-muted-foreground hover:text-primary hover:bg-accent",
          "disabled:opacity-30 disabled:cursor-not-allowed",
          "transition-colors"
        )}
        data-testid="search-button"
        aria-label={isLoading ? "Searching..." : "Search"}
      >
        {isLoading ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <Search className="w-5 h-5" />
        )}
      </button>
    </div>
  );
}
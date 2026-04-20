/**
 * SearchPage — the main page for single-product classification.
 *
 * This is where most users spend their time. The flow:
 *   1. User types a product description in the SearchBar
 *   2. Results appear as a ranked list of HTS codes
 *   3. If results are ambiguous, the RefinementPanel helps narrow them down
 *
 * State management is handled by TanStack Query (useClassify hook),
 * not manual useState. The hook gives us loading, error, and data
 * states automatically.
 *
 * Compare this to v1's App.jsx which had 10+ useState hooks and ~60 lines
 * of fetch/error/loading logic. This page is ~80 lines total.
 */

import { useState } from "react";
import { SearchBar } from "@/components/search/SearchBar";
import { RefinementPanel } from "@/components/search/RefinementPanel";
import { ResultsList } from "@/components/results/ResultsList";
import { useClassify } from "@/api/hooks";

// Example queries shown as quick-start buttons when the page is empty
const EXAMPLES = [
  "Cotton knitted t-shirts from China",
  "Stainless steel bolts for industrial use",
  "Fresh Arabica coffee beans",
  "Laptop computers with touchscreen",
];

export function SearchPage() {
  // --- Local state (just the input values) ---
  const [query, setQuery] = useState("");
  const [refinements, setRefinements] = useState({
    material: "",
    intended_use: "",
    form: "",
  });

  // --- TanStack Query hook handles API state ---
  // mutate: triggers the API call
  // data: the response (after success)
  // isPending: true while loading
  // error: Error object if request failed
  // reset: clears the response (for "new search")
  const { mutate, data, isPending, error, reset } = useClassify();

  // --- Submit the search ---
  function handleSearch() {
    if (!query.trim()) return;

    // Build the request, including any non-empty refinements
    const request = {
      query: query.trim(),
      ...(refinements.material && { material: refinements.material }),
      ...(refinements.intended_use && { intended_use: refinements.intended_use }),
      ...(refinements.form && { form: refinements.form }),
    };

    mutate(request);
  }

  // --- Quick-start: fill in an example query ---
  function handleExample(example: string) {
    setQuery(example);
    reset(); // Clear any previous results
  }

  return (
    <div className="space-y-6">
      {/* Search input */}
      <SearchBar
        value={query}
        onChange={setQuery}
        onSubmit={handleSearch}
        isLoading={isPending}
      />

      {/* Error message */}
      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
          <p className="font-medium">Classification failed</p>
          <p className="mt-1">{error.message}</p>
          <button
            onClick={handleSearch}
            className="mt-2 text-xs underline hover:no-underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Results */}
      {data && <ResultsList data={data} />}

      {/* Refinement panel — shown after first search */}
      {data && data.results.length > 0 && (
        <RefinementPanel
          values={refinements}
          onChange={setRefinements}
          onRefine={handleSearch}
          isLoading={isPending}
        />
      )}

      {/* Empty state — example queries as quick-start buttons */}
      {!data && !isPending && !error && (
        <div className="text-center py-12 space-y-6">
          <div>
            <h2 className="text-xl font-semibold">Classify a product</h2>
            <p className="mt-2 text-muted-foreground text-sm">
              Describe a product and we'll find the matching HTS tariff code with duty rates.
            </p>
          </div>

          <div className="flex flex-wrap justify-center gap-2">
            {EXAMPLES.map((example) => (
              <button
                key={example}
                onClick={() => handleExample(example)}
                className="px-4 py-2 rounded-full border text-sm text-muted-foreground hover:text-foreground hover:border-primary/30 hover:bg-accent transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
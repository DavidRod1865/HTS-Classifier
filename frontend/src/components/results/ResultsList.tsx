/**
 * ResultsList — renders the ranked list of HTS code matches.
 *
 * Shows a header with the classification method (vector_only vs llm_assisted),
 * Claude's analysis (if applicable), and the list of ResultCards.
 *
 * The latency display helps users understand system performance:
 *   "vector_only" results are fast (< 500ms)
 *   "llm_assisted" results are slower (1-3s) but more accurate for edge cases
 */

import { ResultCard } from "./ResultCard";
import type { ClassifyResponse } from "@/api/client";

interface ResultsListProps {
  data: ClassifyResponse;
}

export function ResultsList({ data }: ResultsListProps) {
  if (data.results.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No matching HTS codes found. Try a more specific description.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header — method + latency */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">
            {data.results.length} results
          </span>
          {/* Show how the results were classified */}
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-muted text-muted-foreground">
            {data.method === "vector_only" ? "Vector search" : "AI-assisted"}
          </span>
        </div>
        <span className="text-muted-foreground text-xs">
          {data.latency_ms}ms
        </span>
      </div>

      {/* Claude's analysis — only shown when Claude helped */}
      {data.analysis && (
        <div className="rounded-lg bg-accent/50 border p-3 text-sm">
          <p className="font-medium text-xs text-muted-foreground mb-1">AI Analysis</p>
          <p>{data.analysis}</p>
        </div>
      )}

      {/* Result cards */}
      <div className="space-y-3">
        {data.results.map((result, i) => (
          <ResultCard key={result.hts_code} result={result} rank={i} />
        ))}
      </div>
    </div>
  );
}
/**
 * ProgressTable — shows real-time batch classification progress.
 *
 * As SSE events arrive, this component displays:
 *   - Overall progress bar with phase label
 *   - A table of items that fills in as each one is classified
 *   - Status badges (confident, ambiguous, needs_review)
 *
 * The table is the primary view — unlike v1's chat interface where
 * you had to scroll through messages, here you see everything at a glance.
 */

import { cn } from "@/lib/utils";
import type { BatchItem, BatchSummary } from "@/api/batch";

// Phase labels for human-readable display
const PHASE_LABELS: Record<string, string> = {
  extracting_text: "Extracting text from PDF...",
  extracting_commodities: "Identifying products...",
  searching: "Classifying products...",
  resolving: "Resolving ambiguous items...",
};

// Status badge colors
const STATUS_COLORS: Record<string, string> = {
  confident: "bg-green-50 text-green-700",
  llm_assisted: "bg-blue-50 text-blue-700",
  ambiguous: "bg-yellow-50 text-yellow-700",
  needs_review: "bg-red-50 text-red-700",
  searching: "bg-gray-50 text-gray-500",
};

interface ProgressTableProps {
  phase: string;
  progress: number;
  items: BatchItem[];
  summary: BatchSummary | null;
  isComplete: boolean;
}

export function ProgressTable({
  phase,
  progress,
  items,
  summary,
  isComplete,
}: ProgressTableProps) {
  return (
    <div className="space-y-4">
      {/* Progress bar — hidden when complete */}
      {!isComplete && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {PHASE_LABELS[phase] ?? phase}
            </span>
            <span className="font-medium">{progress}%</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Summary cards — shown when complete */}
      {isComplete && summary && (
        <div className="grid grid-cols-3 gap-3">
          <SummaryCard label="Total Items" value={summary.total} />
          <SummaryCard label="Classified" value={summary.classified} color="text-green-600" />
          <SummaryCard label="Needs Review" value={summary.needs_review} color="text-yellow-600" />
        </div>
      )}

      {/* Items table */}
      {items.length > 0 && (
        <div className="rounded-xl border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left px-4 py-2 font-medium">#</th>
                <th className="text-left px-4 py-2 font-medium">Product</th>
                <th className="text-left px-4 py-2 font-medium">HTS Code</th>
                <th className="text-left px-4 py-2 font-medium">Duty</th>
                <th className="text-left px-4 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, i) => (
                <tr key={i} className="border-t">
                  <td className="px-4 py-2 text-muted-foreground">{i + 1}</td>
                  <td className="px-4 py-2 max-w-xs truncate">{item.commodity}</td>
                  <td className="px-4 py-2 font-mono text-xs">
                    {item.hts_code || "—"}
                  </td>
                  <td className="px-4 py-2">{item.general_rate || "—"}</td>
                  <td className="px-4 py-2">
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded-full text-xs font-medium",
                        STATUS_COLORS[item.status] ?? "bg-gray-50 text-gray-500"
                      )}
                    >
                      {item.status.replace("_", " ")}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/** Small stat card for the summary row */
function SummaryCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color?: string;
}) {
  return (
    <div className="rounded-lg border bg-background p-3 text-center">
      <p className={cn("text-2xl font-bold", color)}>{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
/**
 * ResultCard — displays a single HTS code match.
 *
 * Shows the HTS code, description, duty rate, and confidence score.
 * The top result gets a highlighted border. Each card is expandable
 * to show additional details (special rates, context path, unit).
 *
 * The USITC link lets users verify the code against the official source.
 * We strip trailing "00" from the code for the search URL because the
 * USITC website uses the shorter format.
 */

import { useState } from "react";
import { Copy, ExternalLink, ChevronDown, ChevronUp, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { HtsResult } from "@/api/client";

interface ResultCardProps {
  result: HtsResult;
  rank: number;  // 0 = top result (gets special styling)
}

export function ResultCard({ result, rank }: ResultCardProps) {
  const [expanded, setExpanded] = useState(rank === 0); // Top result starts expanded
  const [copied, setCopied] = useState(false);
  const isTop = rank === 0;

  // Copy HTS code to clipboard
  async function handleCopy() {
    await navigator.clipboard.writeText(result.hts_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  // Build USITC link — strip trailing "00" for the search URL
  const usitcCode = result.hts_code.replace(/\.?00$/, "");
  const usitcUrl = `https://hts.usitc.gov/search#query=${usitcCode}&type=HTS`;

  // Confidence color: green (high), blue (medium), gray (low)
  const confidenceColor =
    result.confidence_score >= 80
      ? "text-green-600 bg-green-50"
      : result.confidence_score >= 60
        ? "text-blue-600 bg-blue-50"
        : "text-gray-600 bg-gray-50";

  return (
    <div
      className={cn(
        "rounded-xl border bg-background transition-shadow",
        isTop ? "border-primary/40 shadow-md" : "hover:shadow-sm"
      )}
    >
      {/* Main row — always visible */}
      <div className="p-4 flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* HTS code + copy button */}
          <div className="flex items-center gap-2">
            <code className="text-lg font-bold font-mono">{result.hts_code}</code>
            <button
              onClick={handleCopy}
              className="p-1 rounded hover:bg-muted transition-colors"
              aria-label="Copy HTS code"
            >
              {copied ? (
                <Check className="w-4 h-4 text-green-500" />
              ) : (
                <Copy className="w-4 h-4 text-muted-foreground" />
              )}
            </button>
            <a
              href={usitcUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1 rounded hover:bg-muted transition-colors"
              aria-label="View on USITC"
            >
              <ExternalLink className="w-4 h-4 text-muted-foreground" />
            </a>
          </div>

          {/* Description */}
          <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
            {result.description}
          </p>

          {/* Duty rate + unit (compact row) */}
          <div className="mt-2 flex items-center gap-3 text-sm">
            {result.general_rate && (
              <span className="font-medium">
                Duty: {result.general_rate}
              </span>
            )}
            {result.unit && (
              <span className="text-muted-foreground">
                per {result.unit}
              </span>
            )}
          </div>
        </div>

        {/* Confidence badge + expand button */}
        <div className="flex flex-col items-end gap-2">
          <span className={cn("px-2.5 py-1 rounded-full text-xs font-semibold", confidenceColor)}>
            {result.confidence_score}%
          </span>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 rounded hover:bg-muted transition-colors"
            aria-label={expanded ? "Collapse details" : "Expand details"}
          >
            {expanded ? (
              <ChevronUp className="w-4 h-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            )}
          </button>
        </div>
      </div>

      {/* Expanded details — hidden by default (except for top result) */}
      {expanded && (
        <div className="px-4 pb-4 pt-0 border-t text-sm space-y-2">
          {result.special_rate && (
            <div>
              <span className="font-medium text-muted-foreground">Special rates: </span>
              <span>{result.special_rate}</span>
            </div>
          )}
          {result.context_path && (
            <div>
              <span className="font-medium text-muted-foreground">Category: </span>
              <span>{result.context_path}</span>
            </div>
          )}
          <div>
            <span className="font-medium text-muted-foreground">Chapter: </span>
            <span>{result.chapter}</span>
          </div>
        </div>
      )}
    </div>
  );
}
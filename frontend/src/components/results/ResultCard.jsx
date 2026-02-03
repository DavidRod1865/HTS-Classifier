import React, { useState } from "react";
import { ChevronDown, ChevronUp, ExternalLink, Copy, CheckCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

/** Strip trailing "00" so USITC search works correctly. */
const formatForUSITC = (code) => (code?.endsWith("00") ? code.slice(0, -2) : code);

/** Colour class based on confidence percentage. */
const confidenceColor = (score) => {
  if (score >= 90) return "bg-green-100 text-green-800";
  if (score >= 70) return "bg-blue-100 text-blue-800";
  return "bg-gray-100 text-gray-800";
};

/**
 * A single HTS classification result rendered inline in the chat thread.
 *
 * Props:
 *   result  — { hts_code, description, effective_duty, special_duty,
 *               unit, confidence_score, chapter, match_type, duty_source }
 *   isTop   — boolean; first / best result gets highlighted styling
 */
const ResultCard = ({ result, isTop }) => {
  const [expanded, setExpanded] = useState(isTop);
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(result.hts_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard API unavailable in some contexts */
    }
  };

  return (
    <Card className={isTop ? "border-blue-400 border-2 shadow-md" : "border-gray-200"}>
      <CardContent className="p-4">
        {isTop && (
          <Badge className="bg-blue-600 text-white text-xs mb-2">Best Match</Badge>
        )}

        {/* HTS code + copy / USITC buttons */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          <span
            className={`text-xl font-bold font-mono ${
              isTop ? "text-blue-900" : "text-gray-900"
            }`}
          >
            {result.hts_code}
          </span>

          <div className="flex gap-1.5">
            <Button variant="outline" size="sm" onClick={copy} className="h-7 px-2 text-xs">
              {copied ? (
                <CheckCircle className="h-3 w-3 text-green-600" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
              <span className="ml-1">{copied ? "Copied" : "Copy"}</span>
            </Button>

            <a
              href={`https://hts.usitc.gov/search?query=${formatForUSITC(result.hts_code)}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button variant="outline" size="sm" className="h-7 px-2 text-xs">
                <ExternalLink className="h-3 w-3" />
                <span className="ml-1">USITC</span>
              </Button>
            </a>
          </div>
        </div>

        {/* Duty rate / confidence / unit row */}
        <div className="flex flex-wrap gap-4 mt-3">
          <div>
            <p className="text-xs text-gray-500">Duty</p>
            <p
              className={`text-sm font-semibold ${
                result.effective_duty === "Free" ? "text-green-600" : "text-gray-900"
              }`}
            >
              {result.effective_duty || "—"}
            </p>
          </div>

          <div>
            <p className="text-xs text-gray-500">Confidence</p>
            <Badge className={confidenceColor(result.confidence_score)}>
              {result.confidence_score}%
            </Badge>
          </div>

          {result.unit && (
            <div>
              <p className="text-xs text-gray-500">Unit</p>
              <p className="text-sm text-gray-700">{result.unit}</p>
            </div>
          )}
        </div>

        {/* Expand / collapse toggle */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 mt-3"
        >
          {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          {expanded ? "Hide details" : "Show details"}
        </button>

        {/* Expandable detail section */}
        {expanded && (
          <div className="mt-3 pt-3 border-t border-gray-100 space-y-2 text-sm">
            <p className="text-gray-700">{result.description}</p>

            {result.special_duty && (
              <p className="text-gray-500">
                <span className="font-medium">Special rates:</span> {result.special_duty}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ResultCard;

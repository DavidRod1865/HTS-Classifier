import React, { useState } from "react";
import {
  ArrowLeft,
  Download,
  FileText,
  CheckCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import ResultCard from "@/components/results/ResultCard";

/* ------------------------------------------------------------------ */
/*  Stat card used in the summary row                                  */
/* ------------------------------------------------------------------ */
const StatCard = ({ label, value, accent }) => {
  const accents = {
    default: "border-gray-200 text-gray-900",
    green: "border-green-300 text-green-700 bg-green-50",
    orange: "border-orange-300 text-orange-700 bg-orange-50",
  };

  return (
    <Card className={`flex-1 min-w-[140px] ${accents[accent] || accents.default}`}>
      <CardContent className="p-4 text-center">
        <p className="text-3xl font-bold">{value}</p>
        <p className="text-xs mt-1 uppercase tracking-wide opacity-80">{label}</p>
      </CardContent>
    </Card>
  );
};

/* ------------------------------------------------------------------ */
/*  Single line-item card                                              */
/* ------------------------------------------------------------------ */
const ItemCard = ({ item }) => {
  const [expanded, setExpanded] = useState(false);

  const isClassified = item.classification?.type === "result";
  const topResult = item.classification?.results?.[0];
  const allResults = item.classification?.results ?? [];
  const analysis = item.classification?.analysis;

  return (
    <Card className="border-gray-200 hover:shadow-md transition-shadow duration-200">
      <CardContent className="p-5">
        {/* Top row: line number, commodity, status badge */}
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono text-gray-400">#{item.line_number}</span>
              <h3 className="text-sm font-bold text-gray-900 truncate">
                {item.commodity}
              </h3>
            </div>

            {/* Quantity / unit price */}
            {(item.quantity || item.unit_price) && (
              <p className="text-xs text-gray-500 mt-0.5">
                {[item.quantity, item.unit_price].filter(Boolean).join(" · ")}
              </p>
            )}
          </div>

          <Badge
            className={
              isClassified
                ? "bg-green-100 text-green-800"
                : "bg-orange-100 text-orange-800"
            }
          >
            {isClassified ? (
              <CheckCircle className="h-3 w-3 mr-1 inline" />
            ) : (
              <AlertCircle className="h-3 w-3 mr-1 inline" />
            )}
            {isClassified ? "Classified" : "Needs Review"}
          </Badge>
        </div>

        {/* Top result preview */}
        {topResult && (
          <div className="flex flex-wrap gap-4 mt-3 text-sm">
            <div>
              <p className="text-xs text-gray-500">HTS Code</p>
              <p className="font-mono font-semibold text-gray-900">{topResult.hts_code}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Duty</p>
              <p
                className={`font-semibold ${
                  topResult.effective_duty === "Free" ? "text-green-600" : "text-gray-900"
                }`}
              >
                {topResult.effective_duty || "—"}
              </p>
            </div>
            {topResult.confidence_score != null && (
              <div>
                <p className="text-xs text-gray-500">Confidence</p>
                <p className="font-semibold text-gray-900">{topResult.confidence_score}%</p>
              </div>
            )}
          </div>
        )}

        {/* Expand toggle */}
        {allResults.length > 0 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 mt-3"
          >
            {expanded ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
            {expanded
              ? "Hide details"
              : `Show details (${allResults.length} result${allResults.length !== 1 ? "s" : ""})`}
          </button>
        )}

        {/* Expanded detail section */}
        {expanded && (
          <div className="mt-3 pt-3 border-t border-gray-100 space-y-3">
            {analysis && (
              <p className="text-sm text-gray-600 italic">{analysis}</p>
            )}
            {allResults.map((r, idx) => (
              <ResultCard key={r.hts_code ?? idx} result={r} isTop={idx === 0} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */
const BatchResultsView = ({ batchResults, onDownloadReport, onBackToChat, loading }) => {
  const { filename, items = [], summary = {} } = batchResults ?? {};

  /* ---- Empty state ---- */
  if (!items.length && !loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-500 fade-in">
        <FileText className="h-12 w-12 mb-3 opacity-40" />
        <p className="text-sm">No items to display.</p>
        <Button variant="outline" size="sm" className="mt-4" onClick={onBackToChat}>
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Chat
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6 fade-in">
      {/* ---- Header bar ---- */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={onBackToChat}>
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Chat
          </Button>
          <div>
            <h1 className="text-lg font-bold text-gray-900">Invoice Classification Results</h1>
            {filename && (
              <p className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
                <FileText className="h-3 w-3" />
                {filename}
              </p>
            )}
          </div>
        </div>

        <Button
          size="sm"
          className="bg-blue-600 hover:bg-blue-700 text-white"
          onClick={onDownloadReport}
          disabled={loading}
        >
          <Download className="h-4 w-4 mr-1" />
          {loading ? "Generating…" : "Download PDF Report"}
        </Button>
      </div>

      {/* ---- Summary cards ---- */}
      <div className="flex gap-3 flex-wrap">
        <StatCard
          label="Total Items"
          value={summary.total ?? items.length}
          accent="default"
        />
        <StatCard
          label="Classified"
          value={summary.classified ?? 0}
          accent="green"
        />
        <StatCard
          label="Needs Review"
          value={summary.needs_review ?? 0}
          accent="orange"
        />
      </div>

      {/* ---- Items list ---- */}
      <div className="space-y-3">
        {items.map((item, idx) => (
          <ItemCard key={item.line_number ?? idx} item={item} />
        ))}
      </div>
    </div>
  );
};

export default BatchResultsView;

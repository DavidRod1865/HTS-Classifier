import React from "react";
import ResultCard from "@/components/results/ResultCard";

/**
 * Renders a single message in the chat thread.
 *
 * message shapes:
 *   User:        { role: "user",      content: string }
 *   Question:    { role: "assistant", type: "question", question: string }
 *   Result:      { role: "assistant", type: "result",   results: [...], analysis?: string }
 */
const ChatMessage = ({ message }) => {
  // ── User message (right-aligned bubble) ────────────────────────────
  if (message.role === "user") {
    return (
      <div className="flex justify-end fade-in">
        <div className="bg-blue-600 text-white text-sm rounded-lg rounded-br-sm px-4 py-2.5 max-w-[75%] shadow-sm transition-all">
          {message.content}
        </div>
      </div>
    );
  }

  // ── Assistant: clarifying question ──────────────────────────────────
  if (message.type === "question") {
    return (
      <div className="flex justify-start fade-in">
        <div className="bg-white border border-gray-200 text-sm rounded-lg rounded-bl-sm px-4 py-3 max-w-[80%] shadow-sm transition-all">
          <p className="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">
            HTS Oracle
          </p>
          <p className="text-gray-800">{message.question}</p>
        </div>
      </div>
    );
  }

  // ── Assistant: classification results ───────────────────────────────
  if (message.type === "result") {
    const topConfidence = message.results?.[0]?.confidence_score;
    return (
      <div className="flex justify-start w-full fade-in">
        <div className="w-full max-w-[90%]">
          <p className="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-2">
            HTS Oracle
          </p>

          {/* Claude's analysis text (when present) */}
          {message.analysis && (
            <p className="text-sm text-gray-600 mb-3">{message.analysis}</p>
          )}

          <details className="group bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-600 mb-3">
            <summary className="cursor-pointer text-xs font-semibold text-gray-500 uppercase tracking-wide list-none">
              Why these results?
            </summary>
            <div className="mt-2 space-y-1">
              <p>
                Ranked by semantic similarity to your description using embeddings and vector search.
              </p>
              <p>
                Source: USITC HTS schedule. Confidence reflects match strength
                {topConfidence ? ` (top match: ${topConfidence}%).` : "."}
              </p>
              <p>Use the USITC link on each result to verify the official entry.</p>
            </div>
          </details>

          {/* Result cards */}
          <div className="space-y-2">
            {message.results?.map((result, i) => (
              <ResultCard key={`${result.hts_code}-${i}`} result={result} isTop={i === 0} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default ChatMessage;

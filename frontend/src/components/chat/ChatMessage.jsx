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
      <div className="flex justify-end">
        <div className="bg-blue-600 text-white text-sm rounded-lg rounded-br-sm px-4 py-2.5 max-w-[75%]">
          {message.content}
        </div>
      </div>
    );
  }

  // ── Assistant: clarifying question ──────────────────────────────────
  if (message.type === "question") {
    return (
      <div className="flex justify-start">
        <div className="bg-white border border-gray-200 text-sm rounded-lg rounded-bl-sm px-4 py-3 max-w-[80%] shadow-sm">
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
    return (
      <div className="flex justify-start w-full">
        <div className="w-full max-w-[90%]">
          <p className="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-2">
            HTS Oracle
          </p>

          {/* Claude's analysis text (when present) */}
          {message.analysis && (
            <p className="text-sm text-gray-600 mb-3">{message.analysis}</p>
          )}

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

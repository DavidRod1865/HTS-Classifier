import React, { useState, useRef, useEffect } from "react";
import MainLayout from "@/components/layout/MainLayout";
import ChatMessage from "@/components/chat/ChatMessage";
import ChatInput from "@/components/chat/ChatInput";
import BatchResultsView from "@/components/results/BatchResultsView";
import PdfUploadZone from "@/components/upload/PdfUploadZone";
import AdminPage from "@/pages/AdminPage";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

const App = () => {
  // ── Routing (simple path-based, no react-router needed) ───────────
  const [currentPage, setCurrentPage] = useState(
    window.location.pathname === "/admin" ? "admin" : "chat"
  );

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPage(window.location.pathname === "/admin" ? "admin" : "chat");
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  // ── Chat state ────────────────────────────────────────────────────
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const bottomRef = useRef(null);

  // ── Batch (PDF invoice) state ─────────────────────────────────────
  const [batchResults, setBatchResults] = useState(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [batchProgress, setBatchProgress] = useState(null);
  const [completedItems, setCompletedItems] = useState([]);

  // Auto-scroll to the latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ── Chat: send text message ───────────────────────────────────────
  const sendMessage = async (text) => {
    if (!text.trim() || loading) return;

    // Optimistically add user message to the thread
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setHistory((prev) => [
      text,
      ...prev.filter((item) => item.toLowerCase() !== text.toLowerCase()),
    ].slice(0, 6));
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text }),
      });

      if (!res.ok) throw new Error(`Server error ${res.status}`);

      const data = await res.json();

      // Persist session ID for follow-up turns
      if (data.session_id) setSessionId(data.session_id);

      // Add the assistant's response
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          type: data.type,          // "result" | "question"
          results: data.results,
          question: data.question,
          analysis: data.analysis,
        },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ── PDF upload: classify invoice (SSE streaming) ─────────────────
  const uploadPdf = async (file) => {
    setBatchLoading(true);
    setBatchResults(null);
    setBatchProgress(null);
    setCompletedItems([]);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE_URL}/api/classify-invoice`, {
        method: "POST",
        body: formData,
      });

      // Non-streaming error (validation failures return JSON)
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || `Server error ${res.status}`);
      }

      // Read the SSE stream
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // SSE events are separated by double newlines
        const parts = buffer.split("\n\n");
        buffer = parts.pop(); // keep incomplete chunk

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data: ")) continue;
          const evt = JSON.parse(line.slice(6));

          if (evt.event === "phase") {
            setBatchProgress({
              phase: evt.phase,
              progress: evt.progress,
              current: 0,
              total: evt.total || 0,
              currentItem: null,
            });
          } else if (evt.event === "item_start") {
            // Search phase: 20% → 85%
            const progress = 20 + (65 * (evt.current - 1)) / evt.total;
            setBatchProgress((prev) => ({
              ...prev,
              phase: "searching",
              progress,
              current: evt.current,
              total: evt.total,
              currentItem: evt.commodity,
            }));
          } else if (evt.event === "item_done") {
            const progress = 20 + (65 * evt.current) / evt.total;
            setBatchProgress((prev) => ({
              ...prev,
              progress,
              currentItem: null,
            }));
            setCompletedItems((prev) => [
              {
                commodity: evt.commodity,
                htsCode: evt.top_result?.hts_code || "—",
                confidence: evt.top_result?.confidence || 0,
                status: evt.status, // "confident" or "ambiguous"
              },
              ...prev,
            ]);
          } else if (evt.event === "complete") {
            setBatchResults({ filename: file.name, ...evt });
            setBatchLoading(false);
            setBatchProgress(null);
            setCompletedItems([]);
          } else if (evt.event === "error") {
            throw new Error(evt.message);
          }
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBatchLoading(false);
      setBatchProgress(null);
    }
  };

  // ── Download PDF report ───────────────────────────────────────────
  const downloadReport = async () => {
    if (!batchResults?.items) return;

    setReportLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/generate-report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: batchResults.items,
          filename: batchResults.filename || "",
        }),
      });

      if (!res.ok) throw new Error(`Report generation failed (${res.status})`);

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "hts_classification_report.pdf";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setReportLoading(false);
    }
  };

  // ── Navigation helpers ────────────────────────────────────────────
  const newChat = () => {
    setMessages([]);
    setSessionId(null);
    setBatchResults(null);
    setBatchProgress(null);
    setCompletedItems([]);
    setError(null);
  };

  const backToChat = () => {
    setBatchResults(null);
    setError(null);
  };

  // ── Render admin page ─────────────────────────────────────────────
  if (currentPage === "admin") {
    return <AdminPage />;
  }

  // ── Render batch results view ─────────────────────────────────────
  if (batchResults) {
    return (
      <MainLayout onNewChat={newChat}>
        <BatchResultsView
          batchResults={batchResults}
          onDownloadReport={downloadReport}
          onBackToChat={backToChat}
          loading={reportLoading}
        />
      </MainLayout>
    );
  }

  // ── Render main chat view ─────────────────────────────────────────
  return (
    <MainLayout onNewChat={messages.length > 0 ? newChat : null}>
      <div className="flex flex-col min-h-[calc(100vh-180px)] md:h-[calc(100vh-180px)]">
        {/* Message thread */}
        <div className="flex-1 overflow-y-auto space-y-4 pb-4 px-1 md:px-2">
          {/* Empty state with example hints + PDF upload zone */}
          {messages.length === 0 && !batchLoading && (
            <div className="text-center pt-10 md:pt-16 px-2 sm:px-4">
              <p className="text-gray-700 text-base font-medium">
                Start with a clear product description
              </p>
              <p className="text-gray-500 text-sm mt-2">
                Include material, use, and any key specs — or upload a PDF invoice.
              </p>
              <div className="flex flex-wrap justify-center gap-2 mt-4">
                {[
                  "100% cotton knitted t-shirts",
                  "Stainless steel pipes, 2-inch diameter",
                  "LED light bulbs, 60W equivalent",
                  "Passenger car rubber tires",
                ].map((hint) => (
                  <button
                    key={hint}
                    onClick={() => sendMessage(hint)}
                    className="text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-full transition-colors"
                  >
                    {hint}
                  </button>
                ))}
              </div>

              {/* PDF upload drop zone */}
              <div className="mt-6 max-w-md mx-auto">
                <PdfUploadZone onUploadPdf={uploadPdf} disabled={loading} />
              </div>
            </div>
          )}

          {history.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl px-4 py-3 shadow-sm">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Recent Prompts
                </p>
                <button
                  onClick={() => setShowHistory((prev) => !prev)}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  {showHistory ? "Hide" : `Show (${history.length})`}
                </button>
              </div>
              {showHistory && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {history.map((item) => (
                    <button
                      key={item}
                      onClick={() => sendMessage(item)}
                      disabled={loading}
                      className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-full transition-colors disabled:opacity-50"
                    >
                      {item}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Rendered messages */}
          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} />
          ))}

          {/* Loading indicator — text search */}
          {loading && (
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <div className="typing-dots">
                <span />
                <span />
                <span />
              </div>
              Searching…
            </div>
          )}

          {/* Loading indicator — PDF processing with progress bar */}
          {batchLoading && !batchProgress && (
            <div className="flex items-center gap-2 text-gray-500 text-sm fade-in">
              <div className="typing-dots">
                <span />
                <span />
                <span />
              </div>
              Starting…
            </div>
          )}

          {batchLoading && batchProgress && (
            <div className="bg-white border border-gray-200 rounded-xl px-4 py-4 shadow-sm fade-in w-full">
              {/* Phase label */}
              <p className="text-sm font-medium text-gray-700 mb-2">
                {batchProgress.phase === "extracting_text" && "Extracting text from PDF…"}
                {batchProgress.phase === "extracting_commodities" && "Identifying commodities…"}
                {batchProgress.phase === "classifying" && "Classifying commodities…"}
                {batchProgress.phase === "searching" && "Searching tariff codes…"}
                {batchProgress.phase === "resolving" && "Analyzing ambiguous items…"}
              </p>

              {/* Progress bar */}
              <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${batchProgress.progress}%` }}
                />
              </div>

              {/* Counter */}
              <p className="text-xs text-gray-500">
                {batchProgress.phase === "classifying" && batchProgress.total
                  ? `Item ${batchProgress.current} of ${batchProgress.total}`
                  : `${Math.round(batchProgress.progress)}%`}
              </p>

              {/* Currently classifying item */}
              {batchProgress.currentItem && (
                <div className="mt-3 flex items-center gap-2 text-xs text-blue-600 animate-pulse">
                  <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2" />
                    <circle cx="12" cy="12" r="10" />
                  </svg>
                  <span className="truncate">{batchProgress.currentItem}</span>
                </div>
              )}

              {/* Completed items preview */}
              {completedItems.length > 0 && (
                <div className="mt-3 space-y-1.5 border-t border-gray-100 pt-3">
                  {completedItems.slice(0, 4).map((item, idx) => (
                    <div
                      key={`${item.commodity}-${idx}`}
                      className={`flex items-center justify-between text-xs ${
                        idx === 0 ? "animate-slideIn" : ""
                      } ${idx === 3 ? "opacity-40" : idx === 2 ? "opacity-60" : ""}`}
                    >
                      <div className="flex items-center gap-1.5 min-w-0">
                        {item.status === "ambiguous" ? (
                          <svg className="w-3 h-3 text-orange-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <circle cx="12" cy="12" r="10" />
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01" />
                          </svg>
                        ) : (
                          <svg className="w-3 h-3 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                        <span className="truncate text-gray-600">{item.commodity}</span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0 ml-2">
                        <span className="font-mono text-gray-800">{item.htsCode}</span>
                        {item.confidence > 0 && (
                          <span className={`${
                            item.confidence >= 90 ? "text-green-600" :
                            item.confidence >= 70 ? "text-blue-600" : "text-gray-500"
                          }`}>
                            {Math.round(item.confidence)}%
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Error banner */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3">
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input bar — always at the bottom */}
        <ChatInput
          onSend={sendMessage}
          onUploadPdf={uploadPdf}
          disabled={loading || batchLoading}
        />
      </div>
    </MainLayout>
  );
};

export default App;

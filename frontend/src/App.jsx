import React, { useState, useRef, useEffect } from "react";
import MainLayout from "@/components/layout/MainLayout";
import ChatMessage from "@/components/chat/ChatMessage";
import ChatInput from "@/components/chat/ChatInput";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

const App = () => {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return;

    // Optimistically add user message to the thread
    setMessages((prev) => [...prev, { role: "user", content: text }]);
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

  const newChat = () => {
    setMessages([]);
    setSessionId(null);
    setError(null);
  };

  return (
    <MainLayout onNewChat={messages.length > 0 ? newChat : null}>
      <div className="flex flex-col" style={{ height: "calc(100vh - 180px)" }}>
        {/* Message thread */}
        <div className="flex-1 overflow-y-auto space-y-4 pb-4 px-1">
          {/* Empty state with example hints */}
          {messages.length === 0 && (
            <div className="text-center pt-16 px-4">
              <p className="text-gray-500 text-base">Describe a commodity to classify</p>
              <div className="flex flex-wrap justify-center gap-2 mt-4">
                {["Cotton t-shirts", "Steel pipes", "LED light bulbs", "Rubber tires"].map(
                  (hint) => (
                    <button
                      key={hint}
                      onClick={() => sendMessage(hint)}
                      className="text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-full transition-colors"
                    >
                      {hint}
                    </button>
                  )
                )}
              </div>
            </div>
          )}

          {/* Rendered messages */}
          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} />
          ))}

          {/* Loading indicator */}
          {loading && (
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />
              Searching…
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
        <ChatInput onSend={sendMessage} disabled={loading} />
      </div>
    </MainLayout>
  );
};

export default App;

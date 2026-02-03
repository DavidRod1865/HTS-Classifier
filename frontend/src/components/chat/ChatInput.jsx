import React, { useState } from "react";
import { Send } from "lucide-react";

const ChatInput = ({ onSend, disabled }) => {
  const [text, setText] = useState("");

  const submit = (e) => {
    e.preventDefault();
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText("");
  };

  return (
    <form onSubmit={submit} className="flex gap-2 border-t border-gray-200 pt-4">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Describe your commodity…"
        disabled={disabled}
        className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                   disabled:bg-gray-100 disabled:text-gray-400"
        autoFocus
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="bg-blue-600 text-white px-4 py-2.5 rounded-lg
                   disabled:bg-gray-300 hover:bg-blue-700 transition-colors
                   flex items-center gap-1.5"
        aria-label="Send"
      >
        <Send className="h-4 w-4" />
        <span className="text-sm font-medium">Send</span>
      </button>
    </form>
  );
};

export default ChatInput;

import React, { useRef, useState } from "react";
import { Send, Paperclip } from "lucide-react";

const ChatInput = ({ onSend, onUploadPdf, disabled }) => {
  const [text, setText] = useState("");
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);

  const submit = (e) => {
    e.preventDefault();
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText("");
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && onUploadPdf) {
      onUploadPdf(file);
    }
    // Reset so the same file can be re-selected
    e.target.value = "";
  };

  return (
    <form onSubmit={submit} className="flex flex-col gap-2 border-t border-gray-200 pt-4">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleFileChange}
        className="hidden"
      />
      <div
        className="flex flex-col sm:flex-row gap-2"
        onPointerDown={() => {
          if (!disabled) inputRef.current?.focus();
        }}
      >
        <button
          type="button"
          disabled={disabled}
          onClick={() => fileInputRef.current?.click()}
          className="border border-gray-300 bg-white text-gray-500 px-3 py-2.5 rounded-lg
                     hover:bg-gray-50 hover:text-blue-600 transition-colors
                     disabled:bg-gray-100 disabled:text-gray-400
                     flex items-center justify-center shrink-0"
          aria-label="Upload PDF"
          title="Upload PDF"
        >
          <Paperclip className="h-4 w-4" />
        </button>
        <input
          ref={inputRef}
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Describe the product (material, use, specs)…"
          disabled={disabled}
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm bg-white shadow-sm
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     disabled:bg-gray-100 disabled:text-gray-400"
          autoFocus
        />
        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="bg-blue-600 text-white px-4 py-2.5 rounded-lg w-full sm:w-auto
                     disabled:bg-gray-300 hover:bg-blue-700 transition-colors
                     flex items-center gap-1.5"
          aria-label="Send"
        >
          <Send className="h-4 w-4" />
          <span className="text-sm font-medium">Send</span>
        </button>
      </div>
      <p className="text-xs text-gray-500">
        Describe a product or upload a PDF invoice to classify items automatically.
      </p>
    </form>
  );
};

export default ChatInput;

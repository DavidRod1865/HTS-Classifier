import React from "react";
import { Package } from "lucide-react";

const Header = ({ onNewChat }) => (
  <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
    <div className="max-w-3xl mx-auto px-4 sm:px-6">
      <div className="flex items-center justify-between h-14">
        {/* Brand */}
        <div className="flex items-center gap-2.5">
          <div className="flex items-center justify-center w-8 h-8 bg-blue-600 rounded-lg">
            <Package className="h-4 w-4 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-gray-900">HTS Oracle</h1>
            <p className="text-xs text-gray-500">Classification Assistant</p>
          </div>
        </div>

        {/* New Chat button — only visible once a conversation has started */}
        {onNewChat && (
          <button
            onClick={onNewChat}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            New Chat
          </button>
        )}
      </div>
    </div>
  </header>
);

export default Header;

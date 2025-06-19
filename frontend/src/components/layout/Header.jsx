import React from "react";
import { Package, Settings, History, HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import AccessibilityControls from "@/components/AccessibilityControls";

const Header = ({ onShowHistory, onShowHelp, searchCount = 0 }) => {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Title */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-600 rounded-lg">
              <Package className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                HTS Oracle
              </h1>
              <p className="text-xs text-gray-600">
                Classification Assistant
              </p>
            </div>
          </div>

          {/* Navigation and Controls */}
          <div className="flex items-center space-x-4">
            {/* Search counter */}
            {searchCount > 0 && (
              <Badge variant="outline" className="hidden sm:flex">
                {searchCount} searches today
              </Badge>
            )}

            {/* Action buttons */}
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={onShowHistory}
                className="hidden sm:flex items-center space-x-1"
              >
                <History className="h-4 w-4" />
                <span>History</span>
              </Button>

              <Button
                variant="ghost"
                size="sm"
                onClick={onShowHelp}
                className="flex items-center space-x-1"
              >
                <HelpCircle className="h-4 w-4" />
                <span className="hidden sm:inline">Help</span>
              </Button>

              {/* Accessibility Controls */}
              <div className="hidden lg:block">
                <AccessibilityControls />
              </div>

              <Button
                variant="ghost"
                size="sm"
                className="lg:hidden"
              >
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
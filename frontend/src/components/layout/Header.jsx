import React, { useState } from "react";
import { Package, History, HelpCircle, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import AccessibilityControls from "@/components/AccessibilityControls";

const Header = ({ onShowHistory, onShowHelp, searchCount = 0 }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14 sm:h-16">
          {/* Logo and Title */}
          <div className="flex items-center space-x-2 sm:space-x-3 flex-shrink-0">
            <div className="flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 bg-blue-600 rounded-lg">
              <Package className="h-4 w-4 sm:h-6 sm:w-6 text-white" />
            </div>
            <div className="min-w-0">
              <h1 className="text-lg sm:text-xl font-bold text-gray-900 truncate">
                HTS Oracle
              </h1>
              <p className="text-xs text-gray-600 hidden sm:block">
                Classification Assistant
              </p>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-4">
            {/* Search counter */}
            {searchCount > 0 && (
              <Badge variant="outline" className="text-xs">
                {searchCount} searches
              </Badge>
            )}

            {/* Action buttons */}
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={onShowHistory}
                className="flex items-center space-x-1"
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
                <span>Help</span>
              </Button>

              <AccessibilityControls />
            </div>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2"
              aria-label="Toggle mobile menu"
            >
              {isMobileMenuOpen ? (
                <X className="h-5 w-5" />
              ) : (
                <Menu className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200 py-3 space-y-2">
            {searchCount > 0 && (
              <div className="px-2">
                <Badge variant="outline" className="text-xs">
                  {searchCount} searches today
                </Badge>
              </div>
            )}
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                onShowHistory();
                setIsMobileMenuOpen(false);
              }}
              className="w-full justify-start"
            >
              <History className="h-4 w-4 mr-2" />
              Search History
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                onShowHelp();
                setIsMobileMenuOpen(false);
              }}
              className="w-full justify-start"
            >
              <HelpCircle className="h-4 w-4 mr-2" />
              Help & Support
            </Button>

            <div className="px-2 pt-2 border-t border-gray-100">
              <AccessibilityControls />
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
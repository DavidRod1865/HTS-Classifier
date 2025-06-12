import React, { useState, useEffect } from "react";
import { Settings, Sun, Moon, Type, Minus, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tooltip } from "@/components/ui/tooltip";

const AccessibilityControls = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [highContrast, setHighContrast] = useState(false);
  const [fontSize, setFontSize] = useState(100);

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedContrast = localStorage.getItem('hts-high-contrast') === 'true';
    const savedFontSize = parseInt(localStorage.getItem('hts-font-size') || '100');
    
    setHighContrast(savedContrast);
    setFontSize(savedFontSize);
    
    // Apply settings to document
    if (savedContrast) {
      document.documentElement.classList.add('high-contrast');
    }
    document.documentElement.style.fontSize = `${savedFontSize}%`;
  }, []);

  const toggleHighContrast = () => {
    const newValue = !highContrast;
    setHighContrast(newValue);
    localStorage.setItem('hts-high-contrast', newValue.toString());
    
    if (newValue) {
      document.documentElement.classList.add('high-contrast');
    } else {
      document.documentElement.classList.remove('high-contrast');
    }
  };

  const adjustFontSize = (adjustment) => {
    const newSize = Math.max(75, Math.min(150, fontSize + adjustment));
    setFontSize(newSize);
    localStorage.setItem('hts-font-size', newSize.toString());
    document.documentElement.style.fontSize = `${newSize}%`;
  };

  const resetSettings = () => {
    setHighContrast(false);
    setFontSize(100);
    localStorage.removeItem('hts-high-contrast');
    localStorage.removeItem('hts-font-size');
    document.documentElement.classList.remove('high-contrast');
    document.documentElement.style.fontSize = '100%';
  };

  return (
    <div className="fixed top-4 right-4 z-50">
      <Tooltip content="Accessibility settings" position="left">
        <Button
          onClick={() => setIsOpen(!isOpen)}
          variant="outline"
          size="sm"
          className="bg-white shadow-lg"
          aria-label="Open accessibility controls"
          aria-expanded={isOpen}
        >
          <Settings className="h-4 w-4" />
        </Button>
      </Tooltip>

      {isOpen && (
        <Card className="absolute top-12 right-0 w-72 shadow-xl bg-white border-2">
          <CardContent className="p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-sm">Accessibility Settings</h3>
              <Button
                onClick={() => setIsOpen(false)}
                variant="ghost"
                size="sm"
                aria-label="Close accessibility controls"
              >
                ×
              </Button>
            </div>

            {/* High Contrast Toggle */}
            <div className="space-y-2">
              <label className="text-sm font-medium">High Contrast Mode</label>
              <Button
                onClick={toggleHighContrast}
                variant={highContrast ? "default" : "outline"}
                className="w-full justify-start"
                aria-pressed={highContrast}
              >
                {highContrast ? <Sun className="h-4 w-4 mr-2" /> : <Moon className="h-4 w-4 mr-2" />}
                {highContrast ? "Disable" : "Enable"} High Contrast
              </Button>
            </div>

            {/* Font Size Controls */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Font Size: {fontSize}%</label>
              <div className="flex gap-2">
                <Button
                  onClick={() => adjustFontSize(-10)}
                  variant="outline"
                  size="sm"
                  disabled={fontSize <= 75}
                  aria-label="Decrease font size"
                >
                  <Minus className="h-4 w-4" />
                </Button>
                <Button
                  onClick={() => adjustFontSize(10)}
                  variant="outline"
                  size="sm"
                  disabled={fontSize >= 150}
                  aria-label="Increase font size"
                >
                  <Plus className="h-4 w-4" />
                </Button>
                <Button
                  onClick={resetSettings}
                  variant="outline"
                  size="sm"
                  className="flex-1"
                  aria-label="Reset to default settings"
                >
                  Reset
                </Button>
              </div>
            </div>

            {/* Keyboard Navigation Info */}
            <div className="text-xs text-gray-600 space-y-1">
              <p><strong>Keyboard Navigation:</strong></p>
              <p>• Tab: Navigate between elements</p>
              <p>• Enter/Space: Activate buttons</p>
              <p>• Escape: Close dialogs</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AccessibilityControls;
import React, { createContext, useContext, useEffect, useState } from "react";

const AccessibilityContext = createContext();

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error("useAccessibility must be used within AccessibilityProvider");
  }
  return context;
};

export const AccessibilityProvider = ({ children }) => {
  const [announcements, setAnnouncements] = useState([]);
  const [focusTarget, setFocusTarget] = useState(null);

  // Announce to screen readers
  const announce = (message, priority = "polite") => {
    const id = Date.now();
    setAnnouncements(prev => [...prev, { id, message, priority }]);
    
    // Clean up after announcement
    setTimeout(() => {
      setAnnouncements(prev => prev.filter(item => item.id !== id));
    }, 1000);
  };

  // Focus management
  const moveFocusTo = (elementId) => {
    setFocusTarget(elementId);
  };

  useEffect(() => {
    if (focusTarget) {
      const element = document.getElementById(focusTarget);
      if (element) {
        element.focus();
        setFocusTarget(null);
      }
    }
  }, [focusTarget]);

  // Keyboard navigation helpers
  const handleKeyboardNavigation = (event, actions) => {
    switch (event.key) {
      case 'Escape':
        actions.onEscape?.();
        break;
      case 'Enter':
      case ' ':
        if (event.target.tagName !== 'INPUT' && event.target.tagName !== 'TEXTAREA') {
          event.preventDefault();
          actions.onActivate?.();
        }
        break;
      case 'ArrowDown':
        event.preventDefault();
        actions.onDown?.();
        break;
      case 'ArrowUp':
        event.preventDefault();
        actions.onUp?.();
        break;
      case 'Tab':
        // Let natural tab behavior work
        actions.onTab?.(event);
        break;
      default:
        break;
    }
  };

  const value = {
    announce,
    moveFocusTo,
    handleKeyboardNavigation,
    announcements
  };

  return (
    <AccessibilityContext.Provider value={value}>
      {children}
      
      {/* Live regions for announcements */}
      <div className="sr-only">
        {announcements.map(({ id, message, priority }) => (
          <div key={id} aria-live={priority} aria-atomic="true">
            {message}
          </div>
        ))}
      </div>
      
      {/* Skip links */}
      <div className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 z-50">
        <a
          href="#main-content"
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium"
        >
          Skip to main content
        </a>
      </div>
    </AccessibilityContext.Provider>
  );
};

// Screen reader only styles
export const ScreenReaderOnly = ({ children }) => (
  <span className="sr-only">{children}</span>
);

// Focus trap hook for modals
export const useFocusTrap = (isActive) => {
  useEffect(() => {
    if (!isActive) return;

    const focusableElements = document.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement.focus();
            e.preventDefault();
          }
        }
      }
    };

    document.addEventListener('keydown', handleTabKey);
    
    // Focus first element when trap activates
    if (firstElement) {
      firstElement.focus();
    }

    return () => {
      document.removeEventListener('keydown', handleTabKey);
    };
  }, [isActive]);
};
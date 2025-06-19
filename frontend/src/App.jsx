import React, { useState } from "react";

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Utility function to format HTS codes for USITC links
const formatHtsCodeForUSITC = (htsCode) => {
  if (!htsCode) return htsCode;
  
  // Remove trailing "00" if present
  if (htsCode.endsWith('00')) {
    return htsCode.slice(0, -2);
  }
  
  return htsCode;
};

// Layout Components
import MainLayout from "@/components/layout/MainLayout";

// Feature Components
import SearchForm from "@/components/search/SearchForm";
import ResultsContainer from "@/components/results/ResultsContainer";

// Shared Components
import { ProcessingLoadingState, ResultsLoadingSkeleton } from "@/components/shared/LoadingStates";
import { WelcomeState, NoResultsState, ErrorState } from "@/components/shared/EmptyStates";
import ContextualHelp from "@/components/shared/ContextualHelp";
import { AccessibilityProvider } from "@/components/shared/AccessibilityProvider";

// Utilities
import { exportToHTMLReport } from "@/utils/pdfExport";

const App = () => {
  // Core state
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Additional state
  const [currentProduct, setCurrentProduct] = useState("");
  const [claudeAnalysis, setClaudeAnalysis] = useState("");
  const [searchCount, setSearchCount] = useState(0);
  const [hasSearched, setHasSearched] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  // Debug: Log when component mounts
  React.useEffect(() => {
    console.log("HTSClassifier component mounted");
  }, []);

  const classifyProduct = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setCurrentProduct(query.trim());
    setHasSearched(true);
    
    console.log("STARTING NEW CLASSIFICATION for:", query);
    console.log("📡 Making API request to /api/classify (NEW)");
    console.log("📡 Session ID:", `session_${Date.now()}`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/classify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query.trim(),
        }),
      });

      console.log("📨 Response status:", response.status);

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      console.log("🔄 Full response data:", data);

      if (data.success) {
        if (data.type === "final_classification" && data.data?.results) {
          setResults(data.data.results);
          setClaudeAnalysis(data.data.claude_analysis || "");
          setSearchCount(prev => prev + 1);
          console.log("✅ SUCCESS: STARTING NEW classification completed");
        } else if (data.type === "no_results") {
          setResults([]);
          setClaudeAnalysis(data.data?.claude_analysis || "");
          console.log("⚠️ No results found");
        } else {
          console.log("🔄 Received data:", data);
          setError("Unexpected response format from server");
        }
      } else {
        setError(data.error || "Classification failed");
        console.error("❌ API Error:", data.error);
      }
    } catch (err) {
      console.error("❌ Network/Server Error:", err);
      setError(`Network error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleNewSearch = () => {
    setQuery("");
    setResults([]);
    setError("");
    setCurrentProduct("");
    setClaudeAnalysis("");
    setHasSearched(false);
  };

  const handleRetry = () => {
    if (currentProduct) {
      setQuery(currentProduct);
      classifyProduct({ preventDefault: () => {} });
    }
  };

  const handleExportPDF = async (resultsToExport) => {
    try {
      exportToHTMLReport(resultsToExport, currentProduct, claudeAnalysis);
      console.log("PDF report exported successfully");
    } catch (error) {
      console.error("Error exporting PDF:", error);
      alert("Error exporting report. Please try again.");
    }
  };

  const handleShowHistory = () => {
    // TODO: Implement search history
    console.log("Show search history");
    alert("Search history feature coming soon!");
  };

  const handleShowHelp = () => {
    setShowHelp(true);
  };

  // Render different states
  const renderMainContent = () => {
    // Loading state
    if (loading) {
      return <ProcessingLoadingState />;
    }

    // Error state
    if (error) {
      return (
        <ErrorState 
          error={error}
          onRetry={handleRetry}
          onNewSearch={handleNewSearch}
        />
      );
    }

    // Results state
    if (results.length > 0) {
      return (
        <ResultsContainer
          results={results}
          currentProduct={currentProduct}
          claudeAnalysis={claudeAnalysis}
          onNewSearch={handleNewSearch}
          onExportPDF={handleExportPDF}
        />
      );
    }

    // No results state (after search)
    if (hasSearched && results.length === 0 && !loading) {
      return (
        <NoResultsState
          query={currentProduct}
          onRetry={handleRetry}
          onNewSearch={handleNewSearch}
        />
      );
    }

    // Welcome state (initial)
    return <WelcomeState />;
  };

  return (
    <AccessibilityProvider>
      <MainLayout
        onShowHistory={handleShowHistory}
        onShowHelp={handleShowHelp}
        searchCount={searchCount}
      >
        <div className="space-y-8" id="main-content">
          {/* Search Section - Always visible */}
          <SearchForm
            query={query}
            setQuery={setQuery}
            loading={loading}
            onSubmit={classifyProduct}
            showHints={!hasSearched} // Hide hints after first search
          />

          {/* Main Content Area */}
          {renderMainContent()}
        </div>
        
        {/* Contextual Help Modal */}
        <ContextualHelp 
          isOpen={showHelp} 
          onClose={() => setShowHelp(false)} 
        />
      </MainLayout>
    </AccessibilityProvider>
  );
};

export default App;
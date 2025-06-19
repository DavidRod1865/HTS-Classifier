import React, { useState } from "react";
import { Search, Loader2, AlertCircle, Package, Info, ExternalLink, RotateCcw, Sparkles } from "lucide-react";

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

// shadcn/ui components
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tooltip } from "@/components/ui/tooltip";
import { Collapsible } from "@/components/ui/collapsible";
import AccessibilityControls from "@/components/AccessibilityControls";
import BreadcrumbNav from "@/components/BreadcrumbNav";

// Table components built with Tailwind
const Table = ({ children, className = "" }) => (
  <div className={`w-full overflow-auto ${className}`}>
    <table className="w-full caption-bottom text-sm">{children}</table>
  </div>
);

const TableHeader = ({ children }) => (
  <thead className="[&_tr]:border-b">{children}</thead>
);

const TableBody = ({ children }) => (
  <tbody className="[&_tr:last-child]:border-0">{children}</tbody>
);

const TableRow = ({ children }) => (
  <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
    {children}
  </tr>
);

const TableHead = ({ children, className = "" }) => (
  <th
    className={`h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 ${className}`}
  >
    {children}
  </th>
);

const TableCell = ({ children, className = "" }) => (
  <td className={`p-4 align-middle [&:has([role=checkbox])]:pr-0 ${className}`}>
    {children}
  </td>
);

const App = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [questions, setQuestions] = useState([]);
  const [options, setOptions] = useState([]);
  const [sessionId] = useState("session_" + Date.now());
  const [currentTurn, setCurrentTurn] = useState(1);
  const [conversationActive, setConversationActive] = useState(false);
  const [currentProduct, setCurrentProduct] = useState(""); // Track what we're classifying
  const [awaitingResponse, setAwaitingResponse] = useState(false); // Track if we're waiting for user response to questions

  // Debug: Log when component mounts
  React.useEffect(() => {
    console.log("HTSClassifier component mounted");
    console.log("Initial state:", {
      query,
      results,
      loading,
      error,
      questions,
      options,
    });
  }, []);

  // Debug: Log state changes
  React.useEffect(() => {
    console.log("State updated:", {
      results: results ? results.length : 0,
      questions: questions ? questions.length : 0,
      options: options ? options.length : 0,
      error,
      loading,
      currentTurn,
    });
  }, [results, questions, options, error, loading, currentTurn]);

  const classifyProduct = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    // This is a NEW search - start fresh conversation
    await startNewClassification(query.trim());
  };

  const refineSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    // This is a REFINED search - start fresh but indicate it's a refinement
    console.log("🔄 REFINING SEARCH from", currentProduct, "to", query.trim());
    await startNewClassification(query.trim(), true);
  };

  const startNewClassification = async (searchQuery, isRefinement = false) => {
    const actionType = isRefinement ? "REFINING" : "STARTING NEW";
    console.log(`🆕 ${actionType} CLASSIFICATION for:`, searchQuery);
    
    setCurrentProduct(searchQuery); // Track current product
    setConversationActive(true);
    setLoading(true);
    
    try {
      console.log("📡 Making API request to /api/classify (NEW)");
      console.log("📡 Session ID:", sessionId);
      
      const response = await fetch(`${API_BASE_URL}/api/classify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          query: searchQuery
        }),
      });

      console.log("📨 Response status:", response.status);
      const data = await response.json();
      console.log("📨 Full response data:", JSON.stringify(data, null, 2));

      if (data.success) {
        console.log(`✅ SUCCESS: ${actionType} classification completed`);
        
        // Handle the new backend response format
        if (data.type === "final_classification" && data.data.results) {
          setResults(data.data.results);
          setQuestions([]);
          setOptions([]);
          setAwaitingResponse(false);
          setConversationActive(false);
        } else if (data.type === "no_results") {
          setResults([]);
          setQuestions([]);
          setOptions([]);
          setAwaitingResponse(false);
          setConversationActive(false);
          setError(data.message || "No HTS classifications found.");
        }
      } else {
        console.log(`❌ FAILURE: ${actionType} classification failed:`, data.error);
        setError(data.error || "Classification failed");
        clearConversationState();
      }
    } catch (err) {
      console.error("💥 NETWORK ERROR:", err);
      setError(`Connection failed: ${err.message}`);
      clearConversationState();
    } finally {
      setLoading(false);
    }
  };

  // Simplified: no conversation continuation needed for RAG backend
  const continueConversation = async (responseText) => {
    // For RAG backend, just treat as new search
    await startNewClassification(responseText);
  };

  // Simplified response handling for RAG backend
  const handleConversationalResponse = (data) => {
    console.log("🎯 handleConversationalResponse called with type:", data.type);
    
    // Clear error first
    setError("");

    // Process response based on type
    if (data.type === 'final_classification' && data.data.results) {
      console.log("🔍 Processing final_classification");
      setResults(data.data.results);
      setQuestions([]);
      setOptions([]);
      setAwaitingResponse(false);
      setConversationActive(false);
    } else if (data.type === 'no_results') {
      console.log("🔍 Processing no_results");
      setResults([]);
      setQuestions([]);
      setOptions([]);
      setAwaitingResponse(false);
      setConversationActive(false);
      setError(data.message || "No HTS classifications found. Try being more specific.");
    } else {
      console.log("❌ Unknown response type:", data.type);
      setError("Unexpected response type: " + data.type);
      setAwaitingResponse(false);
    }
    
    console.log("🔍 handleConversationalResponse completed");
  };

  // Simplified for RAG backend - no options or questions
  const selectOption = async (optionIndex) => {
    console.log("🎯 Selecting option:", optionIndex);
    // Not needed for RAG backend
  };

  const respondToQuestion = async (response) => {
    console.log("📝 Responding to question with:", response);
    // Not needed for RAG backend
  };

  const startNewSearch = async () => {
    console.log("🔄 Starting completely new search...");
    
    // Reset all frontend state (no backend session to clear for RAG)
    setQuery("");
    setCurrentProduct("");
    setResults([]);
    setError("");
    setQuestions([]);
    setOptions([]);
    setCurrentTurn(1);
    setConversationActive(false);
    setAwaitingResponse(false);
  };

  const clearConversationState = () => {
    setQuestions([]);
    setOptions([]);
    setCurrentTurn(1);
    setConversationActive(false);
    setAwaitingResponse(false);
  };

  const getDutyBadgeVariant = (duty) => {
    if (duty === "Free") return "secondary";
    if (duty === "Variable") return "outline";
    return "default";
  };

  const getConfidenceBadgeVariant = (score) => {
    if (score >= 90) return "default";
    if (score >= 70) return "secondary";
    return "outline";
  };

  const getMatchTypeBadge = (type) => {
    const variants = {
      exact: "default",
      fuzzy: "secondary",
      keyword: "outline",
      hierarchy_parts: "destructive",
      general: "outline",
    };
    return variants[type] || "outline";
  };

  // Show refine search button ONLY if we have final results and are NOT awaiting a response to questions
  const showRefineSearch = ((results && results.length > 0) && !awaitingResponse);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-2 sm:p-4" role="main">
      <AccessibilityControls />
      
      <div className="max-w-6xl mx-auto space-y-4 sm:space-y-6">
        {/* Header */}
        <Card className="border-0 shadow-lg bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
          <CardHeader className="text-center p-4 sm:p-6">
            <CardTitle className="text-2xl sm:text-3xl font-bold flex items-center justify-center gap-2">
              <Package className="h-6 w-6 sm:h-8 sm:w-8" />
              <Tooltip 
                content="HTS (Harmonized Tariff Schedule) codes are used to classify imported goods for customs purposes and determine duty rates."
                position="bottom"
              >
                <span>HTS Classifier</span>
              </Tooltip>
            </CardTitle>
            <CardDescription className="text-blue-100 text-sm sm:text-base">
              Enter your product description for instant HTS classification
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Breadcrumb Navigation */}
        <BreadcrumbNav 
          currentProduct={currentProduct}
          conversationActive={conversationActive}
          currentTurn={currentTurn}
          awaitingResponse={awaitingResponse}
          hasResults={results && results.length > 0}
          hasQuestions={questions && questions.length > 0}
          hasOptions={options && options.length > 0}
        />

        {/* Search Form */}
        <Card className="shadow-lg">
          <CardContent className="p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
              <div className="flex-1">
                <label htmlFor="product-search" className="sr-only">
                  Product description for HTS classification
                </label>
                <Input
                  id="product-search"
                  placeholder="e.g., laptop computer, board games, smartphone..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="text-base sm:text-lg h-12"
                  disabled={loading}
                  aria-describedby={currentProduct ? "current-product" : undefined}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      if (showRefineSearch) {
                        refineSearch(e);
                      } else {
                        classifyProduct(e);
                      }
                    }
                    if (e.key === "Escape") {
                      setQuery("");
                    }
                  }}
                />
              </div>
              
              <div className="flex gap-2 sm:gap-3">
                {!showRefineSearch ? (
                  // Initial search button
                  <Button
                    onClick={classifyProduct}
                    size="lg"
                    disabled={loading || !query.trim()}
                    className="px-6 sm:px-8 flex-1 sm:flex-none"
                    aria-label="Start new HTS classification"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        <span className="hidden sm:inline">Searching...</span>
                        <span className="sm:hidden">...</span>
                      </>
                    ) : (
                      <>
                        <Search className="mr-2 h-4 w-4" />
                        <span className="hidden sm:inline">Classify</span>
                        <span className="sm:hidden">Go</span>
                      </>
                    )}
                  </Button>
                ) : (
                  // Refine search and start over buttons when results exist
                  <>
                    <Tooltip content="Search for a different variation of the same product type" position="top">
                      <Button
                        onClick={refineSearch}
                        size="lg"
                        disabled={loading || !query.trim()}
                        variant="default"
                        className="px-4 sm:px-6 flex-1 sm:flex-none"
                        aria-label="Refine current search with new description"
                      >
                        {loading ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            <span className="hidden sm:inline">Refining...</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="mr-2 h-4 w-4" />
                            <span className="hidden sm:inline">Refine</span>
                            <span className="sm:hidden">Refine</span>
                          </>
                        )}
                      </Button>
                    </Tooltip>
                    
                    <Tooltip content="Start completely over with a new product" position="top">
                      <Button
                        onClick={startNewSearch}
                        size="lg"
                        variant="outline"
                        className="px-4 sm:px-6"
                        aria-label="Start completely new classification"
                      >
                        <RotateCcw className="mr-2 h-4 w-4" />
                        <span className="hidden sm:inline">New</span>
                        <span className="sm:hidden">New</span>
                      </Button>
                    </Tooltip>
                  </>
                )}
              </div>
            </div>

            {/* Action descriptions for clarity */}
            {showRefineSearch && (
              <div className="mt-3 p-3 bg-gray-50 rounded-lg text-sm text-gray-700">
                <div className="flex flex-col sm:flex-row gap-2 sm:gap-4">
                  <div className="flex items-start gap-2">
                    <Sparkles className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <strong>Refine:</strong> Try different keywords for the same product type
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <RotateCcw className="h-4 w-4 text-gray-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <strong>New:</strong> Start over with a completely different product
                    </div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Clarifying Questions */}
        {questions && questions.length > 0 && (
          <Card className="shadow-lg border-orange-200 bg-orange-50" role="region" aria-labelledby="questions-heading">
            <CardHeader className="bg-gradient-to-r from-orange-100 to-yellow-100">
              <CardTitle id="questions-heading" className="flex items-center gap-2 text-orange-800">
                <Info className="h-5 w-5" aria-hidden="true" />
                I need more information (Turn {currentTurn})
              </CardTitle>
              <CardDescription className="text-orange-700">
                Please help me narrow down the classification by answering these
                questions:
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 p-4 sm:p-6">
              <div role="list" aria-label="Clarifying questions">
                {questions.map((question, index) => (
                  <div
                    key={index}
                    role="listitem"
                    className="p-3 bg-white rounded-lg border border-orange-200 mb-3"
                  >
                    <p className="font-medium text-orange-900">{question}</p>
                  </div>
                ))}
              </div>
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                <label htmlFor="question-answer" className="sr-only">
                  Your answer to the clarifying questions
                </label>
                <Input
                  id="question-answer"
                  placeholder="Your answer..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      respondToQuestion(query);
                    }
                  }}
                  className="flex-1"
                  aria-describedby="questions-heading"
                />
                <Button
                  onClick={() => respondToQuestion(query)}
                  disabled={loading || !query.trim()}
                  className="w-full sm:w-auto"
                  aria-label="Submit answer to clarifying questions"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  ) : (
                    "Answer"
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Multiple Options Selection */}
        {options && options.length > 0 && (
          <Card className="shadow-lg border-blue-200 bg-blue-50" role="region" aria-labelledby="options-heading">
            <CardHeader className="bg-gradient-to-r from-blue-100 to-indigo-100">
              <CardTitle id="options-heading" className="flex items-center gap-2 text-blue-800">
                <Package className="h-5 w-5" aria-hidden="true" />
                Multiple matches found
              </CardTitle>
              <CardDescription className="text-blue-700">
                Please select the option that best describes your product:
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 p-4 sm:p-6">
              <div role="radiogroup" aria-labelledby="options-heading">
                {options.map((option) => (
                  <button
                    key={option.index}
                    onClick={() => selectOption(option.index)}
                    disabled={loading}
                    role="radio"
                    aria-checked="false"
                    aria-labelledby={`option-${option.index}-label`}
                    aria-describedby={`option-${option.index}-details`}
                    className="w-full text-left p-4 bg-white rounded-lg border border-blue-200 hover:border-blue-400 hover:bg-blue-50 transition-colors disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div id={`option-${option.index}-label`} className="font-semibold text-blue-900">
                          {option.index}. {option.hts_code}
                        </div>
                        <div id={`option-${option.index}-details`} className="text-sm text-blue-700 mt-1">
                          {option.description}
                        </div>
                        <div className="flex flex-wrap gap-2 mt-2">
                          <Tooltip 
                            content="How well this option matches your product description"
                            position="top"
                          >
                            <Badge variant="outline" className="text-xs">
                              {option.confidence_score}% match
                            </Badge>
                          </Tooltip>
                          <Tooltip 
                            content="The import duty rate for this classification"
                            position="top"
                          >
                            <Badge
                              variant={getDutyBadgeVariant(option.effective_duty)}
                              className="text-xs"
                            >
                              {option.effective_duty}
                            </Badge>
                          </Tooltip>
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results */}
        {results && results.length > 0 && (
          <section className="space-y-4 sm:space-y-6" role="region" aria-labelledby="results-heading">
            <div className="flex items-center gap-2">
              <Info className="h-5 w-5 text-blue-600" aria-hidden="true" />
              <h2 id="results-heading" className="text-lg sm:text-xl font-semibold">
                Found {results.length} HTS Classification
                {results.length > 1 ? "s" : ""}
              </h2>
            </div>

            {results.map((result, index) => (
              <Card key={result.hts_code || index} className="shadow-lg">
                <CardHeader className="bg-gradient-to-r from-slate-50 to-slate-100">
                  <CardTitle className="flex items-center justify-between">
                    <span className="text-xl">
                      <Tooltip 
                        content="HTS codes are 10-digit numbers that classify products for import/export purposes. Each digit adds more specificity to the classification."
                        position="bottom"
                      >
                        <span>HTS Result {index + 1}: {result.hts_code}</span>
                      </Tooltip>
                    </span>
                    <div className="flex gap-2">
                      <Tooltip 
                        content="Confidence score indicates how well your product matches this HTS code. 90%+ is excellent, 70-89% is good, below 70% may need refinement."
                        position="bottom"
                      >
                        <Badge
                          variant={getConfidenceBadgeVariant(
                            result.confidence_score
                          )}
                        >
                          {result.confidence_score}% confidence
                        </Badge>
                      </Tooltip>
                      <Tooltip 
                        content={`Match type: ${result.match_type === 'exact' ? 'Exact text match found' : result.match_type === 'fuzzy' ? 'Similar text match found' : result.match_type === 'keyword' ? 'Key words matched' : 'General category match'}`}
                        position="bottom"
                      >
                        <Badge variant={getMatchTypeBadge(result.match_type)}>
                          {result.match_type}
                        </Badge>
                      </Tooltip>
                    </div>
                  </CardTitle>
                  <CardDescription className="text-base">
                    {result.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-4">
                  {/* Summary View */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-800 font-mono">
                        {result.hts_code}
                      </div>
                      <div className="text-sm text-blue-600">HTS Code</div>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-800">
                        <Tooltip 
                          content="The duty rate applied to imports of this product. 'Free' means no duty is charged."
                          position="top"
                        >
                          <span>{result.effective_duty}</span>
                        </Tooltip>
                      </div>
                      <div className="text-sm text-green-600">Duty Rate</div>
                    </div>
                    <div className="text-center p-3 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-800">
                        {result.confidence_score}%
                      </div>
                      <div className="text-sm text-purple-600">Confidence</div>
                    </div>
                  </div>

                  {/* Detailed Information - Collapsible */}
                  <Collapsible 
                    title="Customs Clearance & Documentation Requirements"
                    defaultOpen={false}
                    className="mt-4"
                  >
                    <div className="pt-4">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="w-1/3 font-semibold">
                              Requirement
                            </TableHead>
                            <TableHead className="font-semibold">Details</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {result.unit && (
                            <TableRow>
                              <TableCell className="font-medium bg-slate-50">
                                <Tooltip 
                                  content="The unit of measurement used for statistical and duty calculation purposes (e.g., pieces, kilograms, liters)"
                                  position="right"
                                >
                                  <span>Unit of Quantity</span>
                                </Tooltip>
                              </TableCell>
                              <TableCell>{result.unit}</TableCell>
                            </TableRow>
                          )}
                          <TableRow>
                            <TableCell className="font-medium bg-slate-50">
                              <Tooltip 
                                content="US government agencies that may need to inspect or approve your goods before customs clearance"
                                position="right"
                              >
                                <span>Regulatory Agencies</span>
                              </Tooltip>
                            </TableCell>
                            <TableCell>
                              <div className="space-y-1">
                                {/* Food and Agricultural Products */}
                                {(result.hts_code.startsWith('01') || result.hts_code.startsWith('02') || result.hts_code.startsWith('03') || 
                                  result.hts_code.startsWith('04') || result.hts_code.startsWith('07') || result.hts_code.startsWith('08') || 
                                  result.hts_code.startsWith('09') || result.hts_code.startsWith('10') || result.hts_code.startsWith('11') || 
                                  result.hts_code.startsWith('12') || result.hts_code.startsWith('13') || result.hts_code.startsWith('14') || 
                                  result.hts_code.startsWith('15') || result.hts_code.startsWith('16') || result.hts_code.startsWith('17') || 
                                  result.hts_code.startsWith('18') || result.hts_code.startsWith('19') || result.hts_code.startsWith('20') || 
                                  result.hts_code.startsWith('21') || result.hts_code.startsWith('22') || result.hts_code.startsWith('23') || 
                                  result.hts_code.startsWith('24')) && (
                                  <>
                                    <Badge variant="secondary" className="mr-1 mb-1">FDA - Food & Drug Administration</Badge>
                                    <Badge variant="secondary" className="mr-1 mb-1">APHIS - Animal & Plant Health Inspection</Badge>
                                  </>
                                )}
                                
                                {/* Wildlife and Fish Products */}
                                {(result.hts_code.startsWith('03') || result.hts_code.startsWith('05') || 
                                  result.hts_code.startsWith('41') || result.hts_code.startsWith('42') || 
                                  result.hts_code.startsWith('43')) && (
                                  <Badge variant="secondary" className="mr-1 mb-1">FWS - Fish & Wildlife Service</Badge>
                                )}
                                
                                {/* Textiles and Consumer Products */}
                                {(result.hts_code.startsWith('50') || result.hts_code.startsWith('51') || result.hts_code.startsWith('52') || 
                                  result.hts_code.startsWith('53') || result.hts_code.startsWith('54') || result.hts_code.startsWith('55') || 
                                  result.hts_code.startsWith('56') || result.hts_code.startsWith('57') || result.hts_code.startsWith('58') || 
                                  result.hts_code.startsWith('59') || result.hts_code.startsWith('60') || result.hts_code.startsWith('61') || 
                                  result.hts_code.startsWith('62') || result.hts_code.startsWith('63')) && (
                                  <Badge variant="secondary" className="mr-1 mb-1">CPSC - Consumer Product Safety Commission</Badge>
                                )}
                                
                                {/* Electronics and Communications */}
                                {(result.hts_code.startsWith('84') || result.hts_code.startsWith('85')) && (
                                  <Badge variant="secondary" className="mr-1 mb-1">FCC - Federal Communications Commission</Badge>
                                )}
                                
                                {/* Vehicles */}
                                {result.hts_code.startsWith('87') && (
                                  <>
                                    <Badge variant="secondary" className="mr-1 mb-1">NHTSA - National Highway Traffic Safety</Badge>
                                    <Badge variant="secondary" className="mr-1 mb-1">EPA - Environmental Protection Agency</Badge>
                                  </>
                                )}
                                
                                {/* Medical Devices and Pharmaceuticals */}
                                {(result.hts_code.startsWith('30') || result.hts_code.startsWith('90')) && (
                                  <Badge variant="secondary" className="mr-1 mb-1">FDA - Food & Drug Administration</Badge>
                                )}
                                
                                {/* Chemicals */}
                                {result.hts_code.startsWith('28') && (
                                  <Badge variant="secondary" className="mr-1 mb-1">EPA - Environmental Protection Agency</Badge>
                                )}
                                
                                {/* Firearms and Ammunition */}
                                {result.hts_code.startsWith('93') && (
                                  <Badge variant="secondary" className="mr-1 mb-1">ATF - Bureau of Alcohol, Tobacco, Firearms</Badge>
                                )}
                                
                                {/* Precious Metals */}
                                {result.hts_code.startsWith('71') && (
                                  <Badge variant="secondary" className="mr-1 mb-1">OFAC - Office of Foreign Assets Control</Badge>
                                )}
                                
                                {/* Alcoholic Beverages */}
                                {result.hts_code.startsWith('2203') || result.hts_code.startsWith('2204') || 
                                 result.hts_code.startsWith('2205') || result.hts_code.startsWith('2206') || 
                                 result.hts_code.startsWith('2207') || result.hts_code.startsWith('2208') ? (
                                  <Badge variant="secondary" className="mr-1 mb-1">TTB - Alcohol & Tobacco Tax Bureau</Badge>
                                ) : null}
                                
                                {/* Tobacco Products */}
                                {result.hts_code.startsWith('24') && (
                                  <Badge variant="secondary" className="mr-1 mb-1">TTB - Alcohol & Tobacco Tax Bureau</Badge>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell className="font-medium bg-slate-50">
                              <Tooltip 
                                content="Required documentation for customs clearance and regulatory compliance"
                                position="right"
                              >
                                <span>Required Documents</span>
                              </Tooltip>
                            </TableCell>
                            <TableCell>
                              <div className="space-y-2">
                                <div className="text-sm">
                                  <strong>Standard Requirements:</strong>
                                  <ul className="list-disc list-inside mt-1 text-gray-700">
                                    <li>Commercial Invoice</li>
                                    <li>Bill of Lading / Airway Bill</li>
                                    <li>Packing List</li>
                                    <li>Entry Summary (CBP Form 7501)</li>
                                  </ul>
                                </div>
                                {(result.hts_code.startsWith('21') || result.hts_code.startsWith('90')) && (
                                  <div className="text-sm">
                                    <strong>FDA Requirements:</strong>
                                    <ul className="list-disc list-inside mt-1 text-gray-700">
                                      <li>FDA Registration</li>
                                      <li>Prior Notice (for food)</li>
                                      <li>510(k) Clearance (medical devices)</li>
                                    </ul>
                                  </div>
                                )}
                                {(result.hts_code.startsWith('84') || result.hts_code.startsWith('85')) && (
                                  <div className="text-sm">
                                    <strong>FCC Requirements:</strong>
                                    <ul className="list-disc list-inside mt-1 text-gray-700">
                                      <li>Equipment Authorization</li>
                                      <li>FCC ID (if required)</li>
                                      <li>Declaration of Conformity</li>
                                    </ul>
                                  </div>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                          {result.special_duty && (
                            <TableRow>
                              <TableCell className="font-medium bg-slate-50">
                                <Tooltip 
                                  content="Additional duties that may apply beyond the standard rate"
                                  position="right"
                                >
                                  <span>Special Duties</span>
                                </Tooltip>
                              </TableCell>
                              <TableCell>{result.special_duty}</TableCell>
                            </TableRow>
                          )}
                          <TableRow>
                            <TableCell className="font-medium bg-slate-50">
                              <Tooltip 
                                content="Estimated timeframe for customs clearance based on product type and regulatory requirements"
                                position="right"
                              >
                                <span>Processing Time</span>
                              </Tooltip>
                            </TableCell>
                            <TableCell>
                              <div className="space-y-1">
                                <div>Standard clearance: 1-3 business days</div>
                                {(result.hts_code.startsWith('21') || result.hts_code.startsWith('90')) && (
                                  <div className="text-amber-700">FDA review may add 2-5 business days</div>
                                )}
                                {(result.hts_code.startsWith('84') || result.hts_code.startsWith('85')) && (
                                  <div className="text-amber-700">FCC verification may add 1-2 business days</div>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell className="font-medium bg-slate-50">
                              <Tooltip 
                                content="Official HTS database and detailed classification information"
                                position="right"
                              >
                                <span>Official Reference</span>
                              </Tooltip>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline">
                                  {result.duty_source === "stored"
                                    ? "Direct Rate"
                                    : result.duty_source === "inherited"
                                    ? "Inherited from Parent"
                                    : result.duty_source}
                                </Badge>
                                <a
                                  href={`https://hts.usitc.gov/search?query=${formatHtsCodeForUSITC(result.hts_code)}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 text-sm font-medium"
                                >
                                  View on USITC
                                  <ExternalLink className="h-3 w-3" />
                                </a>
                              </div>
                            </TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </div>
                  </Collapsible>
                </CardContent>
              </Card>
            ))}
          </section>
        )}


        {/* No Results */}
        {!loading &&
          !error &&
          (!results || results.length === 0) &&
          (!questions || questions.length === 0) &&
          (!options || options.length === 0) &&
          query && (
            <Card className="shadow-lg">
              <CardContent className="text-center py-12">
                <Package className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  No Results Found
                </h3>
                <p className="text-gray-600">
                  No HTS classifications found for your search. Try using
                  different keywords or being more specific.
                </p>
              </CardContent>
            </Card>
          )}

        {/* Info Footer */}
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-blue-600 mt-0.5" />
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">How it works:</p>
                <p>
                  Our experienced customs broker AI reviews your product, searches the HTS database, 
                  and asks up to 3 clarifying questions to find the correct classification. 
                  Use "Refine Search" to try a different product while keeping your session, 
                  or "Start New Classification" to completely start over.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default App;
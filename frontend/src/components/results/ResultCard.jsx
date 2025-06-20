import React, { useState, useRef } from "react";
import { ChevronDown, ChevronUp, ExternalLink, Copy, FileText, AlertCircle, CheckCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible } from "@/components/ui/collapsible";

// Utility function to format HTS codes for USITC links
const formatHtsCodeForUSITC = (htsCode) => {
  if (!htsCode) return htsCode;
  if (htsCode.endsWith('00')) {
    return htsCode.slice(0, -2);
  }
  return htsCode;
};

const ResultCard = ({ result, index, isHighlighted = false }) => {
  const [isExpanded, setIsExpanded] = useState(index === 0); // First result expanded by default
  const [copySuccess, setCopySuccess] = useState(false);
  const cardRef = useRef(null);
  const touchStartRef = useRef({ x: 0, y: 0, time: 0 });
  
  const handleCopyHTS = async () => {
    try {
      await navigator.clipboard.writeText(result.hts_code);
      setCopySuccess(true);
      // Reset success state after 2 seconds
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy HTS code:', err);
    }
  };

  // Mobile-specific touch handlers for swipe gestures
  const handleTouchStart = (e) => {
    const touch = e.touches[0];
    touchStartRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now()
    };
    
    // Add subtle scale effect on touch start for mobile feedback
    if (cardRef.current && window.innerWidth <= 768) {
      cardRef.current.style.transform = 'scale(0.98)';
      cardRef.current.style.transition = 'transform 0.1s ease';
    }
  };

  const handleTouchEnd = (e) => {
    const touch = e.changedTouches[0];
    const deltaX = touch.clientX - touchStartRef.current.x;
    const deltaY = touch.clientY - touchStartRef.current.y;
    const deltaTime = Date.now() - touchStartRef.current.time;
    
    // Reset scale effect
    if (cardRef.current && window.innerWidth <= 768) {
      cardRef.current.style.transform = 'scale(1)';
    }
    
    // Detect swipe gesture (only on mobile)
    if (window.innerWidth <= 768 && deltaTime < 300) {
      const minSwipeDistance = 50;
      
      // Vertical swipe to toggle expand/collapse
      if (Math.abs(deltaY) > minSwipeDistance && Math.abs(deltaY) > Math.abs(deltaX)) {
        if (deltaY < 0) {
          // Swipe up to expand
          setIsExpanded(true);
        } else {
          // Swipe down to collapse
          setIsExpanded(false);
        }
      }
    }
  };

  const getConfidenceColor = (score) => {
    if (score >= 90) return "bg-green-100 text-green-800 border-green-200";
    if (score >= 80) return "bg-blue-100 text-blue-800 border-blue-200";
    if (score >= 70) return "bg-yellow-100 text-yellow-800 border-yellow-200";
    return "bg-gray-100 text-gray-800 border-gray-200";
  };

  const getMatchTypeDisplay = (matchType) => {
    const types = {
      'csv_lookup': { label: 'Official HTS Data', color: 'bg-green-100 text-green-800', icon: CheckCircle },
      'ai_analysis': { label: 'AI Analysis', color: 'bg-blue-100 text-blue-800', icon: AlertCircle },
      'rag_search': { label: 'Database Match', color: 'bg-purple-100 text-purple-800', icon: CheckCircle }
    };
    return types[matchType] || { label: matchType, color: 'bg-gray-100 text-gray-800', icon: AlertCircle };
  };

  const matchTypeInfo = getMatchTypeDisplay(result.match_type);
  const IconComponent = matchTypeInfo.icon;

  return (
    <Card 
      ref={cardRef}
      className={`transition-all duration-200 ${
        isHighlighted 
          ? 'border-2 border-blue-500 shadow-lg bg-blue-50' 
          : 'border border-gray-200 hover:shadow-md'
      } touch-manipulation`}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            {/* Priority indicator for first result */}
            {index === 0 && (
              <div className="flex items-center space-x-2 mb-2">
                <Badge className="bg-blue-600 text-white">PRIMARY CLASSIFICATION</Badge>
              </div>
            )}
            
            {/* HTS Code - Large and prominent */}
            <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-3 mb-3">
              <div className={`px-3 sm:px-4 py-2 rounded-lg border-2 text-center sm:text-left ${
                index === 0 ? 'bg-blue-100 border-blue-300' : 'bg-gray-100 border-gray-300'
              }`}>
                <span className={`text-lg sm:text-xl lg:text-2xl font-bold break-all ${
                  index === 0 ? 'text-blue-900' : 'text-gray-900'
                }`}>
                  {result.hts_code}
                </span>
              </div>
              
              {/* Quick action buttons */}
              <div className="flex space-x-2 justify-center sm:justify-start">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopyHTS}
                  className={`flex items-center space-x-1 text-xs sm:text-sm transition-colors duration-200 ${
                    copySuccess ? 'bg-green-100 border-green-300 text-green-700' : ''
                  }`}
                >
                  <Copy className="h-3 w-3 sm:h-4 sm:w-4" />
                  <span>{copySuccess ? 'Copied!' : 'Copy'}</span>
                </Button>
                
                <a
                  href={`https://hts.usitc.gov/search?query=${formatHtsCodeForUSITC(result.hts_code)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="outline" size="sm" className="flex items-center space-x-1 text-xs sm:text-sm">
                    <ExternalLink className="h-3 w-3 sm:h-4 sm:w-4" />
                    <span>USITC</span>
                  </Button>
                </a>
              </div>
            </div>

            {/* Key information - always visible */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mb-4">
              <div>
                <p className="text-sm font-medium text-gray-600">Effective Duty</p>
                <p className={`text-lg font-semibold ${
                  result.effective_duty === 'Free' ? 'text-green-600' : 'text-gray-900'
                }`}>
                  {result.effective_duty || 'Not available'}
                </p>
              </div>
              
              <div>
                <p className="text-sm font-medium text-gray-600">Confidence</p>
                <Badge className={`${getConfidenceColor(result.confidence_score)} border`}>
                  {result.confidence_score}% match
                </Badge>
              </div>
              
              <div>
                <p className="text-sm font-medium text-gray-600">Data Source</p>
                <Badge className={`${matchTypeInfo.color} border flex items-center space-x-1`}>
                  <IconComponent className="h-3 w-3" />
                  <span>{matchTypeInfo.label}</span>
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </CardHeader>

      {/* Collapsible detailed information */}
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CardContent className="pt-0">
          {/* Toggle button */}
          <Button
            variant="ghost"
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full flex items-center justify-center space-x-2 mb-4 border-t pt-4"
          >
            <span className="font-medium">
              {isExpanded ? 'Hide Details' : 'Show Details'}
            </span>
            {isExpanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>

          {/* Detailed information - only shown when expanded */}
          {isExpanded && (
            <div className="space-y-6">
              {/* Description */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Product Description</h4>
                <p className="text-gray-700 leading-relaxed">{result.description}</p>
              </div>

              {/* Technical Details */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Classification Details</h4>
                <div className="bg-gray-50 rounded-lg p-3 sm:p-4">
                  {/* Mobile-friendly list layout */}
                  <div className="space-y-3 sm:hidden">
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-600 text-sm">HTS Chapter</span>
                      <span className="text-gray-900 text-sm">{result.chapter}</span>
                    </div>
                    
                    {result.unit && (
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-600 text-sm">Unit of Quantity</span>
                        <span className="text-gray-900 text-sm">{result.unit}</span>
                      </div>
                    )}
                    
                    {result.special_duty && (
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-600 text-sm">Special Duty</span>
                        <span className="text-gray-900 text-sm">{result.special_duty}</span>
                      </div>
                    )}
                    
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-600 text-sm">Data Source</span>
                      <span className="text-gray-900 text-sm capitalize">{result.duty_source}</span>
                    </div>
                  </div>
                  
                  {/* Desktop table layout */}
                  <table className="w-full text-sm hidden sm:table">
                    <tbody className="space-y-2">
                      <tr className="border-b border-gray-200">
                        <td className="py-2 font-medium text-gray-600">HTS Chapter</td>
                        <td className="py-2 text-gray-900">{result.chapter}</td>
                      </tr>
                      
                      {result.unit && (
                        <tr className="border-b border-gray-200">
                          <td className="py-2 font-medium text-gray-600">Unit of Quantity</td>
                          <td className="py-2 text-gray-900">{result.unit}</td>
                        </tr>
                      )}
                      
                      {result.special_duty && (
                        <tr className="border-b border-gray-200">
                          <td className="py-2 font-medium text-gray-600">Special Duty Rates</td>
                          <td className="py-2 text-gray-900">{result.special_duty}</td>
                        </tr>
                      )}
                      
                      <tr>
                        <td className="py-2 font-medium text-gray-600">Data Source</td>
                        <td className="py-2 text-gray-900 capitalize">{result.duty_source}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex flex-col sm:flex-row flex-wrap gap-2 sm:gap-3 pt-4 border-t">
                <Button className="flex items-center justify-center space-x-2 w-full sm:w-auto">
                  <FileText className="h-4 w-4" />
                  <span>Generate Report</span>
                </Button>
                
                <Button variant="outline" className="flex items-center justify-center space-x-2 w-full sm:w-auto">
                  <span>Save to Favorites</span>
                </Button>
                
                <Button variant="outline" className="flex items-center justify-center space-x-2 w-full sm:w-auto">
                  <span>Search Similar</span>
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Collapsible>
    </Card>
  );
};

export default ResultCard;
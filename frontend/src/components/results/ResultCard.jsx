import React, { useState } from "react";
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
  
  const handleCopyHTS = async () => {
    try {
      await navigator.clipboard.writeText(result.hts_code);
      // You could add a toast notification here
    } catch (err) {
      console.error('Failed to copy HTS code:', err);
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
    <Card className={`transition-all duration-200 ${
      isHighlighted 
        ? 'border-2 border-blue-500 shadow-lg bg-blue-50' 
        : 'border border-gray-200 hover:shadow-md'
    }`}>
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
            <div className="flex items-center space-x-3 mb-3">
              <div className={`px-4 py-2 rounded-lg border-2 ${
                index === 0 ? 'bg-blue-100 border-blue-300' : 'bg-gray-100 border-gray-300'
              }`}>
                <span className={`text-2xl font-bold ${
                  index === 0 ? 'text-blue-900' : 'text-gray-900'
                }`}>
                  {result.hts_code}
                </span>
              </div>
              
              {/* Quick action buttons */}
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopyHTS}
                  className="flex items-center space-x-1"
                >
                  <Copy className="h-4 w-4" />
                  <span>Copy</span>
                </Button>
                
                <a
                  href={`https://hts.usitc.gov/search?query=${formatHtsCodeForUSITC(result.hts_code)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="outline" size="sm" className="flex items-center space-x-1">
                    <ExternalLink className="h-4 w-4" />
                    <span>USITC</span>
                  </Button>
                </a>
              </div>
            </div>

            {/* Key information - always visible */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
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

              {/* Technical Details Table */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Classification Details</h4>
                <div className="bg-gray-50 rounded-lg p-4">
                  <table className="w-full text-sm">
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
              <div className="flex flex-wrap gap-3 pt-4 border-t">
                <Button className="flex items-center space-x-2">
                  <FileText className="h-4 w-4" />
                  <span>Generate Report</span>
                </Button>
                
                <Button variant="outline" className="flex items-center space-x-2">
                  <span>Save to Favorites</span>
                </Button>
                
                <Button variant="outline" className="flex items-center space-x-2">
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
import React, { useState } from "react";
import { FileText, Download, RefreshCw, AlertCircle, CheckCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import ResultCard from "./ResultCard";

const ResultsContainer = ({ 
  results, 
  currentProduct,
  claudeAnalysis,
  onNewSearch,
  onExportPDF 
}) => {
  const [selectedResults, setSelectedResults] = useState([]);

  if (!results || results.length === 0) {
    return (
      <Card className="border-2 border-yellow-200 bg-yellow-50 mx-2 sm:mx-0">
        <CardContent className="p-4 sm:p-8 text-center">
          <AlertCircle className="h-8 w-8 sm:h-12 sm:w-12 text-yellow-600 mx-auto mb-3 sm:mb-4" />
          <h3 className="text-lg sm:text-xl font-semibold text-yellow-800 mb-2">
            No Classifications Found
          </h3>
          <p className="text-sm sm:text-base text-yellow-700 mb-4 px-2">
            We couldn't find any HTS classifications for your product. 
            Try being more specific or using different keywords.
          </p>
          <Button onClick={onNewSearch} variant="outline" className="w-full sm:w-auto">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Another Search
          </Button>
        </CardContent>
      </Card>
    );
  }

  const handleSelectResult = (index) => {
    setSelectedResults(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Results Header */}
      <Card className="border-2 border-green-200 bg-green-50 mx-2 sm:mx-0">
        <CardHeader className="pb-3 sm:pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <div className="flex items-center space-x-2 sm:space-x-3">
              <CheckCircle className="h-6 w-6 sm:h-8 sm:w-8 text-green-600 flex-shrink-0" />
              <div className="min-w-0">
                <CardTitle className="text-lg sm:text-2xl text-green-900">
                  Classification Complete
                </CardTitle>
                <p className="text-sm sm:text-base text-green-700 mt-1 truncate">
                  Found {results.length} HTS classification{results.length !== 1 ? 's' : ''} for "{currentProduct}"
                </p>
              </div>
            </div>
            
            {/* Action buttons */}
            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
              <Button 
                onClick={() => onExportPDF && onExportPDF(results)}
                className="flex items-center justify-center space-x-2 w-full sm:w-auto"
                size="sm"
              >
                <FileText className="h-4 w-4" />
                <span className="hidden sm:inline">Export PDF</span>
                <span className="sm:hidden">Export</span>
              </Button>
              
              <Button 
                variant="outline"
                onClick={onNewSearch}
                className="flex items-center justify-center space-x-2 w-full sm:w-auto"
                size="sm"
              >
                <RefreshCw className="h-4 w-4" />
                <span className="hidden sm:inline">New Search</span>
                <span className="sm:hidden">New</span>
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Classification Results */}
      <div className="space-y-3 sm:space-y-4 mx-2 sm:mx-0">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900">
            HTS Classifications
          </h2>
          
          {results.length > 1 && (
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs sm:text-sm">
                {results.length} options found
              </Badge>
            </div>
          )}
        </div>

        {/* Important notice for multiple results */}
        {results.length > 1 && (
          <Alert className="border-blue-200 bg-blue-50">
            <AlertCircle className="h-4 w-4 text-blue-600 flex-shrink-0" />
            <AlertDescription className="text-blue-800 text-sm sm:text-base">
              <strong>Multiple classifications found.</strong> The first result is typically the most accurate. 
              Review all options and consult with a customs broker for final determination.
            </AlertDescription>
          </Alert>
        )}

        {/* Results Cards */}
        <div className="space-y-4">
          {results.map((result, index) => (
            <ResultCard
              key={`${result.hts_code}-${index}`}
              result={result}
              index={index}
              isHighlighted={index === 0}
            />
          ))}
        </div>
      </div>

      {/* Claude Analysis Section */}
      {claudeAnalysis && (
        <Card className="border border-gray-200 mx-2 sm:mx-0">
          <CardHeader className="pb-3 sm:pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
              <CardTitle className="text-lg sm:text-xl text-gray-900">
                AI Analysis & Recommendations
              </CardTitle>
              <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200 text-xs sm:text-sm">
                Additional Insights
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="prose prose-sm max-w-none">
              <div className="bg-gray-50 rounded-lg p-3 sm:p-4 border">
                <pre className="whitespace-pre-wrap text-xs sm:text-sm text-gray-700 font-sans leading-relaxed">
                  {claudeAnalysis}
                </pre>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Next Steps Card */}
      <Card className="border border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 mx-2 sm:mx-0">
        <CardHeader>
          <CardTitle className="text-lg sm:text-xl text-blue-900">
            Next Steps
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
            <div className="space-y-3">
              <h4 className="font-semibold text-blue-800 text-sm sm:text-base">For Import/Export:</h4>
              <ul className="space-y-2 text-blue-700">
                <li className="flex items-start space-x-2">
                  <span className="text-blue-500 flex-shrink-0">•</span>
                  <span className="text-sm sm:text-base">Verify classification with customs broker</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-blue-500 flex-shrink-0">•</span>
                  <span className="text-sm sm:text-base">Check current duty rates and trade agreements</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-blue-500 flex-shrink-0">•</span>
                  <span className="text-sm sm:text-base">Review regulatory requirements</span>
                </li>
              </ul>
            </div>
            
            <div className="space-y-3">
              <h4 className="font-semibold text-blue-800 text-sm sm:text-base">Documentation Needed:</h4>
              <ul className="space-y-2 text-blue-700">
                <li className="flex items-start space-x-2">
                  <span className="text-blue-500 flex-shrink-0">•</span>
                  <span className="text-sm sm:text-base">Commercial invoice</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-blue-500 flex-shrink-0">•</span>
                  <span className="text-sm sm:text-base">Certificate of origin</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-blue-500 flex-shrink-0">•</span>
                  <span className="text-sm sm:text-base">Product specifications</span>
                </li>
              </ul>
            </div>
          </div>
          
          <div className="mt-4 sm:mt-6 pt-3 sm:pt-4 border-t border-blue-200">
            <div className="flex flex-col sm:flex-row sm:flex-wrap gap-2 sm:gap-3">
              <Button 
                variant="outline" 
                className="border-blue-300 text-blue-700 hover:bg-blue-100 w-full sm:w-auto text-sm"
                size="sm"
              >
                Find Customs Broker
              </Button>
              <Button 
                variant="outline" 
                className="border-blue-300 text-blue-700 hover:bg-blue-100 w-full sm:w-auto text-sm"
                size="sm"
              >
                Check Trade Agreements
              </Button>
              <Button 
                variant="outline" 
                className="border-blue-300 text-blue-700 hover:bg-blue-100 w-full sm:w-auto text-sm"
                size="sm"
              >
                View Regulatory Info
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ResultsContainer;
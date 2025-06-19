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
      <Card className="border-2 border-yellow-200 bg-yellow-50">
        <CardContent className="p-8 text-center">
          <AlertCircle className="h-12 w-12 text-yellow-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-yellow-800 mb-2">
            No Classifications Found
          </h3>
          <p className="text-yellow-700 mb-4">
            We couldn't find any HTS classifications for your product. 
            Try being more specific or using different keywords.
          </p>
          <Button onClick={onNewSearch} variant="outline">
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
    <div className="space-y-6">
      {/* Results Header */}
      <Card className="border-2 border-green-200 bg-green-50">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CheckCircle className="h-8 w-8 text-green-600" />
              <div>
                <CardTitle className="text-2xl text-green-900">
                  Classification Complete
                </CardTitle>
                <p className="text-green-700 mt-1">
                  Found {results.length} HTS classification{results.length !== 1 ? 's' : ''} for "{currentProduct}"
                </p>
              </div>
            </div>
            
            {/* Action buttons */}
            <div className="flex space-x-3">
              <Button 
                onClick={() => onExportPDF && onExportPDF(results)}
                className="flex items-center space-x-2"
              >
                <FileText className="h-4 w-4" />
                <span>Export PDF</span>
              </Button>
              
              <Button 
                variant="outline"
                onClick={onNewSearch}
                className="flex items-center space-x-2"
              >
                <RefreshCw className="h-4 w-4" />
                <span>New Search</span>
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Classification Results */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">
            HTS Classifications
          </h2>
          
          {results.length > 1 && (
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                {results.length} options found
              </Badge>
            </div>
          )}
        </div>

        {/* Important notice for multiple results */}
        {results.length > 1 && (
          <Alert className="border-blue-200 bg-blue-50">
            <AlertCircle className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800">
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
        <Card className="border border-gray-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl text-gray-900">
                AI Analysis & Recommendations
              </CardTitle>
              <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
                Additional Insights
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none">
              <div className="bg-gray-50 rounded-lg p-4 border">
                <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans leading-relaxed">
                  {claudeAnalysis}
                </pre>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Next Steps Card */}
      <Card className="border border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardHeader>
          <CardTitle className="text-xl text-blue-900">
            Next Steps
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <h4 className="font-semibold text-blue-800">For Import/Export:</h4>
              <ul className="space-y-2 text-blue-700">
                <li className="flex items-start space-x-2">
                  <span className="text-blue-500">•</span>
                  <span>Verify classification with customs broker</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-blue-500">•</span>
                  <span>Check current duty rates and trade agreements</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-blue-500">•</span>
                  <span>Review regulatory requirements</span>
                </li>
              </ul>
            </div>
            
            <div className="space-y-3">
              <h4 className="font-semibold text-blue-800">Documentation Needed:</h4>
              <ul className="space-y-2 text-blue-700">
                <li className="flex items-start space-x-2">
                  <span className="text-blue-500">•</span>
                  <span>Commercial invoice</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-blue-500">•</span>
                  <span>Certificate of origin</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-blue-500">•</span>
                  <span>Product specifications</span>
                </li>
              </ul>
            </div>
          </div>
          
          <div className="mt-6 pt-4 border-t border-blue-200">
            <div className="flex flex-wrap gap-3">
              <Button variant="outline" className="border-blue-300 text-blue-700 hover:bg-blue-100">
                Find Customs Broker
              </Button>
              <Button variant="outline" className="border-blue-300 text-blue-700 hover:bg-blue-100">
                Check Trade Agreements
              </Button>
              <Button variant="outline" className="border-blue-300 text-blue-700 hover:bg-blue-100">
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
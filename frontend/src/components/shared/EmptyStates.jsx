import React from "react";
import { Search, Package, AlertTriangle, RefreshCw } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

// Empty state when no search has been performed
export const WelcomeState = () => (
  <Card className="border-2 border-dashed border-gray-300 bg-gray-50">
    <CardContent className="p-12 text-center">
      <Package className="h-16 w-16 text-gray-400 mx-auto mb-6" />
      <h3 className="text-2xl font-semibold text-gray-900 mb-3">
        Ready to Classify Your Products
      </h3>
      <p className="text-lg text-gray-600 max-w-md mx-auto mb-6">
        Enter a product description above to get accurate HTS classifications 
        with official duty rates and regulatory requirements.
      </p>
      <div className="text-sm text-gray-500">
        Powered by official USITC HTS schedule data
      </div>
    </CardContent>
  </Card>
);

// Empty state when search returns no results
export const NoResultsState = ({ query, onRetry, onNewSearch }) => (
  <Card className="border-2 border-yellow-200 bg-yellow-50">
    <CardContent className="p-12 text-center">
      <AlertTriangle className="h-16 w-16 text-yellow-500 mx-auto mb-6" />
      <h3 className="text-2xl font-semibold text-yellow-800 mb-3">
        No Classifications Found
      </h3>
      <p className="text-lg text-yellow-700 mb-6">
        We couldn't find any HTS classifications for "{query}".
      </p>
      
      <div className="bg-yellow-100 rounded-lg p-4 mb-6 text-left max-w-md mx-auto">
        <h4 className="font-semibold text-yellow-800 mb-2">Try these tips:</h4>
        <ul className="space-y-1 text-sm text-yellow-700">
          <li>• Be more specific about materials (cotton, steel, plastic)</li>
          <li>• Include the intended use (construction, automotive, clothing)</li>
          <li>• Mention key characteristics (size, weight, function)</li>
          <li>• Avoid brand names and focus on product description</li>
        </ul>
      </div>
      
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Button onClick={onRetry} variant="outline" className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4" />
          <span>Try Again</span>
        </Button>
        <Button onClick={onNewSearch} className="flex items-center space-x-2">
          <Search className="h-4 w-4" />
          <span>New Search</span>
        </Button>
      </div>
    </CardContent>
  </Card>
);

// Error state for when something goes wrong
export const ErrorState = ({ error, onRetry, onNewSearch }) => (
  <Card className="border-2 border-red-200 bg-red-50">
    <CardContent className="p-12 text-center">
      <AlertTriangle className="h-16 w-16 text-red-500 mx-auto mb-6" />
      <h3 className="text-2xl font-semibold text-red-800 mb-3">
        Something Went Wrong
      </h3>
      <p className="text-lg text-red-700 mb-6">
        {error || "An unexpected error occurred while processing your request."}
      </p>
      
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Button onClick={onRetry} variant="outline" className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4" />
          <span>Try Again</span>
        </Button>
        <Button onClick={onNewSearch} className="flex items-center space-x-2">
          <Search className="h-4 w-4" />
          <span>New Search</span>
        </Button>
      </div>
    </CardContent>
  </Card>
);

export default { WelcomeState, NoResultsState, ErrorState };
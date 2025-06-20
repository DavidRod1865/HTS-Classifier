import React from "react";
import { Search, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";

const SearchForm = ({ 
  query, 
  setQuery, 
  loading, 
  onSubmit, 
  showHints = true 
}) => {
  const searchHints = [
    "cotton t-shirts from China",
    "rubber tires for passenger cars", 
    "steel pipes for construction",
    "LED light bulbs",
    "smartphones from South Korea",
    "wooden furniture from Vietnam"
  ];

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Main Search Card */}
      <Card className="border-2 shadow-lg mx-2 sm:mx-0">
        <CardContent className="p-4 sm:p-6 lg:p-8">
          <div className="text-center mb-4 sm:mb-6">
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-2 sm:mb-3">
              HTS Classification Assistant
            </h1>
            <p className="text-base sm:text-lg lg:text-xl text-gray-600 max-w-2xl mx-auto px-2">
              Get accurate Harmonized Tariff Schedule classifications for your products 
              with official duty rates and regulatory requirements
            </p>
          </div>

          {/* Search Form */}
          <form onSubmit={onSubmit} className="max-w-2xl mx-auto">
            <div className="relative">
              <div className="relative">
                <Search className="absolute left-3 sm:left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4 sm:h-5 sm:w-5" />
                <Input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Describe your product (e.g., cotton t-shirts, steel pipes...)"
                  className="pl-10 sm:pl-12 pr-3 sm:pr-4 py-3 sm:py-4 text-base sm:text-lg border-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-lg"
                  disabled={loading}
                  required
                />
              </div>
              
              <Button
                type="submit"
                disabled={loading || !query.trim()}
                className="mt-3 sm:mt-4 w-full py-3 sm:py-4 text-base sm:text-lg font-semibold bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 rounded-lg"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-b-2 border-white mr-2 sm:mr-3"></div>
                    <span className="hidden sm:inline">Analyzing Product...</span>
                    <span className="sm:hidden">Analyzing...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <Sparkles className="h-4 w-4 sm:h-5 sm:w-5 mr-2" />
                    <span className="hidden sm:inline">Classify Product</span>
                    <span className="sm:hidden">Classify</span>
                  </div>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Search Hints */}
      {showHints && (
        <Card className="border border-gray-200 mx-2 sm:mx-0">
          <CardContent className="p-4 sm:p-6">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3">
              Try these examples:
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3">
              {searchHints.map((hint, index) => (
                <button
                  key={index}
                  onClick={() => setQuery(hint)}
                  className="text-left p-2 sm:p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors text-xs sm:text-sm text-gray-700 hover:text-blue-700 active:bg-blue-100"
                  disabled={loading}
                >
                  {hint}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SearchForm;
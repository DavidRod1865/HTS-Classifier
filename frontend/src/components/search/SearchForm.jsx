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
    <div className="space-y-6">
      {/* Main Search Card */}
      <Card className="border-2 shadow-lg">
        <CardContent className="p-8">
          <div className="text-center mb-6">
            <h1 className="text-4xl font-bold text-gray-900 mb-3">
              HTS Classification Assistant
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Get accurate Harmonized Tariff Schedule classifications for your products 
              with official duty rates and regulatory requirements
            </p>
          </div>

          {/* Search Form */}
          <form onSubmit={onSubmit} className="max-w-2xl mx-auto">
            <div className="relative">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                <Input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Describe your product (e.g., cotton t-shirts, steel pipes, LED bulbs...)"
                  className="pl-12 pr-4 py-4 text-lg border-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={loading}
                  required
                />
              </div>
              
              <Button
                type="submit"
                disabled={loading || !query.trim()}
                className="mt-4 w-full py-4 text-lg font-semibold bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                    Analyzing Product...
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <Sparkles className="h-5 w-5 mr-2" />
                    Classify Product
                  </div>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Search Hints */}
      {showHints && (
        <Card className="border border-gray-200">
          <CardContent className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Try these examples:
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {searchHints.map((hint, index) => (
                <button
                  key={index}
                  onClick={() => setQuery(hint)}
                  className="text-left p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors text-sm text-gray-700 hover:text-blue-700"
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
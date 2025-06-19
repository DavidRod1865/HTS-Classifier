import React, { useState } from "react";
import { HelpCircle, X, Book, AlertCircle, CheckCircle, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useFocusTrap } from "./AccessibilityProvider";

const ContextualHelp = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState("getting-started");
  
  // Enable focus trap when modal is open
  useFocusTrap(isOpen);

  const tabs = [
    {
      id: "getting-started",
      label: "Getting Started",
      icon: CheckCircle,
      content: (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              How to Classify Your Products
            </h3>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-full">
                  <span className="text-sm font-semibold text-blue-600">1</span>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">Describe Your Product</h4>
                  <p className="text-sm text-gray-600">
                    Enter a clear description including materials, purpose, and key characteristics.
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-full">
                  <span className="text-sm font-semibold text-blue-600">2</span>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">Review Classifications</h4>
                  <p className="text-sm text-gray-600">
                    Analyze the suggested HTS codes and their confidence scores.
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-full">
                  <span className="text-sm font-semibold text-blue-600">3</span>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">Verify & Export</h4>
                  <p className="text-sm text-gray-600">
                    Check official USITC data and export results for customs documentation.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="font-semibold text-blue-900 mb-2">💡 Pro Tips</h4>
            <ul className="space-y-1 text-sm text-blue-800">
              <li>• Include material composition (cotton, steel, plastic, etc.)</li>
              <li>• Specify intended use or industry</li>
              <li>• Mention key physical characteristics</li>
              <li>• Avoid brand names - focus on product description</li>
            </ul>
          </div>
        </div>
      )
    },
    {
      id: "understanding-results",
      label: "Understanding Results",
      icon: Book,
      content: (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              How to Read Your Results
            </h3>
            
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">HTS Code Format</h4>
                <div className="bg-gray-50 rounded-lg p-3">
                  <code className="text-lg font-mono text-blue-600">8539.21.0000</code>
                  <div className="mt-2 text-sm text-gray-600">
                    <div>• First 4 digits (8539): Chapter - Product category</div>
                    <div>• Next 2 digits (21): Heading - Subcategory</div>
                    <div>• Last 4 digits (0000): Subheading - Specific classification</div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Confidence Scores</h4>
                <div className="space-y-2">
                  <div className="flex items-center space-x-3">
                    <Badge className="bg-green-100 text-green-800">90-100%</Badge>
                    <span className="text-sm text-gray-600">Excellent match - High confidence</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Badge className="bg-blue-100 text-blue-800">80-89%</Badge>
                    <span className="text-sm text-gray-600">Good match - Review recommended</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Badge className="bg-yellow-100 text-yellow-800">70-79%</Badge>
                    <span className="text-sm text-gray-600">Fair match - Verification needed</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Badge className="bg-gray-100 text-gray-800">&lt;70%</Badge>
                    <span className="text-sm text-gray-600">Low match - Expert consultation advised</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Data Sources</h4>
                <div className="space-y-2">
                  <div className="flex items-center space-x-3">
                    <Badge className="bg-green-100 text-green-800 flex items-center space-x-1">
                      <CheckCircle className="h-3 w-3" />
                      <span>Official HTS Data</span>
                    </Badge>
                    <span className="text-sm text-gray-600">Direct match from USITC database</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Badge className="bg-blue-100 text-blue-800 flex items-center space-x-1">
                      <AlertCircle className="h-3 w-3" />
                      <span>AI Analysis</span>
                    </Badge>
                    <span className="text-sm text-gray-600">AI-suggested classification</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      id: "best-practices",
      label: "Best Practices",
      icon: AlertCircle,
      content: (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Classification Best Practices
            </h3>
            
            <div className="space-y-4">
              <div className="border-l-4 border-green-400 bg-green-50 p-4">
                <h4 className="font-semibold text-green-800 mb-2">✅ Do This</h4>
                <ul className="space-y-1 text-sm text-green-700">
                  <li>• Use specific material descriptions (100% cotton, stainless steel)</li>
                  <li>• Include intended use or application</li>
                  <li>• Mention key technical specifications</li>
                  <li>• Consider the primary function of the product</li>
                  <li>• Consult with customs brokers for final verification</li>
                </ul>
              </div>

              <div className="border-l-4 border-red-400 bg-red-50 p-4">
                <h4 className="font-semibold text-red-800 mb-2">❌ Avoid This</h4>
                <ul className="space-y-1 text-sm text-red-700">
                  <li>• Using only brand names or model numbers</li>
                  <li>• Vague descriptions like "machine parts"</li>
                  <li>• Ignoring material composition</li>
                  <li>• Relying solely on AI classification for critical shipments</li>
                  <li>• Assuming similar products have identical codes</li>
                </ul>
              </div>

              <div className="border-l-4 border-yellow-400 bg-yellow-50 p-4">
                <h4 className="font-semibold text-yellow-800 mb-2">⚠️ Important Notes</h4>
                <ul className="space-y-1 text-sm text-yellow-700">
                  <li>• HTS classifications can affect duty rates significantly</li>
                  <li>• Misclassification can result in penalties and delays</li>
                  <li>• Trade agreements may offer preferential rates</li>
                  <li>• Some products require special licenses or permits</li>
                  <li>• Classifications may change with product modifications</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      id: "resources",
      label: "Resources",
      icon: ExternalLink,
      content: (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Additional Resources
            </h3>
            
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Official Sources</h4>
                <div className="space-y-2">
                  <a href="https://hts.usitc.gov" target="_blank" rel="noopener noreferrer" 
                     className="flex items-center space-x-2 text-blue-600 hover:text-blue-800">
                    <ExternalLink className="h-4 w-4" />
                    <span>USITC HTS Database</span>
                  </a>
                  <a href="https://www.cbp.gov" target="_blank" rel="noopener noreferrer" 
                     className="flex items-center space-x-2 text-blue-600 hover:text-blue-800">
                    <ExternalLink className="h-4 w-4" />
                    <span>U.S. Customs and Border Protection</span>
                  </a>
                  <a href="https://rulings.cbp.gov" target="_blank" rel="noopener noreferrer" 
                     className="flex items-center space-x-2 text-blue-600 hover:text-blue-800">
                    <ExternalLink className="h-4 w-4" />
                    <span>CBP Rulings Database</span>
                  </a>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Professional Services</h4>
                <div className="space-y-2 text-sm text-gray-600">
                  <div>• Licensed Customs Brokers</div>
                  <div>• International Trade Attorneys</div>
                  <div>• Trade Compliance Consultants</div>
                  <div>• Freight Forwarders</div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Trade Programs</h4>
                <div className="space-y-2 text-sm text-gray-600">
                  <div>• NAFTA/USMCA Preferences</div>
                  <div>• Generalized System of Preferences (GSP)</div>
                  <div>• Free Trade Agreements</div>
                  <div>• Special Trade Programs</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )
    }
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-4xl max-h-[80vh] overflow-hidden">
        <CardHeader className="border-b">
          <div className="flex items-center justify-between">
            <CardTitle className="text-2xl text-gray-900 flex items-center space-x-2">
              <HelpCircle className="h-6 w-6 text-blue-600" />
              <span>HTS Classification Help</span>
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>
        </CardHeader>
        
        <div className="flex h-[60vh]">
          {/* Sidebar */}
          <div className="w-64 border-r bg-gray-50 p-4">
            <nav className="space-y-2">
              {tabs.map((tab) => {
                const IconComponent = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-100 text-blue-700 border border-blue-200'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <IconComponent className="h-4 w-4" />
                    <span className="text-sm font-medium">{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>
          
          {/* Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {tabs.find(tab => tab.id === activeTab)?.content}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ContextualHelp;
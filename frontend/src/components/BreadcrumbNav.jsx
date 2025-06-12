import React from "react";
import { ChevronRight, Search, MessageCircle, CheckCircle, Package } from "lucide-react";

const BreadcrumbNav = ({ 
  currentProduct, 
  conversationActive, 
  currentTurn, 
  awaitingResponse, 
  hasResults, 
  hasQuestions, 
  hasOptions 
}) => {
  const steps = [
    {
      id: "search",
      label: "Product Entry",
      icon: Search,
      completed: !!currentProduct,
      active: !currentProduct
    },
    {
      id: "conversation",
      label: `Conversation${currentTurn > 1 ? ` (Turn ${currentTurn})` : ''}`,
      icon: MessageCircle,
      completed: conversationActive && !awaitingResponse && (hasResults || hasOptions),
      active: conversationActive && (hasQuestions || awaitingResponse)
    },
    {
      id: "results",
      label: "Classification Results",
      icon: hasResults ? CheckCircle : Package,
      completed: hasResults && !awaitingResponse,
      active: hasResults || hasOptions
    }
  ];

  if (!currentProduct) return null;

  return (
    <nav aria-label="Classification progress" className="mb-6">
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex items-center space-x-2 text-sm">
          <span className="text-gray-600 font-medium">Classification Journey:</span>
          
          <ol className="flex items-center space-x-2 ml-2">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isLast = index === steps.length - 1;
              
              return (
                <li key={step.id} className="flex items-center">
                  <div className={`flex items-center space-x-2 px-3 py-1 rounded-full transition-colors ${
                    step.completed 
                      ? 'bg-green-100 text-green-800' 
                      : step.active 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-gray-100 text-gray-500'
                  }`}>
                    <Icon className="h-4 w-4" />
                    <span className="font-medium">{step.label}</span>
                  </div>
                  
                  {!isLast && (
                    <ChevronRight className="h-4 w-4 text-gray-400 mx-2" />
                  )}
                </li>
              );
            })}
          </ol>
        </div>
        
        {/* Current Product Info */}
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <div>
              <span className="text-gray-600">Classifying:</span>
              <span className="ml-2 font-medium text-gray-900">{currentProduct}</span>
            </div>
            
            {conversationActive && (
              <div className="text-gray-500">
                {awaitingResponse ? (
                  <span className="flex items-center">
                    <div className="animate-pulse h-2 w-2 bg-blue-500 rounded-full mr-2"></div>
                    Awaiting your response
                  </span>
                ) : hasResults ? (
                  <span className="flex items-center text-green-600">
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Complete
                  </span>
                ) : (
                  <span className="flex items-center">
                    <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full mr-2"></div>
                    Processing
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default BreadcrumbNav;
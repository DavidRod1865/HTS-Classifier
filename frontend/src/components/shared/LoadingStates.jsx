import React from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

// Skeleton loading animation
const Skeleton = ({ className = "" }) => (
  <div className={`animate-pulse bg-gray-200 rounded ${className}`}></div>
);

// Loading state for search results
export const ResultsLoadingSkeleton = () => (
  <div className="space-y-6">
    {/* Progress indicator */}
    <Card className="border-2 border-blue-200 bg-blue-50">
      <CardContent className="p-6">
        <div className="flex items-center justify-center space-x-4">
          <div className="flex space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce"></div>
            <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
            <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
          </div>
          <span className="text-blue-700 font-medium">Analyzing your product...</span>
        </div>
        
        <div className="mt-4 space-y-2">
          <div className="text-sm text-blue-600 text-center">
            🔍 Interpreting product description
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
          </div>
        </div>
      </CardContent>
    </Card>

    {/* Skeleton cards for results */}
    {[1, 2, 3].map((index) => (
      <Card key={index} className="border">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-6 w-20" />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* HTS Code skeleton */}
          <div className="flex items-center space-x-3">
            <Skeleton className="h-8 w-8 rounded-full" />
            <Skeleton className="h-6 w-40" />
          </div>
          
          {/* Description skeleton */}
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>
          
          {/* Table skeleton */}
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-4">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-24" />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-12" />
              <Skeleton className="h-4 w-20" />
            </div>
          </div>
          
          {/* Action buttons skeleton */}
          <div className="flex space-x-3 pt-4">
            <Skeleton className="h-9 w-24" />
            <Skeleton className="h-9 w-20" />
          </div>
        </CardContent>
      </Card>
    ))}
  </div>
);

// Loading state for search processing with steps
export const ProcessingLoadingState = ({ currentStep = "interpreting" }) => {
  const steps = [
    { id: "interpreting", label: "Interpreting product description", icon: "🔍" },
    { id: "searching", label: "Searching HTS database", icon: "📊" },
    { id: "analyzing", label: "Analyzing classification matches", icon: "🧠" },
    { id: "finalizing", label: "Preparing results", icon: "✨" }
  ];

  return (
    <Card className="border-2 border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50">
      <CardContent className="p-8">
        <div className="text-center">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">
            Classifying Your Product
          </h3>
          
          <div className="space-y-4">
            {steps.map((step, index) => {
              const isActive = step.id === currentStep;
              const isCompleted = steps.findIndex(s => s.id === currentStep) > index;
              
              return (
                <div
                  key={step.id}
                  className={`flex items-center space-x-3 p-3 rounded-lg transition-all ${
                    isActive 
                      ? 'bg-blue-100 border-2 border-blue-300' 
                      : isCompleted 
                      ? 'bg-green-50 border border-green-200' 
                      : 'bg-gray-50 border border-gray-200'
                  }`}
                >
                  <div className={`text-2xl ${isActive ? 'animate-pulse' : ''}`}>
                    {isCompleted ? '✅' : step.icon}
                  </div>
                  <span className={`font-medium ${
                    isActive ? 'text-blue-800' : isCompleted ? 'text-green-800' : 'text-gray-600'
                  }`}>
                    {step.label}
                  </span>
                  {isActive && (
                    <div className="ml-auto">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Simple inline loading spinner
export const InlineLoader = ({ text = "Loading..." }) => (
  <div className="flex items-center justify-center py-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
    <span className="text-gray-600">{text}</span>
  </div>
);

export default { ResultsLoadingSkeleton, ProcessingLoadingState, InlineLoader };
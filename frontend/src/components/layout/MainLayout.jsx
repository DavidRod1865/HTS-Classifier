import React from "react";
import Header from "./Header";

const MainLayout = ({ 
  children, 
  onShowHistory, 
  onShowHelp, 
  searchCount 
}) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        onShowHistory={onShowHistory}
        onShowHelp={onShowHelp}
        searchCount={searchCount}
      />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      
      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                About HTS Oracle
              </h3>
              <p className="text-sm text-gray-600">
                AI-powered HTS classification tool using official USITC data 
                to help importers and exporters classify their products accurately.
              </p>
            </div>
            
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                Resources
              </h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>
                  <a href="https://hts.usitc.gov" target="_blank" rel="noopener noreferrer" 
                     className="hover:text-blue-600">
                    Official HTS Database
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-blue-600">
                    Classification Guide
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-blue-600">
                    Customs Brokers
                  </a>
                </li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                Disclaimer
              </h3>
              <p className="text-xs text-gray-600">
                Classifications provided are for reference only. 
                Consult with a licensed customs broker for official determinations. 
                Duty rates and regulations subject to change.
              </p>
            </div>
          </div>
          
          <div className="mt-8 pt-8 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              © 2024 HTS Oracle. Data sourced from USITC HTS Schedule.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default MainLayout;
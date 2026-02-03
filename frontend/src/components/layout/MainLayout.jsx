import React from "react";
import Header from "./Header";

const MainLayout = ({ children, onNewChat }) => (
  <div className="min-h-screen bg-gray-50">
    <Header onNewChat={onNewChat} />

    <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">{children}</main>

    <footer className="text-center text-xs text-gray-400 py-4 mt-8 border-t border-gray-200">
      Classifications are for reference only.<br/> Verify with a licensed customs broker. Data from{" "}
      <a
        href="https://hts.usitc.gov"
        target="_blank"
        rel="noopener noreferrer"
        className="underline hover:text-gray-600"
      >
        USITC
      </a>
      .{" "}<br />
      Built by David Rodriguez.{" "}
      <a
        href="https://github.com/DavidRod1865/HTS-Classifier"
        target="_blank"
        rel="noopener noreferrer"
        className="underline hover:text-gray-600"
      >
        GitHub
      </a>
      .
    </footer>
  </div>
);

export default MainLayout;

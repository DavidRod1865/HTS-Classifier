import React from "react";
import Header from "./Header";

const MainLayout = ({ children, onNewChat }) => (
  <div className="min-h-screen bg-gray-50">
    <Header onNewChat={onNewChat} />

    <main className="max-w-3xl mx-auto px-4 sm:px-6 py-6">{children}</main>

    <footer className="text-center text-xs text-gray-400 py-4 mt-8 border-t border-gray-200">
      Classifications are for reference only. Consult a licensed customs broker for
      official determinations. Data from{" "}
      <a
        href="https://hts.usitc.gov"
        target="_blank"
        rel="noopener noreferrer"
        className="underline hover:text-gray-600"
      >
        USITC
      </a>
      .
    </footer>
  </div>
);

export default MainLayout;

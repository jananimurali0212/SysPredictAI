import React, { useState } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

export default function MainLayout({
  activeTab,
  setActiveTab,
  connectionStatus,
  riskStatus,
  lastUpdated,
  children,
}) {
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen bg-navy-900 text-slate-100 flex flex-col font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isOpen={isMobileNavOpen}
        setIsOpen={setIsMobileNavOpen}
        connectionStatus={connectionStatus}
      />

      {/* Main Content Area */}
      <div className="lg:pl-64 flex flex-col flex-1 min-w-0">
        <Header
          activeTab={activeTab}
          onOpenMobileNav={() => setIsMobileNavOpen(true)}
          connectionStatus={connectionStatus}
          riskStatus={riskStatus}
          lastUpdated={lastUpdated}
        />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

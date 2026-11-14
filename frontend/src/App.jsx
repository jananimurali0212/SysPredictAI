import React, { useState, useEffect } from 'react';
import MainLayout from './components/layout/MainLayout';
import Overview from './components/pages/Overview';
import LiveMonitoring from './components/pages/LiveMonitoring';
import ProcessMonitoring from './components/pages/ProcessMonitoring';
import Predictions from './components/pages/Predictions';
import AnomalyDetection from './components/pages/AnomalyDetection';
import AIInsights from './components/pages/AIInsights';
import SettingsPage from './components/pages/Settings';
import { useMetricsWebSocket } from './services/websocket';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [riskStatus, setRiskStatus] = useState('Normal');

  const {
    latestSnapshot,
    connectionStatus,
    reconnect,
  } = useMetricsWebSocket();

  // Periodic risk poll to keep header pill synced
  useEffect(() => {
    const fetchRisk = async () => {
      try {
        const res = await api.getRisk();
        if (res?.risk_status) {
          setRiskStatus(res.risk_status);
        }
      } catch (err) {
        // quiet fallback
      }
    };
    fetchRisk();
    const interval = setInterval(fetchRisk, 12000);
    return () => clearInterval(interval);
  }, []);

  const renderActivePage = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <Overview
            latestSnapshot={latestSnapshot}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        );
      case 'live':
        return (
          <LiveMonitoring
            latestSnapshot={latestSnapshot}
            connectionStatus={connectionStatus}
            reconnect={reconnect}
          />
        );
      case 'processes':
        return <ProcessMonitoring />;
      case 'predictions':
        return <Predictions />;
      case 'anomalies':
        return <AnomalyDetection />;
      case 'ai-insights':
        return <AIInsights />;
      case 'settings':
        return <SettingsPage />;
      default:
        return (
          <Overview
            latestSnapshot={latestSnapshot}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        );
    }
  };

  return (
    <MainLayout
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      connectionStatus={connectionStatus}
      riskStatus={riskStatus}
      lastUpdated={latestSnapshot?.timestamp}
    >
      {renderActivePage()}
    </MainLayout>
  );
}

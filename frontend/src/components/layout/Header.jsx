import React from 'react';
import { Menu, Wifi, WifiOff, ShieldCheck, Clock } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';

const TITLES = {
  overview: { title: 'System Overview', subtitle: 'Live telemetry health & hardware summary' },
  live: { title: 'Live System Monitoring', subtitle: 'Real-time telemetry stream & hardware graphs' },
  processes: { title: 'Process Monitoring', subtitle: 'Active host processes sorted by resource consumption' },
  predictions: { title: 'Predictive Analytics', subtitle: 'Random Forest forecasting for CPU & RAM utilization' },
  anomalies: { title: 'Anomaly Detection', subtitle: 'Rule-based threshold & Isolation Forest multivariate outliers' },
  'ai-insights': { title: 'Gemini AI Insights', subtitle: 'Intelligent diagnostic reasoning & performance advice' },
  settings: { title: 'Platform Settings', subtitle: 'Monitoring refresh intervals, thresholds & configurations' },
};

export default function Header({
  activeTab,
  onOpenMobileNav,
  connectionStatus,
  riskStatus,
  lastUpdated,
}) {
  const current = TITLES[activeTab] || { title: 'Dashboard', subtitle: 'Host monitoring' };

  return (
    <header className="h-16 bg-navy-950/80 backdrop-blur border-b border-navy-700/60 sticky top-0 z-30 px-4 sm:px-6 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <button
          onClick={onOpenMobileNav}
          className="lg:hidden p-2 text-slate-400 hover:text-white rounded-lg hover:bg-navy-800 transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-base sm:text-lg font-bold text-white tracking-tight flex items-center space-x-2">
            <span>{current.title}</span>
          </h1>
          <p className="hidden sm:block text-xs text-slate-400 font-medium">
            {current.subtitle}
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-3 sm:space-x-4">
        {/* Risk Status Pill */}
        {riskStatus && (
          <div className="hidden md:flex items-center space-x-2 bg-navy-800/80 px-3 py-1 rounded-full border border-navy-700 text-xs">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-slate-400">Risk:</span>
            <StatusBadge status={riskStatus} size="xs" />
          </div>
        )}

        {/* WebSocket Status Indicator */}
        <div
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full border text-xs font-mono transition-colors ${
            connectionStatus === 'connected'
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              : connectionStatus === 'connecting'
              ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
              : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
          }`}
          title={`WebSocket Status: ${connectionStatus}`}
        >
          {connectionStatus === 'connected' ? (
            <Wifi className="w-3.5 h-3.5" />
          ) : (
            <WifiOff className="w-3.5 h-3.5" />
          )}
          <span className="hidden sm:inline capitalize">{connectionStatus}</span>
        </div>

        {/* Last Timestamp */}
        {lastUpdated && (
          <div className="hidden lg:flex items-center space-x-1.5 text-xs text-slate-400 font-mono">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span>{new Date(lastUpdated).toLocaleTimeString()}</span>
          </div>
        )}
      </div>
    </header>
  );
}

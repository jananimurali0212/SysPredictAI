import React from 'react';
import {
  LayoutDashboard,
  Activity,
  Cpu,
  TrendingUp,
  AlertOctagon,
  Sparkles,
  Settings,
  X,
  Server,
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'live', label: 'Live Monitoring', icon: Activity },
  { id: 'processes', label: 'Process Monitoring', icon: Cpu },
  { id: 'predictions', label: 'Predictions', icon: TrendingUp },
  { id: 'anomalies', label: 'Anomaly Detection', icon: AlertOctagon },
  { id: 'ai-insights', label: 'AI Insights', icon: Sparkles, badge: 'Gemini' },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export default function Sidebar({ activeTab, setActiveTab, isOpen, setIsOpen, connectionStatus }) {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-navy-950 border-r border-navy-700/70 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Logo and Brand */}
        <div className="h-16 px-6 flex items-center justify-between border-b border-navy-700/60 bg-navy-950">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20 text-white font-bold">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-base tracking-wide text-white block">
                SysPredict<span className="text-blue-500">AI</span>
              </span>
              <span className="text-[10px] text-slate-400 uppercase tracking-widest font-mono">
                System Telemetry
              </span>
            </div>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="lg:hidden text-slate-400 hover:text-white p-1 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-6 space-y-1.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setIsOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 shadow-md shadow-blue-900/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-navy-800/60 border border-transparent'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-mono font-normal border border-blue-500/30">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Server & Stream Footer */}
        <div className="p-4 border-t border-navy-700/60 bg-navy-950/70">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="flex items-center space-x-2">
              <Server className="w-3.5 h-3.5 text-slate-400" />
              <span>Daemon Status</span>
            </span>
            <span
              className={`inline-flex items-center text-[10px] px-2 py-0.5 rounded-full font-mono ${
                connectionStatus === 'connected'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : connectionStatus === 'connecting'
                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current animate-pulse"></span>
              {connectionStatus === 'connected' ? 'LIVE' : connectionStatus.toUpperCase()}
            </span>
          </div>
          <div className="text-[11px] text-slate-500 font-mono text-center">
            SysPredictAI Platform v1.0.0
          </div>
        </div>
      </aside>
    </>
  );
}

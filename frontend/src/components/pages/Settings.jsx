import React, { useEffect, useState } from 'react';
import {
  Settings as SettingsIcon,
  Bell,
  Sliders,
  Palette,
  Sparkles,
  Save,
  CheckCircle2,
  RefreshCw,
  Server,
} from 'lucide-react';
import { api } from '../../services/api';

export default function SettingsPage() {
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('syspredictai_settings');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        // fallback
      }
    }
    return {
      refreshInterval: 1, // seconds
      cpuWarning: 75,
      cpuCritical: 90,
      memoryWarning: 80,
      memoryCritical: 92,
      denseMode: false,
      smoothAnimations: true,
    };
  });

  const [systemInfo, setSystemInfo] = useState(null);
  const [health, setHealth] = useState(null);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    api.getSystemInfo().then(setSystemInfo).catch(console.error);
    api.getHealth().then(setHealth).catch(console.error);
  }, []);

  const handleSave = () => {
    localStorage.setItem('syspredictai_settings', JSON.stringify(settings));
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Settings Header */}
      <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-5 flex items-center justify-between backdrop-blur shadow-lg">
        <div className="flex items-center space-x-3.5">
          <div className="p-2.5 rounded-xl bg-blue-600/10 border border-blue-500/20 text-blue-400">
            <SettingsIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white">Platform Configuration & Thresholds</h2>
            <p className="text-xs text-slate-400">
              Customize local telemetry thresholds, sampling cadence, and interface preferences
            </p>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-blue-600/20 transition-all hover:scale-[1.02]"
        >
          {savedSuccess ? (
            <>
              <CheckCircle2 className="w-4 h-4 text-emerald-300" />
              <span>Saved!</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>Save Settings</span>
            </>
          )}
        </button>
      </div>

      {/* 1. Alert Thresholds Card */}
      <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-6 shadow-xl backdrop-blur space-y-5">
        <div className="flex items-center space-x-2.5 pb-3 border-b border-navy-700/60">
          <Bell className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
            Resource Alert Thresholds (%)
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
          {/* CPU Warning */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <label className="text-slate-300 font-medium">CPU Warning Threshold</label>
              <span className="font-mono text-amber-400 font-bold">{settings.cpuWarning}%</span>
            </div>
            <input
              type="range"
              min="50"
              max="95"
              value={settings.cpuWarning}
              onChange={(e) => setSettings({ ...settings, cpuWarning: Number(e.target.value) })}
              className="w-full accent-amber-500 bg-navy-950 h-1.5 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          {/* CPU Critical */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <label className="text-slate-300 font-medium">CPU Critical Threshold</label>
              <span className="font-mono text-rose-400 font-bold">{settings.cpuCritical}%</span>
            </div>
            <input
              type="range"
              min="75"
              max="100"
              value={settings.cpuCritical}
              onChange={(e) => setSettings({ ...settings, cpuCritical: Number(e.target.value) })}
              className="w-full accent-rose-500 bg-navy-950 h-1.5 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          {/* RAM Warning */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <label className="text-slate-300 font-medium">Memory Warning Threshold</label>
              <span className="font-mono text-amber-400 font-bold">{settings.memoryWarning}%</span>
            </div>
            <input
              type="range"
              min="60"
              max="95"
              value={settings.memoryWarning}
              onChange={(e) => setSettings({ ...settings, memoryWarning: Number(e.target.value) })}
              className="w-full accent-amber-500 bg-navy-950 h-1.5 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          {/* RAM Critical */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <label className="text-slate-300 font-medium">Memory Critical Threshold</label>
              <span className="font-mono text-rose-400 font-bold">{settings.memoryCritical}%</span>
            </div>
            <input
              type="range"
              min="80"
              max="100"
              value={settings.memoryCritical}
              onChange={(e) => setSettings({ ...settings, memoryCritical: Number(e.target.value) })}
              className="w-full accent-rose-500 bg-navy-950 h-1.5 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* 2. Streaming Cadence & Display */}
      <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-6 shadow-xl backdrop-blur space-y-5">
        <div className="flex items-center space-x-2.5 pb-3 border-b border-navy-700/60">
          <Sliders className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
            Sampling Cadence & Visual Layout
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
          <div className="space-y-2">
            <label className="text-slate-300 font-medium block">Polling & Chart Refresh Interval</label>
            <select
              value={settings.refreshInterval}
              onChange={(e) => setSettings({ ...settings, refreshInterval: Number(e.target.value) })}
              className="w-full px-3 py-2 bg-navy-900 border border-navy-700 rounded-xl text-white focus:outline-none focus:border-blue-500 font-mono text-xs"
            >
              <option value="1">1 second (Real-Time WebSocket default)</option>
              <option value="2">2 seconds</option>
              <option value="5">5 seconds</option>
              <option value="10">10 seconds</option>
            </select>
          </div>

          <div className="space-y-3 pt-3 sm:pt-0">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.denseMode}
                onChange={(e) => setSettings({ ...settings, denseMode: e.target.checked })}
                className="w-4 h-4 rounded border-navy-700 bg-navy-900 text-blue-600 focus:ring-0"
              />
              <span className="text-slate-300 font-medium">Compact Table Mode (higher row density)</span>
            </label>

            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.smoothAnimations}
                onChange={(e) => setSettings({ ...settings, smoothAnimations: e.target.checked })}
                className="w-4 h-4 rounded border-navy-700 bg-navy-900 text-blue-600 focus:ring-0"
              />
              <span className="text-slate-300 font-medium">Enable Animated Transitions & Charts</span>
            </label>
          </div>
        </div>
      </div>

      {/* 3. Host System Details & Backend State */}
      <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-6 shadow-xl backdrop-blur space-y-4">
        <div className="flex items-center space-x-2.5 pb-3 border-b border-navy-700/60">
          <Server className="w-4 h-4 text-slate-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
            Host System & Backend Environment
          </h3>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-3 bg-navy-900/80 rounded-xl border border-navy-700/60">
            <span className="text-[10px] text-slate-500 uppercase block">Host Platform</span>
            <span className="text-white font-semibold">
              {systemInfo?.os_name || '--'} {systemInfo?.architecture || ''}
            </span>
          </div>

          <div className="p-3 bg-navy-900/80 rounded-xl border border-navy-700/60">
            <span className="text-[10px] text-slate-500 uppercase block">Logical Cores</span>
            <span className="text-white font-semibold">
              {systemInfo?.logical_cores || '--'} Cores
            </span>
          </div>

          <div className="p-3 bg-navy-900/80 rounded-xl border border-navy-700/60">
            <span className="text-[10px] text-slate-500 uppercase block">Installed RAM</span>
            <span className="text-white font-semibold">
              {systemInfo?.total_ram_bytes ? `${(systemInfo.total_ram_bytes / (1024**3)).toFixed(1)} GB` : '--'}
            </span>
          </div>

          <div className="p-3 bg-navy-900/80 rounded-xl border border-navy-700/60">
            <span className="text-[10px] text-slate-500 uppercase block">API Server Status</span>
            <span className="text-emerald-400 font-semibold">
              {health?.status ? health.status.toUpperCase() : 'CHECKING'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

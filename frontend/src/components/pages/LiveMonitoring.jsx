import React, { useEffect, useState } from 'react';
import {
  Activity,
  Cpu,
  Database,
  HardDrive,
  Network,
  Clock,
  Wifi,
  WifiOff,
  RefreshCw,
  Gauge,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import MetricCard from '../common/MetricCard';
import StatusBadge from '../common/StatusBadge';

export default function LiveMonitoring({ latestSnapshot, connectionStatus, reconnect }) {
  const [telemetryHistory, setTelemetryHistory] = useState([]);

  useEffect(() => {
    if (latestSnapshot) {
      setTelemetryHistory((prev) => {
        const timeStr = new Date(latestSnapshot.timestamp).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });
        const point = {
          time: timeStr,
          cpu: latestSnapshot.cpu?.utilization_percent || 0,
          memory: latestSnapshot.memory?.utilization_percent || 0,
          disk: latestSnapshot.disk?.utilization_percent || 0,
          uploadKbps: latestSnapshot.network?.upload_speed_bps ? parseFloat((latestSnapshot.network.upload_speed_bps / 1024).toFixed(1)) : 0,
          downloadKbps: latestSnapshot.network?.download_speed_bps ? parseFloat((latestSnapshot.network.download_speed_bps / 1024).toFixed(1)) : 0,
        };
        const updated = [...prev, point];
        return updated.length > 40 ? updated.slice(updated.length - 40) : updated;
      });
    }
  }, [latestSnapshot]);

  const cpu = latestSnapshot?.cpu;
  const memory = latestSnapshot?.memory;
  const disk = latestSnapshot?.disk;
  const network = latestSnapshot?.network;

  return (
    <div className="space-y-6">
      {/* Top Stream Status Header */}
      <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 backdrop-blur shadow-lg">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-blue-600/10 border border-blue-500/20 text-blue-400">
            <Activity className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h2 className="text-sm sm:text-base font-bold text-white flex items-center space-x-2">
              <span>High-Frequency Telemetry Stream</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-navy-700 text-slate-300 font-mono">
                1-sec interval
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Direct host telemetry streaming via WebSocket (/ws/metrics)
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-xl border text-xs font-mono ${
              connectionStatus === 'connected'
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : connectionStatus === 'connecting'
                ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
            }`}
          >
            {connectionStatus === 'connected' ? (
              <Wifi className="w-4 h-4 text-emerald-400" />
            ) : (
              <WifiOff className="w-4 h-4 text-rose-400" />
            )}
            <span className="font-semibold uppercase tracking-wider">{connectionStatus}</span>
          </div>

          {connectionStatus !== 'connected' && (
            <button
              onClick={reconnect}
              className="px-3 py-1.5 rounded-xl bg-navy-700 hover:bg-navy-600 border border-navy-600 text-xs font-semibold text-white flex items-center space-x-1.5 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reconnect</span>
            </button>
          )}
        </div>
      </div>

      {/* Main 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="CPU Utilization"
          value={cpu?.utilization_percent ?? '--'}
          unit="%"
          percentage={cpu?.utilization_percent}
          icon={Cpu}
          status={cpu?.utilization_percent >= 90 ? 'Critical' : cpu?.utilization_percent >= 75 ? 'Warning' : 'Normal'}
          subValue={`${cpu?.core_count_logical || '--'} Logical Threads`}
        />

        <MetricCard
          title="Memory Utilization"
          value={memory?.utilization_percent ?? '--'}
          unit="%"
          percentage={memory?.utilization_percent}
          icon={Database}
          status={memory?.utilization_percent >= 92 ? 'Critical' : memory?.utilization_percent >= 80 ? 'Warning' : 'Normal'}
          subValue={
            memory
              ? `${(memory.used_bytes / (1024**3)).toFixed(1)} / ${(memory.total_bytes / (1024**3)).toFixed(1)} GB`
              : '--'
          }
        />

        <MetricCard
          title="Disk Capacity"
          value={disk?.utilization_percent ?? '--'}
          unit="%"
          percentage={disk?.utilization_percent}
          icon={HardDrive}
          status={disk?.utilization_percent >= 90 ? 'Critical' : disk?.utilization_percent >= 80 ? 'Warning' : 'Normal'}
          subValue={
            disk
              ? `${(disk.available_bytes / (1024**3)).toFixed(1)} GB free (${disk.mount_point})`
              : '--'
          }
        />

        <MetricCard
          title="Network Bandwidth"
          value={network?.download_speed_bps ? (network.download_speed_bps / 1024).toFixed(1) : '0.0'}
          unit="KB/s"
          icon={Network}
          status="Normal"
          subValue={
            network
              ? `Upload: ${(network.upload_speed_bps / 1024).toFixed(1)} KB/s`
              : '--'
          }
        />
      </div>

      {/* Real-time Line Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU & Memory Waveform Chart */}
        <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-6 shadow-xl backdrop-blur">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Cpu className="w-4 h-4 text-blue-400" />
                <span>CPU & Memory Trajectory</span>
              </h3>
              <p className="text-xs text-slate-400">Live sliding window of last 40 samples</p>
            </div>
            <div className="flex items-center space-x-3 text-xs font-mono">
              <span className="flex items-center space-x-1 text-blue-400">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                <span>CPU</span>
              </span>
              <span className="flex items-center space-x-1 text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>RAM</span>
              </span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={telemetryHistory} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="memGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} tickLine={false} />
                <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 10 }} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#f8fafc',
                  }}
                />
                <Area type="monotone" dataKey="cpu" stroke="#3b82f6" fillOpacity={1} fill="url(#cpuGrad)" strokeWidth={2} isAnimationActive={false} />
                <Area type="monotone" dataKey="memory" stroke="#10b981" fillOpacity={1} fill="url(#memGrad)" strokeWidth={2} isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Network I/O Speed Chart */}
        <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-6 shadow-xl backdrop-blur">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Network className="w-4 h-4 text-indigo-400" />
                <span>Network I/O Bandwidth (KB/s)</span>
              </h3>
              <p className="text-xs text-slate-400">Differential upload and download speeds</p>
            </div>
            <div className="flex items-center space-x-3 text-xs font-mono">
              <span className="flex items-center space-x-1 text-cyan-400">
                <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                <span>Down</span>
              </span>
              <span className="flex items-center space-x-1 text-purple-400">
                <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                <span>Up</span>
              </span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetryHistory} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} tickLine={false} />
                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#f8fafc',
                  }}
                />
                <Line type="monotone" dataKey="downloadKbps" stroke="#22d3ee" strokeWidth={2} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="uploadKbps" stroke="#c084fc" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Per-Core Breakdown Grid */}
      {cpu?.per_core_utilization && cpu.per_core_utilization.length > 0 && (
        <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-6 shadow-xl backdrop-blur">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Gauge className="w-4 h-4 text-blue-400" />
                <span>Per-Core CPU Load Distribution</span>
              </h3>
              <p className="text-xs text-slate-400">Individual logical CPU core metrics</p>
            </div>
            <span className="text-xs font-mono text-slate-400">
              {cpu.per_core_utilization.length} Logical Cores Active
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-3">
            {cpu.per_core_utilization.map((load, index) => (
              <div key={index} className="bg-navy-900/80 border border-navy-700/60 rounded-xl p-3 text-center">
                <span className="text-[10px] font-mono font-semibold text-slate-400 uppercase block mb-1">
                  Core {index}
                </span>
                <span className="text-base font-bold font-mono text-white block">
                  {load}%
                </span>
                <div className="w-full bg-navy-800 rounded-full h-1 mt-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      load >= 90 ? 'bg-rose-500' : load >= 75 ? 'bg-amber-500' : 'bg-blue-500'
                    }`}
                    style={{ width: `${Math.min(100, Math.max(0, load))}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

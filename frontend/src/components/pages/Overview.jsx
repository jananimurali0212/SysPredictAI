import React, { useEffect, useState } from 'react';
import {
  Cpu,
  HardDrive,
  Database,
  Network,
  Sparkles,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
  Server,
  Zap,
} from 'lucide-react';
import {
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
import { CardSkeleton } from '../common/LoadingState';
import ErrorAlert from '../common/ErrorAlert';
import { api } from '../../services/api';

export default function Overview({ latestSnapshot, onNavigate }) {
  const [history, setHistory] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [aiSummary, setAiSummary] = useState(null);
  const [risk, setRisk] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [histRes, anomRes, sumRes, riskRes] = await Promise.all([
        api.getHistory(30).catch(() => ({ metrics: [] })),
        api.getAnomalies().catch(() => ({ anomalies: [] })),
        api.getAISummary().catch(() => null),
        api.getRisk().catch(() => null),
      ]);

      // Reverse history for chronological display in chart (oldest -> newest)
      const formattedHistory = (histRes.metrics || [])
        .slice()
        .reverse()
        .map((m) => ({
          time: new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          cpu: m.cpu?.utilization_percent || 0,
          memory: m.memory?.utilization_percent || 0,
        }));

      setHistory(formattedHistory);
      setAnomalies(anomRes.anomalies || []);
      setAiSummary(sumRes);
      setRisk(riskRes);
    } catch (err) {
      setError(err.message || 'Failed to load system overview.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // 10s poll for summary/anomalies/history
    return () => clearInterval(interval);
  }, []);

  // Incorporate real-time snapshot into chart history
  useEffect(() => {
    if (latestSnapshot) {
      setHistory((prev) => {
        const timeStr = new Date(latestSnapshot.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const newPoint = {
          time: timeStr,
          cpu: latestSnapshot.cpu?.utilization_percent || 0,
          memory: latestSnapshot.memory?.utilization_percent || 0,
        };
        const next = [...prev, newPoint];
        return next.length > 30 ? next.slice(next.length - 30) : next;
      });
    }
  }, [latestSnapshot]);

  const cpuVal = latestSnapshot?.cpu?.utilization_percent ?? (history.length ? history[history.length - 1].cpu : 0);
  const memVal = latestSnapshot?.memory?.utilization_percent ?? (history.length ? history[history.length - 1].memory : 0);
  const diskVal = latestSnapshot?.disk?.utilization_percent ?? 0;
  const upSpeed = latestSnapshot?.network?.upload_speed_bps ? (latestSnapshot.network.upload_speed_bps / 1024).toFixed(1) : '0.0';
  const downSpeed = latestSnapshot?.network?.download_speed_bps ? (latestSnapshot.network.download_speed_bps / 1024).toFixed(1) : '0.0';

  return (
    <div className="space-y-6">
      {error && <ErrorAlert message={error} onRetry={loadData} />}

      {/* Top Banner / AI Headline Insight */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-900/40 via-navy-800 to-indigo-950/40 border border-blue-500/20 p-6 shadow-xl backdrop-blur">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="p-1.5 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-400/30">
                <Sparkles className="w-4 h-4" />
              </span>
              <span className="text-xs font-semibold text-blue-400 tracking-wider uppercase">
                AI Diagnostic Summary
              </span>
              {aiSummary && <StatusBadge status={aiSummary.health_level} size="xs" />}
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              {aiSummary?.headline || 'Autonomous System Diagnostics Initializing...'}
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 max-w-3xl leading-relaxed">
              {aiSummary?.summary || 'SysPredictAI telemetry engine is monitoring physical hardware counters, rolling variance, and predictive regressors in real time.'}
            </p>
          </div>
          <div className="flex items-center space-x-3 shrink-0">
            <button
              onClick={() => onNavigate('ai-insights')}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/20 transition-all hover:scale-[1.02]"
            >
              <span>Explore AI Insights</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-48 h-48 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>
      </div>

      {/* Key Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {loading && !latestSnapshot ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : (
          <>
            <MetricCard
              title="CPU Load"
              value={cpuVal}
              unit="%"
              percentage={cpuVal}
              icon={Cpu}
              status={cpuVal >= 90 ? 'Critical' : cpuVal >= 75 ? 'Warning' : 'Normal'}
              subValue={`${latestSnapshot?.cpu?.core_count_logical || '--'} Logical Threads`}
              trend={risk?.recent_cpu_trend ? `Trend: ${risk.recent_cpu_trend}` : null}
            />
            <MetricCard
              title="Memory Used"
              value={memVal}
              unit="%"
              percentage={memVal}
              icon={Database}
              status={memVal >= 92 ? 'Critical' : memVal >= 80 ? 'Warning' : 'Normal'}
              subValue={
                latestSnapshot?.memory
                  ? `${(latestSnapshot.memory.used_bytes / (1024**3)).toFixed(1)} / ${(latestSnapshot.memory.total_bytes / (1024**3)).toFixed(1)} GB`
                  : '-- GB'
              }
              trend={risk?.recent_memory_trend ? `Trend: ${risk.recent_memory_trend}` : null}
            />
            <MetricCard
              title="Disk Storage"
              value={diskVal}
              unit="%"
              percentage={diskVal}
              icon={HardDrive}
              status={diskVal >= 90 ? 'Critical' : diskVal >= 80 ? 'Warning' : 'Normal'}
              subValue={
                latestSnapshot?.disk
                  ? `${(latestSnapshot.disk.used_bytes / (1024**3)).toFixed(1)} GB used (${latestSnapshot.disk.mount_point})`
                  : '--'
              }
            />
            <MetricCard
              title="Network Throughput"
              value={downSpeed}
              unit="KB/s"
              icon={Network}
              status="Normal"
              subValue={`Upload: ${upSpeed} KB/s`}
            />
          </>
        )}
      </div>

      {/* Live Charts & Overview Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Live Telemetry Chart */}
        <div className="lg:col-span-2 bg-navy-800/90 border border-navy-700/80 rounded-2xl p-6 shadow-xl backdrop-blur">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <Zap className="w-4 h-4 text-blue-400" />
                <span>Live CPU & Memory Utilization</span>
              </h3>
              <p className="text-xs text-slate-400">Streaming real-time samples from active WebSocket</p>
            </div>
            <div className="flex items-center space-x-4 text-xs font-medium">
              <span className="flex items-center space-x-1.5 text-blue-400">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
                <span>CPU %</span>
              </span>
              <span className="flex items-center space-x-1.5 text-emerald-400">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                <span>RAM %</span>
              </span>
            </div>
          </div>

          <div className="h-64 sm:h-72 w-full">
            {history.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
                  <Line
                    type="monotone"
                    dataKey="cpu"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={false}
                    name="CPU Utilization"
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="memory"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={false}
                    name="Memory Utilization"
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                Awaiting telemetry stream points...
              </div>
            )}
          </div>
        </div>

        {/* Recent Anomalies Card */}
        <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-6 shadow-xl backdrop-blur flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>Recent Anomaly Alerts</span>
              </h3>
              <button
                onClick={() => onNavigate('anomalies')}
                className="text-xs text-blue-400 hover:text-blue-300 font-semibold"
              >
                View all
              </button>
            </div>

            {anomalies.length > 0 ? (
              <div className="space-y-3">
                {anomalies.slice(0, 3).map((a, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-navy-900/80 border border-navy-700/70 hover:border-navy-600 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-white uppercase tracking-wider font-mono">
                        {a.metric_name}
                      </span>
                      <StatusBadge status={a.severity} size="xs" />
                    </div>
                    <p className="text-xs text-slate-300 line-clamp-2">{a.explanation}</p>
                    <span className="text-[10px] text-slate-500 font-mono mt-1 block">
                      {new Date(a.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center bg-navy-900/40 rounded-xl border border-navy-700/40">
                <ShieldAlert className="w-8 h-8 text-emerald-400/60 mx-auto mb-2" />
                <h4 className="text-xs font-bold text-slate-200">No Active Anomalies</h4>
                <p className="text-[11px] text-slate-400 mt-1">All monitored metrics conform to expected baseline.</p>
              </div>
            )}
          </div>

          {/* Quick System Info Pill */}
          <div className="mt-4 pt-3 border-t border-navy-700/60 flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center space-x-1.5">
              <Server className="w-3.5 h-3.5 text-blue-400" />
              <span>Platform</span>
            </span>
            <span className="font-mono text-slate-300">
              {latestSnapshot?.cpu?.core_count_physical ? `${latestSnapshot.cpu.core_count_physical} Cores` : 'Local Host'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

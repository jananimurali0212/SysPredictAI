import React, { useEffect, useState } from 'react';
import {
  Cpu,
  Search,
  ArrowUpDown,
  RefreshCw,
  SlidersHorizontal,
  Flame,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../../services/api';
import { TableSkeleton } from '../common/LoadingState';
import ErrorAlert from '../common/ErrorAlert';

export default function ProcessMonitoring() {
  const [processes, setProcesses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('cpu'); // 'cpu' or 'memory'
  const [limit, setLimit] = useState(50);
  const [lastRefreshed, setLastRefreshed] = useState(null);

  const fetchProcesses = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getProcesses(limit, sortBy);
      setProcesses(res.processes || []);
      setLastRefreshed(new Date());
    } catch (err) {
      setError(err.message || 'Failed to fetch process table.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProcesses();
    const timer = setInterval(fetchProcesses, 5000); // 5s cadence
    return () => clearInterval(timer);
  }, [sortBy, limit]);

  const filteredProcesses = processes.filter((p) =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    String(p.pid).includes(searchTerm)
  );

  const topCpuProc = processes.length > 0 ? [...processes].sort((a, b) => b.cpu_percent - a.cpu_percent)[0] : null;
  const topMemProc = processes.length > 0 ? [...processes].sort((a, b) => b.memory_percent - a.memory_percent)[0] : null;

  return (
    <div className="space-y-6">
      {error && <ErrorAlert message={error} onRetry={fetchProcesses} />}

      {/* Top High-Consumer Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-5 shadow-lg backdrop-blur flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1">
              <Flame className="w-4 h-4 text-amber-400" />
              <span>Highest CPU Consumer</span>
            </div>
            <h4 className="text-lg font-bold text-white font-mono truncate max-w-xs">
              {topCpuProc?.name || 'N/A'}
            </h4>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              PID: {topCpuProc?.pid || '--'} | Status: {topCpuProc?.status || 'running'}
            </p>
          </div>
          <div className="text-right">
            <span className="text-2xl font-bold font-mono text-amber-400">
              {topCpuProc?.cpu_percent ?? 0}%
            </span>
            <span className="text-xs text-slate-400 block">CPU Load</span>
          </div>
        </div>

        <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-5 shadow-lg backdrop-blur flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1">
              <Cpu className="w-4 h-4 text-blue-400" />
              <span>Highest Memory Consumer</span>
            </div>
            <h4 className="text-lg font-bold text-white font-mono truncate max-w-xs">
              {topMemProc?.name || 'N/A'}
            </h4>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              PID: {topMemProc?.pid || '--'} | RSS: {topMemProc?.memory_rss_bytes ? `${(topMemProc.memory_rss_bytes / (1024**2)).toFixed(1)} MB` : '--'}
            </p>
          </div>
          <div className="text-right">
            <span className="text-2xl font-bold font-mono text-blue-400">
              {topMemProc?.memory_percent ?? 0}%
            </span>
            <span className="text-xs text-slate-400 block">RAM Share</span>
          </div>
        </div>
      </div>

      {/* Process Table Card */}
      <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl shadow-xl backdrop-blur overflow-hidden">
        {/* Table Toolbar */}
        <div className="p-4 sm:p-5 border-b border-navy-700/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter processes by name or PID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-navy-900 border border-navy-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div className="flex items-center space-x-3 text-xs">
            {/* Sort Toggle */}
            <div className="flex items-center bg-navy-900 rounded-xl p-1 border border-navy-700">
              <button
                onClick={() => setSortBy('cpu')}
                className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                  sortBy === 'cpu' ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                Sort CPU
              </button>
              <button
                onClick={() => setSortBy('memory')}
                className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                  sortBy === 'memory' ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                Sort RAM
              </button>
            </div>

            {/* Refresh Button */}
            <button
              onClick={fetchProcesses}
              disabled={loading}
              className="p-2 rounded-xl bg-navy-900 border border-navy-700 text-slate-400 hover:text-white hover:border-navy-600 transition-colors"
              title="Refresh process list"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
            </button>
          </div>
        </div>

        {/* Process Table View */}
        <div className="overflow-x-auto">
          {loading && processes.length === 0 ? (
            <TableSkeleton rows={8} />
          ) : (
            <table className="w-full text-left text-xs">
              <thead className="bg-navy-900/60 border-b border-navy-700/60 text-slate-400 uppercase font-mono font-semibold tracking-wider">
                <tr>
                  <th className="py-3 px-4">PID</th>
                  <th className="py-3 px-4">Process Name</th>
                  <th className="py-3 px-4">CPU %</th>
                  <th className="py-3 px-4">Memory %</th>
                  <th className="py-3 px-4">Memory (RSS)</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-700/40 text-slate-300 font-mono">
                {filteredProcesses.length > 0 ? (
                  filteredProcesses.map((p) => {
                    const cpuHigh = p.cpu_percent >= 50;
                    const memHigh = p.memory_percent >= 25;
                    return (
                      <tr key={p.pid} className="hover:bg-navy-750/50 transition-colors">
                        <td className="py-3 px-4 text-slate-400">{p.pid}</td>
                        <td className="py-3 px-4 font-semibold text-white max-w-xs truncate">
                          {p.name}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-block font-bold ${
                              cpuHigh ? 'text-amber-400' : 'text-slate-200'
                            }`}
                          >
                            {p.cpu_percent}%
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-block font-bold ${
                              memHigh ? 'text-blue-400' : 'text-slate-200'
                            }`}
                          >
                            {p.memory_percent}%
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-400">
                          {(p.memory_rss_bytes / (1024 * 1024)).toFixed(1)} MB
                        </td>
                        <td className="py-3 px-4">
                          <span className="inline-flex items-center text-[10px] px-2 py-0.5 rounded-full bg-navy-700 text-slate-300">
                            {p.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500 font-sans">
                      No matching processes found for "{searchTerm}".
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>

        {/* Table Footer */}
        <div className="p-3 bg-navy-900/60 border-t border-navy-700/60 flex items-center justify-between text-[11px] text-slate-500 font-mono px-4">
          <span>Displaying {filteredProcesses.length} active processes</span>
          {lastRefreshed && <span>Updated at {lastRefreshed.toLocaleTimeString()}</span>}
        </div>
      </div>
    </div>
  );
}

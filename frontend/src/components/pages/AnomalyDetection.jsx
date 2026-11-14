import React, { useEffect, useState } from 'react';
import {
  AlertOctagon,
  ShieldAlert,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Activity,
  Layers,
  RefreshCw,
} from 'lucide-react';
import { api } from '../../services/api';
import StatusBadge from '../common/StatusBadge';
import { LoadingSpinner } from '../common/LoadingState';
import ErrorAlert from '../common/ErrorAlert';

export default function AnomalyDetection() {
  const [anomalies, setAnomalies] = useState([]);
  const [isolationForestActive, setIsolationForestActive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeverity, setSelectedSeverity] = useState('ALL'); // 'ALL' | 'Critical' | 'High' | 'Medium' | 'Low'
  const [lastRefreshed, setLastRefreshed] = useState(null);

  const fetchAnomalies = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getAnomalies();
      setAnomalies(res.anomalies || []);
      setIsolationForestActive(Boolean(res.isolation_forest_enabled));
      setLastRefreshed(new Date());
    } catch (err) {
      setError(err.message || 'Failed to retrieve system anomalies.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomalies();
    const interval = setInterval(fetchAnomalies, 8000);
    return () => clearInterval(interval);
  }, []);

  const filteredAnomalies = anomalies.filter((a) => {
    if (selectedSeverity === 'ALL') return true;
    return String(a.severity).toLowerCase() === selectedSeverity.toLowerCase();
  });

  const criticalCount = anomalies.filter((a) => a.severity === 'Critical').length;
  const highCount = anomalies.filter((a) => a.severity === 'High').length;
  const mediumCount = anomalies.filter((a) => a.severity === 'Medium').length;
  const lowCount = anomalies.filter((a) => a.severity === 'Low').length;

  return (
    <div className="space-y-6">
      {error && <ErrorAlert message={error} onRetry={fetchAnomalies} />}

      {/* Top Header Card */}
      <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 backdrop-blur shadow-lg">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-rose-600/10 border border-rose-500/20 text-rose-400">
            <AlertOctagon className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-bold text-white">System Anomaly Detection</h2>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-navy-700 text-slate-300 font-mono">
                {isolationForestActive ? 'Isolation Forest + Rules' : 'Rule-Based Engine'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Continuous detection of threshold violations and multivariate telemetry outliers
            </p>
          </div>
        </div>

        <button
          onClick={fetchAnomalies}
          disabled={loading}
          className="self-start md:self-auto px-3.5 py-2 rounded-xl bg-navy-900 border border-navy-700 text-slate-400 hover:text-white hover:border-navy-600 text-xs font-semibold flex items-center space-x-2 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-400' : ''}`} />
          <span>Refresh Alerts</span>
        </button>
      </div>

      {/* Severity Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => setSelectedSeverity('ALL')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
            selectedSeverity === 'ALL'
              ? 'bg-blue-600 text-white border-blue-500 shadow-md shadow-blue-900/20'
              : 'bg-navy-800/90 text-slate-400 border-navy-700 hover:text-white'
          }`}
        >
          All Alerts ({anomalies.length})
        </button>
        <button
          onClick={() => setSelectedSeverity('Critical')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
            selectedSeverity === 'Critical'
              ? 'bg-rose-600 text-white border-rose-500 shadow-md shadow-rose-900/20'
              : 'bg-navy-800/90 text-rose-400 border-navy-700 hover:bg-rose-950/30'
          }`}
        >
          Critical ({criticalCount})
        </button>
        <button
          onClick={() => setSelectedSeverity('High')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
            selectedSeverity === 'High'
              ? 'bg-orange-600 text-white border-orange-500 shadow-md shadow-orange-900/20'
              : 'bg-navy-800/90 text-orange-400 border-navy-700 hover:bg-orange-950/30'
          }`}
        >
          High ({highCount})
        </button>
        <button
          onClick={() => setSelectedSeverity('Medium')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
            selectedSeverity === 'Medium'
              ? 'bg-amber-600 text-white border-amber-500 shadow-md shadow-amber-900/20'
              : 'bg-navy-800/90 text-amber-400 border-navy-700 hover:bg-amber-950/30'
          }`}
        >
          Medium ({mediumCount})
        </button>
        <button
          onClick={() => setSelectedSeverity('Low')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
            selectedSeverity === 'Low'
              ? 'bg-blue-600 text-white border-blue-500'
              : 'bg-navy-800/90 text-slate-400 border-navy-700 hover:text-white'
          }`}
        >
          Low ({lowCount})
        </button>
      </div>

      {/* Anomalies List / Cards */}
      {loading && anomalies.length === 0 ? (
        <LoadingSpinner text="Analyzing telemetry anomalies..." />
      ) : filteredAnomalies.length > 0 ? (
        <div className="grid grid-cols-1 gap-4">
          {filteredAnomalies.map((anom) => (
            <div
              key={anom.anomaly_id}
              className="bg-navy-800/90 border border-navy-700/80 hover:border-navy-600 rounded-2xl p-5 shadow-xl backdrop-blur transition-all"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                <div className="flex items-center space-x-3">
                  <span className="font-mono text-sm font-bold text-white uppercase tracking-wider">
                    {anom.metric_name}
                  </span>
                  <StatusBadge status={anom.severity} size="sm" />
                  <span className="text-xs px-2 py-0.5 rounded-full bg-navy-700/80 text-slate-300 font-mono">
                    {anom.detection_method === 'isolation_forest' ? 'Isolation Forest ML' : 'Rule Based'}
                  </span>
                </div>
                <div className="flex items-center space-x-3 text-xs text-slate-400 font-mono">
                  {anom.anomaly_score !== null && anom.anomaly_score !== undefined && (
                    <span className="text-amber-400">Score: {anom.anomaly_score}</span>
                  )}
                  <span>{new Date(anom.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>

              <div className="space-y-2 text-xs">
                <p className="text-slate-200 leading-relaxed font-medium">
                  {anom.explanation}
                </p>

                <div className="pt-3 border-t border-navy-700/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-slate-400">
                  <div className="flex items-center space-x-2">
                    <span className="text-slate-500 font-mono">Observed:</span>
                    <span className="text-white font-mono font-semibold">
                      {anom.observed_value}
                    </span>
                    {anom.threshold_or_baseline !== null && (
                      <span className="text-slate-500 font-mono">
                        (Baseline: {anom.threshold_or_baseline})
                      </span>
                    )}
                  </div>

                  <div className="flex items-start sm:items-center space-x-1.5 text-blue-300 font-medium bg-blue-950/40 border border-blue-800/40 rounded-xl px-3 py-1.5">
                    <span className="text-slate-400 text-[11px] font-mono">Action:</span>
                    <span className="text-xs">{anom.recommended_action}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty State */
        <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-12 text-center backdrop-blur shadow-xl space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-white">No Anomalies Detected</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            {selectedSeverity === 'ALL'
              ? 'All monitored hardware metrics (CPU, RAM, Storage, Network) are operating within normal safe thresholds.'
              : `Zero active anomalies found for severity filter "${selectedSeverity}".`}
          </p>
          <span className="text-[11px] font-mono text-slate-500 block">
            SysPredictAI never fabricates alerts. Real events appear as they occur.
          </span>
        </div>
      )}
    </div>
  );
}

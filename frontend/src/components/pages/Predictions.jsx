import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  Cpu,
  Database,
  Info,
  Clock,
  Sparkles,
  Layers,
  BarChart2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { api } from '../../services/api';
import MetricCard from '../common/MetricCard';
import StatusBadge from '../common/StatusBadge';
import { LoadingSpinner } from '../common/LoadingState';
import ErrorAlert from '../common/ErrorAlert';

export default function Predictions() {
  const [cpuForecast, setCpuForecast] = useState(null);
  const [memForecast, setMemForecast] = useState(null);
  const [summary, setSummary] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState('cpu'); // 'cpu' or 'memory'

  const loadPredictions = async () => {
    try {
      setLoading(true);
      setError(null);
      const [cpuRes, memRes, sumRes, histRes] = await Promise.all([
        api.getCPUPrediction('60,300,900'),
        api.getMemoryPrediction('60,300,900'),
        api.getPredictionSummary(),
        api.getHistory(20),
      ]);

      setCpuForecast(cpuRes);
      setMemForecast(memRes);
      setSummary(sumRes);

      // Build historical actual points
      const histPoints = (histRes.metrics || [])
        .slice()
        .reverse()
        .map((m) => ({
          label: new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          actual: selectedMetric === 'cpu' ? m.cpu?.utilization_percent : m.memory?.utilization_percent,
          predicted: null,
          isForecast: false,
        }));

      setHistory(histPoints);
    } catch (err) {
      setError(err.message || 'Failed to load predictive analytics data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPredictions();
  }, [selectedMetric]);

  const activeForecast = selectedMetric === 'cpu' ? cpuForecast : memForecast;
  const isInsufficient = activeForecast?.status === 'insufficient_data';

  // Construct combined chart data: historical points + predicted horizon points
  const combinedChartData = [...history];
  if (!isInsufficient && activeForecast?.predictions && activeForecast.predictions.length > 0) {
    // Connect the last historical point with the forecast
    if (combinedChartData.length > 0) {
      combinedChartData[combinedChartData.length - 1].predicted = combinedChartData[combinedChartData.length - 1].actual;
    }
    activeForecast.predictions.forEach((pt) => {
      combinedChartData.push({
        label: `+${pt.horizon_seconds}s (${new Date(pt.target_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})`,
        actual: null,
        predicted: pt.predicted_value,
        lowerBound: pt.lower_bound,
        upperBound: pt.upper_bound,
        isForecast: true,
      });
    });
  }

  return (
    <div className="space-y-6">
      {error && <ErrorAlert message={error} onRetry={loadPredictions} />}

      {/* Top Banner Notice */}
      <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 backdrop-blur shadow-lg">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-blue-600/10 border border-blue-500/20 text-blue-400">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-bold text-white">Resource Demand Forecasting</h2>
              <StatusBadge status={activeForecast?.method_used || 'Initializing'} size="xs" />
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Multi-horizon time-series regression trained on chronological telemetry records
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Metric Selector Tabs */}
          <div className="flex items-center bg-navy-900 rounded-xl p-1 border border-navy-700 text-xs">
            <button
              onClick={() => setSelectedMetric('cpu')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                selectedMetric === 'cpu' ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>CPU Forecast</span>
            </button>
            <button
              onClick={() => setSelectedMetric('memory')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                selectedMetric === 'memory' ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>RAM Forecast</span>
            </button>
          </div>

          <button
            onClick={loadPredictions}
            disabled={loading}
            className="p-2 rounded-xl bg-navy-900 border border-navy-700 text-slate-400 hover:text-white hover:border-navy-600 transition-colors"
            title="Refresh predictions"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Disclaimers & Model Info Pill */}
      <div className="bg-blue-950/30 border border-blue-800/40 rounded-xl p-3.5 text-xs text-blue-200/90 flex items-center space-x-2.5">
        <Info className="w-4 h-4 text-blue-400 shrink-0" />
        <span>
          <strong>Statistical Estimate Notice:</strong> Predicted values represent short-term regression forecasts calculated from historical lag dynamics and trend momentum. They are probabilistic estimations, not actual physical measurements.
        </span>
      </div>

      {/* Insufficient Data State */}
      {isInsufficient ? (
        <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-8 text-center backdrop-blur shadow-xl space-y-3">
          <AlertCircle className="w-10 h-10 text-amber-400 mx-auto" />
          <h3 className="text-base font-bold text-white">Insufficient Historical Data for Reliable Forecasting</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            {activeForecast?.message || 'The system requires at least 30 historical telemetry records before training Random Forest regression models. Zero fabricated predictions are displayed.'}
          </p>
          <div className="pt-2">
            <span className="text-[11px] font-mono text-slate-500">
              The monitoring daemon is actively logging metric snapshots to SQLite (1-second cadence).
            </span>
          </div>
        </div>
      ) : (
        <>
          {/* Forecast Cards Grid (60s, 300s, 900s) */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {activeForecast?.predictions?.map((pt, idx) => (
              <MetricCard
                key={idx}
                title={`Horizon: +${pt.horizon_seconds}s (${pt.horizon_seconds / 60}m)`}
                value={pt.predicted_value}
                unit="%"
                percentage={pt.predicted_value}
                status={pt.predicted_value >= 85 ? 'Critical' : pt.predicted_value >= 70 ? 'Warning' : 'Normal'}
                subValue={`Bounds: ${pt.lower_bound}% – ${pt.upper_bound}%`}
                trend={`At ${new Date(pt.target_timestamp).toLocaleTimeString()}`}
              />
            ))}
          </div>

          {/* Historical vs. Forecast Chart */}
          <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-6 shadow-xl backdrop-blur">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-2">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                  <BarChart2 className="w-4 h-4 text-blue-400" />
                  <span>Historical Actual vs. Forecasted Utilization</span>
                </h3>
                <p className="text-xs text-slate-400">
                  Solid line denotes recorded historical telemetry; dashed line indicates forward regression
                </p>
              </div>

              <div className="flex items-center space-x-4 text-xs font-mono">
                <span className="flex items-center space-x-1.5 text-blue-400">
                  <span className="w-3 h-0.5 bg-blue-500"></span>
                  <span>Actual Recorded</span>
                </span>
                <span className="flex items-center space-x-1.5 text-purple-400">
                  <span className="w-3 h-0.5 border-t-2 border-dashed border-purple-400"></span>
                  <span>Model Forecast</span>
                </span>
              </div>
            </div>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={combinedChartData} margin={{ top: 15, right: 15, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                  <XAxis dataKey="label" stroke="#64748b" tick={{ fontSize: 10 }} tickLine={false} />
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
                  {/* Actual recorded telemetry */}
                  <Line
                    type="monotone"
                    dataKey="actual"
                    stroke="#3b82f6"
                    strokeWidth={2.5}
                    dot={{ r: 2 }}
                    name="Actual %"
                    isAnimationActive={false}
                  />
                  {/* Predicted forward values */}
                  <Line
                    type="monotone"
                    dataKey="predicted"
                    stroke="#c084fc"
                    strokeWidth={2.5}
                    strokeDasharray="5 5"
                    dot={{ r: 4, fill: '#c084fc' }}
                    name="Forecast %"
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Model Performance Evaluation Card */}
          {activeForecast?.evaluation && (
            <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-6 shadow-xl backdrop-blur">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-blue-400" />
                    <span>Model Architecture & Evaluation Metrics</span>
                  </h3>
                  <p className="text-xs text-slate-400">
                    Chronological test evaluation vs. moving average baseline
                  </p>
                </div>
                <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-navy-700 text-slate-300">
                  {activeForecast?.model_metadata?.model_type || 'RandomForestRegressor'}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center font-mono">
                <div className="bg-navy-900/80 border border-navy-700/60 rounded-xl p-3.5">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                    Model MAE
                  </span>
                  <span className="text-xl font-bold text-emerald-400">
                    {activeForecast.evaluation.model_mae}
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-0.5">Mean Absolute Error</span>
                </div>

                <div className="bg-navy-900/80 border border-navy-700/60 rounded-xl p-3.5">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                    Model RMSE
                  </span>
                  <span className="text-xl font-bold text-blue-400">
                    {activeForecast.evaluation.model_rmse}
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-0.5">Root Mean Squared</span>
                </div>

                <div className="bg-navy-900/80 border border-navy-700/60 rounded-xl p-3.5">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                    Baseline MAE
                  </span>
                  <span className="text-xl font-bold text-slate-300">
                    {activeForecast.evaluation.baseline_mae}
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-0.5">Moving Average Baseline</span>
                </div>

                <div className="bg-navy-900/80 border border-navy-700/60 rounded-xl p-3.5">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                    Samples Evaluated
                  </span>
                  <span className="text-xl font-bold text-slate-200">
                    {activeForecast.model_metadata?.training_samples || 0} / {activeForecast.model_metadata?.test_samples || 0}
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-0.5">Train / Test split</span>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

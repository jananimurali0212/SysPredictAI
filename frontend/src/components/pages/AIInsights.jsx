import React, { useState } from 'react';
import {
  Sparkles,
  Send,
  HelpCircle,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  Cpu,
  Database,
  ShieldCheck,
  Zap,
  Info,
} from 'lucide-react';
import { api } from '../../services/api';
import StatusBadge from '../common/StatusBadge';
import { LoadingSpinner } from '../common/LoadingState';
import ErrorAlert from '../common/ErrorAlert';

const SUGGESTED_QUESTIONS = [
  'Why is my CPU usage high?',
  'Why is my RAM utilization increasing?',
  'Which process is consuming the most resources?',
  'What does this anomaly mean?',
  'What is the current system health?',
  'How can I improve system performance?',
  'Explain my recent system performance.',
];

export default function AIInsights() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  const handleAsk = async (qText) => {
    const targetQ = qText || question;
    if (!targetQ.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.queryAI(targetQ);
      setHistory((prev) => [response, ...prev]);
      if (!qText) setQuestion('');
    } catch (err) {
      setError(err.message || 'Failed to query AI insights service.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {error && <ErrorAlert message={error} onRetry={() => handleAsk()} />}

      {/* AI Assistant Header Card */}
      <div className="bg-gradient-to-r from-blue-900/40 via-navy-800 to-indigo-950/40 border border-blue-500/20 rounded-2xl p-6 shadow-xl backdrop-blur">
        <div className="flex items-center space-x-3.5 mb-2">
          <div className="p-2.5 rounded-xl bg-blue-500/20 border border-blue-400/30 text-blue-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <span>Gemini-Powered Diagnostic Assistant</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-mono border border-blue-500/30">
                Grounding Active
              </span>
            </h2>
            <p className="text-xs text-slate-300">
              Context-aware system diagnostics synthesizing real-time hardware telemetry, process tables, forecasts, and anomaly logs.
            </p>
          </div>
        </div>

        {/* Question Input Box */}
        <div className="mt-5 relative">
          <input
            type="text"
            placeholder="Ask anything about current CPU load, memory churn, anomalies, or performance..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
            disabled={loading}
            className="w-full pl-4 pr-24 py-3.5 bg-navy-900/90 border border-navy-700 rounded-xl text-xs sm:text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 shadow-inner"
          />
          <button
            onClick={() => handleAsk()}
            disabled={loading || !question.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-navy-700 disabled:text-slate-500 text-white font-semibold text-xs rounded-lg flex items-center space-x-1.5 transition-all shadow-md shadow-blue-600/20"
          >
            <span>Ask</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Suggested Quick Questions */}
        <div className="mt-4">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2 font-mono">
            Suggested Diagnostic Inquiries:
          </span>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleAsk(q)}
                disabled={loading}
                className="text-xs px-3 py-1.5 rounded-xl bg-navy-900/80 hover:bg-navy-750 text-slate-300 border border-navy-700/80 hover:border-blue-500/40 transition-colors text-left font-medium"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Security & Grounding Policy Notice */}
      <div className="bg-navy-800/60 border border-navy-700/60 rounded-xl p-3.5 text-xs text-slate-400 flex items-start space-x-2.5">
        <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <span>
          <strong>Telemetry Grounding & Security:</strong> All AI analyses are strictly grounded in live hardware measurements. API keys remain protected on the backend. Directly observed telemetry facts are clearly separated from possible causes.
        </span>
      </div>

      {/* Loading Indicator */}
      {loading && <LoadingSpinner text="Consulting Gemini diagnostic engine..." />}

      {/* Results / History Stream */}
      <div className="space-y-6">
        {history.length > 0 ? (
          history.map((item, idx) => (
            <div
              key={idx}
              className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-6 shadow-xl backdrop-blur space-y-4"
            >
              {/* Question Header & Source */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-navy-700/60">
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-lg bg-blue-600/10 text-blue-400">
                    <HelpCircle className="w-4 h-4" />
                  </div>
                  <h3 className="text-sm font-bold text-white font-mono">{item.question}</h3>
                </div>
                <div className="flex items-center space-x-2 text-xs font-mono">
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-navy-700 text-slate-300">
                    {item.source === 'gemini_api' ? 'Google Gemini 1.5' : 'Grounded Telemetry Engine'}
                  </span>
                  <span className="text-slate-500">{new Date(item.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>

              {/* Main Synthesized Analysis */}
              <div className="text-xs sm:text-sm text-slate-200 leading-relaxed font-sans bg-navy-900/60 p-4 rounded-xl border border-navy-700/60">
                <p>{item.analysis}</p>
              </div>

              {/* Structured Facts vs Causes vs Actions Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                {/* 1. Directly Observed Facts */}
                <div className="bg-navy-900/80 border border-navy-700/60 rounded-xl p-4 space-y-2">
                  <div className="flex items-center space-x-2 text-emerald-400 font-semibold uppercase tracking-wider font-mono text-[11px]">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Observed Facts</span>
                  </div>
                  <ul className="space-y-1.5 text-slate-300">
                    {item.observed_facts?.map((fact, fIdx) => (
                      <li key={fIdx} className="flex items-start space-x-2">
                        <span className="text-emerald-400 font-bold">•</span>
                        <span>{fact}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 2. Plausible Technical Causes */}
                <div className="bg-navy-900/80 border border-navy-700/60 rounded-xl p-4 space-y-2">
                  <div className="flex items-center space-x-2 text-amber-400 font-semibold uppercase tracking-wider font-mono text-[11px]">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Possible Causes</span>
                  </div>
                  <ul className="space-y-1.5 text-slate-300">
                    {item.possible_causes?.map((cause, cIdx) => (
                      <li key={cIdx} className="flex items-start space-x-2">
                        <span className="text-amber-400 font-bold">•</span>
                        <span>{cause}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 3. Recommended Actions */}
                <div className="bg-navy-900/80 border border-navy-700/60 rounded-xl p-4 space-y-2">
                  <div className="flex items-center space-x-2 text-blue-400 font-semibold uppercase tracking-wider font-mono text-[11px]">
                    <Lightbulb className="w-3.5 h-3.5" />
                    <span>Recommended Actions</span>
                  </div>
                  <ul className="space-y-1.5 text-slate-300">
                    {item.recommended_actions?.map((rec, rIdx) => (
                      <li key={rIdx} className="flex items-start space-x-2">
                        <span className="text-blue-400 font-bold">•</span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))
        ) : (
          /* Empty Initial State */
          <div className="bg-navy-800/90 border border-navy-700/80 rounded-2xl p-10 text-center backdrop-blur shadow-xl space-y-3">
            <Sparkles className="w-8 h-8 text-blue-400/60 mx-auto" />
            <h3 className="text-sm font-bold text-white">Ask an AI Performance Question</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Select one of the suggested diagnostic inquiries above or type a custom question to analyze real host system metrics.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

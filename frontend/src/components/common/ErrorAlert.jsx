import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function ErrorAlert({ title = 'Error', message, onRetry }) {
  return (
    <div className="bg-rose-950/40 border border-rose-800/60 rounded-xl p-4 text-rose-200 flex items-start space-x-3 shadow-lg">
      <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
      <div className="flex-1">
        <h4 className="text-sm font-semibold text-rose-300">{title}</h4>
        <p className="text-xs text-rose-200/80 mt-1">{message || 'An unexpected error occurred while communicating with the backend.'}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-3 inline-flex items-center space-x-1.5 px-3 py-1.5 bg-rose-900/60 hover:bg-rose-800/80 border border-rose-700/60 rounded-lg text-xs font-medium text-white transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Connection</span>
          </button>
        )}
      </div>
    </div>
  );
}

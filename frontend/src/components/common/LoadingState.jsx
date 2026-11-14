import React from 'react';
import { Loader2 } from 'lucide-react';

export function LoadingSpinner({ text = 'Loading system telemetry...' }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-slate-400 space-y-3">
      <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      <span className="text-sm font-medium">{text}</span>
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-navy-800/90 border border-navy-700/80 rounded-xl p-5 animate-pulse space-y-3">
      <div className="flex justify-between items-center">
        <div className="h-4 bg-navy-700 rounded w-24"></div>
        <div className="h-4 bg-navy-700 rounded-full w-12"></div>
      </div>
      <div className="h-8 bg-navy-700 rounded w-32"></div>
      <div className="h-2 bg-navy-700 rounded w-full"></div>
    </div>
  );
}

export function TableSkeleton({ rows = 5 }) {
  return (
    <div className="space-y-2 p-4 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-10 bg-navy-800 rounded-lg flex items-center px-4 space-x-4">
          <div className="h-4 bg-navy-700 rounded w-1/4"></div>
          <div className="h-4 bg-navy-700 rounded w-1/6"></div>
          <div className="h-4 bg-navy-700 rounded w-1/6"></div>
          <div className="h-4 bg-navy-700 rounded w-1/4"></div>
        </div>
      ))}
    </div>
  );
}

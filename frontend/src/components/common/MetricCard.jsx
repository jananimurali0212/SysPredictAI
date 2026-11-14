import React from 'react';
import StatusBadge from './StatusBadge';

export default function MetricCard({
  title,
  value,
  unit = '',
  percentage,
  subValue,
  icon: Icon,
  status,
  trend,
  color = 'blue',
  children,
}) {
  const getBarColor = (pct) => {
    if (pct >= 90) return 'bg-rose-500';
    if (pct >= 75) return 'bg-amber-500';
    return 'bg-blue-500';
  };

  return (
    <div className="bg-navy-800/90 border border-navy-700/80 rounded-xl p-5 shadow-lg backdrop-blur hover:border-navy-600/80 transition-all">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2.5">
          {Icon && (
            <div className="p-2 rounded-lg bg-navy-750 text-blue-400 border border-navy-700">
              <Icon className="w-5 h-5" />
            </div>
          )}
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</span>
        </div>
        {status && <StatusBadge status={status} size="xs" />}
      </div>

      <div className="flex items-baseline space-x-2">
        <span className="text-2xl font-bold tracking-tight text-white font-mono">
          {value !== undefined && value !== null ? value : '--'}
        </span>
        {unit && <span className="text-sm font-medium text-slate-400">{unit}</span>}
      </div>

      {percentage !== undefined && percentage !== null && (
        <div className="mt-3">
          <div className="w-full bg-navy-700/60 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${getBarColor(percentage)}`}
              style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
            />
          </div>
        </div>
      )}

      {subValue && (
        <div className="mt-3 pt-2.5 border-t border-navy-700/50 flex items-center justify-between text-xs text-slate-400">
          <span>{subValue}</span>
          {trend && (
            <span className={trend.startsWith('+') ? 'text-amber-400' : 'text-emerald-400'}>
              {trend}
            </span>
          )}
        </div>
      )}

      {children && <div className="mt-3">{children}</div>}
    </div>
  );
}

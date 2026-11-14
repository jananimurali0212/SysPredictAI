import React from 'react';

export default function StatusBadge({ status, size = 'sm' }) {
  if (!status) return null;

  const normalized = String(status).toLowerCase();

  let colorClasses = 'bg-blue-500/10 text-blue-400 border-blue-500/20';

  if (['normal', 'healthy', 'low', 'success', 'stable'].includes(normalized)) {
    colorClasses = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
  } else if (['warning', 'medium', 'degraded', 'rising'].includes(normalized)) {
    colorClasses = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
  } else if (['high', 'high risk'].includes(normalized)) {
    colorClasses = 'bg-orange-500/10 text-orange-400 border-orange-500/20';
  } else if (['critical', 'error', 'failed'].includes(normalized)) {
    colorClasses = 'bg-rose-500/10 text-rose-400 border-rose-500/20';
  }

  const sizeClasses = size === 'xs' 
    ? 'text-[10px] px-1.5 py-0.5' 
    : size === 'md'
    ? 'text-xs px-2.5 py-1'
    : 'text-[11px] px-2 py-0.5';

  return (
    <span className={`inline-flex items-center font-medium rounded-full border ${sizeClasses} ${colorClasses}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current animate-pulse"></span>
      {status}
    </span>
  );
}

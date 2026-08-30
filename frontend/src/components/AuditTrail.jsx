// frontend/src/components/AuditTrail.jsx

import { useEffect, useRef } from 'react'
import { formatTime, formatAuditStatus } from '../utils/formatters'

const AuditTrail = ({ logs }) => {
  const bottomRef = useRef(null)

  useEffect(() => {
      // Auto-scroll disabled — user controls audit trail scrolling
  }, [])

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 flex flex-col h-64">
      <div className="px-4 py-3 border-b border-slate-700 flex items-center justify-between">
        <h3 className="text-slate-400 text-sm font-medium">📋 Audit Trail</h3>
        <span className="text-slate-500 text-xs">{logs.length} events</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {logs.length === 0 ? (
          <p className="text-slate-500 text-xs text-center mt-4">
            No events yet. Start chatting!
          </p>
        ) : (
          logs.map((log, index) => (
            <div
              key={index}
              className="flex items-start gap-2 text-xs"
            >
              {/* Status badge */}
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${formatAuditStatus(log.status)}`}>
                {log.status}
              </span>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1">
                  <span className="text-blue-400 font-medium">{log.node}</span>
                  <span className="text-slate-500">→</span>
                  <span className="text-slate-300 truncate">{log.action}</span>
                </div>
                {log.detail && (
                  <p className="text-slate-500 truncate mt-0.5">{log.detail}</p>
                )}
              </div>

              <span className="text-slate-600 flex-shrink-0">
                {formatTime(log.timestamp)}
              </span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}

export default AuditTrail
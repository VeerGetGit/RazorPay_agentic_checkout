// frontend/src/components/FailureAlert.jsx

const FailureAlert = ({ reason, onRetry, onDismiss }) => {
  return (
    <div className="bg-red-950 border border-red-800 rounded-xl p-4 mx-4 mb-3">
      <div className="flex items-start gap-3">
        <span className="text-red-400 text-xl flex-shrink-0">⚠️</span>
        <div className="flex-1">
          <p className="text-red-300 font-medium text-sm">Payment Failed</p>
          <p className="text-red-400 text-xs mt-1">
            {reason || 'Something went wrong. Please try again.'}
          </p>

          <div className="flex gap-2 mt-3">
            {onRetry && (
              <button
                onClick={onRetry}
                className="px-3 py-1.5 bg-red-800 text-red-200 rounded-lg text-xs hover:bg-red-700 transition-colors"
              >
                Retry Payment
              </button>
            )}
            <button
              onClick={onDismiss}
              className="px-3 py-1.5 bg-[#141414] text-slate-400 rounded-lg text-xs hover:bg-[#1E1E1E] transition-colors"
            >
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FailureAlert
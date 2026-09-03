// frontend/src/components/SpendMeter.jsx

import { formatRupees } from '../utils/formatters'

const SpendMeter = ({ spendLimit, spentSoFar, remainingLimit }) => {
  const percentage = spendLimit > 0
    ? Math.min((spentSoFar / spendLimit) * 100, 100)
    : 0

  const getColor = () => {
    if (percentage >= 90) return 'bg-red-500'
    if (percentage >= 70) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  return (
    <div className="bg-[#141414] rounded-xl p-4 border border-[#2A2A2A]">
      <div className="flex justify-between items-center mb-2">
        <span className="text-slate-400 text-sm font-medium">💰 Spend Limit</span>
        <span className="text-slate-300 text-sm">
          {formatRupees(spentSoFar)} / {formatRupees(spendLimit)}
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-[#1E1E1E] rounded-full h-3 mb-2">
        <div
          className={`h-3 rounded-full transition-all duration-500 ${getColor()}`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      <div className="flex justify-between text-xs">
        <span className="text-slate-500">Used: {formatRupees(spentSoFar)}</span>
        <span className={`font-medium ${
          percentage >= 90 ? 'text-red-400' :
          percentage >= 70 ? 'text-yellow-400' : 'text-[#D4A017]'
        }`}>
          {formatRupees(remainingLimit || spendLimit - spentSoFar)} remaining
        </span>
      </div>
    </div>
  )
}

export default SpendMeter
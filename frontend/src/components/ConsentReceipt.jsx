// frontend/src/components/ConsentReceipt.jsx

import { formatRupees } from '../utils/formatters'

const ConsentReceipt = ({ cart, cartTotal, spendLimit, spentSoFar, onConfirm, onCancel }) => {
  const remaining = spendLimit - spentSoFar

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-2xl border border-slate-600 w-full max-w-sm shadow-2xl">

        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-700">
          <h2 className="text-white font-bold text-lg">💳 Confirm Payment</h2>
          <p className="text-slate-400 text-sm">Review your order before paying</p>
        </div>

        {/* Cart items */}
        <div className="px-6 py-4 space-y-2">
          {cart.map((item, index) => (
            <div key={index} className="flex justify-between text-sm">
              <span className="text-slate-300">
                {item.name} × {item.quantity}
              </span>
              <span className="text-slate-200 font-medium">
                {formatRupees(item.total)}
              </span>
            </div>
          ))}

          <div className="border-t border-slate-700 pt-2 mt-2">
            <div className="flex justify-between font-bold">
              <span className="text-white">Total</span>
              <span className="text-blue-400 text-lg">{formatRupees(cartTotal)}</span>
            </div>
          </div>
        </div>

        {/* Spend info */}
        <div className="px-6 py-3 bg-slate-900 mx-4 rounded-xl mb-4">
          <div className="flex justify-between text-xs text-slate-400">
            <span>Spend limit</span>
            <span>{formatRupees(spendLimit)}</span>
          </div>
          <div className="flex justify-between text-xs text-slate-400 mt-1">
            <span>After payment</span>
            <span className={remaining - cartTotal < 0 ? 'text-red-400' : 'text-green-400'}>
              {formatRupees(remaining - cartTotal)} remaining
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="px-6 pb-6 flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 py-3 rounded-xl bg-slate-700 text-slate-300 font-medium hover:bg-slate-600 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 py-3 rounded-xl bg-blue-600 text-white font-bold hover:bg-blue-500 transition-colors"
          >
            Confirm Payment
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConsentReceipt
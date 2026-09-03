// frontend/src/components/ConsentReceipt.jsx
import { formatRupees } from '../utils/formatters'

const ConsentReceipt = ({ cart, cartTotal, spendLimit, spentSoFar, onConfirm, onCancel }) => {
  const remaining = spendLimit - spentSoFar
  return (
    <div className="bg-[#141414] rounded-2xl border border-[#D4A017] w-full shadow-2xl mb-3">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[#2A2A2A]">
        <h2 className="text-[#D4A017] font-bold text-lg">Confirm Payment</h2>
        <p className="text-slate-400 text-sm">Review your order before paying</p>
      </div>

      {/* Cart items */}
      <div className="px-6 py-4 space-y-2">
        {cart.map((item, index) => (
          <div key={index} className="flex justify-between text-sm">
            <span className="text-slate-300">
              {item.name} x {item.quantity}
            </span>
            <span className="text-white font-medium">
              {formatRupees(item.total)}
            </span>
          </div>
        ))}
        <div className="border-t border-[#2A2A2A] pt-2 mt-2">
          <div className="flex justify-between font-bold">
            <span className="text-white">Total</span>
            <span className="text-[#D4A017] text-lg">{formatRupees(cartTotal)}</span>
          </div>
        </div>
      </div>

      {/* Spend info */}
      <div className="px-6 py-3 bg-[#0A0A0A] mx-4 rounded-xl mb-4">
        <div className="flex justify-between text-xs text-slate-400">
          <span>Spend limit</span>
          <span>{formatRupees(spendLimit)}</span>
        </div>
        <div className="flex justify-between text-xs text-slate-400 mt-1">
          <span>After payment</span>
          <span className={remaining - cartTotal < 0 ? 'text-red-400' : 'text-[#D4A017]'}>
            {formatRupees(remaining - cartTotal)} remaining
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="px-6 pb-6 flex gap-3">
        <button
          onClick={onCancel}
          className="flex-1 py-3 rounded-xl bg-[#1E1E1E] text-slate-300 font-medium hover:bg-[#2A2A2A] transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          className="flex-1 py-3 rounded-xl bg-[#D4A017] text-black font-bold hover:bg-[#F0C040] transition-colors"
        >
          Confirm Payment
        </button>
      </div>
    </div>
  )
}

export default ConsentReceipt
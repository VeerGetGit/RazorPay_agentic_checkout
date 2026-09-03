// frontend/src/components/OrderReceipt.jsx

import { formatRupees, formatTime } from '../utils/formatters'

const OrderReceipt = ({ orderId, amount, cart, onClose }) => {
  return (
    <div className="bg-[#141414] border border-[#D4A017] rounded-xl p-4 mx-0 mb-3">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl">🎉</span>
        <div>
          <p className="text-[#D4A017] font-bold">Payment Successful!</p>
          <p className="text-gray-400 text-xs">Your order has been placed</p>
        </div>
      </div>

      <div className="bg-[#1E1E1E] rounded-lg p-3 space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Order ID</span>
          <span className="text-white font-mono text-xs">{orderId || 'N/A'}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Amount</span>
          <span className="text-[#D4A017] font-bold">{formatRupees(amount)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Time</span>
          <span className="text-white">{formatTime(new Date().toISOString())}</span>
        </div>
      </div>

      {cart && cart.length > 0 && (
        <div className="mt-3 space-y-1">
          {cart.map((item, i) => (
            <div key={i} className="flex justify-between text-xs text-gray-400">
              <span>{item.name} × {item.quantity}</span>
              <span className="text-white">{formatRupees(item.total)}</span>
            </div>
          ))}
        </div>
      )}

      <button
        onClick={onClose}
        className="mt-3 w-full py-2 bg-[#D4A017] text-black rounded-lg text-sm font-bold hover:bg-[#F0C040] transition-colors"
      >
        Continue Shopping
      </button>
    </div>
  )
}

export default OrderReceipt
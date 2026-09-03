// frontend/src/components/OrderReceipt.jsx

import { formatRupees, formatTime } from '../utils/formatters'

const OrderReceipt = ({ orderId, amount, cart, onClose }) => {
  return (
    <div className="bg-green-950 border border-green-800 rounded-xl p-4 mx-0 mb-3">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl">🎉</span>
        <div>
          <p className="text-green-300 font-bold">Payment Successful!</p>
          <p className="text-green-500 text-xs">Your order has been placed</p>
        </div>
      </div>

      <div className="bg-green-900 bg-opacity-50 rounded-lg p-3 space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-[#D4A017]">Order ID</span>
          <span className="text-green-200 font-mono text-xs">{orderId}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-[#D4A017]">Amount</span>
          <span className="text-green-200 font-bold">{formatRupees(amount)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-[#D4A017]">Time</span>
          <span className="text-green-200">{formatTime(new Date().toISOString())}</span>
        </div>
      </div>

      {cart && cart.length > 0 && (
        <div className="mt-3 space-y-1">
          {cart.map((item, i) => (
            <div key={i} className="flex justify-between text-xs text-green-500">
              <span>{item.name} × {item.quantity}</span>
              <span>{formatRupees(item.total)}</span>
            </div>
          ))}
        </div>
      )}

      <button
        onClick={onClose}
        className="mt-3 w-full py-2 bg-green-800 text-green-200 rounded-lg text-sm hover:bg-green-700 transition-colors"
      >
        Continue Shopping
      </button>
    </div>
  )
}

export default OrderReceipt
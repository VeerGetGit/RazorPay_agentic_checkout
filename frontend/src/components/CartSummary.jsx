// frontend/src/components/CartSummary.jsx

import { formatRupees } from '../utils/formatters'

const CartSummary = ({ cart, cartTotal }) => {
  if (!cart || cart.length === 0) {
    return (
      <div className="bg-[#141414] rounded-xl p-4 border border-[#2A2A2A]">
        <h3 className="text-slate-400 text-sm font-medium mb-2">🛒 Cart</h3>
        <p className="text-slate-500 text-sm">Your cart is empty</p>
      </div>
    )
  }

  return (
    <div className="bg-[#141414] rounded-xl p-4 border border-[#2A2A2A]">
      <h3 className="text-slate-400 text-sm font-medium mb-3">
        🛒 Cart ({cart.length} item{cart.length > 1 ? 's' : ''})
      </h3>

      <div className="space-y-2">
        {cart.map((item, index) => (
          <div
            key={index}
            className="flex justify-between items-center py-2 border-b border-[#2A2A2A] last:border-0"
          >
            <div className="flex-1">
              <p className="text-slate-200 text-sm font-medium">{item.name}</p>
              <p className="text-slate-500 text-xs">
                {formatRupees(item.price)} × {item.quantity}
              </p>
            </div>
            <span className="text-slate-300 text-sm font-medium">
              {formatRupees(item.total)}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t border-slate-600 flex justify-between">
        <span className="text-slate-400 text-sm">Total</span>
        <span className="text-white font-bold">{formatRupees(cartTotal)}</span>
      </div>
    </div>
  )
}

export default CartSummary
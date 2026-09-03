// frontend/src/components/RevenueWidget.jsx

import { useState, useEffect } from 'react'

const RevenueWidget = () => {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchMetrics = async () => {
    try {
      const r = await fetch('https://razorpay-agentic-checkout.onrender.com/api/analytics/aov')
      const d = await r.json()
      setMetrics(d)
    } catch (e) {
      console.error('Analytics fetch error:', e)
    } finally {
      setLoading(false)
    }
  }

  // Fetch on mount and every 10 seconds
  useEffect(() => {
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 10000)
    return () => clearInterval(interval)
  }, [])

  if (loading) return (
    <div className="bg-[#141414] rounded-xl p-4 border border-[#2A2A2A]">
      <div className="text-slate-500 text-xs">Loading metrics...</div>
    </div>
  )

    return (
    <div className="bg-[#141414] rounded-xl p-4 border border-[#2A2A2A]">

      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[#D4A017] font-bold text-sm flex items-center gap-2">
          📈 Merchant Revenue
        </h3>
        <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-2">

        <div className="bg-[#1E1E1E] rounded-lg p-2">
          <div className="text-slate-400 text-xs mb-1">Total Revenue</div>
          <div className="text-white font-bold text-sm">
            ₹{(metrics?.total_revenue || 0).toLocaleString('en-IN')}
          </div>
        </div>

        <div className="bg-[#1E1E1E] rounded-lg p-2">
          <div className="text-slate-400 text-xs mb-1">Orders</div>
          <div className="text-white font-bold text-sm">
            {metrics?.total_orders || 0}
          </div>
        </div>

        <div className="bg-[#1E1E1E] rounded-lg p-2">
          <div className="text-slate-400 text-xs mb-1">Avg Order Value</div>
          <div className="text-[#D4A017] font-bold text-sm">
            ₹{Math.round(metrics?.avg_order_value || 0).toLocaleString('en-IN')}
          </div>
        </div>

        <div className="bg-[#1E1E1E] rounded-lg p-2">
          <div className="text-slate-400 text-xs mb-1">Upsell Rate</div>
          <div className="text-blue-400 font-bold text-sm">
            {metrics?.upsell_rate || '0%'}
          </div>
        </div>

        <div className="bg-[#1E1E1E] rounded-lg p-2 col-span-2">
          <div className="text-slate-400 text-xs mb-1">Agent Revenue</div>
          <div className="text-purple-400 font-bold text-sm">
            {metrics?.agent_revenue_pct || '0%'} of total revenue
          </div>
        </div>

      </div>

      {/* Agent Impact */}
      <div className="mt-2 bg-green-900/30 border border-green-700/50 rounded-lg p-2">
        <div className="text-[#D4A017] text-xs font-medium">
          🤖 AI Agent Impact
        </div>
        <div className="text-green-300 text-xs mt-1">
          Revenue generated through AI recommendations
        </div>
      </div>

    </div>
  )
}

export default RevenueWidget
// frontend/src/App.jsx

import { useState, useCallback } from 'react'
import { useSession } from './hooks/useSession'
import { useChat } from './hooks/useChat'
import { useAudit } from './hooks/useAudit'
import ChatWindow from './components/ChatWindow'
import AuditTrail from './components/AuditTrail'
import SpendMeter from './components/SpendMeter'
import CartSummary from './components/CartSummary'

const App = () => {
  const [agentState, setAgentState] = useState({
    cart:           [],
    cartTotal:      0,
    spentSoFar:     0,
    remainingLimit: 100000,
    auditLog:       [],
    paymentStatus:  'pending',
  })

  const [lastOrder, setLastOrder] = useState(null)

  // Session
  const {
    sessionId,
    token,
    spendLimit,
    spentSoFar,
    loading: sessionLoading,
    error: sessionError,
    updateSpend,
  } = useSession()

  // Audit
  const { logs } = useAudit(sessionId)

  // Handle state updates from chat
  const handleStateUpdate = useCallback((newState) => {
    setAgentState(prev => ({ ...prev, ...newState }))
    if (newState.spentSoFar !== undefined) {
      updateSpend(newState.spentSoFar)
    }
    // Track successful payment
    if (newState.paymentStatus === 'success') {
      setLastOrder({
        orderId: newState.orderId,
        amount:  newState.cartTotal,
        cart:    newState.cart,
      })
    }
  }, [updateSpend])

  // Chat
  const {
    messages,
    loading: chatLoading,
    cart,
    cartTotal,
    paymentStatus,
    sendMessage,
  } = useChat(sessionId, handleStateUpdate)

  // Loading state
  if (sessionLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Initializing session...</p>
        </div>
      </div>
    )
  }

  if (sessionError) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{sessionError}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-900 p-4">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-xl">
              🛒
            </div>
            <div>
              <h1 className="text-white font-bold text-lg">
                Razorpay Agentic Checkout
              </h1>
              <p className="text-slate-400 text-xs">
                AI-powered conversational shopping
              </p>
            </div>
          </div>
          <div className="text-xs text-slate-500 font-mono">
            Session: {sessionId?.slice(0, 8)}...
          </div>
        </div>
      </div>

      {/* Main layout */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-4 h-[calc(100vh-120px)]">

        {/* Left sidebar */}
        <div className="lg:col-span-1 flex flex-col gap-4">
          <SpendMeter
            spendLimit={spendLimit}
            spentSoFar={agentState.spentSoFar || spentSoFar}
            remainingLimit={agentState.remainingLimit}
          />
          <CartSummary
            cart={cart}
            cartTotal={cartTotal}
          />
          <div className="flex-1">
            <AuditTrail logs={logs} />
          </div>
        </div>

        {/* Chat window */}
        <div className="lg:col-span-2">
          <ChatWindow
            messages={messages}
            loading={chatLoading}
            onSendMessage={sendMessage}
            paymentStatus={paymentStatus}
            lastOrder={lastOrder}
          />
        </div>
      </div>
    </div>
  )
}

export default App
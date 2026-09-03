// frontend/src/App.jsx

import { useState, useCallback } from 'react'
import { useSession } from './hooks/useSession'
import { useChat } from './hooks/useChat'
import { useAudit } from './hooks/useAudit'
import ChatWindow from './components/ChatWindow'
import AuditTrail from './components/AuditTrail'
import SpendMeter from './components/SpendMeter'
import CartSummary from './components/CartSummary'
import RevenueWidget from './components/RevenueWidget'

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

  const {
    sessionId,
    token,
    spendLimit,
    spentSoFar,
    loading: sessionLoading,
    error: sessionError,
    updateSpend,
  } = useSession()

  const { logs } = useAudit(sessionId)

  const handleStateUpdate = useCallback((newState) => {
    setAgentState(prev => ({ ...prev, ...newState }))
    if (newState.spentSoFar !== undefined) {
      updateSpend(newState.spentSoFar)
    }
    if (newState.paymentStatus === 'success') {
      setLastOrder({
        orderId: newState.orderData?.order_id || '',
        amount:  newState.orderData?.amount || newState.cartTotal || 0,
        cart:    newState.orderData?.items || newState.cart || [],
        time:    new Date().toISOString(), 
      })
    }
  }, [updateSpend])

  const {
    messages,
    loading: chatLoading,
    cart,
    cartTotal,
    paymentStatus,
    sendMessage,
  } = useChat(sessionId, handleStateUpdate)

  if (sessionLoading) {
    return (
      <div className="h-screen bg-[#0A0A0A] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#D4A017] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Initializing session...</p>
        </div>
      </div>
    )
  }

  if (sessionError) {
    return (
      <div className="h-screen bg-[#0A0A0A] flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{sessionError}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-[#D4A017] text-white rounded-lg"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={{height: '100vh', background: '#0A0A0A', padding: '16px', overflow: 'hidden', display: 'flex', flexDirection: 'column'}}>

      {/* Header */}
      <div style={{marginBottom: '16px', flexShrink: 0}}>
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#D4A017] rounded-xl flex items-center justify-center text-xl">
              🛒
            </div>
            <div>
              <h1 className="text-white font-bold text-lg">
                RazorFlow AI
              </h1>
              <p className="text-slate-400 text-xs">
                Agentic Commerce Platform
              </p>
            </div>
          </div>
          <div className="text-xs text-slate-500 font-mono">
            Session: {sessionId?.slice(0, 8)}...
          </div>
        </div>
      </div>

      {/* Main layout */}
      <div
        className="max-w-7xl mx-auto w-full"
        style={{
          flex: 1,
          display: 'grid',
          gridTemplateColumns: '1fr 2fr',
          gap: '16px',
          minHeight: 0,
        }}
      >
        {/* Left sidebar */}
        <div style={{display: 'flex', flexDirection: 'column', gap: '16px', minHeight: 0, overflowY: 'auto', overflowAnchor: 'none'}}>
          <SpendMeter
            spendLimit={spendLimit}
            spentSoFar={agentState.spentSoFar || spentSoFar}
            remainingLimit={agentState.remainingLimit}
          />
          <CartSummary
            cart={cart}
            cartTotal={cartTotal}
          />
          <RevenueWidget />
          <div style={{flex: 1, minHeight: '200px'}}>
            <AuditTrail logs={logs} />
          </div>
        </div>

        {/* Chat window */}
        <div style={{minHeight: 0}}>
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
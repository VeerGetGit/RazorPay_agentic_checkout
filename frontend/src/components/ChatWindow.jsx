// frontend/src/components/ChatWindow.jsx

import { useState, useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble'
import OrderReceipt from './OrderReceipt'

const ChatWindow = ({ messages, loading, onSendMessage, paymentStatus, lastOrder }) => {
  const [input, setInput]     = useState('')
  const bottomRef             = useRef(null)
  const inputRef              = useRef(null)
  const scrollRef             = useRef(null)

  // Auto scroll to bottom only within chat div
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, loading])

  const handleSend = () => {
    if (!input.trim() || loading) return
    onSendMessage(input.trim())
    setInput('')
    inputRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const quickReplies = [
    'show me phones',
    'show me shoes',
    'show me watches',
    'what is my cart?',
  ]

  return (
    <div className="flex flex-col bg-slate-900 rounded-xl border border-slate-700 overflow-hidden" style={{height: '100%'}}>

      {/* Header */}
      <div className="px-4 py-3 bg-slate-800 border-b border-slate-700 flex items-center gap-3 flex-shrink-0">
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
          🤖
        </div>
        <div>
          <h2 className="text-white font-bold text-sm">Razorpay Shopping Agent</h2>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-green-400 text-xs">Online</span>
          </div>
        </div>
      </div>

      {/* Messages — this is the scrollable area */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          padding: '16px',
          minHeight: 0,
        }}
      >
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Payment receipt */}
        {paymentStatus === 'success' && lastOrder && (
          <OrderReceipt
            orderId={lastOrder.orderId}
            amount={lastOrder.amount}
            cart={lastOrder.cart}
            onClose={() => {}}
          />
        )}

        {/* Loading indicator */}
        {loading && (
          <div className="flex justify-start mb-3">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm mr-2">
              🤖
            </div>
            <div className="bg-slate-700 rounded-2xl rounded-tl-none px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Quick replies */}
      <div className="px-4 py-2 flex gap-2 overflow-x-auto border-t border-slate-800 flex-shrink-0">
        {quickReplies.map((reply) => (
          <button
            key={reply}
            onClick={() => onSendMessage(reply)}
            disabled={loading}
            className="flex-shrink-0 px-3 py-1.5 bg-slate-700 text-slate-300 rounded-full text-xs hover:bg-slate-600 transition-colors disabled:opacity-50"
          >
            {reply}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="px-4 py-3 bg-slate-800 border-t border-slate-700 flex gap-2 flex-shrink-0">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message... (e.g. show me phones)"
          disabled={loading}
          className="flex-1 bg-slate-700 text-slate-100 placeholder-slate-500 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="px-4 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  )
}

export default ChatWindow
// frontend/src/hooks/useChat.js

import { useState, useCallback } from 'react'
import { api } from '../api/client'

export const useChat = (sessionId, onStateUpdate) => {
  const [messages, setMessages]     = useState([
    {
      id:      'welcome',
      role:    'agent',
      content: '👋 Welcome! I can help you browse products, add to cart, and make payments. Try saying "show me phones" or "show me shoes"!',
      time:    new Date().toISOString(),
    }
  ])
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState(null)
  const [cart, setCart]             = useState([])
  const [cartTotal, setCartTotal]   = useState(0)
  const [awaitingConsent, setAwaitingConsent] = useState(false)
  const [paymentStatus, setPaymentStatus]     = useState('pending')

  const sendMessage = useCallback(async (text) => {
    if (!sessionId || !text.trim()) return

    // Add user message immediately
    const userMsg = {
      id:      Date.now().toString(),
      role:    'user',
      content: text.trim(),
      time:    new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)
    setError(null)

    try {
      const response = await api.sendMessage(text.trim(), sessionId)
      const data     = response.data

      // Add agent response
      const agentMsg = {
        id:      Date.now().toString() + '_agent',
        role:    'agent',
        content: data.response,
        time:    new Date().toISOString(),
      }
      setMessages(prev => [...prev, agentMsg])

      // Update state
      setCart(data.cart || [])
      setCartTotal(data.cart_total || 0)
      setAwaitingConsent(data.awaiting_consent || false)
      setPaymentStatus(data.payment_status || 'pending')

      // Notify parent of state update
      if (onStateUpdate) {
        onStateUpdate({
          cart:            data.cart || [],
          cartTotal:       data.cart_total || 0,
          spentSoFar:      data.spent_so_far || 0,      // ← check this exists
          remainingLimit:  data.remaining_limit || 0,
          awaitingConsent: data.awaiting_consent || false,
          paymentStatus:   data.payment_status || 'pending',
          auditLog:        data.audit_log || [],
          intent:          data.intent,
          orderData:       data.order_data || null,
        })
      }

    } catch (err) {
      const errMsg = {
        id:      Date.now().toString() + '_error',
        role:    'agent',
        content: '❌ Something went wrong. Please try again.',
        time:    new Date().toISOString(),
        isError: true,
      }
      setMessages(prev => [...prev, errMsg])
      setError(err.message)
      console.error('Chat error:', err)
    } finally {
      setLoading(false)
    }
  }, [sessionId, onStateUpdate])

  const clearChat = () => {
    setMessages([{
      id:      'welcome',
      role:    'agent',
      content: '👋 Welcome back! How can I help you?',
      time:    new Date().toISOString(),
    }])
    setCart([])
    setCartTotal(0)
  }

  return {
    messages,
    loading,
    error,
    cart,
    cartTotal,
    awaitingConsent,
    paymentStatus,
    sendMessage,
    clearChat,
  }
}
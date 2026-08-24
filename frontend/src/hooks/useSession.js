// frontend/src/hooks/useSession.js

import { useState, useEffect } from 'react'
import { api } from '../api/client'

export const useSession = () => {
  const [sessionId, setSessionId]   = useState(null)
  const [token, setToken]           = useState(null)
  const [spendLimit, setSpendLimit] = useState(100000)
  const [spentSoFar, setSpentSoFar] = useState(0)
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)

  useEffect(() => {
    createSession()
  }, [])

  const createSession = async () => {
    try {
      setLoading(true)
      const response = await api.createSession()
      const data     = response.data

      // Store in sessionStorage (cleared on tab close)
      sessionStorage.setItem('session_id',    data.session_id)
      sessionStorage.setItem('session_token', data.token)

      setSessionId(data.session_id)
      setToken(data.token)
      setSpendLimit(data.spend_limit)
      setSpentSoFar(data.spent_so_far)
      setError(null)

    } catch (err) {
      setError('Failed to create session. Please refresh.')
      console.error('Session creation error:', err)
    } finally {
      setLoading(false)
    }
  }

  const updateSpend = (newSpentSoFar) => {
    setSpentSoFar(newSpentSoFar)
  }

  return {
    sessionId,
    token,
    spendLimit,
    spentSoFar,
    loading,
    error,
    updateSpend,
    createSession,
  }
}
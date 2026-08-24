// frontend/src/hooks/useAudit.js

import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client'

export const useAudit = (sessionId) => {
  const [logs, setLogs]       = useState([])
  const [loading, setLoading] = useState(false)
  const intervalRef           = useRef(null)

  useEffect(() => {
    if (!sessionId) return

    // Poll every 2 seconds
    intervalRef.current = setInterval(fetchLogs, 2000)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [sessionId])

  const fetchLogs = async () => {
    if (!sessionId) return
    try {
      const response = await api.getAuditLog(sessionId)
      setLogs(response.data.logs || [])
    } catch (err) {
      console.error('Audit fetch error:', err)
    }
  }

  const addLocalLog = (entry) => {
    setLogs(prev => [...prev, {
      ...entry,
      id:        Date.now().toString(),
      timestamp: new Date().toISOString(),
    }])
  }

  return { logs, loading, addLocalLog }
}
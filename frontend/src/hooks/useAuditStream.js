// frontend/src/hooks/useAuditStream.js

import { useState, useEffect, useRef } from 'react'

export const useAuditStream = (sessionId, token) => {
  const [logs, setLogs]   = useState([])
  const eventSourceRef    = useRef(null)

  useEffect(() => {
    if (!sessionId || !token) return

    // Connect to SSE stream
    const url = `https://razorpay-agentic-checkout.onrender.com/api/stream/${sessionId}`

    const connect = () => {
      const es = new EventSource(url)
      eventSourceRef.current = es

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.event === 'stream_ended') {
            es.close()
            return
          }
          if (data.error) return

          setLogs(prev => {
            // Avoid duplicates
            const exists = prev.find(l => l.id === data.id)
            if (exists) return prev
            return [...prev, data]
          })
        } catch (err) {
          console.error('SSE parse error:', err)
        }
      }

      es.onerror = () => {
        es.close()
        // Reconnect after 3 seconds
        setTimeout(connect, 3000)
      }
    }

    connect()

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [sessionId, token])

  return { logs }
}
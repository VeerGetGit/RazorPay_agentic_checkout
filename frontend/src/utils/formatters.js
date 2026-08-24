// frontend/src/utils/formatters.js

// Format amount in Indian Rupees
export const formatRupees = (amount) => {
  if (!amount && amount !== 0) return '₹0'
  return new Intl.NumberFormat('en-IN', {
    style:    'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

// Format timestamp
export const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-IN', {
    hour:   '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

// Format payment status
export const formatStatus = (status) => {
  const map = {
    pending:   { label: 'Pending',   color: 'text-yellow-400' },
    success:   { label: 'Success',   color: 'text-green-400'  },
    failed:    { label: 'Failed',    color: 'text-red-400'    },
    cancelled: { label: 'Cancelled', color: 'text-gray-400'   },
  }
  return map[status] || { label: status, color: 'text-gray-400' }
}

// Format audit status
export const formatAuditStatus = (status) => {
  const map = {
    success: 'bg-green-900 text-green-300',
    blocked: 'bg-red-900 text-red-300',
    failed:  'bg-yellow-900 text-yellow-300',
    pending: 'bg-blue-900 text-blue-300',
  }
  return map[status] || 'bg-gray-800 text-gray-300'
}

// Truncate text
export const truncate = (text, length = 50) => {
  if (!text) return ''
  return text.length > length ? text.slice(0, length) + '...' : text
}
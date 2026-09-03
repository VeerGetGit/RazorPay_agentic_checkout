// frontend/src/components/MessageBubble.jsx

import { formatTime } from '../utils/formatters'

const MessageBubble = ({ message }) => {
  const isUser  = message.role === 'user'
  const isError = message.isError

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      {/* Agent avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-[#D4A017] flex items-center justify-center text-sm mr-2 flex-shrink-0 mt-1">
          🤖
        </div>
      )}

      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? 'bg-[#D4A017] text-white rounded-tr-none'
              : isError
              ? 'bg-red-900 text-red-200 border border-red-700 rounded-tl-none'
              : 'bg-[#1E1E1E] text-slate-100 rounded-tl-none'
          }`}
        >
          {message.content}
        </div>
        <span className="text-slate-500 text-xs mt-1 px-1">
          {formatTime(message.time)}
        </span>
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center text-sm ml-2 flex-shrink-0 mt-1">
          👤
        </div>
      )}
    </div>
  )
}

export default MessageBubble
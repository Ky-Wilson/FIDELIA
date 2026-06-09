import ToolBadge from './ToolBadge'
import ToolResult from './ToolResult'

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center text-white text-sm font-bold shrink-0">
          F
        </div>
      )}
      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        {message.toolUsed && <ToolBadge tool={message.toolUsed} />}
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'bg-orange-500 text-white rounded-tr-sm'
            : 'bg-white/8 text-gray-100 rounded-tl-sm'
        }`}>
          {message.content}
        </div>
        {message.toolData && <ToolResult tool={message.toolUsed} data={message.toolData} />}
        <span className="text-xs text-gray-600">{message.time}</span>
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-white text-sm shrink-0">
          U
        </div>
      )}
    </div>
  )
}
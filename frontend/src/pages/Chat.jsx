import { useState, useRef, useEffect } from 'react'
import ChatMessage from '../components/ChatMessage'
import { sendMessage } from '../api/mcp'

const SUGGESTIONS = [
  "Convertis 500 000 FCFA en euros",
  "Calcule la TVA sur 500 000 FCFA",
  "Quelles sont les échéances fiscales ?",
  "Calcule les cotisations CNPS pour un salaire de 300 000 FCFA",
  "Que dit l'article sur la DSF ?",
]

export default function Chat() {
  const [messages, setMessages] = useState([{
    id: 1,
    role: 'assistant',
    content: "Bonjour ! Je suis FIDELIA, votre assistant fiscal pour la Côte d'Ivoire. Je peux vérifier des NCC, calculer la TVA, les cotisations CNPS, et vous renseigner sur le Code Général des Impôts. Comment puis-je vous aider ?",
    time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
  }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const nextIdRef = useRef(2)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (text) => {
    const userText = text || input.trim()
    if (!userText || loading) return

    const userMsg = {
      id: nextIdRef.current++,
      role: 'user',
      content: userText,
      time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      // Historique complet au format OpenAI (user + assistant uniquement)
      const history = [...messages, userMsg]
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .map(m => ({ role: m.role, content: m.content }))

      const response = await sendMessage(history)

      setMessages(prev => [...prev, {
        id: nextIdRef.current++,
        role: 'assistant',
        content: response.text,
        toolUsed: response.tool_used,
        toolData: response.tool_data,
        time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
      }])
    } catch (err) {
      console.error(err)
      const content = err.status === 502
        ? "Le service IA n'est pas encore configuré : aucune clé API OpenAI valide n'est renseignée côté serveur. Veuillez entrer une clé API (OPENAI_API_KEY) dans la configuration du backend pour activer le chat."
        : "Erreur de connexion au serveur. Vérifiez que le backend tourne sur le port 8000."
      setMessages(prev => [...prev, {
        id: nextIdRef.current++,
        role: 'assistant',
        content,
        time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto">

      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-white/10">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center text-white font-bold shrink-0">
          F
        </div>
        <div>
          <div className="font-semibold text-white">FIDELIA</div>
          <div className="text-xs text-gray-400">Assistant fiscal CI · FNE · DGI · CNPS</div>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-xs text-gray-400">En ligne</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map(msg => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center text-white text-sm font-bold shrink-0">
              F
            </div>
            <div className="bg-white/10 rounded-2xl rounded-tl-sm px-4 py-3 flex gap-1 items-center">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Suggestions — affichées seulement au départ */}
      {messages.length <= 1 && (
        <div className="px-6 pb-3 flex gap-2 flex-wrap">
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              onClick={() => handleSend(s)}
              className="text-xs px-3 py-1.5 rounded-full border border-white/15 text-gray-300 hover:bg-white/10 transition-colors cursor-pointer"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Zone de saisie */}
      <div className="px-6 py-4 border-t border-white/10">
        <div className="flex gap-3 items-end bg-white/10 rounded-2xl px-4 py-3">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            placeholder="Posez votre question fiscale... (FR / EN)"
            className="flex-1 bg-transparent text-sm text-gray-100 placeholder-gray-500 resize-none outline-none max-h-32"
            rows={1}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            className="w-8 h-8 rounded-xl bg-orange-500 hover:bg-orange-400 disabled:opacity-30 flex items-center justify-center transition-colors shrink-0 cursor-pointer"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
              <path d="M2 21l21-9L2 3v7l15 2-15 2v7z" />
            </svg>
          </button>
        </div>
        <p className="text-center text-xs text-gray-600 mt-2">
          FIDELIA · Plateforme eGov Côte d'Ivoire
        </p>
      </div>

    </div>
  )
}
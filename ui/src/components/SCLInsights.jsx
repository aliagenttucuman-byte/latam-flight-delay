import { useState, useRef, useEffect } from 'react'

const SUGGESTED_QUESTIONS = [
  "¿Por qué se retrasan los vuelos?",
  "¿Cuál es el peor mes para volar?",
  "¿Los vuelos internacionales tienen más retrasos?",
  "¿Cuál es la mejor aerolinea para volar?"
]

export default function SCLInsights({ apiUrl }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showSuggestions, setShowSuggestions] = useState(true)
  const chatEndRef = useRef(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (question) => {
    if (!question.trim() || loading) return

    const userMessage = { role: 'user', content: question }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError(null)
    setShowSuggestions(false)

    try {
      const response = await fetch(`${apiUrl}/ai-insights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      })

      if (!response.ok) throw new Error('Error fetching insight')
      const data = await response.json()

      const assistantMessage = { role: 'assistant', content: data.insight }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      setError('No pude obtener la respuesta. ¿Podés intentar de nuevo?')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage(input)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 lg:p-4 border-b border-[#2a2a2a] bg-[#0f0f0f] shrink-0">
        <h2 className="text-base lg:text-lg font-semibold text-white flex items-center gap-2">
          <span className="text-lg lg:text-xl">💬</span>
          SCL Insights
        </h2>
      </div>

      {showSuggestions && (
        <div className="p-3 lg:p-4 border-b border-[#2a2a2a] bg-[#141414] shrink-0">
          <p className="text-xs lg:text-sm text-gray-400 mb-2 lg:mb-3">
            Preguntame sobre los vuelos del aeropuerto SCL:
          </p>
          <div className="flex flex-wrap gap-1.5 lg:gap-2">
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => sendMessage(q)}
                className="text-xs lg:text-sm px-2.5 lg:px-4 py-1.5 lg:py-2 rounded-full bg-[#1a1a1a] border border-[#2a2a2a]
                           text-gray-300 hover:bg-[#CC0000] hover:text-white hover:border-[#CC0000]
                           transition-all whitespace-nowrap"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-3 lg:p-4 space-y-3 lg:space-y-4 bg-[#0f0f0f]">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] lg:max-w-[85%] rounded-2xl px-3 lg:px-4 py-2 lg:py-3 ${
                msg.role === 'user'
                  ? 'bg-[#CC0000] text-white rounded-br-sm'
                  : 'bg-[#1a1a1a] text-gray-200 border border-[#2a2a2a] rounded-bl-sm'
              }`}
            >
              <p className="whitespace-pre-wrap text-xs lg:text-sm leading-relaxed">{msg.content}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl rounded-bl-sm px-3 lg:px-4 py-2 lg:py-3">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 lg:w-2 lg:h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-1.5 h-1.5 lg:w-2 lg:h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-1.5 h-1.5 lg:w-2 lg:h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="flex justify-start">
            <div className="bg-red-900/20 border border-red-800/50 text-red-300 rounded-2xl rounded-bl-sm px-3 lg:px-4 py-2 lg:py-3">
              <p className="text-xs lg:text-sm">{error}</p>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="p-3 lg:p-4 border-t border-[#2a2a2a] bg-[#0f0f0f] shrink-0">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Escribe tu pregunta..."
            disabled={loading}
            className="flex-1 px-3 lg:px-4 py-2.5 lg:py-3 rounded-xl bg-[#1a1a1a] border border-[#2a2a2a]
                       text-white text-sm placeholder-gray-500 focus:outline-none focus:border-[#CC0000]
                       transition-all"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 lg:px-6 py-2.5 lg:py-3 bg-[#CC0000] text-white font-semibold rounded-xl
                       hover:bg-red-700 active:scale-[0.98] transition-all
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-4 h-4 lg:w-5 lg:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  )
}
import { useState } from 'react'

const SUGGESTED_QUESTIONS = [
  "¿Por qué se retrasan los vuelos?",
  "¿Cuál es la aerolinea con más retrasos?",
  "¿Cuál es el peor mes para volar?",
  "¿Los vuelos internacionales tienen más retrasos que los nacionales?",
  "¿Qué combinación de aerolinea y mes es más problemática?",
  "¿Cuántos vuelos se analizaron?",
  "¿Cuál es la tasa de retrasos general?",
  "¿Cuál es el mejor mes para volar?"
]

export default function AIInsights({ apiUrl }) {
  const [question, setQuestion] = useState('')
  const [insight, setInsight] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const askQuestion = async (q) => {
    setQuestion(q)
    setLoading(true)
    setError(null)
    setInsight(null)

    try {
      const response = await fetch(`${apiUrl}/ai-insights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q })
      })

      if (!response.ok) throw new Error('Error fetching insight')
      const data = await response.json()
      setInsight(data.insight)
    } catch (err) {
      setError('No se pudo obtener el insight. Verifica que la API esté activa.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border-t-4 border-[#CC0000]">
      <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">
        AI Insights
      </h2>

      <div className="mb-4">
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
          Preguntas sugeridas:
        </p>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => askQuestion(q)}
              className="text-xs px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-700
                         text-gray-700 dark:text-gray-300 hover:bg-[#CC0000] hover:text-white
                         transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#CC0000]"></div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 p-4 rounded-lg">
          {error}
        </div>
      )}

      {insight && (
        <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg">
          <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
            {insight}
          </p>
        </div>
      )}
    </div>
  )
}
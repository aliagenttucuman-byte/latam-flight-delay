import { useState } from 'react'

const AIRLINES = [
  "American Airlines", "Air France", "Aerolineas Argentinas", "Avianca",
  "British Airways", "Copa Air", "Delta Air", "Grupo LATAM", "Iberia",
  "JetSmart", "Korean Air", "LATAM", "Latin American Wings",
  "Lloyd Aereo Boliviano", "Sky Airline", "United Airlines"
]

const TIPO_VUELO = [
  { value: 'I', label: 'Internacional' },
  { value: 'N', label: 'Nacional' }
]

export default function FlightForm({ onPredict }) {
  const [opera, setOpera] = useState('LATAM')
  const [tipovuelo, setTipovuelo] = useState('I')
  const [mes, setMes] = useState(new Date().getMonth() + 1)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    await onPredict({ OPERA: opera, TIPOVUELO: tipovuelo, MES: mes })
    setLoading(false)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 lg:space-y-5">
      <h2 className="text-base lg:text-lg font-semibold text-white mb-3 lg:mb-4 flex items-center gap-2">
        <span className="w-0.5 lg:w-1 h-5 lg:h-6 bg-[#CC0000] rounded-full"></span>
        Predecir Retraso
      </h2>

      <div>
        <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5 lg:mb-2">
          Aerolínea
        </label>
        <select
          value={opera}
          onChange={(e) => setOpera(e.target.value)}
          className="w-full px-3 lg:px-4 py-2.5 lg:py-3 rounded-xl bg-[#0f0f0f] border border-[#2a2a2a]
                     text-white text-sm focus:outline-none focus:border-[#CC0000] focus:ring-1 focus:ring-[#CC0000]
                     transition-all cursor-pointer"
        >
          {AIRLINES.map((airline) => (
            <option key={airline} value={airline}>{airline}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5 lg:mb-2">
          Tipo de Vuelo
        </label>
        <div className="flex gap-3 lg:gap-4">
          {TIPO_VUELO.map((tipo) => (
            <label key={tipo.value} className="flex items-center gap-2 cursor-pointer group">
              <div className={`w-4 h-4 lg:w-5 lg:h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                tipovuelo === tipo.value
                  ? 'border-[#CC0000] bg-[#CC0000]'
                  : 'border-[#3a3a3a] group-hover:border-[#5a5a5a]'
              }`}>
                {tipovuelo === tipo.value && (
                  <div className="w-1.5 h-1.5 lg:w-2 lg:h-2 rounded-full bg-white"></div>
                )}
              </div>
              <input
                type="radio"
                name="tipovuelo"
                value={tipo.value}
                checked={tipovuelo === tipo.value}
                onChange={(e) => setTipovuelo(e.target.value)}
                className="hidden"
              />
              <span className="text-gray-300 text-sm group-hover:text-white transition-colors">{tipo.label}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5 lg:mb-2">
          Mes
        </label>
        <select
          value={mes}
          onChange={(e) => setMes(Number(e.target.value))}
          className="w-full px-3 lg:px-4 py-2.5 lg:py-3 rounded-xl bg-[#0f0f0f] border border-[#2a2a2a]
                     text-white text-sm focus:outline-none focus:border-[#CC0000] focus:ring-1 focus:ring-[#CC0000]
                     transition-all cursor-pointer"
        >
          {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
            <option key={m} value={m}>
              {new Date(2024, m - 1).toLocaleString('es-ES', { month: 'long' })}
            </option>
          ))}
        </select>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-[#CC0000] text-white font-semibold py-3 lg:py-4 px-6 rounded-xl
                   hover:bg-red-700 active:scale-[0.98] transition-all text-sm lg:text-base
                   disabled:opacity-50 disabled:cursor-not-allowed
                   shadow-lg shadow-red-900/20"
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4 lg:h-5 lg:w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            Prediciendo...
          </span>
        ) : 'Predecir Retraso'}
      </button>
    </form>
  )
}
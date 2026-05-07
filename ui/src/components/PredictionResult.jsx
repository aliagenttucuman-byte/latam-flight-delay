export default function PredictionResult({ prediction, flight }) {
  if (prediction === null) return null

  const isDelayed = prediction === 1

  return (
    <div className={`rounded-2xl p-6 transition-all ${
      isDelayed
        ? 'bg-gradient-to-br from-red-900/30 to-red-950/50 border border-red-800/50'
        : 'bg-gradient-to-br from-green-900/30 to-green-950/50 border border-green-800/50'
    }`}>
      <div className="text-center">
        <div className={`inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4 ${
          isDelayed ? 'bg-red-900/50' : 'bg-green-900/50'
        }`}>
          {isDelayed ? (
            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          ) : (
            <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          )}
        </div>

        <h3 className={`text-2xl font-bold mb-2 ${
          isDelayed ? 'text-red-300' : 'text-green-300'
        }`}>
          {isDelayed ? '¡Vuelo Retrasado!' : 'Sin Retraso'}
        </h3>

        <p className="text-gray-400 text-sm">
          {flight.OPERA} · {flight.TIPOVUELO === 'I' ? 'Int.' : 'Nac.'} · {
            new Date(2024, flight.MES - 1).toLocaleString('es-ES', { month: 'long' })
          }
        </p>
      </div>
    </div>
  )
}
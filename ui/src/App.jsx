import { useState, useEffect } from 'react'
import Header from './components/Header'
import FlightForm from './components/FlightForm'
import PredictionResult from './components/PredictionResult'
import SCLInsights from './components/SCLInsights'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [prediction, setPrediction] = useState(null)
  const [currentFlight, setCurrentFlight] = useState(null)
  const [apiStatus, setApiStatus] = useState('checking')

  useEffect(() => {
    checkApiHealth()
  }, [])

  const checkApiHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/health`)
      if (response.ok) {
        setApiStatus('online')
      } else {
        setApiStatus('offline')
      }
    } catch {
      setApiStatus('offline')
    }
  }

  const handlePredict = async (flight) => {
    try {
      const response = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flights: [flight] })
      })

      if (!response.ok) throw new Error('Prediction failed')
      const data = await response.json()
      setCurrentFlight(flight)
      setPrediction(data.predict[0])
    } catch (err) {
      console.error('Prediction error:', err)
      setPrediction(null)
      setCurrentFlight(null)
    }
  }

  return (
    <div className="min-h-screen bg-[#0f0f0f]">
      <Header />

      <main className="container mx-auto px-3 py-4 max-w-6xl">
        <div className="mb-4 flex items-center justify-end">
          <a
            href={`${API_URL}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-[#CC0000] hover:text-red-400 transition-colors"
          >
            API Docs
          </a>
        </div>

        <div className="grid lg:grid-cols-2 gap-4 lg:gap-6">
          <div className="space-y-4 lg:space-y-6 order-1 lg:order-1">
            <div className="bg-[#1a1a1a] rounded-2xl p-4 lg:p-6 border border-[#2a2a2a]">
              <FlightForm onPredict={handlePredict} />
            </div>
            <PredictionResult prediction={prediction} flight={currentFlight} />
          </div>

          <div className="bg-[#1a1a1a] rounded-2xl border border-[#2a2a2a] overflow-hidden order-2 lg:order-2 h-[420px] lg:h-[520px]">
            <SCLInsights apiUrl={API_URL} />
          </div>
        </div>
      </main>

      <footer className="border-t border-[#2a2a2a] py-4 mt-4">
        <div className="container mx-auto px-4 text-center text-xs text-gray-500">
          Flight Delay Predictor · SCL Airport
        </div>
      </footer>
    </div>
  )
}

export default App
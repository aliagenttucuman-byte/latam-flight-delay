import latamLogo from '../assets/latam-logo.png'

export default function Header() {
  return (
    <header className="bg-[#0f0f0f] border-b border-[#2a2a2a] py-4 sticky top-0 z-50 backdrop-blur-lg bg-opacity-90">
      <div className="container mx-auto px-4 flex items-center justify-between max-w-6xl">
        <div className="flex items-center gap-3">
          <img src={latamLogo} alt="LATAM" className="h-10" />
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">
              Flight Delay <span className="text-[#CC0000]">Predictor</span>
            </h1>
            <p className="text-xs text-gray-500 uppercase tracking-widest">
              SCL Airport · AI Powered
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
          <span className="text-sm text-gray-400">Live</span>
        </div>
      </div>
    </header>
  )
}
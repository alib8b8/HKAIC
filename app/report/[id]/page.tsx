import Link from "next/link";

export default function Report({ params }: { params: { id: string } }) {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-gray-900/80 backdrop-blur-xl border-b border-gray-800">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center">
                <span className="text-white font-bold">H</span>
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                HKAIC
              </span>
            </Link>
            <div className="flex gap-8 items-center">
              <Link href="/" className="text-gray-400 hover:text-white transition">
                Home
              </Link>
              <Link href="/dashboard" className="text-gray-400 hover:text-white transition">
                Dashboard
              </Link>
              <Link href="/upload" className="text-gray-400 hover:text-white transition">
                Upload
              </Link>
            </div>
          </div>
        </div>
      </nav>
      
      <main className="pt-32 pb-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <div>
              <Link href="/dashboard" className="text-gray-400 hover:text-white flex items-center gap-2 mb-4">
                <span>←</span>
                <span>Back</span>
              </Link>
              <h1 className="text-3xl md:text-4xl font-bold mb-2">Flight Report</h1>
              <p className="text-gray-400">Flight {params.id} - Analysis Results</p>
            </div>
            <div className="flex gap-3">
              <button className="px-4 py-2 rounded-xl bg-gray-800 text-white hover:bg-gray-700 transition flex items-center gap-2">
                <span>📤</span>
                <span>Export</span>
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div className="p-8 rounded-2xl bg-gray-900/50 border border-gray-800 text-center">
              <div className="relative inline-block">
                <div className="w-32 h-32 rounded-full bg-gray-800 flex items-center justify-center">
                  <span className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                    87
                  </span>
                </div>
                <div className="absolute inset-0 rounded-full border-4 border-cyan-400/30"></div>
              </div>
              <div className="mt-4 text-gray-400">Overall Score</div>
              
              <div className="grid grid-cols-2 gap-4 mt-8">
                <div className="p-4 rounded-xl bg-gray-900/50 border border-gray-800">
                  <div className="text-cyan-400 text-sm font-medium mb-2">Efficiency</div>
                  <div className="text-2xl font-bold">92%</div>
                </div>
                <div className="p-4 rounded-xl bg-gray-900/50 border border-gray-800">
                  <div className="text-green-400 text-sm font-medium mb-2">Stability</div>
                  <div className="text-2xl font-bold">81%</div>
                </div>
              </div>
            </div>
            
            <div className="lg:col-span-2 p-6 rounded-2xl bg-gray-900/50 border border-gray-800">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold">Flight Analysis</h2>
                <span className="px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-sm">
                  Low Risk
                </span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-4 rounded-xl bg-gray-900/50 border border-gray-800">
                  <div className="text-gray-400 text-sm mb-3">Pitch PID</div>
                  <div className="font-mono text-sm space-y-1">
                    <div>P: 4.2</div>
                    <div>I: 0.8</div>
                    <div>D: 2.1</div>
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-gray-900/50 border border-gray-800">
                  <div className="text-gray-400 text-sm mb-3">Roll PID</div>
                  <div className="font-mono text-sm space-y-1">
                    <div>P: 4.1</div>
                    <div>I: 0.8</div>
                    <div>D: 2.0</div>
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-gray-900/50 border border-gray-800">
                  <div className="text-gray-400 text-sm mb-3">Yaw PID</div>
                  <div className="font-mono text-sm space-y-1">
                    <div>P: 3.8</div>
                    <div>I: 0.5</div>
                    <div>D: 1.8</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800 mb-8">
            <h2 className="text-xl font-semibold mb-6">AI Recommendations</h2>
            <div className="space-y-6">
              <div className="p-6 rounded-xl bg-gray-900/50 border border-red-500/30">
                <div className="flex items-start justify-between gap-6">
                  <div>
                    <div className="flex items-center gap-3 mb-3">
                      <span className="px-3 py-1 rounded-full bg-red-500/20 text-red-400 text-sm">High Priority</span>
                      <h3 className="font-semibold">Increase D Gain for Pitch</h3>
                    </div>
                    <p className="text-gray-400 mb-4">
                      Minor oscillations detected. Increase D gain by 0.15 for better damping.
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="p-6 rounded-xl bg-gray-900/50 border border-yellow-500/30">
                <div className="flex items-start justify-between gap-6">
                  <div>
                    <div className="flex items-center gap-3 mb-3">
                      <span className="px-3 py-1 rounded-full bg-yellow-500/20 text-yellow-400 text-sm">Medium Priority</span>
                      <h3 className="font-semibold">Add Low-Pass Filter</h3>
                    </div>
                    <p className="text-gray-400">
                      Consider enabling gyro low-pass filter at 100Hz to reduce vibration noise.
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="p-6 rounded-xl bg-gray-900/50 border border-green-500/30">
                <div className="flex items-start justify-between gap-6">
                  <div>
                    <div className="flex items-center gap-3 mb-3">
                      <span className="px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-sm">Low Priority</span>
                      <h3 className="font-semibold">Balance Props</h3>
                    </div>
                    <p className="text-gray-400">
                      Minor vibration spikes detected. Check propeller balance for smoother flight.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/upload">
              <button className="px-6 py-3 rounded-xl bg-gray-800 text-white font-medium hover:bg-gray-700 transition flex items-center gap-2">
                <span>📁</span>
                <span>Upload Another Log</span>
              </button>
            </Link>
            <button className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-400 to-purple-500 text-white font-medium hover:opacity-90 transition flex items-center gap-2">
              <span>⚡</span>
              <span>Apply Recommendations</span>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

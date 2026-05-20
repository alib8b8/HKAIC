import Link from "next/link";

export default function Upload() {
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
              <Link href="/upload" className="text-white font-medium">
                Upload
              </Link>
            </div>
          </div>
        </div>
      </nav>
      
      <main className="pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10">
            <h1 className="text-3xl md:text-4xl font-bold mb-2">Upload Flight Log</h1>
            <p className="text-gray-400">Get AI-powered insights from your flight data</p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 p-6 rounded-2xl bg-gray-900/50 border border-gray-800">
              <div className="text-center p-12 rounded-xl border-2 border-dashed border-gray-700 hover:border-cyan-400 transition">
                <div className="w-20 h-20 mx-auto mb-6 rounded-xl bg-gradient-to-br from-cyan-400/20 to-purple-500/20 flex items-center justify-center">
                  <div className="text-cyan-400 text-4xl">📁</div>
                </div>
                <h3 className="text-xl font-semibold mb-3">Drop your flight log here</h3>
                <p className="text-gray-400 mb-6">Supports .log, .bin, .ulg, .txt files</p>
                <button className="px-6 py-3 rounded-xl bg-gray-800 text-white hover:bg-gray-700 transition">
                  Browse Files
                </button>
              </div>
              
              <div className="mt-8">
                <h4 className="text-sm font-medium text-gray-400 mb-4">Flight Controller Format</h4>
                <div className="flex flex-wrap gap-3">
                  {['DJI', 'PX4', 'Betaflight', 'Ardupilot', 'INAV'].map((format) => (
                    <button key={format} className="px-4 py-2 rounded-xl bg-gray-800 text-white border border-gray-700 hover:border-cyan-400 transition">
                      {format}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className="mt-8 flex gap-4">
                <button className="flex-1 px-6 py-3 rounded-xl bg-gray-800 text-white hover:bg-gray-700 transition">
                  Cancel
                </button>
                <button className="flex-1 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-400 to-purple-500 text-white font-medium hover:opacity-90 transition">
                  Analyze Log
                </button>
              </div>
            </div>
            
            <div className="space-y-6">
              <div className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800">
                <h3 className="text-lg font-semibold mb-4">Supported Formats</h3>
                <div className="space-y-2 text-sm text-gray-400">
                  <div className="flex justify-between p-3 rounded-lg bg-gray-900/50 border border-gray-800">
                    <span>DJI Flight Logs</span>
                    <span className="text-gray-500">.log, .txt</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-lg bg-gray-900/50 border border-gray-800">
                    <span>PX4</span>
                    <span className="text-gray-500">.ulg, .log</span>
                  </div>
                  <div className="flex justify-between p-3 rounded-lg bg-gray-900/50 border border-gray-800">
                    <span>Betaflight</span>
                    <span className="text-gray-500">.bin, .log</span>
                  </div>
                </div>
              </div>
              
              <div className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800">
                <h3 className="text-lg font-semibold mb-4">How it works</h3>
                <div className="space-y-4">
                  <div className="flex gap-3">
                    <div className="w-6 h-6 rounded-full bg-cyan-400/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-cyan-400">1</span>
                    </div>
                    <div>
                      <div className="font-medium">Upload</div>
                      <div className="text-gray-400 text-sm">Upload your flight log file</div>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="w-6 h-6 rounded-full bg-cyan-400/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-cyan-400">2</span>
                    </div>
                    <div>
                      <div className="font-medium">Analyze</div>
                      <div className="text-gray-400 text-sm">AI analyzes thousands of parameters</div>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="w-6 h-6 rounded-full bg-cyan-400/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-cyan-400">3</span>
                    </div>
                    <div>
                      <div className="font-medium">Optimize</div>
                      <div className="text-gray-400 text-sm">Get actionable recommendations</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

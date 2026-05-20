import Link from "next/link";

export default function Dashboard() {
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
              <Link href="/dashboard" className="text-white font-medium">
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
          <h1 className="text-3xl md:text-4xl font-bold mb-2">Dashboard</h1>
          <p className="text-gray-400 mb-10">Welcome back! Here's your flight overview.</p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800">
              <div className="text-gray-400 text-sm font-medium mb-3">Total Flights</div>
              <div className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">147</div>
              <div className="text-green-400 text-sm mt-2 flex items-center gap-1">
                <span>↑</span>
                <span>+12% from last month</span>
              </div>
            </div>
            <div className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800">
              <div className="text-gray-400 text-sm font-medium mb-3">Average Score</div>
              <div className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">82.3</div>
              <div className="text-green-400 text-sm mt-2 flex items-center gap-1">
                <span>↑</span>
                <span>+4.2 points</span>
              </div>
            </div>
            <div className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800">
              <div className="text-gray-400 text-sm font-medium mb-3">Analyses Completed</div>
              <div className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">289</div>
            </div>
            <div className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800">
              <div className="text-gray-400 text-sm font-medium mb-3">Time Saved</div>
              <div className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">18h</div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 p-6 rounded-2xl bg-gray-900/50 border border-gray-800">
              <h2 className="text-xl font-semibold mb-6">Recent Flights</h2>
              <div className="space-y-4">
                {[1, 2, 3].map((flight) => (
                  <div key={flight} className="p-4 rounded-xl bg-gray-900/50 border border-gray-800">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium">Flight {flight}</div>
                        <div className="text-gray-400 text-sm">Uploaded {flight * 2} hours ago</div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-sm">
                          {80 + flight * 2} pts
                        </span>
                        <Link href={`/report/${flight}`}>
                          <button className="px-4 py-2 rounded-xl bg-gray-800 text-sm hover:bg-gray-700 transition">
                            View
                          </button>
                        </Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800">
              <h2 className="text-xl font-semibold mb-6">Quick Actions</h2>
              <div className="space-y-3">
                <Link href="/upload">
                  <button className="w-full px-4 py-3 rounded-xl bg-gradient-to-r from-cyan-400 to-purple-500 text-white font-medium hover:opacity-90 transition">
                    Upload New Log
                  </button>
                </Link>
                <button className="w-full px-4 py-3 rounded-xl bg-gray-800 text-white font-medium hover:bg-gray-700 transition">
                  View All Reports
                </button>
                <button className="w-full px-4 py-3 rounded-xl bg-gray-800 text-white font-medium hover:bg-gray-700 transition">
                  Check Tips
                </button>
              </div>
              
              <div className="mt-8 p-4 rounded-xl bg-gray-900/50 border border-gray-800">
                <h3 className="font-medium mb-2">Pro Tip</h3>
                <p className="text-gray-400 text-sm">
                  Try uploading multiple logs to see trends over time.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

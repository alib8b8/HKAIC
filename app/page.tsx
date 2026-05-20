import Link from "next/link";

export default function Home() {
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
            <div className="hidden md:flex gap-8 items-center">
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
            <div className="flex items-center gap-3">
              <button className="px-4 py-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800 transition">
                Sign In
              </button>
              <button className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-400 to-purple-500 text-white font-medium hover:opacity-90 transition">
                Get Started
              </button>
            </div>
          </div>
        </div>
      </nav>
      
      <main>
        {/* Hero Section */}
        <section className="pt-32 pb-20 px-4">
          <div className="max-w-6xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gray-900/50 border border-gray-800 mb-8">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
              <span className="text-sm text-gray-400">AI Flight Intelligence v2.0</span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              <span className="block">Intelligent</span>
              <span className="bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                Drone Flight Analysis
              </span>
            </h1>
            
            <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
              HKAIC transforms raw flight logs into actionable insights. 
              AI-powered tuning, risk assessment, and optimization recommendations.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <button className="text-lg px-8 py-6 rounded-xl bg-gradient-to-r from-cyan-400 to-purple-500 text-white font-medium hover:opacity-90 transition">
                Start Free Analysis
              </button>
              <button className="text-lg px-8 py-6 rounded-xl bg-gray-800 text-white border border-gray-700 hover:border-cyan-400 transition">
                Watch Demo
              </button>
            </div>
            
            <div className="grid grid-cols-3 gap-8 max-w-2xl mx-auto">
              {[
                { label: 'Flights Analyzed', value: '50K+' },
                { label: 'Avg. Score Boost', value: '32%' },
                { label: 'Response Time', value: '< 30s' },
              ].map((stat, idx) => (
                <div key={idx} className="text-center">
                  <div className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                    {stat.value}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>
        
        {/* Features Section */}
        <section className="py-20 px-4 bg-gray-900/30">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-4xl font-bold mb-4">
                Powerful <span className="bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">Features</span>
              </h2>
              <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                Everything you need to elevate your drone flying experience
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                { icon: '🧠', title: 'AI-Powered Analysis', description: 'Deep learning algorithms analyze thousands of flight parameters in seconds.' },
                { icon: '📊', title: 'Flight Optimization', description: 'Automatically tune PID parameters for maximum performance and stability.' },
                { icon: '🛡️', title: 'Risk Assessment', description: 'Proactive safety monitoring alerts you to potential issues before they happen.' },
                { icon: '⚡', title: 'Instant Insights', description: 'Real-time processing delivers actionable recommendations in under 30 seconds.' },
                { icon: '🧭', title: 'Multi-Format Support', description: 'Works with DJI, PX4, Betaflight, and all major flight controllers.' },
                { icon: '⚙️', title: 'Copilot Mode', description: 'AI assistant guides you through troubleshooting and optimization.' },
              ].map((feature, idx) => (
                <div key={idx} className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800 hover:border-cyan-400/30 transition">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-400/20 to-purple-500/20 flex items-center justify-center mb-4 text-2xl">
                    {feature.icon}
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-gray-400">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
        
        {/* CTA Section */}
        <section className="py-20 px-4">
          <div className="max-w-4xl mx-auto">
            <div className="p-12 bg-gray-900/50 border border-gray-800 rounded-3xl text-center">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Ready to <span className="bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">Elevate</span> Your Drone Flying?
              </h2>
              <p className="text-gray-400 text-lg mb-8 max-w-xl mx-auto">
                Join thousands of pilots who are already optimizing their flights with HKAIC. 
                Get started for free, no credit card required.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
                <button className="text-lg px-8 py-6 rounded-xl bg-gradient-to-r from-cyan-400 to-purple-500 text-white font-medium hover:opacity-90 transition">
                  Get Started Free
                </button>
              </div>
              
              <div className="flex flex-wrap justify-center gap-8 text-sm text-gray-400">
                {['Free tier', 'No credit card', 'Cancel anytime'].map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <span className="text-cyan-400">✓</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </main>
      
      {/* Footer */}
      <footer className="border-t border-gray-800 bg-gray-900/50 py-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center">
                  <span className="text-white font-bold text-sm">H</span>
                </div>
                <span className="text-lg font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                  HKAIC
                </span>
              </div>
              <p className="text-gray-400 text-sm mb-4 max-w-sm">
                AI-powered flight intelligence platform for drone enthusiasts and professionals.
              </p>
            </div>
            
            <div>
              <h4 className="text-white font-medium mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition">Features</a></li>
                <li><a href="#" className="hover:text-white transition">Dashboard</a></li>
                <li><a href="#" className="hover:text-white transition">Pricing</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-white font-medium mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition">About</a></li>
                <li><a href="#" className="hover:text-white transition">Contact</a></li>
                <li><a href="#" className="hover:text-white transition">Privacy</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 pt-8 text-center text-gray-500 text-sm">
            <p>© 2024 HKAIC. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

import { Button } from '@/components/ui/button';

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center pt-20">
      <div className="relative z-10 text-center px-4 max-w-5xl mx-auto">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gray-900/50 border border-gray-700 mb-8">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-sm text-gray-400">AI Flight Intelligence</span>
        </div>
        
        <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
          <span className="block">AI-Powered</span>
          <span className="bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
            Drone Flight Analysis
          </span>
        </h1>
        
        <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
          Professional drone flight analysis and tuning platform
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button className="text-lg px-8 py-6 bg-gradient-to-r from-cyan-400 to-purple-500 hover:opacity-90">
            Get Started
          </Button>
          <Button variant="outline" className="text-lg px-8 py-6 border-gray-600">
            Watch Demo
          </Button>
        </div>
      </div>
    </section>
  );
}

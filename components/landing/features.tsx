import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Brain, Zap, Compass, Shield } from 'lucide-react';

const features = [
  {
    icon: Brain,
    title: "AI Analysis",
    description: "GPT-4 powered intelligent analysis and improvement suggestions"
  },
  {
    icon: Zap,
    title: "Real-time Telemetry",
    description: "Live telemetry monitoring dashboard"
  },
  {
    icon: Compass,
    title: "Multi-format Support",
    description: "Supports Blackbox, ULog, CSV and more"
  },
  {
    icon: Shield,
    title: "Enterprise Security",
    description: "Enterprise-grade security and audit"
  }
];

export default function Features() {
  return (
    <section className="py-24 px-4 bg-gray-900/30">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Powerful Features
          </h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Everything you need for professional drone flight analysis
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <Card key={idx} className="h-full bg-gray-900 border-gray-700">
                <CardHeader>
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-400/20 to-purple-500/20 flex items-center justify-center mb-4">
                    <Icon className="w-6 h-6 text-cyan-400" />
                  </div>
                  <CardTitle className="text-lg text-white">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-400 text-sm">{feature.description}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}

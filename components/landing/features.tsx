"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  Brain,
  BarChart3,
  Shield,
  Zap,
  Compass,
  Cog,
  Radio,
  Cpu,
  Wifi,
  AlertTriangle,
  CheckCircle2,
  Settings2,
  Sparkles,
  Activity,
  LineChart,
  Target,
  Wrench,
  MapPin,
  Battery,
  Gauge,
} from "lucide-react";
import { motion } from "framer-motion";

const features = [
  {
    icon: Brain,
    title: "AI-Powered Analysis",
    description: "Deep learning algorithms analyze thousands of flight parameters in seconds.",
  },
  {
    icon: BarChart3,
    title: "Flight Optimization",
    description: "Automatically tune PID parameters for maximum performance and stability.",
  },
  {
    icon: Shield,
    title: "Risk Assessment",
    description: "Proactive safety monitoring alerts you to potential issues before they happen.",
  },
  {
    icon: Zap,
    title: "Instant Insights",
    description: "Real-time processing delivers actionable recommendations in under 30 seconds.",
  },
  {
    icon: Compass,
    title: "Multi-Format Support",
    description: "Works with DJI, PX4, Betaflight, and all major flight controllers.",
  },
  {
    icon: Cog,
    title: "Copilot Mode",
    description: "AI assistant guides you through troubleshooting and optimization.",
  },
  {
    icon: Radio,
    title: "Real Drone Control",
    description: "Connect and control real drones with MAVSDK integration.",
  },
  {
    icon: Cpu,
    title: "PID Optimization",
    description: "Advanced PID tuning analysis with automated recommendations.",
  },
  {
    icon: Wifi,
    title: "MAVSDK Integration",
    description: "Seamless connection with PX4 and MAVLink-compatible systems.",
  },
  {
    icon: AlertTriangle,
    title: "Anomaly Detection",
    description: "AI-powered detection of motor anomalies and unusual patterns.",
  },
  {
    icon: CheckCircle2,
    title: "Quality Assurance",
    description: "Comprehensive quality checks ensure flight readiness.",
  },
  {
    icon: Settings2,
    title: "Configuration Management",
    description: "Easy setup and management of drone parameters.",
  },
  {
    icon: Sparkles,
    title: "Smart Insights",
    description: "Intelligent recommendations powered by GPT-4.",
  },
  {
    icon: Activity,
    title: "Flight Monitoring",
    description: "Real-time telemetry and flight status monitoring.",
  },
  {
    icon: LineChart,
    title: "Data Visualization",
    description: "Beautiful charts and graphs for performance analysis.",
  },
  {
    icon: Target,
    title: "Precision Tracking",
    description: "GPS drift detection with centimeter-level accuracy.",
  },
  {
    icon: Wrench,
    title: "Maintenance Alerts",
    description: "Proactive maintenance recommendations based on flight data.",
  },
  {
    icon: MapPin,
    title: "GPS Analysis",
    description: "Comprehensive GPS data analysis and drift detection.",
  },
  {
    icon: Battery,
    title: "Battery Health",
    description: "Monitor battery performance and health metrics.",
  },
  {
    icon: Gauge,
    title: "Motor Performance",
    description: "Real-time motor efficiency and temperature monitoring.",
  },
];

const Features = () => {
  return (
    <section className="py-24 px-4 bg-background-secondary">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Powerful <span className="text-gradient">Features</span>
          </h2>
          <p className="text-text-secondary text-lg max-w-2xl mx-auto">
            Everything you need to elevate your drone flying experience
          </p>
        </motion.div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: idx * 0.05 }}
              >
                <Card className="h-full group hover:border-primary/50 transition-all duration-300">
                  <CardHeader>
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center mb-4 group-hover:btn-glow transition-all duration-300">
                      <Icon className="w-6 h-6 text-primary" />
                    </div>
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-text-secondary text-sm">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export { Features };

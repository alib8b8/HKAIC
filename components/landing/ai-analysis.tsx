"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import { motion } from "framer-motion";
import { Activity } from "lucide-react";

const flightData = [
  { time: "0s", pitch: 0, roll: 0, yaw: 0 },
  { time: "10s", pitch: 2.3, roll: -1.1, yaw: 0.5 },
  { time: "20s", pitch: -1.5, roll: 2.8, yaw: -0.3 },
  { time: "30s", pitch: 3.1, roll: -0.8, yaw: 1.2 },
  { time: "40s", pitch: -0.9, roll: 1.5, yaw: -0.7 },
  { time: "50s", pitch: 1.8, roll: -2.2, yaw: 0.4 },
  { time: "60s", pitch: 0.5, roll: 0.8, yaw: 0.1 },
];

const batteryData = [
  { time: "0", voltage: 16.8 },
  { time: "20", voltage: 16.5 },
  { time: "40", voltage: 16.2 },
  { time: "60", voltage: 15.8 },
  { time: "80", voltage: 15.4 },
  { time: "100", voltage: 14.9 },
  { time: "120", voltage: 14.2 },
];

const AIAnalysis = () => {
  return (
    <section className="py-24 px-4">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            AI <span className="text-gradient">Flight Analysis</span>
          </h2>
          <p className="text-text-secondary text-lg max-w-2xl mx-auto">
            See how our AI transforms raw flight data into meaningful insights
          </p>
        </motion.div>
        
        <div className="grid lg:grid-cols-2 gap-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-primary" />
                    Flight Stability
                  </CardTitle>
                  <Badge variant="success">Excellent</Badge>
                </div>
                <p className="text-text-secondary text-sm mt-2">
                  Pitch, Roll & Yaw analysis (degrees)
                </p>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={flightData}>
                      <defs>
                        <linearGradient id="colorPitch" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#00D4FF" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorRoll" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#7C3AED" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1E1E2E" />
                      <XAxis 
                        dataKey="time" 
                        stroke="#64748B" 
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis 
                        stroke="#64748B" 
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#111118', 
                          border: '1px solid #1E1E2E',
                          borderRadius: '8px'
                        }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="pitch" 
                        stroke="#00D4FF" 
                        strokeWidth={2}
                        dot={{ fill: '#00D4FF' }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="roll" 
                        stroke="#7C3AED" 
                        strokeWidth={2}
                        dot={{ fill: '#7C3AED' }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="yaw" 
                        stroke="#10B981" 
                        strokeWidth={2}
                        dot={{ fill: '#10B981' }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="space-y-6"
          >
            <Card>
              <CardHeader>
                <CardTitle>Battery Health</CardTitle>
                <p className="text-text-secondary text-sm mt-2">
                  Voltage drop analysis over flight time
                </p>
              </CardHeader>
              <CardContent>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={batteryData}>
                      <defs>
                        <linearGradient id="colorVoltage" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#F59E0B" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1E1E2E" />
                      <XAxis 
                        dataKey="time" 
                        stroke="#64748B" 
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis 
                        stroke="#64748B" 
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#111118', 
                          border: '1px solid #1E1E2E',
                          borderRadius: '8px'
                        }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="voltage" 
                        stroke="#F59E0B" 
                        fillOpacity={1}
                        fill="url(#colorVoltage)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-background-secondary rounded-xl">
                    <div className="text-2xl font-bold text-primary">87</div>
                    <div className="text-sm text-text-muted">Flight Score</div>
                  </div>
                  <div className="text-center p-4 bg-background-secondary rounded-xl">
                    <div className="text-2xl font-bold text-success">Low</div>
                    <div className="text-sm text-text-muted">Risk Level</div>
                  </div>
                  <div className="text-center p-4 bg-background-secondary rounded-xl">
                    <div className="text-2xl font-bold text-warning">3</div>
                    <div className="text-sm text-text-muted">Suggestions</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export { AIAnalysis };

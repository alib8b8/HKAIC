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
import { TrendingUp, Activity, Shield } from "lucide-react";

const flightData = [
  { time: "0s", pitch: 0, roll: 0, yaw: 0 },
  { time: "10s", pitch: 2.3, roll: -1.1, yaw: 0.5 },
  { time: "20s", pitch: -1.5, roll: 2.8, yaw: -0.3 },
  { time: "30s", pitch: 3.1, roll: -0.8, yaw: 1.2 },
  { time: "40s", pitch: -0.9, roll: 1.5, yaw: -0.7 },
  { time: "50s", pitch: 1.8, roll: -2.2, yaw: 0.4 },
  { time: "60s", pitch: 0.5, roll: 0.8, yaw: 0.1 },
];

const motorData = [
  { motor: 'M1', output: 72, temp: 48 },
  { motor: 'M2', output: 78, temp: 51 },
  { motor: 'M3', output: 69, temp: 46 },
  { motor: 'M4', output: 75, temp: 49 },
];

const ReportOverview = () => {
  const score = 87;
  const efficiency = 92;
  const stability = 81;
  const riskLevel = 'Low';
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <Card className="lg:col-span-1">
        <CardContent className="pt-6">
          <div className="text-center">
            <div className="relative inline-block">
              <svg className="w-48 h-48 transform -rotate-90">
                <circle
                  cx="96"
                  cy="96"
                  r="88"
                  stroke="#1E1E2E"
                  strokeWidth="12"
                  fill="none"
                />
                <motion.circle
                  cx="96"
                  cy="96"
                  r="88"
                  stroke="url(#gradient)"
                  strokeWidth="12"
                  fill="none"
                  strokeLinecap="round"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: score / 100 }}
                  transition={{ duration: 1, ease: "easeOut" }}
                />
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#00D4FF" />
                    <stop offset="100%" stopColor="#7C3AED" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-5xl font-bold text-gradient">{score}</div>
                  <div className="text-text-muted text-sm">Overall Score</div>
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mt-8">
              <div className="p-4 rounded-xl bg-background-secondary">
                <div className="flex items-center justify-center gap-2 text-primary mb-2">
                  <TrendingUp className="w-4 h-4" />
                  <span className="text-sm font-medium">Efficiency</span>
                </div>
                <div className="text-2xl font-bold">{efficiency}%</div>
              </div>
              <div className="p-4 rounded-xl bg-background-secondary">
                <div className="flex items-center justify-center gap-2 text-success mb-2">
                  <Activity className="w-4 h-4" />
                  <span className="text-sm font-medium">Stability</span>
                </div>
                <div className="text-2xl font-bold">{stability}%</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card className="lg:col-span-2">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Flight Stability Analysis</CardTitle>
            <Badge variant={riskLevel === 'Low' ? 'success' : riskLevel === 'Medium' ? 'warning' : 'danger'}>
              <Shield className="w-3 h-3 mr-1" />
              {riskLevel} Risk
            </Badge>
          </div>
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
    </div>
  );
};

export { ReportOverview };

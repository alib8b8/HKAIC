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
  BarChart,
  Bar,
  Cell,
  PieChart,
  Pie,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import { motion } from "framer-motion";
import { TrendingUp, Activity, Shield, Gauge, Battery, Target, Zap } from "lucide-react";

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
  { motor: 'M1', output: 72, temp: 48, efficiency: 92 },
  { motor: 'M2', output: 78, temp: 51, efficiency: 88 },
  { motor: 'M3', output: 69, temp: 46, efficiency: 95 },
  { motor: 'M4', output: 75, temp: 49, efficiency: 89 },
];

const riskDistribution = [
  { name: 'Low Risk', value: 65, color: '#10B981' },
  { name: 'Medium Risk', value: 25, color: '#F59E0B' },
  { name: 'High Risk', value: 10, color: '#EF4444' },
];

const performanceData = [
  { metric: 'Efficiency', score: 92, fullMark: 100 },
  { metric: 'Stability', score: 81, fullMark: 100 },
  { metric: 'Control', score: 85, fullMark: 100 },
  { metric: 'Speed', score: 78, fullMark: 100 },
  { metric: 'Battery', score: 88, fullMark: 100 },
  { metric: 'GPS', score: 95, fullMark: 100 },
];

const altitudeData = [
  { time: '0s', altitude: 0 },
  { time: '10s', altitude: 15 },
  { time: '20s', altitude: 30 },
  { time: '30s', altitude: 45 },
  { time: '40s', altitude: 50 },
  { time: '50s', altitude: 48 },
  { time: '60s', altitude: 35 },
  { time: '70s', altitude: 20 },
  { time: '80s', altitude: 5 },
  { time: '90s', altitude: 0 },
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

      {/* Motor Performance - BarChart */}
      <Card className="lg:col-span-1">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Gauge className="w-5 h-5 text-primary" />
            <CardTitle>Motor Performance</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={motorData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E1E2E" />
                <XAxis dataKey="motor" stroke="#64748B" fontSize={12} />
                <YAxis stroke="#64748B" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111118',
                    border: '1px solid #1E1E2E',
                    borderRadius: '8px'
                  }}
                />
                <Bar dataKey="efficiency" radius={[8, 8, 0, 0]}>
                  {motorData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.efficiency > 90 ? '#10B981' : entry.efficiency > 85 ? '#F59E0B' : '#EF4444'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 flex justify-between text-xs text-text-muted">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-[#10B981]" />
              <span>Excellent</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-[#F59E0B]" />
              <span>Good</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-[#EF4444]" />
              <span>Poor</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risk Distribution - PieChart */}
      <Card className="lg:col-span-1">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-warning" />
            <CardTitle>Risk Distribution</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={70}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {riskDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111118',
                    border: '1px solid #1E1E2E',
                    borderRadius: '8px'
                  }}
                />
                <Legend 
                  iconType="circle"
                  wrapperStyle={{ fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Performance Radar */}
      <Card className="lg:col-span-1">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-secondary" />
            <CardTitle>Multi-Dimensional Analysis</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={performanceData}>
                <PolarGrid stroke="#1E1E2E" />
                <PolarAngleAxis 
                  dataKey="metric" 
                  tick={{ fill: '#64748B', fontSize: 10 }} 
                />
                <PolarRadiusAxis 
                  angle={30} 
                  domain={[0, 100]} 
                  tick={{ fill: '#64748B', fontSize: 10 }}
                />
                <Radar
                  name="Performance"
                  dataKey="score"
                  stroke="#7C3AED"
                  fill="#7C3AED"
                  fillOpacity={0.6}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111118',
                    border: '1px solid #1E1E2E',
                    borderRadius: '8px'
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Altitude Profile - AreaChart */}
      <Card className="lg:col-span-3">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Battery className="w-5 h-5 text-success" />
            <CardTitle>Flight Altitude Profile</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={altitudeData}>
                <defs>
                  <linearGradient id="colorAltitude" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.8}/>
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
                  label={{ value: 'Altitude (m)', angle: -90, position: 'insideLeft', fill: '#64748B' }}
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
                  dataKey="altitude"
                  stroke="#7C3AED"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorAltitude)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export { ReportOverview };

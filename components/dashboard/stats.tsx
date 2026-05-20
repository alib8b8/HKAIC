"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { motion } from "framer-motion";

interface StatCardProps {
  title: string;
  value: string | number;
  trend: 'up' | 'down' | 'stable';
  trendValue?: string;
}

const StatCard = ({ title, value, trend, trendValue }: StatCardProps) => {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'text-success' : trend === 'down' ? 'text-danger' : 'text-text-muted';
  
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between mb-4">
          <p className="text-text-muted text-sm font-medium">{title}</p>
          {trendValue && (
            <div className={`flex items-center gap-1 ${trendColor}`}>
              <TrendIcon className="w-4 h-4" />
              <span className="text-xs font-medium">{trendValue}</span>
            </div>
          )}
        </div>
        <div className="text-3xl font-bold text-gradient">{value}</div>
      </CardContent>
    </Card>
  );
};

const DashboardStats = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        title="Total Flights"
        value="147"
        trend="up"
        trendValue="+12%"
      />
      <StatCard
        title="Avg. Score"
        value="82.3"
        trend="up"
        trendValue="+4.2"
      />
      <StatCard
        title="Analyses Done"
        value="289"
        trend="stable"
      />
      <StatCard
        title="Time Saved"
        value="18h"
        trend="up"
        trendValue="+3h"
      />
    </div>
  );
};

export { DashboardStats, StatCard };

"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  CheckCircle2,
  AlertCircle,
  Zap,
  Copy,
} from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";

const recommendations = [
  {
    id: 1,
    priority: 'high',
    title: 'Increase D Gain for Pitch',
    description: 'Minor oscillations detected. Increase D gain by 0.15 for better damping.',
    before: { p: 4.2, i: 0.8, d: 2.1 },
    after: { p: 4.2, i: 0.8, d: 2.25 },
  },
  {
    id: 2,
    priority: 'medium',
    title: 'Add Low-Pass Filter',
    description: 'Consider enabling gyro low-pass filter at 100Hz to reduce vibration noise.',
  },
  {
    id: 3,
    priority: 'low',
    title: 'Balance Props',
    description: 'Minor vibration spikes detected. Check propeller balance for smoother flight.',
  },
];

const ReportSuggestions = () => {
  const [copied, setCopied] = useState<number | null>(null);
  
  const copyParams = (id: number) => {
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Recommendations</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {recommendations.map((rec, idx) => (
          <motion.div
            key={rec.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: idx * 0.1 }}
            className="p-6 rounded-2xl bg-background-secondary border border-border hover:border-primary/30 transition-colors"
          >
            <div className="flex items-start justify-between gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <Badge variant={rec.priority === 'high' ? 'danger' : rec.priority === 'medium' ? 'warning' : 'success'}>
                    {rec.priority.charAt(0).toUpperCase() + rec.priority.slice(1)}
                  </Badge>
                  <h4 className="font-semibold">{rec.title}</h4>
                </div>
                <p className="text-text-secondary text-sm mb-4">{rec.description}</p>
                
                {rec.before && rec.after && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-surface">
                      <div className="text-xs text-text-muted uppercase tracking-wider mb-2">Current</div>
                      <div className="font-mono text-sm space-y-1">
                        <div>P: {rec.before.p}</div>
                        <div>I: {rec.before.i}</div>
                        <div>D: {rec.before.d}</div>
                      </div>
                    </div>
                    <div className="p-4 rounded-xl bg-primary/10 border border-primary/30">
                      <div className="flex items-center gap-2 text-xs text-primary uppercase tracking-wider mb-2">
                        <CheckCircle2 className="w-3 h-3" />
                        Recommended
                      </div>
                      <div className="font-mono text-sm space-y-1 text-primary">
                        <div>P: {rec.after.p}</div>
                        <div>I: {rec.after.i}</div>
                        <div>D: {rec.after.d}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              {rec.before && rec.after && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyParams(rec.id)}
                  className="flex-shrink-0"
                >
                  {copied === rec.id ? (
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                  ) : (
                    <Copy className="w-4 h-4 mr-2" />
                  )}
                  {copied === rec.id ? 'Copied' : 'Copy'}
                </Button>
              )}
            </div>
          </motion.div>
        ))}
      </CardContent>
    </Card>
  );
};

export { ReportSuggestions };

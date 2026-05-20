"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, Clock, ArrowRight } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

interface FlightLog {
  id: string;
  filename: string;
  date: string;
  duration: string;
  score: number;
  status: 'ready' | 'processing' | 'error';
}

const recentLogs: FlightLog[] = [
  {
    id: '1',
    filename: 'flight_2024_05_19_14_32.log',
    date: '2 hours ago',
    duration: '12:45',
    score: 87,
    status: 'ready',
  },
  {
    id: '2',
    filename: 'dji_mavic_flight.bin',
    date: 'Yesterday',
    duration: '18:20',
    score: 74,
    status: 'ready',
  },
  {
    id: '3',
    filename: 'tuning_session.ulg',
    date: '3 days ago',
    duration: '8:15',
    score: 91,
    status: 'ready',
  },
];

const RecentLogs = () => {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Recent Flights</CardTitle>
          <Link href="/upload">
            <Button variant="ghost" size="sm">
              Upload New
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {recentLogs.map((log, idx) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: idx * 0.1 }}
              className="flex items-center justify-between p-4 rounded-xl bg-background-secondary hover:bg-surface transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="font-medium text-text-primary">{log.filename}</p>
                  <div className="flex items-center gap-3 text-sm text-text-muted">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {log.date}
                    </span>
                    <span>{log.duration}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <Badge variant={log.score >= 80 ? 'success' : log.score >= 60 ? 'warning' : 'danger'}>
                  Score: {log.score}
                </Badge>
                <Link href={`/report/${log.id}`}>
                  <Button variant="ghost" size="sm">
                    View
                  </Button>
                </Link>
              </div>
            </motion.div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export { RecentLogs };

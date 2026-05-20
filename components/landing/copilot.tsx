"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  MessageSquare,
  Sparkles,
  Zap,
  CheckCircle2,
} from "lucide-react";
import { motion } from "framer-motion";
import { useState, useEffect, useRef } from "react";

const Copilot = () => {
  const [messages, setMessages] = useState<{ role: 'user' | 'ai', content: string }[]>([
    {
      role: 'ai',
      content: "Hello! I'm your AI flight copilot. I noticed some oscillations in your last flight log. Would you like me to analyze them?"
    }
  ]);
  const [typing, setTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const handleQuickReply = (reply: string) => {
    setMessages(prev => [...prev, { role: 'user', content: reply }]);
    setTyping(true);
    
    setTimeout(() => {
      let aiResponse = "";
      
      if (reply.includes("analyze")) {
        aiResponse = "Great! I've identified minor oscillations in your pitch axis. I recommend increasing your P gain by 0.2 and D gain by 0.1 for smoother response. Would you like me to generate the full parameter set?";
      } else if (reply.includes("recommendations")) {
        aiResponse = "Here are my top recommendations: 1) Lower your PID gains for smoother flight, 2) Consider adding a low-pass filter for vibration reduction, 3) Check motor balance for consistency.";
      } else {
        aiResponse = "Perfect! I've prepared a complete tuning profile for you. You can apply these settings directly to your flight controller. Would you like to export them?";
      }
      
      setMessages(prev => [...prev, { role: 'ai', content: aiResponse }]);
      setTyping(false);
    }, 1500);
  };
  
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
            AI <span className="text-gradient">Flight Copilot</span>
          </h2>
          <p className="text-text-secondary text-lg max-w-2xl mx-auto">
            Your personal AI assistant for optimizing every flight
          </p>
        </motion.div>
        
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <Card className="overflow-hidden">
              <CardHeader className="border-b border-border pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-base">Flight Copilot</CardTitle>
                    <Badge variant="success" className="mt-1">Online</Badge>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="p-6">
                <div className="space-y-4 max-h-96 overflow-y-auto mb-6">
                  {messages.map((msg, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: idx * 0.1 }}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-2xl p-4 ${
                          msg.role === 'user'
                            ? 'bg-primary text-white rounded-tr-sm'
                            : 'bg-surface border border-border text-text-primary rounded-tl-sm'
                        }`}
                      >
                        <p className="text-sm leading-relaxed">{msg.content}</p>
                      </div>
                    </motion.div>
                  ))}
                  {typing && (
                    <div className="flex justify-start">
                      <div className="bg-surface border border-border rounded-2xl p-4 rounded-tl-sm">
                        <div className="flex gap-2">
                          <div className="w-2 h-2 bg-primary rounded-full animate-bounce" />
                          <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                          <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
                
                <div className="space-y-2">
                  <p className="text-xs text-text-muted uppercase tracking-wider mb-2">Quick Actions</p>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleQuickReply("Yes, analyze them")}
                      className="text-xs"
                    >
                      <CheckCircle2 className="w-3 h-3 mr-2" />
                      Analyze oscillations
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleQuickReply("Show recommendations")}
                      className="text-xs"
                    >
                      <Zap className="w-3 h-3 mr-2" />
                      Recommendations
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleQuickReply("Apply best settings")}
                      className="text-xs"
                    >
                      <Sparkles className="w-3 h-3 mr-2" />
                      Apply settings
                    </Button>
                  </div>
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
            <div className="space-y-4">
              <div className="flex gap-4 items-start">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0 mt-1">
                  <MessageSquare className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Natural Language</h3>
                  <p className="text-text-secondary text-sm">
                    Ask questions in plain English. No technical jargon required.
                  </p>
                </div>
              </div>
              
              <div className="flex gap-4 items-start">
                <div className="w-10 h-10 rounded-xl bg-success/10 flex items-center justify-center flex-shrink-0 mt-1">
                  <CheckCircle2 className="w-5 h-5 text-success" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Actionable Advice</h3>
                  <p className="text-text-secondary text-sm">
                    Get specific tuning parameters you can apply directly.
                  </p>
                </div>
              </div>
              
              <div className="flex gap-4 items-start">
                <div className="w-10 h-10 rounded-xl bg-warning/10 flex items-center justify-center flex-shrink-0 mt-1">
                  <Zap className="w-5 h-5 text-warning" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Instant Response</h3>
                  <p className="text-text-secondary text-sm">
                    Get answers in seconds, not hours. Optimize between flights.
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export { Copilot };

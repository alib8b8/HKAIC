"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { useRef, useEffect, useCallback } from "react";

interface Particle {
  x: number;
  y: number;
  size: number;
  speedX: number;
  speedY: number;
  opacity: number;
}

const Hero = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const particles: Particle[] = [];
    const particleCount = 80;
    
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 3 + 1,
        speedX: (Math.random() - 0.5) * 0.5,
        speedY: (Math.random() - 0.5) * 0.5,
        opacity: Math.random() * 0.5 + 0.2,
      });
    }
    
    const animate = () => {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      particles.forEach((particle) => {
        particle.x += particle.speedX;
        particle.y += particle.speedY;
        
        if (particle.x < 0 || particle.x > canvas.width) particle.speedX *= -1;
        if (particle.y < 0 || particle.y > canvas.height) particle.speedY *= -1;
        
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 212, 255, ${particle.opacity})`;
        ctx.fill();
        
        particles.forEach((other) => {
          const dx = particle.x - other.x;
          const dy = particle.y - other.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance < 100) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(0, 212, 255, ${0.1 * (1 - distance / 100)})`;
            ctx.lineWidth = 0.5;
            ctx.moveTo(particle.x, particle.y);
            ctx.lineTo(other.x, other.y);
            ctx.stroke();
          }
        });
      });
      
      requestAnimationFrame(animate);
    };
    
    animate();
    
    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      <canvas 
        ref={canvasRef} 
        className="absolute inset-0 z-0"
      />
      
      {/* Gradient orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1.5s' }} />
      
      <div className="relative z-10 text-center px-4 max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-surface border border-border mb-8">
            <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
            <span className="text-sm text-text-secondary">AI Flight Intelligence v2.0</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            <span className="block">Intelligent</span>
            <span className="text-gradient">Drone Flight Analysis</span>
          </h1>
          
          <p className="text-xl text-text-secondary mb-10 max-w-2xl mx-auto">
            HKAIC transforms raw flight logs into actionable insights. 
            AI-powered tuning, risk assessment, and optimization suggestions.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button className="text-lg px-8 py-6 btn-glow">
              Start Free Analysis
            </Button>
            <Button variant="outline" className="text-lg px-8 py-6">
              Watch Demo
            </Button>
          </div>
          
          <div className="mt-12 grid grid-cols-3 gap-8">
            {[
              { label: 'Flights Analyzed', value: '50K+' },
              { label: 'Avg. Score Boost', value: '32%' },
              { label: 'Response Time', value: '< 30s' },
            ].map((stat, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.5 + idx * 0.1 }}
              >
                <div className="text-3xl font-bold text-gradient">{stat.value}</div>
                <div className="text-sm text-text-muted">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
      
      <motion.div
        animate={{ y: [0, 10, 0] }}
        transition={{ duration: 2, repeat: Infinity }}
        className="absolute bottom-10 left-1/2 transform -translate-x-1/2"
      >
        <div className="w-6 h-10 border-2 border-text-muted rounded-full flex justify-center pt-2">
          <div className="w-1 h-2 bg-text-muted rounded-full animate-bounce" />
        </div>
      </motion.div>
    </section>
  );
};

export { Hero };

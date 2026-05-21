"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { useTranslations } from "next-intl";

const CTA = () => {
  const t = useTranslations("home.cta");
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      setSubmitted(true);
      setTimeout(() => setSubmitted(false), 3000);
      setEmail("");
    }
  };
  
  return (
    <section className="py-24 px-4">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="relative overflow-hidden rounded-3xl"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-cyan-400/20 via-purple-500/10 to-cyan-400/10" />
          <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-400/30 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-500/30 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
          
          <div className="relative backdrop-blur-sm border border-cyan-400/20 rounded-3xl p-12 text-center bg-gray-900/80">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              {t("title")}
            </h2>
            <p className="text-gray-400 text-lg mb-8 max-w-xl mx-auto">
              {t("description")}
            </p>
            
            {!submitted ? (
              <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
                <Input
                  type="email"
                  placeholder={t("button")}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="flex-1 bg-gray-900 border-cyan-400/30 focus:border-cyan-400"
                />
                <Button type="submit" className="bg-gradient-to-r from-cyan-400 to-purple-500 hover:opacity-90 transition-opacity whitespace-nowrap">
                  {t("button")}
                </Button>
              </form>
            ) : (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-center justify-center gap-3 text-green-400"
              >
                <CheckCircle2 className="w-6 h-6" />
                <span className="font-medium">Check your inbox!</span>
              </motion.div>
            )}
            
            <div className="mt-10 flex flex-wrap justify-center gap-8">
              {[
                { label: "Free tier", icon: "✓" },
                { label: "No credit card", icon: "✓" },
                { label: "Cancel anytime", icon: "✓" },
              ].map((item, idx) => (
                <div key={idx} className="flex items-center gap-2 text-gray-400 text-sm">
                  <span className="text-cyan-400">{item.icon}</span>
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export { CTA };

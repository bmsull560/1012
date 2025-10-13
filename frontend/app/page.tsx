"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Sparkles, TrendingUp, Target, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { UnifiedWorkspace } from "@/components/workspace/UnifiedWorkspace";
import { useAuthStore } from "@/stores/authStore";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);

  const handleGetStarted = () => {
    setIsLoading(true);
    if (isAuthenticated) {
      router.push("/workspace");
    } else {
      router.push("/auth/login");
    }
  };

  const features = [
    {
      icon: Brain,
      title: "AI-Powered Intelligence",
      description: "Four specialized agents working in concert to define, commit, execute, and amplify value",
      color: "text-purple-500",
      bgColor: "bg-purple-50"
    },
    {
      icon: Sparkles,
      title: "Living Value Graph",
      description: "Every interaction contributes to a growing knowledge graph that makes each deal smarter",
      color: "text-blue-500",
      bgColor: "bg-blue-50"
    },
    {
      icon: TrendingUp,
      title: "Compound Learning",
      description: "The system gets smarter with every customer interaction, improving predictions over time",
      color: "text-green-500",
      bgColor: "bg-green-50"
    },
    {
      icon: Target,
      title: "Proven ROI",
      description: "Track and prove value realization with real-time metrics and automated reporting",
      color: "text-orange-500",
      bgColor: "bg-orange-50"
    }
  ];

  const stats = [
    { label: "Deal Velocity", value: "40%", suffix: "faster" },
    { label: "Win Rate", value: "25%", suffix: "increase" },
    { label: "Value Accuracy", value: "94%", suffix: "precision" },
    { label: "NRR", value: "118%", suffix: "retention" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-grid-slate-100 [mask-image:radial-gradient(ellipse_at_center,white,transparent)] -z-10" />
        
        <div className="container mx-auto px-4 py-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center max-w-4xl mx-auto"
          >
            <Badge className="mb-4" variant="secondary">
              <Sparkles className="w-3 h-3 mr-1" />
              Enterprise-Grade B2B Value Platform
            </Badge>
            
            <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent mb-6">
              Transform Customer Value from
              <span className="block text-blue-600 mt-2">Promise to Proof</span>
            </h1>
            
            <p className="text-xl text-slate-600 mb-8 leading-relaxed">
              ValueVerse is the first platform that creates a continuous thread from pre-sales discovery 
              through post-sales success, powered by AI agents that learn from every interaction.
            </p>
            
            <div className="flex gap-4 justify-center mb-12">
              <Button
                size="lg"
                onClick={handleGetStarted}
                disabled={isLoading}
                className="group"
              >
                {isLoading ? "Loading..." : "Get Started"}
                <ChevronRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
              
              <Button size="lg" variant="outline" onClick={() => router.push("/demo")}>
                Watch Demo
              </Button>
            </div>
            
            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {stats.map((stat, index) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white rounded-lg p-4 shadow-sm border"
                >
                  <div className="text-2xl font-bold text-slate-900">{stat.value}</div>
                  <div className="text-sm text-slate-500">{stat.suffix}</div>
                  <div className="text-xs text-slate-400 mt-1">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">
              The Operating System for Value Realization
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Four specialized AI agents work together to create, track, and compound customer value
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card className="h-full hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className={`w-12 h-12 rounded-lg ${feature.bgColor} flex items-center justify-center mb-4`}>
                      <feature.icon className={`w-6 h-6 ${feature.color}`} />
                    </div>
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription>{feature.description}</CardDescription>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Value Lifecycle Section */}
      <section className="py-24 bg-slate-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">
              One Continuous Value Thread
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              From first discovery call through renewal, every interaction builds on the last
            </p>
          </div>
          
          <div className="max-w-4xl mx-auto">
            <div className="relative">
              {/* Connection Line */}
              <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-purple-500 via-blue-500 to-green-500 -translate-y-1/2 hidden md:block" />
              
              <div className="grid md:grid-cols-4 gap-8 relative">
                {[
                  { stage: "Pre-Sales", agent: "ValueArchitect", focus: "Define Value" },
                  { stage: "Sales", agent: "ValueCommitter", focus: "Commit to Value" },
                  { stage: "Delivery", agent: "ValueExecutor", focus: "Execute Value" },
                  { stage: "Success", agent: "ValueAmplifier", focus: "Prove & Grow" }
                ].map((item, index) => (
                  <motion.div
                    key={item.stage}
                    initial={{ opacity: 0, scale: 0.8 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.1 }}
                    viewport={{ once: true }}
                    className="relative"
                  >
                    <div className="bg-white rounded-lg p-6 shadow-md border relative z-10">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 text-white flex items-center justify-center font-bold mb-3">
                        {index + 1}
                      </div>
                      <h3 className="font-semibold text-slate-900 mb-1">{item.stage}</h3>
                      <p className="text-sm text-blue-600 font-medium mb-2">{item.agent}</p>
                      <p className="text-sm text-slate-600">{item.focus}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="container mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="max-w-3xl mx-auto"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-6">
              Ready to Transform Your Value Realization?
            </h2>
            <p className="text-xl mb-8 text-blue-100">
              Join leading B2B companies using ValueVerse to create, track, and compound customer value
            </p>
            <div className="flex gap-4 justify-center">
              <Button
                size="lg"
                variant="secondary"
                onClick={handleGetStarted}
                className="group"
              >
                Start Free Trial
                <ChevronRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="bg-transparent text-white border-white hover:bg-white hover:text-blue-600"
                onClick={() => router.push("/contact")}
              >
                Schedule Demo
              </Button>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}

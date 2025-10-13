"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Brain,
  Layers,
  Users,
  Sparkles,
  ChevronRight,
  Play,
  Pause,
  RotateCcw,
  Info,
  Code,
  Eye,
  Palette,
  Monitor,
  Smartphone,
  Tablet,
} from "lucide-react";
import { DualBrainWorkspace } from "@/components/workspace/DualBrainWorkspace";
import { LivingValueGraph } from "@/components/workspace/LivingValueGraph";
import { PersonaAdaptiveView } from "@/components/workspace/PersonaAdaptiveView";
import { cn } from "@/lib/utils";

export default function DemoPage() {
  const [activeDemo, setActiveDemo] = useState<"dual-brain" | "value-graph" | "persona">("dual-brain");
  const [isPlaying, setIsPlaying] = useState(false);
  const [deviceView, setDeviceView] = useState<"desktop" | "tablet" | "mobile">("desktop");

  const demos = [
    {
      id: "dual-brain",
      title: "Dual-Brain Unified Workspace",
      description: "Experience the revolutionary split-screen interface with conversational AI and visual canvas working in perfect harmony",
      icon: Brain,
      color: "from-purple-500 to-blue-500",
      features: [
        "Real-time agent reasoning transparency",
        "Synchronized left/right brain paradigm",
        "Seamless agent handoffs",
        "Interactive thought stream visualization"
      ]
    },
    {
      id: "value-graph",
      title: "Living Value Graph",
      description: "Interact with the multi-dimensional graph that tracks value evolution from hypothesis to amplification",
      icon: Layers,
      color: "from-blue-500 to-green-500",
      features: [
        "Node-and-edge visualization",
        "Temporal state progression",
        "Intelligence dimension overlays",
        "Real-time graph manipulation"
      ]
    },
    {
      id: "persona",
      title: "Persona-Adaptive Views",
      description: "See how the interface dynamically adapts to different user roles and expertise levels",
      icon: Users,
      color: "from-green-500 to-orange-500",
      features: [
        "Role-based dashboards",
        "Progressive disclosure levels",
        "Guided workflows for beginners",
        "Power user features for experts"
      ]
    }
  ];

  const currentDemo = demos.find(d => d.id === activeDemo)!;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      {/* Header */}
      <div className="border-b bg-white/80 backdrop-blur sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">ValueVerse Interactive Demo</h1>
                <p className="text-sm text-slate-500">Explore the future of B2B value realization</p>
              </div>
            </div>
            
            {/* Device View Selector */}
            <div className="flex items-center gap-2">
              <Button
                variant={deviceView === "desktop" ? "default" : "outline"}
                size="sm"
                onClick={() => setDeviceView("desktop")}
              >
                <Monitor className="w-4 h-4" />
              </Button>
              <Button
                variant={deviceView === "tablet" ? "default" : "outline"}
                size="sm"
                onClick={() => setDeviceView("tablet")}
              >
                <Tablet className="w-4 h-4" />
              </Button>
              <Button
                variant={deviceView === "mobile" ? "default" : "outline"}
                size="sm"
                onClick={() => setDeviceView("mobile")}
              >
                <Smartphone className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Demo Selector */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          {demos.map((demo) => (
            <motion.div
              key={demo.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Card
                className={cn(
                  "cursor-pointer transition-all",
                  activeDemo === demo.id && "ring-2 ring-primary"
                )}
                onClick={() => setActiveDemo(demo.id as any)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div
                      className={cn(
                        "w-12 h-12 rounded-lg flex items-center justify-center text-white",
                        `bg-gradient-to-r ${demo.color}`
                      )}
                    >
                      <demo.icon className="w-6 h-6" />
                    </div>
                    {activeDemo === demo.id && (
                      <Badge variant="secondary">Active</Badge>
                    )}
                  </div>
                  <CardTitle className="mt-4">{demo.title}</CardTitle>
                  <CardDescription>{demo.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {demo.features.map((feature, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <ChevronRight className="w-4 h-4 text-slate-400 mt-0.5" />
                        <span className="text-sm text-slate-600">{feature}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Demo Controls */}
        <Card className="mb-6">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <currentDemo.icon className="w-5 h-5 text-slate-600" />
                <CardTitle className="text-lg">{currentDemo.title}</CardTitle>
              </div>
              
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsPlaying(!isPlaying)}
                >
                  {isPlaying ? (
                    <>
                      <Pause className="w-4 h-4 mr-2" />
                      Pause Demo
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Play Demo
                    </>
                  )}
                </Button>
                <Button variant="outline" size="sm">
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Reset
                </Button>
                <Separator orientation="vertical" className="h-6" />
                <Button variant="outline" size="sm">
                  <Code className="w-4 h-4 mr-2" />
                  View Code
                </Button>
                <Button variant="outline" size="sm">
                  <Info className="w-4 h-4 mr-2" />
                  Learn More
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Demo Content Area */}
        <div className={cn(
          "bg-white rounded-lg border shadow-lg transition-all",
          deviceView === "tablet" && "max-w-4xl mx-auto",
          deviceView === "mobile" && "max-w-md mx-auto"
        )}>
          <div className="border-b bg-slate-50 px-4 py-2">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="ml-4 text-xs text-slate-500">
                {currentDemo.title} - Interactive Demo
              </span>
            </div>
          </div>
          
          <div className={cn(
            "overflow-hidden",
            activeDemo === "dual-brain" && "h-[800px]",
            activeDemo === "value-graph" && "h-[700px]",
            activeDemo === "persona" && "h-auto"
          )}>
            {activeDemo === "dual-brain" && <DualBrainWorkspace />}
            {activeDemo === "value-graph" && (
              <div className="h-full p-4">
                <LivingValueGraph currentStage="hypothesis" editable={true} />
              </div>
            )}
            {activeDemo === "persona" && (
              <div className="p-6">
                <PersonaAdaptiveView />
              </div>
            )}
          </div>
        </div>

        {/* Feature Highlights */}
        <div className="mt-12 space-y-8">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-slate-900 mb-4">
              Key UX/UI Innovations
            </h2>
            <p className="text-lg text-slate-600 max-w-3xl mx-auto">
              The ValueVerse platform introduces groundbreaking interface concepts that make
              complex AI-driven value realization intuitive and accessible
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                title: "Transparent AI Reasoning",
                description: "Watch the AI's thought process in real-time through the unique Thought Stream interface",
                icon: Brain,
              },
              {
                title: "Synchronized Dual Interface",
                description: "Conversational AI and visual canvas work in perfect harmony with <100ms latency",
                icon: Layers,
              },
              {
                title: "Adaptive Complexity",
                description: "Interface automatically adjusts from wizard-style guidance to power-user density",
                icon: Users,
              },
              {
                title: "Living Data Visualization",
                description: "Value graphs that evolve and learn, showing temporal progression and causal relationships",
                icon: Sparkles,
              },
              {
                title: "Seamless Agent Handoffs",
                description: "Four specialized agents collaborate with clear handoff moments for user review",
                icon: ChevronRight,
              },
              {
                title: "Role-Based Optimization",
                description: "Each user sees exactly what they need - from executive summaries to detailed formulas",
                icon: Eye,
              },
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card className="h-full">
                  <CardHeader>
                    <feature.icon className="w-8 h-8 text-primary mb-3" />
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-slate-600">{feature.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Technical Implementation */}
        <Card className="mt-12 bg-gradient-to-r from-slate-50 to-blue-50">
          <CardHeader>
            <CardTitle>Technical Implementation</CardTitle>
            <CardDescription>
              Built with modern, production-ready technologies
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-4 gap-4">
              <div>
                <h4 className="font-semibold mb-2">Frontend</h4>
                <div className="space-y-1 text-sm text-slate-600">
                  <div>React 18 + Next.js 14</div>
                  <div>TypeScript</div>
                  <div>Tailwind CSS</div>
                  <div>Framer Motion</div>
                  <div>D3.js</div>
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Backend</h4>
                <div className="space-y-1 text-sm text-slate-600">
                  <div>FastAPI (Python)</div>
                  <div>PostgreSQL</div>
                  <div>Redis</div>
                  <div>WebSockets</div>
                  <div>Celery</div>
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-2">AI/ML</h4>
                <div className="space-y-1 text-sm text-slate-600">
                  <div>LangChain</div>
                  <div>OpenAI GPT-4</div>
                  <div>Anthropic Claude</div>
                  <div>Vector Databases</div>
                  <div>Custom Agents</div>
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Infrastructure</h4>
                <div className="space-y-1 text-sm text-slate-600">
                  <div>Docker</div>
                  <div>Kubernetes</div>
                  <div>AWS/Azure/GCP</div>
                  <div>CI/CD Pipelines</div>
                  <div>Monitoring</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Call to Action */}
        <div className="mt-12 text-center">
          <Card className="bg-gradient-to-r from-blue-600 to-purple-600 text-white border-0">
            <CardContent className="py-12">
              <h2 className="text-3xl font-bold mb-4">
                Ready to Transform Your Value Realization?
              </h2>
              <p className="text-xl mb-8 text-blue-100 max-w-2xl mx-auto">
                Experience the full power of ValueVerse with a personalized demo
                tailored to your industry and use case
              </p>
              <div className="flex gap-4 justify-center">
                <Button size="lg" variant="secondary">
                  Schedule Demo
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
                <Button size="lg" variant="outline" className="bg-transparent text-white border-white hover:bg-white hover:text-blue-600">
                  Start Free Trial
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

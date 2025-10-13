"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Brain,
  Sparkles,
  Layers,
  FileText,
  BarChart3,
  Target,
  TrendingUp,
  MessageSquare,
  Info,
  ChevronRight,
  Zap,
  BookOpen,
  Code,
  Play,
  Pause,
  RefreshCw,
} from "lucide-react";
import { StructuredAgentChat } from "@/components/agents/StructuredAgentChat";
import { cn } from "@/lib/utils";

export default function AgentDemoPage() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedExample, setSelectedExample] = useState<string | null>(null);

  const examples = [
    {
      id: "value-model",
      title: "Building a Value Model",
      description: "Watch how the agent researches, analyzes, and creates a comprehensive value model",
      icon: Target,
      color: "from-purple-500 to-blue-500",
      prompt: "Build a value model for TechCorp, a mid-market SaaS company struggling with customer retention",
      artifacts: ["Value Model", "ROI Analysis", "Executive Summary"],
      duration: "~15 seconds",
    },
    {
      id: "roi-calculation",
      title: "ROI Calculation & Scenarios",
      description: "See how the agent performs complex ROI calculations with multiple scenarios",
      icon: TrendingUp,
      color: "from-blue-500 to-green-500",
      prompt: "Calculate the 3-year ROI with conservative, realistic, and optimistic scenarios",
      artifacts: ["ROI Analysis", "Scenario Comparison", "Visualization"],
      duration: "~12 seconds",
    },
    {
      id: "progress-tracking",
      title: "Value Realization Tracking",
      description: "Track real-time progress against committed KPIs and value targets",
      icon: BarChart3,
      color: "from-green-500 to-orange-500",
      prompt: "Show me the current value realization progress for Q4",
      artifacts: ["Progress Report", "KPI Dashboard", "Risk Analysis"],
      duration: "~10 seconds",
    },
    {
      id: "executive-brief",
      title: "Executive Presentation",
      description: "Generate C-suite ready presentations with key talking points",
      icon: FileText,
      color: "from-orange-500 to-red-500",
      prompt: "Create an executive summary for the board meeting next week",
      artifacts: ["Executive Summary", "Talking Points", "Slide Deck"],
      duration: "~18 seconds",
    },
  ];

  const features = [
    {
      title: "Structured Artifacts",
      description: "Agent outputs are organized into reusable, versioned artifacts",
      icon: Layers,
    },
    {
      title: "Transparent Processing",
      description: "See exactly what the agent is thinking and doing in real-time",
      icon: Brain,
    },
    {
      title: "Interactive Results",
      description: "Artifacts are interactive components, not just static text",
      icon: Zap,
    },
    {
      title: "Contextual Suggestions",
      description: "Get relevant next actions based on the current context",
      icon: Sparkles,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      {/* Header */}
      <div className="border-b bg-white/80 backdrop-blur">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Structured Agent Experience Demo
              </h1>
              <p className="text-sm text-slate-500 mt-1">
                Experience how agents structure information into digestible, actionable artifacts
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              <Button variant="outline" size="sm">
                <BookOpen className="w-4 h-4 mr-2" />
                Documentation
              </Button>
              <Button variant="outline" size="sm">
                <Code className="w-4 h-4 mr-2" />
                View Code
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Introduction */}
        <Alert className="mb-8 border-blue-200 bg-blue-50/50">
          <Info className="h-4 w-4 text-blue-600" />
          <AlertTitle>What's New?</AlertTitle>
          <AlertDescription>
            This demo showcases a new agent interaction paradigm inspired by Claude's Artifacts system.
            Instead of long, unstructured responses, agents now create organized, reusable components
            that make complex information easy to understand and act upon.
          </AlertDescription>
        </Alert>

        {/* Key Features */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="h-full">
                <CardHeader>
                  <feature.icon className="w-8 h-8 text-primary mb-2" />
                  <CardTitle className="text-base">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-600">{feature.description}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Example Scenarios */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Try Example Scenarios</CardTitle>
            <CardDescription>
              Select a scenario to see how the agent structures different types of requests
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              {examples.map((example) => (
                <Card
                  key={example.id}
                  className={cn(
                    "cursor-pointer transition-all hover:shadow-md",
                    selectedExample === example.id && "ring-2 ring-primary"
                  )}
                  onClick={() => setSelectedExample(example.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div
                        className={cn(
                          "w-10 h-10 rounded-lg flex items-center justify-center text-white",
                          `bg-gradient-to-r ${example.color}`
                        )}
                      >
                        <example.icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-sm mb-1">{example.title}</h4>
                        <p className="text-xs text-slate-600 mb-2">{example.description}</p>
                        
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <MessageSquare className="w-3 h-3 text-slate-400" />
                            <span className="text-xs text-slate-500 italic">
                              "{example.prompt}"
                            </span>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <Layers className="w-3 h-3 text-slate-400" />
                            <div className="flex gap-1">
                              {example.artifacts.map((artifact, i) => (
                                <Badge key={i} variant="secondary" className="text-xs">
                                  {artifact}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <Zap className="w-3 h-3 text-slate-400" />
                            <span className="text-xs text-slate-500">
                              {example.duration}
                            </span>
                          </div>
                        </div>
                        
                        {selectedExample === example.id && (
                          <Button size="sm" className="mt-3 w-full">
                            <Play className="w-3 h-3 mr-2" />
                            Run This Example
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Live Demo */}
        <Card className="overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-slate-50 to-blue-50">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Live Agent Interface</CardTitle>
                <CardDescription>
                  Interact with the agent and see how it structures responses into artifacts
                </CardDescription>
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
                      Pause
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Auto-Play Demo
                    </>
                  )}
                </Button>
                <Button variant="outline" size="sm">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Reset
                </Button>
              </div>
            </div>
          </CardHeader>
          <div className="h-[700px]">
            <StructuredAgentChat />
          </div>
        </Card>

        {/* How It Works */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>How It Works</CardTitle>
            <CardDescription>
              The structured agent experience follows a clear pattern
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-primary">1</span>
                </div>
                <div>
                  <h4 className="font-semibold mb-1">User Request</h4>
                  <p className="text-sm text-slate-600">
                    User asks a question or requests an analysis using natural language
                  </p>
                </div>
              </div>
              
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-primary">2</span>
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Transparent Processing</h4>
                  <p className="text-sm text-slate-600">
                    Agent shows its thinking steps in real-time as it processes the request
                  </p>
                </div>
              </div>
              
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-primary">3</span>
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Structured Artifacts</h4>
                  <p className="text-sm text-slate-600">
                    Results are organized into interactive, reusable artifacts (models, reports, visualizations)
                  </p>
                </div>
              </div>
              
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-primary">4</span>
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Contextual Actions</h4>
                  <p className="text-sm text-slate-600">
                    Agent suggests relevant next steps based on the generated artifacts
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Benefits */}
        <div className="mt-8 grid md:grid-cols-3 gap-6">
          <Card className="bg-gradient-to-br from-purple-50 to-blue-50">
            <CardHeader>
              <CardTitle className="text-lg">For Sales Teams</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <ChevronRight className="w-4 h-4 text-purple-600 mt-0.5" />
                  <span>Get presentation-ready artifacts instantly</span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="w-4 h-4 text-purple-600 mt-0.5" />
                  <span>Reuse value models across similar deals</span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="w-4 h-4 text-purple-600 mt-0.5" />
                  <span>Track version history of proposals</span>
                </li>
              </ul>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-blue-50 to-green-50">
            <CardHeader>
              <CardTitle className="text-lg">For Analysts</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <ChevronRight className="w-4 h-4 text-blue-600 mt-0.5" />
                  <span>Export artifacts to various formats</span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="w-4 h-4 text-blue-600 mt-0.5" />
                  <span>Deep-dive into calculation details</span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="w-4 h-4 text-blue-600 mt-0.5" />
                  <span>Modify and iterate on models</span>
                </li>
              </ul>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-green-50 to-orange-50">
            <CardHeader>
              <CardTitle className="text-lg">For Executives</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <ChevronRight className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Get executive summaries automatically</span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>View high-level insights first</span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Share artifacts with stakeholders</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

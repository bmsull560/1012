"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Brain, 
  Send, 
  Sparkles, 
  ChevronRight, 
  Loader2, 
  Eye, 
  Edit3,
  Search,
  Link2,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Users,
  Target,
  Zap
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

// Agent Types
type AgentType = "architect" | "committer" | "executor" | "amplifier";

interface Agent {
  id: AgentType;
  name: string;
  icon: React.ElementType;
  color: string;
  description: string;
  stage: string;
}

const AGENTS: Record<AgentType, Agent> = {
  architect: {
    id: "architect",
    name: "Value Architect",
    icon: Search,
    color: "text-purple-600",
    description: "Defining value hypothesis through research and pattern matching",
    stage: "Pre-Sales Discovery"
  },
  committer: {
    id: "committer",
    name: "Value Committer",
    icon: Link2,
    color: "text-blue-600",
    description: "Formalizing KPIs and contractual commitments",
    stage: "Sales Commitment"
  },
  executor: {
    id: "executor",
    name: "Value Executor",
    icon: Zap,
    color: "text-green-600",
    description: "Tracking and ensuring value realization",
    stage: "Delivery & Execution"
  },
  amplifier: {
    id: "amplifier",
    name: "Value Amplifier",
    icon: TrendingUp,
    color: "text-orange-600",
    description: "Proving ROI and identifying expansion opportunities",
    stage: "Success & Growth"
  }
};

interface ThoughtStreamItem {
  id: string;
  timestamp: Date;
  agent: AgentType;
  thought: string;
  confidence?: number;
  status: "processing" | "complete" | "error";
}

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  agent?: AgentType;
  confidence?: number;
}

export function DualBrainWorkspace() {
  const [activeAgent, setActiveAgent] = useState<AgentType>("architect");
  const [messages, setMessages] = useState<Message[]>([]);
  const [thoughtStream, setThoughtStream] = useState<ThoughtStreamItem[]>([]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [canvasMode, setCanvasMode] = useState<"view" | "edit">("view");
  const [showHandoff, setShowHandoff] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Simulate agent thinking
  const simulateThoughtStream = async (agent: AgentType) => {
    const thoughts = [
      { text: "Accessing industry benchmarks...", confidence: 0.7 },
      { text: "Mapping pain points to value drivers...", confidence: 0.85 },
      { text: "Analyzing historical patterns from 47 similar deals...", confidence: 0.9 },
      { text: "Calculating ROI projections based on peer data...", confidence: 0.88 },
      { text: "Hypothesis generated with 85% confidence", confidence: 0.85 }
    ];

    for (const thought of thoughts) {
      const item: ThoughtStreamItem = {
        id: Date.now().toString(),
        timestamp: new Date(),
        agent,
        thought: thought.text,
        confidence: thought.confidence,
        status: "processing"
      };
      
      setThoughtStream(prev => [...prev, item]);
      await new Promise(resolve => setTimeout(resolve, 800));
      
      setThoughtStream(prev => 
        prev.map(t => t.id === item.id ? { ...t, status: "complete" } : t)
      );
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isProcessing) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsProcessing(true);
    setThoughtStream([]);

    // Simulate agent processing
    await simulateThoughtStream(activeAgent);

    // Simulate agent response
    const agentResponse: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: `Based on my analysis, I've identified 5 key value drivers that could deliver $2.3M in annual value. The primary opportunity is in customer retention optimization, which alone could yield a 25% improvement in MRR.`,
      timestamp: new Date(),
      agent: activeAgent,
      confidence: 0.85
    };

    setMessages(prev => [...prev, agentResponse]);
    setIsProcessing(false);

    // Check if handoff is needed
    if (Math.random() > 0.7) {
      setTimeout(() => setShowHandoff(true), 1000);
    }
  };

  const handleHandoff = (nextAgent: AgentType) => {
    setActiveAgent(nextAgent);
    setShowHandoff(false);
    
    const handoffMessage: Message = {
      id: Date.now().toString(),
      role: "system",
      content: `Handoff complete. ${AGENTS[nextAgent].name} is now active.`,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, handoffMessage]);
  };

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, thoughtStream]);

  const currentAgent = AGENTS[activeAgent];

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 to-white">
      {/* Left Brain - Conversational AI */}
      <div className="w-1/2 border-r bg-white flex flex-col">
        {/* Agent Status Bar */}
        <div className="border-b bg-gradient-to-r from-white to-slate-50 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={cn(
                "w-10 h-10 rounded-lg flex items-center justify-center",
                "bg-gradient-to-br from-slate-100 to-slate-200"
              )}>
                <currentAgent.icon className={cn("w-5 h-5", currentAgent.color)} />
              </div>
              <div>
                <h2 className="font-semibold text-slate-900 flex items-center gap-2">
                  {currentAgent.name}
                  <Badge variant="outline" className="text-xs">
                    {currentAgent.stage}
                  </Badge>
                </h2>
                <p className="text-xs text-slate-500">{currentAgent.description}</p>
              </div>
            </div>
            
            {/* Agent Lifecycle Progress */}
            <div className="flex items-center gap-1">
              {Object.values(AGENTS).map((agent, index) => (
                <React.Fragment key={agent.id}>
                  <div
                    className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center transition-all",
                      agent.id === activeAgent
                        ? "bg-gradient-to-br from-blue-500 to-purple-600 text-white scale-110"
                        : "bg-slate-100 text-slate-400"
                    )}
                  >
                    <agent.icon className="w-4 h-4" />
                  </div>
                  {index < Object.values(AGENTS).length - 1 && (
                    <ChevronRight className="w-4 h-4 text-slate-300" />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>

        {/* Thought Stream */}
        <AnimatePresence>
          {thoughtStream.length > 0 && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="border-b bg-gradient-to-r from-purple-50 to-blue-50 overflow-hidden"
            >
              <div className="px-6 py-3">
                <div className="flex items-center gap-2 mb-2">
                  <Brain className="w-4 h-4 text-purple-600 animate-pulse" />
                  <span className="text-xs font-medium text-purple-900">
                    Agent Reasoning Process
                  </span>
                </div>
                <div className="space-y-1">
                  {thoughtStream.slice(-3).map((thought) => (
                    <motion.div
                      key={thought.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex items-center gap-2 text-xs"
                    >
                      {thought.status === "processing" ? (
                        <Loader2 className="w-3 h-3 animate-spin text-purple-500" />
                      ) : (
                        <CheckCircle className="w-3 h-3 text-green-500" />
                      )}
                      <span className="text-slate-700">{thought.thought}</span>
                      {thought.confidence && (
                        <Badge variant="secondary" className="text-xs px-1 py-0">
                          {(thought.confidence * 100).toFixed(0)}%
                        </Badge>
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Agent Thread (Messages) */}
        <ScrollArea className="flex-1 px-6 py-4">
          <div className="space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <currentAgent.icon className={cn("w-12 h-12 mx-auto mb-4", currentAgent.color)} />
                <h3 className="text-lg font-medium text-slate-900 mb-2">
                  {currentAgent.name} Ready
                </h3>
                <p className="text-sm text-slate-500 max-w-md mx-auto">
                  I'll help you {currentAgent.stage.toLowerCase()}. Start by telling me about your customer or opportunity.
                </p>
              </div>
            ) : (
              messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn(
                    "flex",
                    message.role === "user" ? "justify-end" : "justify-start"
                  )}
                >
                  {message.role === "system" ? (
                    <div className="w-full">
                      <div className="flex items-center justify-center gap-2 py-2">
                        <Separator className="flex-1" />
                        <span className="text-xs text-slate-500 px-2">
                          {message.content}
                        </span>
                        <Separator className="flex-1" />
                      </div>
                    </div>
                  ) : (
                    <div className={cn(
                      "max-w-[80%] rounded-lg px-4 py-3",
                      message.role === "user"
                        ? "bg-gradient-to-br from-blue-600 to-blue-700 text-white"
                        : "bg-slate-100 text-slate-900"
                    )}>
                      {message.agent && (
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline" className="text-xs">
                            {AGENTS[message.agent].name}
                          </Badge>
                          {message.confidence && (
                            <span className="text-xs opacity-70">
                              {(message.confidence * 100).toFixed(0)}% confident
                            </span>
                          )}
                        </div>
                      )}
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      <span className="text-xs opacity-70 mt-2 block">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  )}
                </motion.div>
              ))
            )}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>

        {/* Agent Prompt Area */}
        <div className="border-t px-6 py-4 bg-gradient-to-t from-slate-50 to-white">
          <div className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={`Ask ${currentAgent.name} anything...`}
              className="min-h-[60px] resize-none"
              disabled={isProcessing}
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isProcessing}
              size="icon"
              className="h-[60px] w-[60px] bg-gradient-to-br from-blue-600 to-purple-600"
            >
              {isProcessing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Right Brain - Interactive Canvas */}
      <div className="w-1/2 flex flex-col bg-gradient-to-br from-slate-50 via-white to-blue-50">
        {/* Canvas Header */}
        <div className="border-b bg-white/80 backdrop-blur px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-slate-900">Living Value Graph</h2>
              <p className="text-sm text-slate-500">
                Interactive visualization of value creation
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Tabs value={canvasMode} onValueChange={(v) => setCanvasMode(v as "view" | "edit")}>
                <TabsList>
                  <TabsTrigger value="view">
                    <Eye className="w-4 h-4 mr-2" />
                    View
                  </TabsTrigger>
                  <TabsTrigger value="edit">
                    <Edit3 className="w-4 h-4 mr-2" />
                    Edit
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </div>
        </div>

        {/* Canvas Content - Placeholder for Value Graph */}
        <div className="flex-1 p-6 overflow-auto">
          <div className="min-h-full flex items-center justify-center">
            <Card className="w-full max-w-2xl">
              <CardHeader>
                <CardTitle>Value Graph Visualization</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600 mb-4">
                  The Living Value Graph will render here, showing nodes for value drivers,
                  outcomes, and KPIs with interactive connections.
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-2xl font-bold text-green-600">$2.3M</div>
                      <p className="text-sm text-slate-600">Annual Value Potential</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-2xl font-bold text-blue-600">85%</div>
                      <p className="text-sm text-slate-600">Confidence Score</p>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Agent Handoff Modal */}
      <AnimatePresence>
        {showHandoff && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowHandoff(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-lg p-6 max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold mb-4">Agent Handoff Ready</h3>
              <p className="text-slate-600 mb-6">
                The {currentAgent.name} has completed the {currentAgent.stage.toLowerCase()}.
                Ready to proceed to the next stage?
              </p>
              <div className="space-y-2">
                {Object.values(AGENTS)
                  .filter(agent => agent.id !== activeAgent)
                  .map(agent => (
                    <Button
                      key={agent.id}
                      onClick={() => handleHandoff(agent.id)}
                      variant="outline"
                      className="w-full justify-start"
                    >
                      <agent.icon className={cn("w-4 h-4 mr-2", agent.color)} />
                      Activate {agent.name}
                    </Button>
                  ))}
              </div>
              <Button
                onClick={() => setShowHandoff(false)}
                variant="ghost"
                className="w-full mt-4"
              >
                Continue with current agent
              </Button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

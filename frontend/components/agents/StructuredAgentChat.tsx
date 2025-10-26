"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { sanitizeMarkdownToHTML } from "@/lib/sanitize";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Progress } from "@/components/ui/progress";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Send,
  Sparkles,
  Brain,
  Loader2,
  ChevronRight,
  Plus,
  Paperclip,
  Mic,
  Image,
  FileText,
  BarChart3,
  Calculator,
  Target,
  TrendingUp,
  Users,
  AlertCircle,
  CheckCircle,
  Info,
  Lightbulb,
  Code,
  Table,
  PieChart,
  GitBranch,
  Briefcase,
  MessageSquare,
  Layers,
  ArrowRight,
  Clock,
  Zap,
  BookOpen,
  Hash,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { AgentArtifacts } from "./AgentArtifacts";

// Safe HTML component that sanitizes content before rendering
const SafeHTML: React.FC<{ content: string }> = ({ content }) => {
  const sanitizedContent = sanitizeMarkdownToHTML(content);
  return <div dangerouslySetInnerHTML={{ __html: sanitizedContent }} />;
};

// Message Types
type MessageRole = "user" | "assistant" | "system" | "artifact";

interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  agent?: string;
  artifacts?: string[]; // IDs of related artifacts
  thinking?: ThinkingStep[];
  suggestions?: Suggestion[];
  metadata?: {
    confidence?: number;
    sources?: string[];
    processingTime?: number;
  };
}

interface ThinkingStep {
  step: string;
  status: "processing" | "complete" | "error";
  detail?: string;
}

interface Suggestion {
  id: string;
  text: string;
  icon: React.ElementType;
  action: () => void;
}

// Quick action templates
const QUICK_ACTIONS = [
  {
    id: "value-model",
    label: "Build Value Model",
    icon: Target,
    prompt: "Build a comprehensive value model for [company]",
    artifacts: ["value-model", "roi-analysis"],
  },
  {
    id: "roi-analysis",
    label: "Calculate ROI",
    icon: TrendingUp,
    prompt: "Calculate the 3-year ROI with scenario analysis",
    artifacts: ["roi-analysis", "visualization"],
  },
  {
    id: "contract",
    label: "Draft Contract Terms",
    icon: FileText,
    prompt: "Generate contract terms with KPIs and commitments",
    artifacts: ["contract-terms", "document"],
  },
  {
    id: "progress",
    label: "Track Progress",
    icon: BarChart3,
    prompt: "Show current value realization progress",
    artifacts: ["progress-report", "data-table"],
  },
  {
    id: "executive",
    label: "Executive Summary",
    icon: Briefcase,
    prompt: "Create an executive summary for C-suite presentation",
    artifacts: ["executive-summary", "document"],
  },
];

export function StructuredAgentChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [showArtifacts, setShowArtifacts] = useState(true);
  const [currentAgent, setCurrentAgent] = useState("ValueArchitect");
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [attachments, setAttachments] = useState<any[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isProcessing) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsProcessing(true);

    // Simulate agent processing with structured response
    await simulateAgentResponse(input);
  };

  const simulateAgentResponse = async (userInput: string) => {
    // Show thinking steps
    const thinkingSteps: ThinkingStep[] = [
      { step: "Analyzing request context", status: "processing" },
      { step: "Researching relevant data", status: "processing" },
      { step: "Generating value hypothesis", status: "processing" },
      { step: "Creating visualizations", status: "processing" },
      { step: "Preparing artifacts", status: "processing" },
    ];

    // Add thinking message
    const thinkingMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: "",
      timestamp: new Date(),
      agent: currentAgent,
      thinking: thinkingSteps,
    };

    setMessages(prev => [...prev, thinkingMessage]);

    // Simulate processing each step
    for (let i = 0; i < thinkingSteps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 500));
      thinkingSteps[i].status = "complete";
      setMessages(prev => 
        prev.map(msg => 
          msg.id === thinkingMessage.id 
            ? { ...msg, thinking: [...thinkingSteps] }
            : msg
        )
      );
    }

    // Generate response with artifacts
    const response: Message = {
      id: (Date.now() + 2).toString(),
      role: "assistant",
      content: `I've completed the analysis and generated a comprehensive value model for your review. 

Based on my research, I've identified **5 key value drivers** that could deliver **$2.3M in annual value** with an ROI of **285% over 3 years**.

The primary opportunities are:
• **Customer Retention Optimization** - $750K annual impact
• **Operational Efficiency** - $500K annual impact  
• **Revenue Growth Acceleration** - $650K annual impact

I've created several artifacts for you to review:`,
      timestamp: new Date(),
      agent: currentAgent,
      artifacts: ["artifact-1", "artifact-2", "artifact-3"],
      suggestions: [
        {
          id: "1",
          text: "Review detailed ROI breakdown",
          icon: TrendingUp,
          action: () => console.log("Review ROI"),
        },
        {
          id: "2",
          text: "Adjust value driver assumptions",
          icon: Calculator,
          action: () => console.log("Adjust assumptions"),
        },
        {
          id: "3",
          text: "Generate executive presentation",
          icon: Briefcase,
          action: () => console.log("Generate presentation"),
        },
      ],
      metadata: {
        confidence: 0.85,
        sources: ["Industry benchmarks", "Historical patterns", "Peer analysis"],
        processingTime: 3.2,
      },
    };

    setMessages(prev => 
      prev.map(msg => msg.id === thinkingMessage.id ? response : msg)
    );
    setIsProcessing(false);
  };

  const handleQuickAction = (action: typeof QUICK_ACTIONS[0]) => {
    setInput(action.prompt);
    setShowQuickActions(false);
  };

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Chat Interface */}
      <div className={cn(
        "flex flex-col bg-white border-r transition-all",
        showArtifacts ? "w-1/2" : "w-full"
      )}>
        {/* Header */}
        <div className="border-b px-6 py-4 bg-gradient-to-r from-white to-slate-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Avatar className="w-10 h-10">
                <AvatarFallback className="bg-gradient-to-r from-purple-500 to-blue-500 text-white">
                  <Brain className="w-5 h-5" />
                </AvatarFallback>
              </Avatar>
              <div>
                <h2 className="font-semibold text-slate-900">{currentAgent}</h2>
                <p className="text-xs text-slate-500">AI Value Realization Expert</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                <Zap className="w-3 h-3 mr-1" />
                Online
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowArtifacts(!showArtifacts)}
              >
                <Layers className="w-4 h-4 mr-2" />
                {showArtifacts ? "Hide" : "Show"} Artifacts
              </Button>
            </div>
          </div>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 px-6 py-4">
          <div className="space-y-6">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 rounded-full bg-gradient-to-r from-purple-100 to-blue-100 flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="w-8 h-8 text-purple-600" />
                </div>
                <h3 className="text-lg font-medium text-slate-900 mb-2">
                  Ready to Create Value
                </h3>
                <p className="text-sm text-slate-500 mb-6 max-w-md mx-auto">
                  I'll help you build value models, calculate ROI, and track realization.
                  How can I assist you today?
                </p>
                
                {/* Quick Actions Grid */}
                <div className="grid grid-cols-2 gap-3 max-w-lg mx-auto">
                  {QUICK_ACTIONS.slice(0, 4).map((action) => (
                    <Button
                      key={action.id}
                      variant="outline"
                      className="justify-start"
                      onClick={() => handleQuickAction(action)}
                    >
                      <action.icon className="w-4 h-4 mr-2" />
                      {action.label}
                    </Button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))
            )}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t px-6 py-4 bg-white">
          {/* Attachments Bar */}
          {attachments.length > 0 && (
            <div className="flex gap-2 mb-3 flex-wrap">
              {attachments.map((attachment, i) => (
                <Badge key={i} variant="secondary" className="pl-1">
                  <Paperclip className="w-3 h-3 mr-1" />
                  {attachment.name}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="ml-1 h-4 w-4 p-0"
                    onClick={() => setAttachments(prev => prev.filter((_, idx) => idx !== i))}
                  >
                    ×
                  </Button>
                </Badge>
              ))}
            </div>
          )}
          
          {/* Input Field */}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask me anything about value realization..."
                className="min-h-[60px] pr-12 resize-none"
                disabled={isProcessing}
              />
              
              {/* Input Actions */}
              <div className="absolute bottom-2 right-2 flex gap-1">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <Paperclip className="w-4 h-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Attach file</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-8 w-8"
                        onClick={() => setShowQuickActions(!showQuickActions)}
                      >
                        <Zap className="w-4 h-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Quick actions</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </div>
            
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isProcessing}
              className="h-[60px] px-6"
            >
              {isProcessing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  Send
                  <Send className="w-4 h-4 ml-2" />
                </>
              )}
            </Button>
          </div>
          
          {/* Quick Actions Popover */}
          {showQuickActions && (
            <Card className="absolute bottom-20 left-6 right-6 z-10">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-2">
                {QUICK_ACTIONS.map((action) => (
                  <Button
                    key={action.id}
                    variant="ghost"
                    className="justify-start"
                    onClick={() => handleQuickAction(action)}
                  >
                    <action.icon className="w-4 h-4 mr-2" />
                    {action.label}
                  </Button>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Artifacts Panel */}
      <AnimatePresence>
        {showArtifacts && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: "50%", opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <AgentArtifacts />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Message Bubble Component
function MessageBubble({ message }: { message: Message }) {
  if (message.thinking) {
    return (
      <div className="flex gap-3">
        <Avatar className="w-8 h-8">
          <AvatarFallback className="bg-gradient-to-r from-purple-500 to-blue-500 text-white text-xs">
            <Brain className="w-4 h-4" />
          </AvatarFallback>
        </Avatar>
        
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium">{message.agent}</span>
            <Badge variant="outline" className="text-xs">
              <Loader2 className="w-3 h-3 mr-1 animate-spin" />
              Processing
            </Badge>
          </div>
          
          <Card className="bg-slate-50 border-slate-200">
            <CardContent className="p-3">
              <div className="space-y-2">
                {message.thinking.map((step, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    {step.status === "processing" ? (
                      <Loader2 className="w-3 h-3 animate-spin text-blue-600" />
                    ) : step.status === "complete" ? (
                      <CheckCircle className="w-3 h-3 text-green-600" />
                    ) : (
                      <AlertCircle className="w-3 h-3 text-red-600" />
                    )}
                    <span className={cn(
                      step.status === "complete" && "text-slate-600",
                      step.status === "processing" && "text-slate-900"
                    )}>
                      {step.step}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%]">
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg px-4 py-3">
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          </div>
          <p className="text-xs text-slate-500 mt-1 text-right">
            {new Date(message.timestamp).toLocaleTimeString()}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <Avatar className="w-8 h-8">
        <AvatarFallback className="bg-gradient-to-r from-purple-500 to-blue-500 text-white text-xs">
          <Brain className="w-4 h-4" />
        </AvatarFallback>
      </Avatar>
      
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-sm font-medium">{message.agent}</span>
          {message.metadata?.confidence && (
            <Badge variant="secondary" className="text-xs">
              {(message.metadata.confidence * 100).toFixed(0)}% confidence
            </Badge>
          )}
          {message.metadata?.processingTime && (
            <span className="text-xs text-slate-500">
              {message.metadata.processingTime}s
            </span>
          )}
        </div>
        
        <div className="prose prose-sm max-w-none">
          <div className="bg-slate-50 rounded-lg px-4 py-3 text-slate-900">
            <SafeHTML content={message.content} />
          </div>
        </div>
        
        {/* Artifact Cards */}
        {message.artifacts && message.artifacts.length > 0 && (
          <div className="mt-3 space-y-2">
            <p className="text-xs text-slate-500 mb-2">Generated artifacts:</p>
            <div className="grid grid-cols-2 gap-2">
              {message.artifacts.map((artifactId) => (
                <Card key={artifactId} className="cursor-pointer hover:shadow-md transition-shadow">
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center">
                        <FileText className="w-4 h-4 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">Value Model</p>
                        <p className="text-xs text-slate-500">Click to view</p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
        
        {/* Suggestions */}
        {message.suggestions && message.suggestions.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.suggestions.map((suggestion) => (
              <Button
                key={suggestion.id}
                variant="outline"
                size="sm"
                onClick={suggestion.action}
                className="text-xs"
              >
                <suggestion.icon className="w-3 h-3 mr-1" />
                {suggestion.text}
              </Button>
            ))}
          </div>
        )}
        
        {/* Metadata */}
        {message.metadata?.sources && (
          <div className="mt-3 flex items-center gap-2">
            <BookOpen className="w-3 h-3 text-slate-400" />
            <span className="text-xs text-slate-500">
              Sources: {message.metadata.sources.join(", ")}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

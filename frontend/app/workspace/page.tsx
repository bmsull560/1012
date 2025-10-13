"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Send, 
  Mic, 
  Paperclip, 
  MoreVertical, 
  Bot, 
  Search, 
  MessageSquare, 
  FileText, 
  Table, 
  Code, 
  CheckCircle,
  Users,
  Target,
  Zap,
  TrendingUp,
  Sparkles,
  ChevronDown,
  Brain,
  Briefcase,
  DollarSign,
  Clock,
  BarChart3,
  Calculator,
  Download,
  Share2,
  Loader2,
  ArrowRight,
  Plus,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Minimize2,
  Maximize2,
  Sliders as SlidersIcon
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { useAuth } from "@/contexts/AuthContext";
import { useWorkspaceStore } from "@/stores/workspaceStore";
import { useAgents } from "@/hooks/useAgents";
import { VALUE_DRIVERS, calculateTotalValue, generateScenarios, calculateNPV, calculatePayback, INDUSTRY_BENCHMARKS, calculateAdoptionFactor } from "@/utils/valueDrivers";
import { ValueModelReport } from "@/components/value-model/ValueModelReport";
import { WhatIfSliders } from "@/components/value-model/WhatIfSliders";
import { valueArchitect, WorkflowStage, ValueModelContext } from "@/services/valueArchitect";
import { exportService } from "@/services/exportService";
import { cn } from "@/lib/utils";

// Agent configurations
const AGENTS = [
  {
    id: "architect",
    name: "Value Architect",
    icon: Brain,
    color: "from-purple-500 to-blue-500",
    status: "ready",
  },
  {
    id: "committer",
    name: "Value Committer",
    icon: Briefcase,
    color: "from-blue-500 to-cyan-500",
    status: "ready",
  },
  {
    id: "executor",
    name: "Value Executor",
    icon: Target,
    color: "from-cyan-500 to-green-500",
    status: "ready",
  },
  {
    id: "amplifier",
    name: "Value Amplifier",
    icon: TrendingUp,
    color: "from-green-500 to-emerald-500",
    status: "ready",
  },
];

// Message interface for conversations
interface Message {
  id: string;
  content: string;
  timestamp: Date;
  role?: "user" | "assistant" | "system";
  type?: "user" | "agent" | "system";
  agent?: string;
  metadata?: {
    confidence?: number;
    processingTime?: number;
  };
  artifacts?: Array<{
    type: string;
    title: string;
    content: string;
  }>;
}

// Conversation interface
interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
  status: "active" | "archived";
}

// Report data interface
interface ReportData {
  company: {
    name: string;
    industry: string;
    size: string;
    analysisType: string;
  };
  keyMetrics: {
    totalBenefitsY1: number;
    netBenefitY1: number;
    npv3Year: number;
    paybackMonths: number;
    adoptionRamp: number;
  };
  executiveSummary: {
    roiYear1: number;
    paybackPeriod: number;
    roi3Year: number;
    keyRecommendation: string;
  };
  valueDrivers: Array<{
    name: string;
    value: number;
    percentOfTotal: number;
    confidence: number;
    category: "revenue" | "cost";
  }>;
  financialDetails: {
    totalBenefitsY1: number;
    totalCostsY1: number;
    netBenefitRealized: number;
    netBenefitSteadyState: number;
    npv3Year: number;
    discountRate: number;
  };
  assumptions: {
    salesReps: number;
    aspPerCase: number;
    grossMargin: number;
    annualProcedures: number;
    adoptionRate: number;
    criticalFactor: string;
  };
  scenarios: {
    base: number;
    conservative: number;
    optimistic: number;
  };
  implementationNotes?: string[];
  keySuccessFactors?: string[];
}

export default function WorkspacePage() {
  // State management
  const [activeAgent, setActiveAgent] = useState(AGENTS[0]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [inputMessage, setInputMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [message, setMessage] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [showArtifactPanel, setShowArtifactPanel] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [workflowStage, setWorkflowStage] = useState<WorkflowStage>('idle');
  const [workflowProgress, setWorkflowProgress] = useState(0);
  const [showWhatIf, setShowWhatIf] = useState(false);
  const [whatIfInputs, setWhatIfInputs] = useState<Map<string, number>>(new Map());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Hooks
  const { user } = useAuth();
  const {
    isConnected,
    isProcessing,
    currentThought,
    messages: agentMessages,
    artifacts,
    sendMessage: sendToAgent,
  } = useAgent(activeAgent.id);

  // Initialize user in valueArchitect when authenticated
  useEffect(() => {
    if (user?.id) {
      valueArchitect.setUser(user.id);
    }
  }, [user]);

  // Initialize conversation
  useEffect(() => {
    if (!activeConversation) {
      createNewConversation();
    }
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    scrollToBottom();
  }, [activeConversation?.messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const createNewConversation = () => {
    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: "New Conversation",
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      status: "active",
    };
    setConversations([newConversation, ...conversations]);
    setActiveConversation(newConversation);
  };

  const handleSendMessage = useCallback(async () => {
    if (!inputMessage.trim() || !activeConversation) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      role: "user",
      timestamp: new Date(),
    };

    // Add user message
    setActiveConversation(prev => prev ? {
      ...prev,
      messages: [...prev.messages, newMessage]
    } : null);

    // Clear input
    const userInput = inputMessage;
    setInputMessage("");

    // Process with Value Architect if active
    if (activeAgent.id === "architect") {
      setIsTyping(true);
      
      try {
        // Process message with Value Architect
        const result = await valueArchitect.processMessage(userInput);
        
        // Update workflow state
        setWorkflowStage(result.stage);
        setWorkflowProgress(result.progress);
        
        // Show report if ready
        if (result.showReport) {
          const report = valueArchitect.getReportData();
          if (report) {
            setReportData(report);
            setShowReport(true);
          }
        }
        
        // Add AI response
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          content: result.response,
          role: "assistant",
          timestamp: new Date(),
        };

        setActiveConversation(prev => prev ? {
          ...prev,
          messages: [...prev.messages, aiResponse]
        } : null);
      } catch (error) {
        console.error('Error processing message:', error);
        
        const errorResponse: Message = {
          id: (Date.now() + 1).toString(),
          content: "Sorry, I encountered an error processing your request. Please try again.",
          role: "assistant",
          timestamp: new Date(),
        };

        setActiveConversation(prev => prev ? {
          ...prev,
          messages: [...prev.messages, errorResponse]
        } : null);
      } finally {
        setIsTyping(false);
      }
    } else {
      // Default response for other agents
      setIsTyping(true);
      setTimeout(() => {
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          content: `I'm the ${activeAgent.name}. I'll help you with that...`,
          role: "assistant",
          timestamp: new Date(),
        };

        setActiveConversation(prev => prev ? {
          ...prev,
          messages: [...prev.messages, aiResponse]
        } : null);
        setIsTyping(false);
      }, 1500);
    }
  }, [inputMessage, activeConversation, activeAgent]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearConversation = () => {
    if (activeConversation) {
      const clearedConversation = {
        ...activeConversation,
        messages: [],
        updatedAt: new Date(),
      };
      setActiveConversation(clearedConversation);
      setConversations(
        conversations.map((c) =>
          c.id === activeConversation.id ? clearedConversation : c
        )
      );
    }
  };

  const exportConversation = () => {
    if (activeConversation) {
      const dataStr = JSON.stringify(activeConversation, null, 2);
      const dataUri = "data:application/json;charset=utf-8," + encodeURIComponent(dataStr);
      const exportFileDefaultName = `conversation-${activeConversation.id}.json`;
      const linkElement = document.createElement("a");
      linkElement.setAttribute("href", dataUri);
      linkElement.setAttribute("download", exportFileDefaultName);
      linkElement.click();
    }
  };

  const renderMessage = (message: Message) => {
    const isUser = message.type === "user";
    const isAgent = message.type === "agent";

    return (
      <motion.div
        key={message.id}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          "flex gap-3 p-4",
          isUser && "bg-slate-50",
          isAgent && "bg-white"
        )}
      >
        <Avatar className="h-8 w-8">
          {isUser ? (
            <AvatarFallback>{user?.first_name?.[0] || "U"}</AvatarFallback>
          ) : (
            <AvatarFallback className="bg-gradient-to-r from-blue-500 to-purple-500 text-white">
              <Brain className="h-4 w-4" />
            </AvatarFallback>
          )}
        </Avatar>

        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm">
              {isUser ? "You" : message.agent || "System"}
            </span>
            <span className="text-xs text-gray-500">
              {message.timestamp.toLocaleTimeString()}
            </span>
            {message.metadata?.confidence && (
              <Badge variant="outline" className="text-xs">
                {Math.round(message.metadata.confidence * 100)}% confident
              </Badge>
            )}
          </div>

          <div className="prose prose-sm max-w-none">
            {message.content}
          </div>

          {message.artifacts && message.artifacts.length > 0 && (
            <div className="mt-3 space-y-2">
              {message.artifacts.map((artifact, idx) => (
                <Card key={idx} className="p-3">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium">Artifact</span>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    );
  };

  return (
    <div className={cn(
      "flex h-screen bg-gray-50",
      isFullscreen && "fixed inset-0 z-50"
    )}>
      {/* Sidebar - Conversation History */}
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.div
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            className="w-80 bg-white border-r flex flex-col"
          >
            {/* Sidebar Header */}
            <div className="p-4 border-b">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold">Conversations</h2>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setIsSidebarOpen(false)}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
              </div>
              <Button
                className="w-full"
                size="sm"
                onClick={createNewConversation}
              >
                <Plus className="h-4 w-4 mr-2" />
                New Conversation
              </Button>
            </div>

            {/* Conversation List */}
            <ScrollArea className="flex-1">
              <div className="p-2 space-y-2">
                {conversations.map((conv) => (
                  <Card
                    key={conv.id}
                    className={cn(
                      "p-3 cursor-pointer transition-colors",
                      activeConversation?.id === conv.id && "bg-blue-50 border-blue-200"
                    )}
                    onClick={() => setActiveConversation(conv)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm truncate">
                          {conv.title}
                        </h4>
                        <p className="text-xs text-gray-500 mt-1">
                          {conv.messages.length} messages
                        </p>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {conv.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-400 mt-2">
                      {conv.updatedAt.toLocaleString()}
                    </p>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-gradient-to-br from-gray-50 via-white to-blue-50">
        {/* Header with Gradient */}
        <div className="bg-gradient-to-r from-white via-blue-50 to-purple-50 border-b border-gray-200 shadow-sm px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {!isSidebarOpen && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setIsSidebarOpen(true)}
                  className="hover:bg-white/60"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              )}
              
              {/* Enhanced Agent Selector */}
              <div className="flex items-center gap-2">
                {AGENTS.map((agent) => (
                  <motion.div
                    key={agent.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Button
                      size="sm"
                      variant={activeAgent.id === agent.id ? "default" : "outline"}
                      onClick={() => setActiveAgent(agent)}
                      className={cn(
                        "gap-2 transition-all duration-300",
                        activeAgent.id === agent.id && `bg-gradient-to-r ${agent.color} text-white border-none shadow-md`
                      )}
                    >
                      <agent.icon className="h-4 w-4" />
                      {agent.name}
                    </Button>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Enhanced Actions */}
            <div className="flex items-center gap-2">
              <Button size="sm" variant="ghost" onClick={clearConversation} className="hover:bg-white/80">
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button size="sm" variant="ghost" onClick={exportConversation} className="hover:bg-white/80">
                <Download className="h-4 w-4" />
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setIsFullscreen(!isFullscreen)} className="hover:bg-white/80">
                {isFullscreen ? (
                  <Minimize2 className="h-4 w-4" />
                ) : (
                  <Maximize2 className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          {/* Connection Status */}
          <div className="flex items-center gap-2 mt-2">
            <div className={cn(
              "h-2 w-2 rounded-full",
              isConnected ? "bg-green-500" : "bg-red-500"
            )} />
            <span className="text-xs text-gray-500">
              {isConnected ? "Connected" : "Disconnected"}
            </span>
            {currentThought && (
              <span className="text-xs text-gray-500 ml-4">
                Agent is thinking: {currentThought}
              </span>
            )}
          </div>
          
          {/* Workflow Progress */}
          {workflowStage !== 'idle' && workflowProgress > 0 && (
            <div className="px-4 pb-2">
              <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                <span>Building Value Model</span>
                <span>{workflowProgress}%</span>
              </div>
              <Progress value={workflowProgress} className="h-1" />
            </div>
          )}
        </div>

        {/* Messages Area or Report */}
        <ScrollArea className="flex-1 bg-white">
          {showReport && reportData ? (
            <div className="space-y-6">
              <ValueModelReport
                data={reportData}
                onExport={async (format: "pdf" | "ppt" | "excel") => {
                  try {
                    switch(format) {
                      case 'pdf':
                        await exportService.exportToPDF(reportData);
                        break;
                      case 'ppt':
                        await exportService.exportToPowerPoint(reportData);
                        break;
                      case 'excel':
                        await exportService.exportToExcel(reportData);
                        break;
                    }
                  } catch (error) {
                    console.error('Export failed:', error);
                    alert('Export failed. Please try again.');
                  }
                }}
                onShare={() => {
                  // Copy link to clipboard
                  const url = window.location.href;
                  navigator.clipboard.writeText(url);
                  alert('Link copied to clipboard!');
                }}
                onScenarioChange={(scenario: "base" | "conservative" | "optimistic") => {
                  console.log(`Switching to ${scenario} scenario`);
                  // TODO: Implement scenario switching
                }}
              />
              
              {/* What-If Analysis Section */}
              {showWhatIf && (
                <div className="max-w-7xl mx-auto px-6">
                  <WhatIfSliders
                    inputs={whatIfInputs}
                    selectedDrivers={valueArchitect.getReportData()?.valueDrivers.map((d: any) => {
                      // Map driver names back to IDs
                      const driver = VALUE_DRIVERS.find(vd => vd.name === d.name);
                      return driver?.id || '';
                    }).filter((id: string) => id) || []}
                    onInputChange={(inputId, value) => {
                      const newInputs = new Map(whatIfInputs);
                      newInputs.set(inputId, value);
                      setWhatIfInputs(newInputs);
                    }}
                    onApply={(inputs) => {
                      // Recalculate with new inputs
                      const newReportData = valueArchitect.recalculateWithInputs(inputs);
                      if (newReportData) {
                        setReportData(newReportData);
                      }
                    }}
                    onReset={() => {
                      const originalData = valueArchitect.getReportData();
                      if (originalData) {
                        setReportData(originalData);
                        setWhatIfInputs(new Map());
                      }
                    }}
                    currentMetrics={reportData ? {
                      totalBenefits: reportData.keyMetrics.totalBenefitsY1,
                      netBenefit: reportData.keyMetrics.netBenefitY1,
                      npv: reportData.keyMetrics.npv3Year,
                      payback: reportData.keyMetrics.paybackMonths
                    } : undefined}
                  />
                </div>
              )}
            </div>
          ) : (
            <div className="max-w-4xl mx-auto">
              {!activeConversation || activeConversation.messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-96 text-gray-500">
                <MessageSquare className="h-12 w-12 mb-4 text-gray-300" />
                <h3 className="text-lg font-medium mb-2">Start a conversation</h3>
                <p className="text-sm text-center max-w-md">
                  Ask {activeAgent.name} anything about value realization, ROI calculations,
                  or business strategy.
                </p>
                <div className="mt-6 space-y-2">
                  <p className="text-xs text-gray-500 font-medium">Try these examples:</p>
                  <div className="flex flex-col gap-2 items-center">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setInputMessage("Build a value model for Anika Therapeutics");
                      }}
                      className="text-xs"
                    >
                      "Build a value model for Anika Therapeutics"
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setInputMessage("Create ROI analysis for Rush University orthopedics");
                      }}
                      className="text-xs"
                    >
                      "Create ROI analysis for Rush University"
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              <div>
                {activeConversation.messages.map(renderMessage)}
                {isTyping && (
                  <div className="flex gap-3 p-4 bg-gray-50">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="bg-gradient-to-r from-blue-500 to-purple-500 text-white">
                        <Brain className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm text-gray-500">
                        {activeAgent.name} is typing...
                      </span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
          )}
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t bg-white p-4">
          <div className="max-w-4xl mx-auto">
            {showReport && (
              <div className="mb-4 flex items-center justify-between">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setShowReport(false);
                    setInputMessage("");
                  }}
                  className="gap-2"
                >
                  <MessageSquare className="h-4 w-4" />
                  Back to Conversation
                </Button>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowWhatIf(!showWhatIf)}
                  >
                    <SlidersIcon className="h-4 w-4 mr-1" />
                    {showWhatIf ? 'Hide' : 'Show'} What-If Analysis
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      valueArchitect.reset();
                      setShowReport(false);
                      setShowWhatIf(false);
                      setWorkflowStage('idle');
                      setWorkflowProgress(0);
                      setReportData(null);
                      setWhatIfInputs(new Map());
                    }}
                  >
                    Start New Model
                  </Button>
                </div>
              </div>
            )}
            <div className="flex gap-2">
              <Textarea
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`Ask ${activeAgent.name} anything...`}
                className="flex-1 min-h-[60px] max-h-[200px] resize-none"
                disabled={isProcessing}
              />
              <div className="flex flex-col gap-2">
                <Button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isProcessing}
                  className="h-full"
                >
                  {isProcessing ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-gray-500">
                Press Enter to send, Shift+Enter for new line
              </p>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>Model: GPT-4</span>
                <span>Context: {activeConversation?.messages.length || 0} messages</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Send, Sparkles, ChevronRight, Loader2, Eye, Edit3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ValueCanvas } from "./ValueCanvas";
import { AgentThoughtStream } from "./AgentThoughtStream";
import { QuickActions } from "./QuickActions";
import { useWorkspaceStore } from "@/stores/workspaceStore";
import { useWebSocket } from "@/hooks/useWebSocket";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  agent?: string;
  confidence?: number;
  thinking?: boolean;
}

export function UnifiedWorkspace() {
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [canvasMode, setCanvasMode] = useState<"view" | "edit">("view");
  const scrollRef = useRef<HTMLDivElement>(null);
  
  const { 
    activeTemplate, 
    canvasComponents,
    updateCanvas,
    setActiveTemplate 
  } = useWorkspaceStore();
  
  const { socket, connected, sendMessage } = useWebSocket();

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (!socket) return;

    socket.on("agent_thinking", (data) => {
      setIsThinking(true);
    });

    socket.on("agent_response", (data) => {
      setIsThinking(false);
      const newMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: data.content,
        timestamp: new Date(),
        agent: data.agent,
        confidence: data.confidence
      };
      setMessages(prev => [...prev, newMessage]);
    });

    socket.on("canvas_update", (data) => {
      updateCanvas(data.components);
    });

    return () => {
      socket.off("agent_thinking");
      socket.off("agent_response");
      socket.off("canvas_update");
    };
  }, [socket, updateCanvas]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isThinking) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsThinking(true);

    // Send to backend via WebSocket
    sendMessage("user_input", {
      content: input,
      context: {
        template: activeTemplate,
        canvasState: canvasComponents
      }
    });
  };

  const handleQuickAction = (action: string) => {
    setInput(action);
    handleSend();
  };

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Left Brain - Conversational AI */}
      <div className="w-1/2 border-r bg-white flex flex-col">
        {/* Header */}
        <div className="border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="font-semibold text-slate-900">AI Assistant</h2>
                <div className="flex items-center gap-2">
                  <div className={cn(
                    "w-2 h-2 rounded-full",
                    connected ? "bg-green-500" : "bg-red-500"
                  )} />
                  <span className="text-xs text-slate-500">
                    {connected ? "Connected" : "Disconnected"}
                  </span>
                </div>
              </div>
            </div>
            <Badge variant="secondary">
              <Sparkles className="w-3 h-3 mr-1" />
              ValueArchitect Active
            </Badge>
          </div>
        </div>

        {/* Thought Stream */}
        {isThinking && (
          <div className="border-b bg-slate-50 px-6 py-3">
            <AgentThoughtStream />
          </div>
        )}

        {/* Messages */}
        <ScrollArea className="flex-1 px-6 py-4">
          <div className="space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <Brain className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-900 mb-2">
                  Ready to Create Value
                </h3>
                <p className="text-sm text-slate-500 mb-6">
                  Start by telling me about your customer or selecting a quick action
                </p>
                <QuickActions onAction={handleQuickAction} />
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
                  <div className={cn(
                    "max-w-[80%] rounded-lg px-4 py-3",
                    message.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-slate-100 text-slate-900"
                  )}>
                    {message.agent && (
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline" className="text-xs">
                          {message.agent}
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
                </motion.div>
              ))
            )}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>

        {/* Input */}
        <div className="border-t px-6 py-4">
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
              placeholder="Ask me anything about value creation..."
              className="min-h-[60px] resize-none"
              disabled={isThinking}
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isThinking}
              size="icon"
              className="h-[60px] w-[60px]"
            >
              {isThinking ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Right Brain - Interactive Canvas */}
      <div className="w-1/2 flex flex-col bg-slate-50">
        {/* Canvas Header */}
        <div className="border-b bg-white px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-slate-900">Value Canvas</h2>
              <p className="text-sm text-slate-500">
                Interactive value model visualization
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

        {/* Canvas Content */}
        <div className="flex-1 p-6 overflow-auto">
          <ValueCanvas
            mode={canvasMode}
            template={activeTemplate}
            components={canvasComponents}
            onUpdate={updateCanvas}
          />
        </div>

        {/* Canvas Footer - Template Selector */}
        <div className="border-t bg-white px-6 py-3">
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-500">Template:</span>
            <div className="flex gap-2">
              {["impact_cascade", "trinity_dashboard", "scenario_matrix"].map((template) => (
                <Button
                  key={template}
                  variant={activeTemplate === template ? "default" : "outline"}
                  size="sm"
                  onClick={() => setActiveTemplate(template)}
                >
                  {template.replace("_", " ").replace(/\b\w/g, l => l.toUpperCase())}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

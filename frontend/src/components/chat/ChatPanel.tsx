'use client'

import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Send, 
  Sparkles, 
  Brain, 
  Zap, 
  AlertCircle,
  CheckCircle,
  Clock,
  ChevronDown,
  Loader2
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'

interface Message {
  id: string
  type: 'user' | 'assistant' | 'agent' | 'system'
  content: string
  timestamp: Date
  agent?: 'architect' | 'committer' | 'executor' | 'amplifier'
  reasoning?: string[]
  confidence?: number
  suggestions?: string[]
}

interface ChatPanelProps {
  onNodeSelect?: (node: any) => void
  selectedNode?: any
  userLevel: 'beginner' | 'intermediate' | 'expert'
}

export function ChatPanel({ onNodeSelect, selectedNode, userLevel }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Welcome to ValueVerse! I\'m your AI assistant, orchestrating four specialized agents to help you realize customer value. How can I help you today?',
      timestamp: new Date(),
      suggestions: [
        'Show me the current value pipeline',
        'Analyze risks in Q1 commitments',
        'Generate expansion opportunities',
        'Review customer health scores'
      ]
    }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [showReasoning, setShowReasoning] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: generateAIResponse(input, selectedNode),
        timestamp: new Date(),
        reasoning: [
          'Analyzing value graph patterns',
          'Identifying optimization opportunities',
          'Cross-referencing with historical data',
          'Generating actionable insights'
        ],
        confidence: 0.87,
        suggestions: [
          'Deep dive into supply chain metrics',
          'Schedule stakeholder review',
          'Update risk mitigation plan'
        ]
      }
      setMessages(prev => [...prev, aiMessage])
      setIsTyping(false)
    }, 1500)
  }

  const generateAIResponse = (query: string, node: any) => {
    if (node) {
      return `Based on the selected ${node.type} node "${node.label}", I can see a value potential of $${(node.value / 1000000).toFixed(1)}M with ${(node.confidence * 100).toFixed(0)}% confidence. The current status is ${node.status}. Would you like me to analyze the dependencies or suggest optimization strategies?`
    }
    
    const responses = [
      'I\'ve analyzed your value pipeline and identified 3 high-impact opportunities totaling $4.2M in potential value. The supply chain optimization initiative shows the strongest ROI with a 3.2x multiplier.',
      'The Q1 commitments are tracking well with 78% on-target. However, I\'ve detected an at-risk indicator in the customer onboarding timeline that could impact $500K in committed value.',
      'Based on successful realizations in similar accounts, I recommend expanding the automation initiative to the EMEA region. Historical patterns suggest a 85% success probability with $4.1M potential.',
      'All four agents are synchronized and ready. The Architect has identified new value drivers, the Committer has locked in Q2 targets, the Executor is tracking 12 active initiatives, and the Amplifier has queued 5 expansion opportunities.'
    ]
    
    return responses[Math.floor(Math.random() * responses.length)]
  }

  const getAgentColor = (agent?: string) => {
    switch (agent) {
      case 'architect': return 'text-blue-600 bg-blue-50'
      case 'committer': return 'text-green-600 bg-green-50'
      case 'executor': return 'text-amber-600 bg-amber-50'
      case 'amplifier': return 'text-purple-600 bg-purple-50'
      default: return 'text-slate-600 bg-slate-50'
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={cn(
                  "flex gap-3",
                  message.type === 'user' && "flex-row-reverse"
                )}
              >
                {/* Avatar */}
                <Avatar className="h-8 w-8 shrink-0">
                  <AvatarFallback className={cn(
                    message.type === 'user' ? 'bg-blue-600 text-white' : 'bg-gradient-to-br from-purple-600 to-blue-600 text-white'
                  )}>
                    {message.type === 'user' ? 'U' : 'AI'}
                  </AvatarFallback>
                </Avatar>

                {/* Message Content */}
                <div className={cn(
                  "flex flex-col gap-2 max-w-[80%]",
                  message.type === 'user' && "items-end"
                )}>
                  <div className={cn(
                    "rounded-lg px-4 py-2",
                    message.type === 'user' 
                      ? "bg-blue-600 text-white" 
                      : "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                  )}>
                    {/* Agent Badge */}
                    {message.agent && (
                      <Badge className={cn("mb-2", getAgentColor(message.agent))}>
                        <Brain className="w-3 h-3 mr-1" />
                        {message.agent.charAt(0).toUpperCase() + message.agent.slice(1)} Agent
                      </Badge>
                    )}

                    {/* Message Text */}
                    <p className={cn(
                      "text-sm",
                      message.type !== 'user' && "text-slate-700 dark:text-slate-300"
                    )}>
                      {message.content}
                    </p>

                    {/* Confidence Score */}
                    {message.confidence && (
                      <div className="mt-2 flex items-center gap-2">
                        <div className="flex items-center gap-1">
                          <CheckCircle className="w-3 h-3 text-green-500" />
                          <span className="text-xs text-slate-500">
                            {(message.confidence * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Reasoning (for expert mode) */}
                  {message.reasoning && userLevel === 'expert' && (
                    <button
                      onClick={() => setShowReasoning(!showReasoning)}
                      className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700"
                    >
                      <Sparkles className="w-3 h-3" />
                      View reasoning
                      <ChevronDown className={cn(
                        "w-3 h-3 transition-transform",
                        showReasoning && "rotate-180"
                      )} />
                    </button>
                  )}

                  {showReasoning && message.reasoning && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      className="bg-slate-50 dark:bg-slate-900 rounded-lg p-3 text-xs space-y-1"
                    >
                      {message.reasoning.map((step, i) => (
                        <div key={i} className="flex items-start gap-2">
                          <span className="text-slate-400">{i + 1}.</span>
                          <span className="text-slate-600 dark:text-slate-400">{step}</span>
                        </div>
                      ))}
                    </motion.div>
                  )}

                  {/* Suggestions */}
                  {message.suggestions && message.type === 'assistant' && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {message.suggestions.map((suggestion, i) => (
                        <Button
                          key={i}
                          variant="outline"
                          size="sm"
                          className="text-xs"
                          onClick={() => setInput(suggestion)}
                        >
                          {suggestion}
                        </Button>
                      ))}
                    </div>
                  )}

                  {/* Timestamp */}
                  <span className="text-xs text-slate-400">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Typing Indicator */}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2 text-slate-500"
            >
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">AI is thinking...</span>
            </motion.div>
          )}

          <div ref={scrollRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800">
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            placeholder={
              userLevel === 'beginner' 
                ? "Ask me anything about your customer value..."
                : "Enter command or query (Shift+Enter for new line)"
            }
            className="resize-none"
            rows={2}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="px-3"
          >
            {isTyping ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
        
        {/* Quick Actions */}
        <div className="flex items-center gap-2 mt-2">
          <button className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700">
            <Zap className="w-3 h-3" />
            Quick Analysis
          </button>
          <button className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700">
            <Brain className="w-3 h-3" />
            Agent Status
          </button>
          <button className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700">
            <AlertCircle className="w-3 h-3" />
            Risk Assessment
          </button>
        </div>
      </div>
    </div>
  )
}

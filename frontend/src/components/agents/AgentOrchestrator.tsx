'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Brain, 
  Target, 
  Users, 
  Zap, 
  TrendingUp,
  Play,
  Pause,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Clock,
  Activity,
  ChevronRight
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/utils/cn'

interface Agent {
  id: string
  name: string
  role: string
  status: 'idle' | 'thinking' | 'executing' | 'completed' | 'error'
  currentTask?: string
  progress: number
  insights: string[]
  metrics: {
    tasksCompleted: number
    successRate: number
    avgResponseTime: number
  }
  icon: React.ElementType
  color: string
}

interface AgentOrchestratorProps {
  onAgentAction?: (action: any) => void
}

export function AgentOrchestrator({ onAgentAction }: AgentOrchestratorProps) {
  const [agents, setAgents] = useState<Agent[]>([
    {
      id: 'architect',
      name: 'Value Architect',
      role: 'Pre-Sales Intelligence',
      status: 'thinking',
      currentTask: 'Analyzing market patterns for expansion opportunities',
      progress: 65,
      insights: [
        'Identified $2.3M opportunity in supply chain optimization',
        'Risk score increased 12% for customer onboarding timeline',
        'Competitor analysis shows 3 differentiation points'
      ],
      metrics: {
        tasksCompleted: 47,
        successRate: 92,
        avgResponseTime: 2.3
      },
      icon: Target,
      color: 'blue'
    },
    {
      id: 'committer',
      name: 'Value Committer',
      role: 'Contract Intelligence',
      status: 'executing',
      currentTask: 'Generating success criteria for Q2 commitments',
      progress: 45,
      insights: [
        'Q1 targets 78% achieved with 3 weeks remaining',
        'Recommended penalty clause adjustment for Deal #4521',
        'SLA compliance at 94% across all accounts'
      ],
      metrics: {
        tasksCompleted: 23,
        successRate: 88,
        avgResponseTime: 3.1
      },
      icon: Users,
      color: 'green'
    },
    {
      id: 'executor',
      name: 'Value Executor',
      role: 'Delivery Orchestration',
      status: 'executing',
      currentTask: 'Tracking 12 active value realization initiatives',
      progress: 78,
      insights: [
        'Warehouse automation ahead of schedule by 2 weeks',
        'Resource allocation optimized - saved 120 hours',
        'Critical path analysis shows Q2 delivery on track'
      ],
      metrics: {
        tasksCompleted: 156,
        successRate: 85,
        avgResponseTime: 1.8
      },
      icon: Zap,
      color: 'amber'
    },
    {
      id: 'amplifier',
      name: 'Value Amplifier',
      role: 'Growth Intelligence',
      status: 'idle',
      currentTask: undefined,
      progress: 0,
      insights: [
        'EMEA expansion validated - $4.1M potential',
        'Upsell opportunity identified in 3 accounts',
        'Success story generated for marketing team'
      ],
      metrics: {
        tasksCompleted: 31,
        successRate: 94,
        avgResponseTime: 4.2
      },
      icon: TrendingUp,
      color: 'purple'
    }
  ])

  const [orchestrationMode, setOrchestrationMode] = useState<'auto' | 'manual'>('auto')
  const [isOrchestrating, setIsOrchestrating] = useState(true)

  // Simulate agent activity
  useEffect(() => {
    if (!isOrchestrating) return

    const interval = setInterval(() => {
      setAgents(prev => prev.map(agent => {
        // Randomly update agent status and progress
        const random = Math.random()
        let newStatus = agent.status
        let newProgress = agent.progress

        if (agent.status === 'idle' && random > 0.8) {
          newStatus = 'thinking'
          newProgress = 10
        } else if (agent.status === 'thinking') {
          newProgress = Math.min(100, agent.progress + Math.random() * 20)
          if (newProgress >= 100) {
            newStatus = 'executing'
            newProgress = 10
          }
        } else if (agent.status === 'executing') {
          newProgress = Math.min(100, agent.progress + Math.random() * 15)
          if (newProgress >= 100) {
            newStatus = 'completed'
            setTimeout(() => {
              setAgents(prev => prev.map(a => 
                a.id === agent.id ? { ...a, status: 'idle', progress: 0 } : a
              ))
            }, 3000)
          }
        }

        return { ...agent, status: newStatus, progress: newProgress }
      }))
    }, 2000)

    return () => clearInterval(interval)
  }, [isOrchestrating])

  const getStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'idle': return 'text-slate-400'
      case 'thinking': return 'text-blue-500'
      case 'executing': return 'text-amber-500'
      case 'completed': return 'text-green-500'
      case 'error': return 'text-red-500'
    }
  }

  const getStatusIcon = (status: Agent['status']) => {
    switch (status) {
      case 'idle': return Clock
      case 'thinking': return Brain
      case 'executing': return Activity
      case 'completed': return CheckCircle
      case 'error': return AlertCircle
    }
  }

  const triggerAgent = (agentId: string, task: string) => {
    setAgents(prev => prev.map(agent => 
      agent.id === agentId 
        ? { ...agent, status: 'thinking', currentTask: task, progress: 10 }
        : agent
    ))
    onAgentAction?.({ type: 'trigger', agentId, task })
  }

  return (
    <div className="h-full overflow-auto p-6 space-y-6">
      {/* Orchestration Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Agent Orchestration Center</CardTitle>
              <CardDescription>
                Four specialized AI agents working in symphony to realize customer value
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={orchestrationMode === 'auto' ? 'default' : 'outline'}>
                {orchestrationMode === 'auto' ? 'Autonomous' : 'Manual'} Mode
              </Badge>
              <Button
                size="sm"
                variant={isOrchestrating ? 'default' : 'outline'}
                onClick={() => setIsOrchestrating(!isOrchestrating)}
              >
                {isOrchestrating ? (
                  <>
                    <Pause className="w-4 h-4 mr-1" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-1" />
                    Resume
                  </>
                )}
              </Button>
              <Button size="sm" variant="outline">
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Agent Grid */}
      <div className="grid grid-cols-2 gap-4">
        {agents.map((agent) => {
          const StatusIcon = getStatusIcon(agent.status)
          const AgentIcon = agent.icon
          
          return (
            <motion.div
              key={agent.id}
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
            >
              <Card className={cn(
                "relative overflow-hidden transition-all",
                agent.status !== 'idle' && "ring-2 ring-offset-2",
                agent.status === 'thinking' && "ring-blue-500",
                agent.status === 'executing' && "ring-amber-500",
                agent.status === 'completed' && "ring-green-500",
                agent.status === 'error' && "ring-red-500"
              )}>
                {/* Background Animation */}
                {agent.status !== 'idle' && (
                  <div className="absolute inset-0 opacity-5">
                    <div className={cn(
                      "absolute inset-0 bg-gradient-to-br",
                      agent.color === 'blue' && "from-blue-500 to-indigo-500",
                      agent.color === 'green' && "from-green-500 to-emerald-500",
                      agent.color === 'amber' && "from-amber-500 to-orange-500",
                      agent.color === 'purple' && "from-purple-500 to-pink-500"
                    )} />
                  </div>
                )}

                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        "p-2 rounded-lg",
                        agent.color === 'blue' && "bg-blue-100 dark:bg-blue-900/50",
                        agent.color === 'green' && "bg-green-100 dark:bg-green-900/50",
                        agent.color === 'amber' && "bg-amber-100 dark:bg-amber-900/50",
                        agent.color === 'purple' && "bg-purple-100 dark:bg-purple-900/50"
                      )}>
                        <AgentIcon className={cn(
                          "w-5 h-5",
                          agent.color === 'blue' && "text-blue-600 dark:text-blue-400",
                          agent.color === 'green' && "text-green-600 dark:text-green-400",
                          agent.color === 'amber' && "text-amber-600 dark:text-amber-400",
                          agent.color === 'purple' && "text-purple-600 dark:text-purple-400"
                        )} />
                      </div>
                      <div>
                        <CardTitle className="text-base">{agent.name}</CardTitle>
                        <CardDescription className="text-xs">{agent.role}</CardDescription>
                      </div>
                    </div>
                    <StatusIcon className={cn("w-4 h-4", getStatusColor(agent.status))} />
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Current Task */}
                  {agent.currentTask && (
                    <div className="space-y-2">
                      <p className="text-xs text-slate-600 dark:text-slate-400">
                        {agent.currentTask}
                      </p>
                      <Progress value={agent.progress} className="h-1" />
                    </div>
                  )}

                  {/* Metrics */}
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <p className="text-slate-500">Tasks</p>
                      <p className="font-semibold">{agent.metrics.tasksCompleted}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Success</p>
                      <p className="font-semibold">{agent.metrics.successRate}%</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Avg Time</p>
                      <p className="font-semibold">{agent.metrics.avgResponseTime}s</p>
                    </div>
                  </div>

                  {/* Recent Insights */}
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-slate-700 dark:text-slate-300">
                      Recent Insights
                    </p>
                    {agent.insights.slice(0, 2).map((insight, i) => (
                      <div key={i} className="flex items-start gap-1">
                        <ChevronRight className="w-3 h-3 text-slate-400 mt-0.5 shrink-0" />
                        <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-1">
                          {insight}
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* Actions */}
                  {orchestrationMode === 'manual' && agent.status === 'idle' && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full"
                      onClick={() => triggerAgent(agent.id, 'Manual task execution')}
                    >
                      Trigger Agent
                    </Button>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </div>

      {/* Orchestration Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Orchestration Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {['10:32 AM - Architect identified new opportunity', 
              '10:28 AM - Executor completed warehouse automation tracking',
              '10:15 AM - Committer locked Q2 success criteria',
              '10:02 AM - Amplifier generated expansion analysis'].map((event, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <div className="w-2 h-2 rounded-full bg-blue-500" />
                <p className="text-slate-600 dark:text-slate-400">{event}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

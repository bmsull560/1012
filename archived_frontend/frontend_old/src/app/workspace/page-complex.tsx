'use client'

import React, { useState, useEffect } from 'react'
import { DualBrainLayout } from '@/components/layout/DualBrainLayout'
import { SimpleValueGraph } from '@/components/graph/SimpleValueGraph'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { AgentOrchestrator } from '@/components/agents/AgentOrchestrator'
import { MetricsDashboard } from '@/components/metrics/MetricsDashboard'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Brain, 
  Network, 
  BarChart3, 
  Users,
  Sparkles,
  TrendingUp,
  Target,
  DollarSign
} from 'lucide-react'

// Mock data for demonstration
const mockNodes = [
  {
    id: '1',
    type: 'hypothesis' as const,
    label: 'Supply Chain Optimization',
    value: 2300000,
    confidence: 0.85,
    status: 'active' as const
  },
  {
    id: '2',
    type: 'commitment' as const,
    label: 'Q1 Cost Reduction',
    value: 750000,
    confidence: 0.92,
    status: 'active' as const
  },
  {
    id: '3',
    type: 'realization' as const,
    label: 'Warehouse Automation',
    value: 450000,
    confidence: 0.78,
    status: 'achieved' as const
  },
  {
    id: '4',
    type: 'amplification' as const,
    label: 'EMEA Expansion',
    value: 4100000,
    confidence: 0.65,
    status: 'pending' as const
  },
  {
    id: '5',
    type: 'hypothesis' as const,
    label: 'Customer Onboarding',
    value: 1200000,
    confidence: 0.88,
    status: 'active' as const
  },
  {
    id: '6',
    type: 'commitment' as const,
    label: 'Time-to-Value Reduction',
    value: 500000,
    confidence: 0.75,
    status: 'at-risk' as const
  }
]

const mockEdges = [
  { source: '1', target: '2', type: 'causal' as const, strength: 0.9 },
  { source: '2', target: '3', type: 'dependency' as const, strength: 0.8 },
  { source: '3', target: '4', type: 'attribution' as const, strength: 0.7 },
  { source: '5', target: '6', type: 'causal' as const, strength: 0.85 },
  { source: '1', target: '5', type: 'dependency' as const, strength: 0.6 }
]

export default function WorkspacePage() {
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [activeView, setActiveView] = useState<'graph' | 'metrics' | 'agents'>('graph')
  const [userLevel, setUserLevel] = useState<'beginner' | 'intermediate' | 'expert'>('intermediate')

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      // Update mock data here for real-time effect
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const leftPanel = (
    <div className="h-full flex flex-col">
      {/* Agent Status Bar */}
      <div className="px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-500" />
            <span className="text-sm font-medium">Four-Agent Symphony</span>
          </div>
          <div className="flex gap-1">
            <Badge variant="outline" className="text-xs">
              <div className="w-2 h-2 rounded-full bg-green-500 mr-1 animate-pulse" />
              Architect
            </Badge>
            <Badge variant="outline" className="text-xs">
              <div className="w-2 h-2 rounded-full bg-blue-500 mr-1 animate-pulse" />
              Committer
            </Badge>
            <Badge variant="outline" className="text-xs">
              <div className="w-2 h-2 rounded-full bg-amber-500 mr-1" />
              Executor
            </Badge>
            <Badge variant="outline" className="text-xs">
              <div className="w-2 h-2 rounded-full bg-purple-500 mr-1" />
              Amplifier
            </Badge>
          </div>
        </div>
      </div>

      {/* Chat Panel */}
      <div className="flex-1 overflow-hidden">
        <ChatPanel 
          onNodeSelect={setSelectedNode}
          selectedNode={selectedNode}
          userLevel={userLevel}
        />
      </div>
    </div>
  )

  const rightPanel = (
    <div className="h-full flex flex-col">
      {/* View Tabs */}
      <div className="px-4 py-2 border-b border-slate-200 dark:border-slate-800">
        <Tabs value={activeView} onValueChange={(v: any) => setActiveView(v)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="graph" className="flex items-center gap-2">
              <Network className="w-4 h-4" />
              Value Graph
            </TabsTrigger>
            <TabsTrigger value="metrics" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Metrics
            </TabsTrigger>
            <TabsTrigger value="agents" className="flex items-center gap-2">
              <Brain className="w-4 h-4" />
              Agents
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden">
        {activeView === 'graph' && (
          <SimpleValueGraph
            nodes={mockNodes}
            edges={mockEdges}
            onNodeClick={setSelectedNode}
            onNodeHover={(node) => {
              // Handle hover
            }}
          />
        )}
        
        {activeView === 'metrics' && (
          <MetricsDashboard 
            nodes={mockNodes}
            userLevel={userLevel}
          />
        )}
        
        {activeView === 'agents' && (
          <AgentOrchestrator 
            onAgentAction={(action) => {
              console.log('Agent action:', action)
            }}
          />
        )}
      </div>

      {/* Quick Stats Bar */}
      <div className="px-4 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
        <div className="grid grid-cols-4 gap-4">
          <div className="flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-blue-600" />
            <div>
              <p className="text-xs text-slate-500">Pipeline</p>
              <p className="text-sm font-bold">$12.4M</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-green-600" />
            <div>
              <p className="text-xs text-slate-500">Realized</p>
              <p className="text-sm font-bold">$2.7M</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-amber-600" />
            <div>
              <p className="text-xs text-slate-500">Velocity</p>
              <p className="text-sm font-bold">+23%</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-purple-600" />
            <div>
              <p className="text-xs text-slate-500">Accounts</p>
              <p className="text-sm font-bold">47</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="h-screen flex flex-col bg-slate-50 dark:bg-slate-950">
      {/* Top Navigation */}
      <div className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            ValueVerse
          </h1>
          <Badge variant="secondary">Enterprise</Badge>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-500">Experience Level:</span>
          <div className="flex gap-1">
            <Button
              size="sm"
              variant={userLevel === 'beginner' ? 'default' : 'outline'}
              onClick={() => setUserLevel('beginner')}
            >
              Beginner
            </Button>
            <Button
              size="sm"
              variant={userLevel === 'intermediate' ? 'default' : 'outline'}
              onClick={() => setUserLevel('intermediate')}
            >
              Intermediate
            </Button>
            <Button
              size="sm"
              variant={userLevel === 'expert' ? 'default' : 'outline'}
              onClick={() => setUserLevel('expert')}
            >
              Expert
            </Button>
          </div>
        </div>
      </div>

      {/* Dual Brain Layout */}
      <div className="flex-1 overflow-hidden">
        <DualBrainLayout
          leftPanel={leftPanel}
          rightPanel={rightPanel}
        />
      </div>
    </div>
  )
}

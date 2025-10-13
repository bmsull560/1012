'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Users,
  Clock,
  AlertTriangle,
  CheckCircle,
  Activity,
  Zap
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

interface MetricsDashboardProps {
  nodes?: any[]
  userLevel: 'beginner' | 'intermediate' | 'expert'
}

export function MetricsDashboard({ nodes = [], userLevel }: MetricsDashboardProps) {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | '1y'>('30d')
  const [selectedMetric, setSelectedMetric] = useState<string>('revenue')

  // Mock data for charts
  const timeSeriesData = [
    { month: 'Jan', realized: 1200000, committed: 1500000, pipeline: 2000000 },
    { month: 'Feb', realized: 1400000, committed: 1700000, pipeline: 2300000 },
    { month: 'Mar', realized: 1650000, committed: 1900000, pipeline: 2500000 },
    { month: 'Apr', realized: 1900000, committed: 2100000, pipeline: 2800000 },
    { month: 'May', realized: 2100000, committed: 2400000, pipeline: 3200000 },
    { month: 'Jun', realized: 2300000, committed: 2700000, pipeline: 3500000 }
  ]

  const velocityData = [
    { week: 'W1', velocity: 65, target: 70 },
    { week: 'W2', velocity: 72, target: 70 },
    { week: 'W3', velocity: 78, target: 70 },
    { week: 'W4', velocity: 85, target: 70 },
    { week: 'W5', velocity: 82, target: 70 },
    { week: 'W6', velocity: 88, target: 70 }
  ]

  const stageDistribution = [
    { name: 'Hypothesis', value: 35, color: '#3B82F6' },
    { name: 'Commitment', value: 25, color: '#10B981' },
    { name: 'Realization', value: 30, color: '#F59E0B' },
    { name: 'Amplification', value: 10, color: '#8B5CF6' }
  ]

  const riskMatrix = [
    { subject: 'Timeline', A: 85, B: 90, fullMark: 100 },
    { subject: 'Budget', A: 78, B: 85, fullMark: 100 },
    { subject: 'Resources', A: 92, B: 88, fullMark: 100 },
    { subject: 'Stakeholder', A: 70, B: 75, fullMark: 100 },
    { subject: 'Technical', A: 88, B: 82, fullMark: 100 },
    { subject: 'Market', A: 65, B: 70, fullMark: 100 }
  ]

  const kpiCards = [
    {
      title: 'Total Pipeline Value',
      value: '$12.4M',
      change: '+23%',
      trend: 'up',
      icon: DollarSign,
      color: 'blue',
      description: 'Across 47 active accounts'
    },
    {
      title: 'Realized Value',
      value: '$2.7M',
      change: '+18%',
      trend: 'up',
      icon: CheckCircle,
      color: 'green',
      description: 'Q1 achievement rate: 117%'
    },
    {
      title: 'Value Velocity',
      value: '82%',
      change: '+5%',
      trend: 'up',
      icon: Zap,
      color: 'amber',
      description: 'Above target by 12 points'
    },
    {
      title: 'At-Risk Value',
      value: '$0.5M',
      change: '-8%',
      trend: 'down',
      icon: AlertTriangle,
      color: 'red',
      description: '2 accounts need attention'
    }
  ]

  const accountHealth = [
    { name: 'Acme Corp', health: 92, value: 3200000, status: 'healthy' },
    { name: 'TechGlobal', health: 78, value: 2100000, status: 'healthy' },
    { name: 'Innovate Inc', health: 65, value: 1800000, status: 'warning' },
    { name: 'FutureScale', health: 88, value: 2900000, status: 'healthy' },
    { name: 'DataDrive', health: 45, value: 500000, status: 'critical' }
  ]

  return (
    <div className="h-full overflow-auto p-6 space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        {kpiCards.map((kpi, index) => {
          const Icon = kpi.icon
          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium text-slate-600">
                      {kpi.title}
                    </CardTitle>
                    <div className={cn(
                      "p-2 rounded-lg",
                      kpi.color === 'blue' && "bg-blue-100 dark:bg-blue-900/50",
                      kpi.color === 'green' && "bg-green-100 dark:bg-green-900/50",
                      kpi.color === 'amber' && "bg-amber-100 dark:bg-amber-900/50",
                      kpi.color === 'red' && "bg-red-100 dark:bg-red-900/50"
                    )}>
                      <Icon className={cn(
                        "w-4 h-4",
                        kpi.color === 'blue' && "text-blue-600",
                        kpi.color === 'green' && "text-green-600",
                        kpi.color === 'amber' && "text-amber-600",
                        kpi.color === 'red' && "text-red-600"
                      )} />
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-bold">{kpi.value}</span>
                    <Badge variant={kpi.trend === 'up' ? 'default' : 'destructive'} className="text-xs">
                      {kpi.trend === 'up' ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                      {kpi.change}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{kpi.description}</p>
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-2 gap-6">
        {/* Value Pipeline Trend */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Value Pipeline Trend</CardTitle>
                <CardDescription>Realized vs Committed vs Pipeline</CardDescription>
              </div>
              <Tabs value={timeRange} onValueChange={(v: any) => setTimeRange(v)}>
                <TabsList className="h-8">
                  <TabsTrigger value="7d" className="text-xs">7D</TabsTrigger>
                  <TabsTrigger value="30d" className="text-xs">30D</TabsTrigger>
                  <TabsTrigger value="90d" className="text-xs">90D</TabsTrigger>
                  <TabsTrigger value="1y" className="text-xs">1Y</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={timeSeriesData}>
                <defs>
                  <linearGradient id="colorRealized" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0.1}/>
                  </linearGradient>
                  <linearGradient id="colorCommitted" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1}/>
                  </linearGradient>
                  <linearGradient id="colorPipeline" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="month" stroke="#6B7280" fontSize={12} />
                <YAxis stroke="#6B7280" fontSize={12} tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`} />
                <Tooltip 
                  formatter={(value: any) => `$${(value / 1000000).toFixed(2)}M`}
                  contentStyle={{ backgroundColor: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: '8px' }}
                />
                <Area type="monotone" dataKey="pipeline" stroke="#8B5CF6" fillOpacity={1} fill="url(#colorPipeline)" />
                <Area type="monotone" dataKey="committed" stroke="#3B82F6" fillOpacity={1} fill="url(#colorCommitted)" />
                <Area type="monotone" dataKey="realized" stroke="#10B981" fillOpacity={1} fill="url(#colorRealized)" />
                <Legend />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Value Velocity */}
        <Card>
          <CardHeader>
            <CardTitle>Value Velocity</CardTitle>
            <CardDescription>Speed of value realization vs target</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={velocityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="week" stroke="#6B7280" fontSize={12} />
                <YAxis stroke="#6B7280" fontSize={12} tickFormatter={(value) => `${value}%`} />
                <Tooltip 
                  formatter={(value: any) => `${value}%`}
                  contentStyle={{ backgroundColor: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: '8px' }}
                />
                <Line type="monotone" dataKey="velocity" stroke="#3B82F6" strokeWidth={2} dot={{ fill: '#3B82F6' }} />
                <Line type="monotone" dataKey="target" stroke="#EF4444" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                <Legend />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Stage Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Value Stage Distribution</CardTitle>
            <CardDescription>Current distribution across lifecycle stages</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={stageDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {stageDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Risk Assessment */}
        <Card>
          <CardHeader>
            <CardTitle>Risk Assessment Matrix</CardTitle>
            <CardDescription>Multi-dimensional risk analysis</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart data={riskMatrix}>
                <PolarGrid stroke="#E5E7EB" />
                <PolarAngleAxis dataKey="subject" stroke="#6B7280" fontSize={12} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#6B7280" fontSize={10} />
                <Radar name="Current" dataKey="A" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.6} />
                <Radar name="Target" dataKey="B" stroke="#10B981" fill="#10B981" fillOpacity={0.6} />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Account Health Table */}
      <Card>
        <CardHeader>
          <CardTitle>Account Health Monitor</CardTitle>
          <CardDescription>Real-time health scores across key accounts</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {accountHealth.map((account, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-800"
              >
                <div className="flex items-center gap-4">
                  <div className={cn(
                    "w-2 h-8 rounded-full",
                    account.status === 'healthy' && "bg-green-500",
                    account.status === 'warning' && "bg-amber-500",
                    account.status === 'critical' && "bg-red-500"
                  )} />
                  <div>
                    <p className="font-medium">{account.name}</p>
                    <p className="text-sm text-slate-500">
                      ${(account.value / 1000000).toFixed(1)}M value
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm font-medium">Health Score</p>
                    <p className={cn(
                      "text-lg font-bold",
                      account.health >= 80 && "text-green-600",
                      account.health >= 60 && account.health < 80 && "text-amber-600",
                      account.health < 60 && "text-red-600"
                    )}>
                      {account.health}%
                    </p>
                  </div>
                  <Progress value={account.health} className="w-24" />
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

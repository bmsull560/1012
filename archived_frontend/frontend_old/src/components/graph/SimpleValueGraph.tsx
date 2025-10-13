'use client'

import React, { useEffect, useRef } from 'react'
import { 
  DollarSign,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Target,
  Users,
  Zap,
  Network
} from 'lucide-react'

interface SimpleValueGraphProps {
  nodes?: any[]
  edges?: any[]
  onNodeClick?: (node: any) => void
  onNodeHover?: (node: any | null) => void
  className?: string
}

export function SimpleValueGraph({
  nodes = [],
  edges = [],
  onNodeClick,
  onNodeHover,
  className = ''
}: SimpleValueGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  // Mock data for display
  const defaultNodes = [
    { id: '1', label: 'Supply Chain', value: 2300000, status: 'active', x: 200, y: 150, type: 'hypothesis' },
    { id: '2', label: 'Q1 Cost Reduction', value: 750000, status: 'active', x: 400, y: 150, type: 'commitment' },
    { id: '3', label: 'Warehouse Auto', value: 450000, status: 'achieved', x: 600, y: 150, type: 'realization' },
    { id: '4', label: 'EMEA Expansion', value: 4100000, status: 'pending', x: 400, y: 300, type: 'amplification' },
    { id: '5', label: 'Customer Onboard', value: 1200000, status: 'active', x: 200, y: 300, type: 'hypothesis' },
    { id: '6', label: 'Time Reduction', value: 500000, status: 'at-risk', x: 600, y: 300, type: 'commitment' }
  ]

  const displayNodes = nodes.length > 0 ? nodes : defaultNodes

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'hypothesis': return 'from-blue-500 to-indigo-600'
      case 'commitment': return 'from-green-500 to-emerald-600'
      case 'realization': return 'from-amber-500 to-orange-600'
      case 'amplification': return 'from-purple-500 to-violet-600'
      default: return 'from-gray-500 to-gray-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'achieved': return <CheckCircle2 className="w-4 h-4 text-green-500" />
      case 'active': return <Zap className="w-4 h-4 text-blue-500" />
      case 'at-risk': return <AlertCircle className="w-4 h-4 text-red-500" />
      default: return <Target className="w-4 h-4 text-gray-500" />
    }
  }

  const totalValue = displayNodes.reduce((sum, node) => sum + (node.value || 0), 0)
  const achievedValue = displayNodes
    .filter(n => n.status === 'achieved')
    .reduce((sum, node) => sum + (node.value || 0), 0)
  const atRiskValue = displayNodes
    .filter(n => n.status === 'at-risk')
    .reduce((sum, node) => sum + (node.value || 0), 0)

  return (
    <div ref={containerRef} className={`relative w-full h-full bg-gradient-to-br from-slate-50 to-slate-100 ${className}`}>
      {/* SVG Canvas Replacement with HTML/CSS */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Connection Lines */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          <defs>
            <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#10B981" stopOpacity="0.3" />
            </linearGradient>
          </defs>
          {/* Draw simple connections */}
          <line x1="250" y1="150" x2="400" y2="150" stroke="url(#lineGradient)" strokeWidth="2" />
          <line x1="450" y1="150" x2="600" y2="150" stroke="url(#lineGradient)" strokeWidth="2" />
          <line x1="400" y1="200" x2="400" y2="250" stroke="url(#lineGradient)" strokeWidth="2" strokeDasharray="5,5" />
          <line x1="250" y1="300" x2="350" y2="300" stroke="url(#lineGradient)" strokeWidth="2" />
          <line x1="450" y1="300" x2="550" y2="300" stroke="url(#lineGradient)" strokeWidth="2" />
        </svg>

        {/* Nodes */}
        {displayNodes.map((node) => (
          <div
            key={node.id}
            className="absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-all hover:scale-110"
            style={{ left: `${node.x}px`, top: `${node.y}px` }}
            onClick={() => onNodeClick?.(node)}
            onMouseEnter={() => onNodeHover?.(node)}
            onMouseLeave={() => onNodeHover?.(null)}
          >
            <div className={`relative p-4 rounded-full bg-gradient-to-r ${getNodeColor(node.type)} shadow-lg hover:shadow-xl`}>
              <div className="absolute -top-2 -right-2 bg-white rounded-full p-1 shadow-md">
                {getStatusIcon(node.status)}
              </div>
              <div className="text-white text-center">
                <div className="text-xs font-bold">
                  ${(node.value / 1000000).toFixed(1)}M
                </div>
              </div>
            </div>
            <div className="mt-2 text-center">
              <div className="text-xs font-medium text-slate-700 bg-white/90 px-2 py-1 rounded shadow">
                {node.label}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2">
        <button className="p-2 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
          <Network className="w-5 h-5 text-slate-600" />
        </button>
      </div>

      {/* Value Summary */}
      <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur rounded-lg shadow-lg p-4">
        <div className="grid grid-cols-3 gap-4">
          <div className="flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-blue-600" />
            <div>
              <p className="text-xs text-slate-500">Total Value</p>
              <p className="text-sm font-bold text-slate-900">
                ${(totalValue / 1000000).toFixed(1)}M
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-600" />
            <div>
              <p className="text-xs text-slate-500">Achieved</p>
              <p className="text-sm font-bold text-green-600">
                ${(achievedValue / 1000000).toFixed(1)}M
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <div>
              <p className="text-xs text-slate-500">At Risk</p>
              <p className="text-sm font-bold text-red-600">
                ${(atRiskValue / 1000000).toFixed(1)}M
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute top-4 left-4 bg-white/95 backdrop-blur rounded-lg shadow-lg p-3">
        <p className="text-xs font-semibold text-slate-700 mb-2">Value Lifecycle</p>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600" />
            <span className="text-xs text-slate-600">Hypothesis</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gradient-to-r from-green-500 to-emerald-600" />
            <span className="text-xs text-slate-600">Commitment</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gradient-to-r from-amber-500 to-orange-600" />
            <span className="text-xs text-slate-600">Realization</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gradient-to-r from-purple-500 to-violet-600" />
            <span className="text-xs text-slate-600">Amplification</span>
          </div>
        </div>
      </div>

      {/* Center Message if no D3 */}
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
        <h3 className="text-lg font-semibold text-slate-700 mb-2">Living Value Graph</h3>
        <p className="text-sm text-slate-500">Interactive value visualization</p>
      </div>
    </div>
  )
}

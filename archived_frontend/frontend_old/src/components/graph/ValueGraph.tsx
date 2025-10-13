'use client'

import React, { useRef, useEffect, useState, useCallback } from 'react'
import * as d3 from 'd3'
import { motion } from 'framer-motion'
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize, 
  Target,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Clock,
  DollarSign
} from 'lucide-react'
import { cn } from '@/utils/cn'

interface ValueNode {
  id: string
  type: 'hypothesis' | 'commitment' | 'realization' | 'amplification'
  label: string
  value: number
  confidence: number
  status: 'pending' | 'active' | 'achieved' | 'at-risk'
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

interface ValueEdge {
  source: string
  target: string
  type: 'causal' | 'dependency' | 'attribution'
  strength: number
}

interface ValueGraphProps {
  nodes: ValueNode[]
  edges: ValueEdge[]
  onNodeClick?: (node: ValueNode) => void
  onNodeHover?: (node: ValueNode | null) => void
  className?: string
}

export function ValueGraph({
  nodes,
  edges,
  onNodeClick,
  onNodeHover,
  className
}: ValueGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)
  const [zoom, setZoom] = useState(1)

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect()
        setDimensions({ width, height })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  // D3 Force Simulation
  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const { width, height } = dimensions

    // Create zoom behavior
    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform.toString())
        setZoom(event.transform.k)
      })

    svg.call(zoomBehavior)

    // Create main group for zoom/pan
    const g = svg.append('g')

    // Create force simulation
    const simulation = d3.forceSimulation<ValueNode>(nodes)
      .force('link', d3.forceLink<ValueNode, ValueEdge>(edges)
        .id(d => d.id)
        .distance(d => 150 / d.strength)
        .strength(d => d.strength))
      .force('charge', d3.forceManyBody().strength(-500))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(50))

    // Create gradient definitions
    const defs = svg.append('defs')

    // Create gradients for each node type
    const gradients = [
      { id: 'hypothesis', colors: ['#3B82F6', '#6366F1'] },
      { id: 'commitment', colors: ['#10B981', '#059669'] },
      { id: 'realization', colors: ['#F59E0B', '#D97706'] },
      { id: 'amplification', colors: ['#8B5CF6', '#7C3AED'] }
    ]

    gradients.forEach(({ id, colors }) => {
      const gradient = defs.append('radialGradient')
        .attr('id', `gradient-${id}`)
        .attr('cx', '50%')
        .attr('cy', '50%')
        .attr('r', '50%')

      gradient.append('stop')
        .attr('offset', '0%')
        .attr('stop-color', colors[0])
        .attr('stop-opacity', 0.8)

      gradient.append('stop')
        .attr('offset', '100%')
        .attr('stop-color', colors[1])
        .attr('stop-opacity', 1)
    })

    // Create glow filter
    const filter = defs.append('filter')
      .attr('id', 'glow')
      .attr('x', '-50%')
      .attr('y', '-50%')
      .attr('width', '200%')
      .attr('height', '200%')

    filter.append('feGaussianBlur')
      .attr('stdDeviation', '4')
      .attr('result', 'coloredBlur')

    const feMerge = filter.append('feMerge')
    feMerge.append('feMergeNode').attr('in', 'coloredBlur')
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic')

    // Create links
    const link = g.append('g')
      .selectAll('line')
      .data(edges)
      .join('line')
      .attr('stroke', d => {
        switch (d.type) {
          case 'causal': return '#3B82F6'
          case 'dependency': return '#10B981'
          case 'attribution': return '#F59E0B'
          default: return '#94A3B8'
        }
      })
      .attr('stroke-opacity', d => 0.3 + d.strength * 0.4)
      .attr('stroke-width', d => 1 + d.strength * 3)
      .attr('stroke-dasharray', d => d.type === 'dependency' ? '5,5' : 'none')

    // Create node groups
    const nodeGroup = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(d3.drag<SVGGElement, ValueNode>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended))

    // Add circles for nodes
    nodeGroup.append('circle')
      .attr('r', d => 30 + Math.sqrt(d.value / 100000) * 10)
      .attr('fill', d => `url(#gradient-${d.type})`)
      .attr('stroke', d => {
        if (selectedNode === d.id) return '#1E293B'
        if (hoveredNode === d.id) return '#475569'
        return '#CBD5E1'
      })
      .attr('stroke-width', d => {
        if (selectedNode === d.id) return 3
        if (hoveredNode === d.id) return 2
        return 1
      })
      .attr('filter', d => (selectedNode === d.id || hoveredNode === d.id) ? 'url(#glow)' : 'none')

    // Add status indicator
    nodeGroup.append('circle')
      .attr('r', 8)
      .attr('cx', d => 20 + Math.sqrt(d.value / 100000) * 7)
      .attr('cy', d => -20 - Math.sqrt(d.value / 100000) * 7)
      .attr('fill', d => {
        switch (d.status) {
          case 'achieved': return '#10B981'
          case 'active': return '#3B82F6'
          case 'at-risk': return '#EF4444'
          default: return '#94A3B8'
        }
      })
      .attr('stroke', '#FFFFFF')
      .attr('stroke-width', 2)

    // Add value label
    nodeGroup.append('text')
      .text(d => `$${(d.value / 1000000).toFixed(1)}M`)
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', '#FFFFFF')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .attr('pointer-events', 'none')

    // Add node label
    nodeGroup.append('text')
      .text(d => d.label)
      .attr('text-anchor', 'middle')
      .attr('dy', d => 45 + Math.sqrt(d.value / 100000) * 10)
      .attr('fill', '#475569')
      .attr('font-size', '11px')
      .attr('pointer-events', 'none')

    // Add confidence arc
    nodeGroup.each(function(d) {
      const arc = d3.arc()
        .innerRadius(35 + Math.sqrt(d.value / 100000) * 10)
        .outerRadius(38 + Math.sqrt(d.value / 100000) * 10)
        .startAngle(0)
        .endAngle(Math.PI * 2 * d.confidence)

      d3.select(this).append('path')
        .attr('d', arc as any)
        .attr('fill', '#10B981')
        .attr('opacity', 0.6)
    })

    // Node interactions
    nodeGroup
      .on('click', (event, d) => {
        setSelectedNode(d.id)
        onNodeClick?.(d)
      })
      .on('mouseenter', (event, d) => {
        setHoveredNode(d.id)
        onNodeHover?.(d)
      })
      .on('mouseleave', () => {
        setHoveredNode(null)
        onNodeHover?.(null)
      })

    // Simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as any).x)
        .attr('y1', d => (d.source as any).y)
        .attr('x2', d => (d.target as any).x)
        .attr('y2', d => (d.target as any).y)

      nodeGroup.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    // Drag functions
    function dragstarted(event: any, d: ValueNode) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
    }

    function dragged(event: any, d: ValueNode) {
      d.fx = event.x
      d.fy = event.y
    }

    function dragended(event: any, d: ValueNode) {
      if (!event.active) simulation.alphaTarget(0)
      d.fx = null
      d.fy = null
    }

    // Center view button handler
    const centerView = () => {
      svg.transition()
        .duration(750)
        .call(zoomBehavior.transform, d3.zoomIdentity)
    }

    // Expose center function
    ;(window as any).centerValueGraph = centerView

    return () => {
      simulation.stop()
      delete (window as any).centerValueGraph
    }
  }, [nodes, edges, dimensions, selectedNode, hoveredNode, onNodeClick, onNodeHover])

  const handleZoomIn = () => {
    const svg = d3.select(svgRef.current)
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
      1.3
    )
  }

  const handleZoomOut = () => {
    const svg = d3.select(svgRef.current)
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
      0.7
    )
  }

  const handleCenterView = () => {
    ;(window as any).centerValueGraph?.()
  }

  // Calculate total value
  const totalValue = nodes.reduce((sum, node) => sum + node.value, 0)
  const atRiskValue = nodes
    .filter(n => n.status === 'at-risk')
    .reduce((sum, node) => sum + node.value, 0)
  const achievedValue = nodes
    .filter(n => n.status === 'achieved')
    .reduce((sum, node) => sum + node.value, 0)

  return (
    <div ref={containerRef} className={cn("relative w-full h-full", className)}>
      {/* SVG Canvas */}
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="w-full h-full"
        style={{ background: 'linear-gradient(to br, #F8FAFC, #F1F5F9)' }}
      />

      {/* Controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleZoomIn}
          className="p-2 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
          title="Zoom in"
        >
          <ZoomIn className="w-5 h-5 text-slate-600" />
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleZoomOut}
          className="p-2 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
          title="Zoom out"
        >
          <ZoomOut className="w-5 h-5 text-slate-600" />
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleCenterView}
          className="p-2 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
          title="Center view"
        >
          <Maximize className="w-5 h-5 text-slate-600" />
        </motion.button>
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

      {/* Zoom indicator */}
      <div className="absolute bottom-4 right-4 bg-white/95 backdrop-blur rounded-lg shadow-lg px-3 py-1">
        <p className="text-xs text-slate-600">
          Zoom: {Math.round(zoom * 100)}%
        </p>
      </div>
    </div>
  )
}

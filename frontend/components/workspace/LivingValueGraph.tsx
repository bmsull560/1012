"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import * as d3 from "d3";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Target,
  TrendingUp,
  DollarSign,
  Users,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  Link2,
  Plus,
  Minus,
  Maximize2,
  Filter,
  Layers,
  GitBranch,
  Activity
} from "lucide-react";
import { cn } from "@/lib/utils";

// Types for the Value Graph
interface GraphNode {
  id: string;
  type: "hypothesis" | "driver" | "outcome" | "kpi" | "risk" | "stakeholder";
  label: string;
  value?: number;
  confidence?: number;
  status?: "active" | "pending" | "achieved" | "at-risk";
  stage: "hypothesis" | "commitment" | "realization" | "amplification";
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface GraphEdge {
  source: string | GraphNode;
  target: string | GraphNode;
  type: "causal" | "dependency" | "attribution";
  strength: number;
  label?: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// Value Stage Colors
const STAGE_COLORS = {
  hypothesis: "#8b5cf6", // Purple
  commitment: "#3b82f6", // Blue
  realization: "#10b981", // Green
  amplification: "#f59e0b", // Orange
};

// Node Type Icons
const NODE_ICONS = {
  hypothesis: Target,
  driver: TrendingUp,
  outcome: CheckCircle,
  kpi: Activity,
  risk: AlertTriangle,
  stakeholder: Users,
};

interface LivingValueGraphProps {
  data?: GraphData;
  currentStage: "hypothesis" | "commitment" | "realization" | "amplification";
  onNodeClick?: (node: GraphNode) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
  editable?: boolean;
}

export function LivingValueGraph({
  data,
  currentStage = "hypothesis",
  onNodeClick,
  onEdgeClick,
  editable = false
}: LivingValueGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [viewMode, setViewMode] = useState<"temporal" | "causal" | "intelligence">("temporal");
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showLabels, setShowLabels] = useState(true);
  const [filterByStage, setFilterByStage] = useState<string>("all");

  // Sample data if none provided
  const graphData: GraphData = data || {
    nodes: [
      {
        id: "hyp1",
        type: "hypothesis",
        label: "25% Customer Retention Improvement",
        confidence: 0.85,
        stage: "hypothesis",
        status: "active"
      },
      {
        id: "driver1",
        type: "driver",
        label: "Predictive Analytics Implementation",
        value: 500000,
        stage: "hypothesis",
        status: "active"
      },
      {
        id: "driver2",
        type: "driver",
        label: "Customer Success Automation",
        value: 300000,
        stage: "hypothesis",
        status: "active"
      },
      {
        id: "outcome1",
        type: "outcome",
        label: "Reduced Churn Rate",
        value: 800000,
        stage: "commitment",
        status: "pending"
      },
      {
        id: "kpi1",
        type: "kpi",
        label: "Monthly Retention Rate",
        value: 0.92,
        stage: "realization",
        status: "active"
      },
      {
        id: "kpi2",
        type: "kpi",
        label: "Customer Lifetime Value",
        value: 45000,
        stage: "realization",
        status: "achieved"
      },
      {
        id: "risk1",
        type: "risk",
        label: "Implementation Complexity",
        confidence: 0.3,
        stage: "hypothesis",
        status: "at-risk"
      },
      {
        id: "stakeholder1",
        type: "stakeholder",
        label: "VP of Customer Success",
        stage: "commitment",
        status: "active"
      }
    ],
    edges: [
      { source: "hyp1", target: "driver1", type: "causal", strength: 0.9 },
      { source: "hyp1", target: "driver2", type: "causal", strength: 0.8 },
      { source: "driver1", target: "outcome1", type: "causal", strength: 0.85 },
      { source: "driver2", target: "outcome1", type: "causal", strength: 0.75 },
      { source: "outcome1", target: "kpi1", type: "attribution", strength: 0.9 },
      { source: "outcome1", target: "kpi2", type: "attribution", strength: 0.8 },
      { source: "driver1", target: "risk1", type: "dependency", strength: 0.6 },
      { source: "stakeholder1", target: "outcome1", type: "dependency", strength: 0.7 }
    ]
  };

  // Filter nodes based on selected stage
  const filteredData = useCallback(() => {
    if (filterByStage === "all") return graphData;
    
    const filteredNodes = graphData.nodes.filter(n => n.stage === filterByStage);
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = graphData.edges.filter(e => {
      const sourceId = typeof e.source === "string" ? e.source : e.source.id;
      const targetId = typeof e.target === "string" ? e.target : e.target.id;
      return nodeIds.has(sourceId) && nodeIds.has(targetId);
    });
    
    return { nodes: filteredNodes, edges: filteredEdges };
  }, [graphData, filterByStage]);

  // Initialize D3 Force Simulation
  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    // Clear previous content
    svg.selectAll("*").remove();

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 3])
      .on("zoom", (event) => {
        setZoomLevel(event.transform.k);
        g.attr("transform", event.transform.toString());
      });

    svg.call(zoom);

    // Create main group
    const g = svg.append("g");

    // Create arrow markers for directed edges
    svg.append("defs").selectAll("marker")
      .data(["causal", "dependency", "attribution"])
      .enter().append("marker")
      .attr("id", d => `arrow-${d}`)
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 25)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", d => {
        switch(d) {
          case "causal": return "#3b82f6";
          case "dependency": return "#f59e0b";
          case "attribution": return "#10b981";
          default: return "#94a3b8";
        }
      });

    const currentData = filteredData();

    // Create force simulation
    const simulation = d3.forceSimulation<GraphNode>(currentData.nodes)
      .force("link", d3.forceLink<GraphNode, GraphEdge>(currentData.edges)
        .id(d => d.id)
        .distance(d => 100 / d.strength))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(40));

    // Create edges
    const link = g.append("g")
      .selectAll("line")
      .data(currentData.edges)
      .enter().append("line")
      .attr("stroke", d => {
        switch(d.type) {
          case "causal": return "#3b82f6";
          case "dependency": return "#f59e0b";
          case "attribution": return "#10b981";
          default: return "#94a3b8";
        }
      })
      .attr("stroke-width", d => d.strength * 3)
      .attr("stroke-opacity", 0.6)
      .attr("marker-end", d => `url(#arrow-${d.type})`)
      .style("cursor", "pointer")
      .on("click", (event, d) => {
        setSelectedEdge(d);
        onEdgeClick?.(d);
      });

    // Create edge labels
    if (showLabels) {
      const linkLabel = g.append("g")
        .selectAll("text")
        .data(currentData.edges)
        .enter().append("text")
        .attr("font-size", "10px")
        .attr("fill", "#64748b")
        .text(d => d.label || d.type);
    }

    // Create nodes
    const node = g.append("g")
      .selectAll("g")
      .data(currentData.nodes)
      .enter().append("g")
      .style("cursor", editable ? "move" : "pointer")
      .call(d3.drag<SVGGElement, GraphNode>()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    // Add circles for nodes
    node.append("circle")
      .attr("r", d => {
        switch(d.type) {
          case "hypothesis": return 25;
          case "outcome": return 20;
          case "driver": return 18;
          default: return 15;
        }
      })
      .attr("fill", d => STAGE_COLORS[d.stage])
      .attr("fill-opacity", d => d.confidence || 0.8)
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);

    // Add status indicator
    node.append("circle")
      .attr("r", 4)
      .attr("cx", 15)
      .attr("cy", -15)
      .attr("fill", d => {
        switch(d.status) {
          case "active": return "#10b981";
          case "achieved": return "#3b82f6";
          case "at-risk": return "#ef4444";
          case "pending": return "#f59e0b";
          default: return "#94a3b8";
        }
      });

    // Add labels
    if (showLabels) {
      node.append("text")
        .attr("dy", 35)
        .attr("text-anchor", "middle")
        .attr("font-size", "12px")
        .attr("fill", "#1e293b")
        .text(d => d.label)
        .each(function(d) {
          const text = d3.select(this);
          const words = d.label.split(/\s+/);
          if (words.length > 3) {
            text.text(words.slice(0, 3).join(" ") + "...");
          }
        });
    }

    // Add click handler
    node.on("click", (event, d) => {
      setSelectedNode(d);
      onNodeClick?.(d);
    });

    // Update positions on simulation tick
    simulation.on("tick", () => {
      link
        .attr("x1", d => (d.source as GraphNode).x!)
        .attr("y1", d => (d.source as GraphNode).y!)
        .attr("x2", d => (d.target as GraphNode).x!)
        .attr("y2", d => (d.target as GraphNode).y!);

      node.attr("transform", d => `translate(${d.x},${d.y})`);

      if (showLabels) {
        g.selectAll("text")
          .attr("x", d => {
            if ((d as GraphEdge).source) {
              const edge = d as GraphEdge;
              return ((edge.source as GraphNode).x! + (edge.target as GraphNode).x!) / 2;
            }
            return 0;
          })
          .attr("y", d => {
            if ((d as GraphEdge).source) {
              const edge = d as GraphEdge;
              return ((edge.source as GraphNode).y! + (edge.target as GraphNode).y!) / 2;
            }
            return 0;
          });
      }
    });

    // Drag functions
    function dragstarted(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) {
      if (!event.active) simulation.alphaTarget(0);
      if (!editable) {
        d.fx = null;
        d.fy = null;
      }
    }

    return () => {
      simulation.stop();
    };
  }, [filteredData, showLabels, editable, onNodeClick, onEdgeClick]);

  return (
    <div className="relative w-full h-full bg-white rounded-lg border">
      {/* Graph Controls */}
      <div className="absolute top-4 left-4 right-4 z-10 flex justify-between">
        {/* View Mode Selector */}
        <Card className="bg-white/95 backdrop-blur">
          <CardContent className="p-2">
            <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as any)}>
              <TabsList className="grid grid-cols-3 w-[300px]">
                <TabsTrigger value="temporal">
                  <Clock className="w-4 h-4 mr-2" />
                  Temporal
                </TabsTrigger>
                <TabsTrigger value="causal">
                  <GitBranch className="w-4 h-4 mr-2" />
                  Causal
                </TabsTrigger>
                <TabsTrigger value="intelligence">
                  <Layers className="w-4 h-4 mr-2" />
                  Intelligence
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </CardContent>
        </Card>

        {/* Zoom and Filter Controls */}
        <div className="flex gap-2">
          {/* Stage Filter */}
          <Card className="bg-white/95 backdrop-blur">
            <CardContent className="p-2">
              <Select value={filterByStage} onValueChange={setFilterByStage}>
                <SelectTrigger className="w-[150px]">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Stages</SelectItem>
                  <SelectItem value="hypothesis">Hypothesis</SelectItem>
                  <SelectItem value="commitment">Commitment</SelectItem>
                  <SelectItem value="realization">Realization</SelectItem>
                  <SelectItem value="amplification">Amplification</SelectItem>
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          {/* Zoom Controls */}
          <Card className="bg-white/95 backdrop-blur">
            <CardContent className="p-2 flex items-center gap-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setZoomLevel(Math.max(0.5, zoomLevel - 0.2))}
              >
                <Minus className="w-4 h-4" />
              </Button>
              <span className="text-sm font-medium w-12 text-center">
                {Math.round(zoomLevel * 100)}%
              </span>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setZoomLevel(Math.min(3, zoomLevel + 0.2))}
              >
                <Plus className="w-4 h-4" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setZoomLevel(1)}
              >
                <Maximize2 className="w-4 h-4" />
              </Button>
            </CardContent>
          </Card>

          {/* Label Toggle */}
          <Card className="bg-white/95 backdrop-blur">
            <CardContent className="p-2">
              <Button
                size="sm"
                variant={showLabels ? "default" : "ghost"}
                onClick={() => setShowLabels(!showLabels)}
              >
                Labels
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* SVG Canvas */}
      <svg
        ref={svgRef}
        className="w-full h-full"
        style={{ minHeight: "600px" }}
      />

      {/* Node/Edge Details Panel */}
      <AnimatePresence>
        {(selectedNode || selectedEdge) && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="absolute bottom-4 right-4 w-80"
          >
            <Card className="bg-white/95 backdrop-blur shadow-lg">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center justify-between">
                  {selectedNode ? "Node Details" : "Edge Details"}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setSelectedNode(null);
                      setSelectedEdge(null);
                    }}
                  >
                    ×
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {selectedNode && (
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs text-slate-500">Type</label>
                      <div className="flex items-center gap-2 mt-1">
                        {React.createElement(NODE_ICONS[selectedNode.type], {
                          className: "w-4 h-4"
                        })}
                        <span className="text-sm font-medium capitalize">
                          {selectedNode.type}
                        </span>
                      </div>
                    </div>
                    
                    <div>
                      <label className="text-xs text-slate-500">Label</label>
                      <p className="text-sm font-medium">{selectedNode.label}</p>
                    </div>
                    
                    {selectedNode.value && (
                      <div>
                        <label className="text-xs text-slate-500">Value</label>
                        <p className="text-sm font-medium">
                          {selectedNode.type === "kpi" 
                            ? selectedNode.value.toFixed(2)
                            : `$${(selectedNode.value / 1000).toFixed(0)}K`}
                        </p>
                      </div>
                    )}
                    
                    {selectedNode.confidence && (
                      <div>
                        <label className="text-xs text-slate-500">Confidence</label>
                        <div className="flex items-center gap-2 mt-1">
                          <div className="flex-1 bg-slate-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${selectedNode.confidence * 100}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium">
                            {(selectedNode.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    )}
                    
                    <div>
                      <label className="text-xs text-slate-500">Stage</label>
                      <Badge
                        className="mt-1"
                        style={{ backgroundColor: STAGE_COLORS[selectedNode.stage] }}
                      >
                        {selectedNode.stage}
                      </Badge>
                    </div>
                    
                    {selectedNode.status && (
                      <div>
                        <label className="text-xs text-slate-500">Status</label>
                        <Badge
                          variant={
                            selectedNode.status === "achieved" ? "default" :
                            selectedNode.status === "at-risk" ? "destructive" :
                            "secondary"
                          }
                          className="mt-1"
                        >
                          {selectedNode.status}
                        </Badge>
                      </div>
                    )}
                  </div>
                )}
                
                {selectedEdge && (
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs text-slate-500">Relationship Type</label>
                      <Badge className="mt-1 capitalize">
                        {selectedEdge.type}
                      </Badge>
                    </div>
                    
                    <div>
                      <label className="text-xs text-slate-500">Strength</label>
                      <div className="flex items-center gap-2 mt-1">
                        <div className="flex-1 bg-slate-200 rounded-full h-2">
                          <div
                            className="bg-green-600 h-2 rounded-full"
                            style={{ width: `${selectedEdge.strength * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">
                          {(selectedEdge.strength * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    
                    {selectedEdge.label && (
                      <div>
                        <label className="text-xs text-slate-500">Description</label>
                        <p className="text-sm">{selectedEdge.label}</p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Stage Timeline */}
      <div className="absolute bottom-4 left-4 z-10">
        <Card className="bg-white/95 backdrop-blur">
          <CardContent className="p-3">
            <div className="flex items-center gap-2">
              {["hypothesis", "commitment", "realization", "amplification"].map((stage, index) => (
                <React.Fragment key={stage}>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <div
                          className={cn(
                            "w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold transition-all",
                            currentStage === stage ? "scale-110 ring-2 ring-offset-2" : "opacity-60"
                          )}
                          style={{ 
                            backgroundColor: STAGE_COLORS[stage as keyof typeof STAGE_COLORS],
                            ringColor: currentStage === stage ? STAGE_COLORS[stage as keyof typeof STAGE_COLORS] : undefined
                          }}
                        >
                          {index + 1}
                        </div>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="capitalize">{stage}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                  {index < 3 && (
                    <div className={cn(
                      "w-12 h-0.5 bg-slate-300",
                      index === 0 && currentStage !== "hypothesis" && "bg-green-500",
                      index === 1 && ["realization", "amplification"].includes(currentStage) && "bg-green-500",
                      index === 2 && currentStage === "amplification" && "bg-green-500"
                    )} />
                  )}
                </React.Fragment>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

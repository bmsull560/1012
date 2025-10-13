"use client";

import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  TrendingUp, 
  DollarSign, 
  Target, 
  AlertTriangle,
  Plus,
  Minus,
  Edit3,
  Save,
  X
} from "lucide-react";
import { cn } from "@/lib/utils";

interface ValueDriver {
  id: string;
  name: string;
  category: string;
  currentValue: number;
  targetValue: number;
  impact: number;
  confidence: number;
  dependencies: string[];
}

interface CanvasComponent {
  id: string;
  type: "value_driver" | "metric" | "chart" | "narrative";
  position: { x: number; y: number };
  size: { width: number; height: number };
  data: any;
}

interface ValueCanvasProps {
  mode: "view" | "edit";
  template: string;
  components: CanvasComponent[];
  onUpdate: (components: CanvasComponent[]) => void;
}

export function ValueCanvas({ mode, template, components, onUpdate }: ValueCanvasProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedComponent, setSelectedComponent] = useState<string | null>(null);
  const [editingComponent, setEditingComponent] = useState<string | null>(null);
  const [draggedComponent, setDraggedComponent] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);

  // Initialize D3 canvas
  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    // Clear previous content
    svg.selectAll("*").remove();

    // Create zoom behavior
    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 2])
      .on("zoom", (event) => {
        setZoom(event.transform.k);
        svg.select(".canvas-content")
          .attr("transform", event.transform.toString());
      });

    svg.call(zoomBehavior);

    // Create main group for content
    const g = svg.append("g").attr("class", "canvas-content");

    // Add grid pattern
    const gridSize = 20;
    const grid = g.append("g").attr("class", "grid");
    
    // Vertical lines
    for (let x = 0; x <= width; x += gridSize) {
      grid.append("line")
        .attr("x1", x)
        .attr("y1", 0)
        .attr("x2", x)
        .attr("y2", height)
        .attr("stroke", "#e2e8f0")
        .attr("stroke-width", 0.5);
    }
    
    // Horizontal lines
    for (let y = 0; y <= height; y += gridSize) {
      grid.append("line")
        .attr("x1", 0)
        .attr("y1", y)
        .attr("x2", width)
        .attr("y2", y)
        .attr("stroke", "#e2e8f0")
        .attr("stroke-width", 0.5);
    }

    // Draw connections between components
    const connections = g.append("g").attr("class", "connections");
    
    components.forEach((component) => {
      if (component.data?.dependencies) {
        component.data.dependencies.forEach((depId: string) => {
          const target = components.find(c => c.id === depId);
          if (target) {
            connections.append("path")
              .attr("d", `M ${component.position.x + component.size.width/2} ${component.position.y + component.size.height/2} 
                          L ${target.position.x + target.size.width/2} ${target.position.y + target.size.height/2}`)
              .attr("stroke", "#94a3b8")
              .attr("stroke-width", 2)
              .attr("stroke-dasharray", "5,5")
              .attr("fill", "none")
              .attr("opacity", 0.5);
          }
        });
      }
    });

  }, [components, mode]);

  // Render template-specific layout
  const renderTemplate = () => {
    switch (template) {
      case "impact_cascade":
        return <ImpactCascadeTemplate components={components} onUpdate={onUpdate} mode={mode} />;
      case "trinity_dashboard":
        return <TrinityDashboardTemplate components={components} onUpdate={onUpdate} mode={mode} />;
      case "scenario_matrix":
        return <ScenarioMatrixTemplate components={components} onUpdate={onUpdate} mode={mode} />;
      default:
        return <DefaultTemplate components={components} onUpdate={onUpdate} mode={mode} />;
    }
  };

  return (
    <div className="relative w-full h-full bg-white rounded-lg border">
      {/* Canvas Controls */}
      <div className="absolute top-4 right-4 z-10 flex gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => setZoom(zoom * 1.2)}
        >
          <Plus className="w-4 h-4" />
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => setZoom(zoom * 0.8)}
        >
          <Minus className="w-4 h-4" />
        </Button>
        <Badge variant="secondary">
          {Math.round(zoom * 100)}%
        </Badge>
      </div>

      {/* SVG Canvas */}
      <svg
        ref={svgRef}
        className="w-full h-full"
        style={{ minHeight: "600px" }}
      />

      {/* Template-specific overlay */}
      <div className="absolute inset-0 pointer-events-none">
        {renderTemplate()}
      </div>
    </div>
  );
}

// Impact Cascade Template
function ImpactCascadeTemplate({ components, onUpdate, mode }: any) {
  const valueDrivers = components.filter((c: CanvasComponent) => c.type === "value_driver");
  
  return (
    <div className="p-6 pointer-events-auto">
      <h3 className="text-lg font-semibold mb-4">Value Impact Cascade</h3>
      
      <div className="space-y-4">
        {valueDrivers.map((driver: CanvasComponent, index: number) => (
          <motion.div
            key={driver.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium">
                    {driver.data.name}
                  </CardTitle>
                  <Badge variant={driver.data.confidence > 0.7 ? "default" : "secondary"}>
                    {(driver.data.confidence * 100).toFixed(0)}% confidence
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">Impact</span>
                    <span className="font-semibold text-green-600">
                      +${(driver.data.impact / 1000).toFixed(0)}K
                    </span>
                  </div>
                  
                  <Progress value={driver.data.confidence * 100} className="h-2" />
                  
                  {mode === "edit" && (
                    <div className="pt-2">
                      <label className="text-xs text-slate-500">Adjust Impact</label>
                      <Slider
                        value={[driver.data.impact]}
                        onValueChange={([value]) => {
                          const updated = components.map((c: CanvasComponent) =>
                            c.id === driver.id
                              ? { ...c, data: { ...c.data, impact: value } }
                              : c
                          );
                          onUpdate(updated);
                        }}
                        max={1000000}
                        step={10000}
                        className="mt-1"
                      />
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
      
      {/* Total Impact */}
      <Card className="mt-6 bg-gradient-to-r from-blue-50 to-purple-50">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Total Value Impact</p>
              <p className="text-3xl font-bold text-slate-900">
                ${(valueDrivers.reduce((sum: number, d: CanvasComponent) => sum + d.data.impact, 0) / 1000000).toFixed(1)}M
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-blue-600" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Trinity Dashboard Template
function TrinityDashboardTemplate({ components, onUpdate, mode }: any) {
  const metrics = {
    revenue: components.find((c: CanvasComponent) => c.data?.category === "revenue"),
    cost: components.find((c: CanvasComponent) => c.data?.category === "cost"),
    risk: components.find((c: CanvasComponent) => c.data?.category === "risk")
  };

  return (
    <div className="p-6 pointer-events-auto">
      <h3 className="text-lg font-semibold mb-4">Trinity Dashboard</h3>
      
      <div className="grid grid-cols-3 gap-4">
        {/* Revenue Pillar */}
        <Card className="border-green-200 bg-green-50/50">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-green-600" />
              Revenue Impact
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-700">
              +${metrics.revenue?.data?.impact ? (metrics.revenue.data.impact / 1000).toFixed(0) : "0"}K
            </div>
            <p className="text-xs text-green-600 mt-2">
              Annual recurring revenue increase
            </p>
          </CardContent>
        </Card>

        {/* Cost Pillar */}
        <Card className="border-blue-200 bg-blue-50/50">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-blue-600" />
              Cost Savings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-700">
              ${metrics.cost?.data?.impact ? (metrics.cost.data.impact / 1000).toFixed(0) : "0"}K
            </div>
            <p className="text-xs text-blue-600 mt-2">
              Operational cost reduction
            </p>
          </CardContent>
        </Card>

        {/* Risk Pillar */}
        <Card className="border-orange-200 bg-orange-50/50">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-orange-600" />
              Risk Mitigation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-700">
              {metrics.risk?.data?.impact ? metrics.risk.data.impact : "0"}%
            </div>
            <p className="text-xs text-orange-600 mt-2">
              Compliance risk reduction
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Combined ROI */}
      <Card className="mt-6">
        <CardContent className="pt-6">
          <div className="text-center">
            <p className="text-sm text-slate-600 mb-2">Combined 3-Year ROI</p>
            <p className="text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              247%
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Scenario Matrix Template
function ScenarioMatrixTemplate({ components, onUpdate, mode }: any) {
  const scenarios = [
    { name: "Conservative", multiplier: 0.7, color: "blue" },
    { name: "Realistic", multiplier: 1.0, color: "green" },
    { name: "Optimistic", multiplier: 1.3, color: "purple" }
  ];

  return (
    <div className="p-6 pointer-events-auto">
      <h3 className="text-lg font-semibold mb-4">Scenario Analysis</h3>
      
      <div className="space-y-4">
        {scenarios.map((scenario) => (
          <Card key={scenario.name}>
            <CardHeader>
              <CardTitle className="text-sm">{scenario.name} Scenario</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-slate-500">Year 1</p>
                  <p className="font-semibold">
                    ${(250000 * scenario.multiplier / 1000).toFixed(0)}K
                  </p>
                </div>
                <div>
                  <p className="text-slate-500">Year 2</p>
                  <p className="font-semibold">
                    ${(500000 * scenario.multiplier / 1000).toFixed(0)}K
                  </p>
                </div>
                <div>
                  <p className="text-slate-500">Year 3</p>
                  <p className="font-semibold">
                    ${(750000 * scenario.multiplier / 1000).toFixed(0)}K
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Default Template
function DefaultTemplate({ components, onUpdate, mode }: any) {
  return (
    <div className="p-6 pointer-events-auto">
      <h3 className="text-lg font-semibold mb-4">Value Model</h3>
      <p className="text-sm text-slate-600">
        Select a template to visualize your value model
      </p>
    </div>
  );
}

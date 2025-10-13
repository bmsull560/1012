"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Code,
  FileText,
  BarChart3,
  Table,
  Calculator,
  Lightbulb,
  ChevronDown,
  ChevronRight,
  Copy,
  Download,
  Share2,
  Maximize2,
  Edit3,
  Check,
  AlertCircle,
  TrendingUp,
  DollarSign,
  Users,
  Target,
  Sparkles,
  Brain,
  Layers,
  GitBranch,
  Clock,
  RefreshCw,
  BookOpen,
  MessageSquare,
  FileSpreadsheet,
  PieChart,
  LineChart,
  Briefcase,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

// Artifact Types - Similar to Claude's structured outputs
type ArtifactType = 
  | "value-model"
  | "roi-analysis" 
  | "contract-terms"
  | "implementation-plan"
  | "progress-report"
  | "executive-summary"
  | "formula"
  | "data-table"
  | "visualization"
  | "document"
  | "code";

interface Artifact {
  id: string;
  type: ArtifactType;
  title: string;
  description?: string;
  agent: string;
  timestamp: Date;
  version: number;
  status: "draft" | "final" | "approved";
  content: any;
  metadata?: {
    confidence?: number;
    sources?: string[];
    dependencies?: string[];
    tags?: string[];
  };
}

// Component Registry - Different component types for different artifacts
const ARTIFACT_COMPONENTS = {
  "value-model": ValueModelArtifact,
  "roi-analysis": ROIAnalysisArtifact,
  "contract-terms": ContractTermsArtifact,
  "implementation-plan": ImplementationPlanArtifact,
  "progress-report": ProgressReportArtifact,
  "executive-summary": ExecutiveSummaryArtifact,
  "formula": FormulaArtifact,
  "data-table": DataTableArtifact,
  "visualization": VisualizationArtifact,
  "document": DocumentArtifact,
  "code": CodeArtifact,
};

// Main Agent Artifacts Container
export function AgentArtifacts() {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);
  const [viewMode, setViewMode] = useState<"grid" | "list" | "timeline">("grid");
  const [filterAgent, setFilterAgent] = useState<string>("all");
  const [isGenerating, setIsGenerating] = useState(false);

  // Simulate agent generating artifacts
  useEffect(() => {
    // Sample artifacts
    const sampleArtifacts: Artifact[] = [
      {
        id: "1",
        type: "value-model",
        title: "TechCorp Value Realization Model",
        description: "Comprehensive value model with 5 key drivers",
        agent: "ValueArchitect",
        timestamp: new Date(),
        version: 1,
        status: "final",
        content: {
          company: "TechCorp Solutions",
          totalValue: 2300000,
          confidence: 0.85,
          drivers: [
            { name: "Customer Retention", impact: 750000, confidence: 0.9 },
            { name: "Operational Efficiency", impact: 500000, confidence: 0.85 },
            { name: "Revenue Growth", impact: 650000, confidence: 0.8 },
            { name: "Cost Reduction", impact: 400000, confidence: 0.88 },
          ],
          timeline: "6-9 months",
          investment: 580000,
        },
        metadata: {
          confidence: 0.85,
          sources: ["Industry benchmarks", "Historical patterns", "Peer analysis"],
          tags: ["SaaS", "Mid-Market", "High-Priority"],
        },
      },
      {
        id: "2",
        type: "roi-analysis",
        title: "3-Year ROI Projection",
        description: "Detailed ROI analysis with scenario modeling",
        agent: "ValueArchitect",
        timestamp: new Date(),
        version: 1,
        status: "draft",
        content: {
          scenarios: {
            conservative: { roi: 185, payback: 11 },
            realistic: { roi: 285, payback: 8 },
            optimistic: { roi: 385, payback: 6 },
          },
          yearlyBreakdown: [
            { year: 1, value: 650000, cost: 380000 },
            { year: 2, value: 920000, cost: 150000 },
            { year: 3, value: 730000, cost: 50000 },
          ],
        },
      },
      {
        id: "3",
        type: "executive-summary",
        title: "Executive Value Proposition",
        description: "C-suite ready presentation points",
        agent: "ValueCommitter",
        timestamp: new Date(),
        version: 2,
        status: "approved",
        content: {
          headline: "25% Revenue Growth Through Digital Transformation",
          keyPoints: [
            "Proven ROI of 285% over 3 years",
            "Payback period under 8 months",
            "Risk mitigation through phased approach",
            "Success with 3 similar companies",
          ],
          callToAction: "Secure competitive advantage before Q2",
        },
      },
    ];

    setArtifacts(sampleArtifacts);
    setSelectedArtifact(sampleArtifacts[0]);
  }, []);

  const handleGenerateArtifact = async (type: ArtifactType) => {
    setIsGenerating(true);
    // Simulate generation
    setTimeout(() => {
      setIsGenerating(false);
      // Add new artifact
    }, 2000);
  };

  return (
    <div className="flex h-full">
      {/* Left Panel - Artifact List */}
      <div className="w-80 border-r bg-slate-50 flex flex-col">
        <div className="p-4 border-b bg-white">
          <h3 className="font-semibold text-sm mb-3">Agent Artifacts</h3>
          
          {/* View Mode Selector */}
          <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as any)}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="grid">
                <Layers className="w-3 h-3" />
              </TabsTrigger>
              <TabsTrigger value="list">
                <FileText className="w-3 h-3" />
              </TabsTrigger>
              <TabsTrigger value="timeline">
                <Clock className="w-3 h-3" />
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <ScrollArea className="flex-1 p-4">
          <div className="space-y-2">
            {artifacts.map((artifact) => (
              <ArtifactCard
                key={artifact.id}
                artifact={artifact}
                isSelected={selectedArtifact?.id === artifact.id}
                onClick={() => setSelectedArtifact(artifact)}
                viewMode={viewMode}
              />
            ))}
          </div>
        </ScrollArea>

        {/* Quick Generate Actions */}
        <div className="p-4 border-t bg-white">
          <Button
            className="w-full"
            onClick={() => handleGenerateArtifact("value-model")}
            disabled={isGenerating}
          >
            {isGenerating ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Generate New Artifact
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Right Panel - Artifact Viewer */}
      <div className="flex-1 flex flex-col bg-white">
        {selectedArtifact ? (
          <>
            {/* Artifact Header */}
            <div className="border-b px-6 py-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="outline">{selectedArtifact.type}</Badge>
                    <Badge 
                      variant={
                        selectedArtifact.status === "approved" ? "default" :
                        selectedArtifact.status === "final" ? "secondary" :
                        "outline"
                      }
                    >
                      {selectedArtifact.status}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      v{selectedArtifact.version}
                    </span>
                  </div>
                  <h2 className="text-xl font-semibold">{selectedArtifact.title}</h2>
                  {selectedArtifact.description && (
                    <p className="text-sm text-muted-foreground mt-1">
                      {selectedArtifact.description}
                    </p>
                  )}
                  <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Brain className="w-3 h-3" />
                      {selectedArtifact.agent}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(selectedArtifact.timestamp).toLocaleString()}
                    </span>
                    {selectedArtifact.metadata?.confidence && (
                      <span className="flex items-center gap-1">
                        <Target className="w-3 h-3" />
                        {(selectedArtifact.metadata.confidence * 100).toFixed(0)}% confidence
                      </span>
                    )}
                  </div>
                </div>

                {/* Artifact Actions */}
                <div className="flex items-center gap-2">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <Edit3 className="w-4 h-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Edit</TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                  
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <Copy className="w-4 h-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Copy</TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                  
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <Download className="w-4 h-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Export</TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                  
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <Share2 className="w-4 h-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Share</TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                  
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <Maximize2 className="w-4 h-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Fullscreen</TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
              </div>
            </div>

            {/* Artifact Content */}
            <ScrollArea className="flex-1 p-6">
              <ArtifactRenderer artifact={selectedArtifact} />
            </ScrollArea>

            {/* Metadata Footer */}
            {selectedArtifact.metadata && (
              <div className="border-t px-6 py-3 bg-slate-50">
                <div className="flex items-center gap-6 text-xs">
                  {selectedArtifact.metadata.sources && (
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-3 h-3 text-muted-foreground" />
                      <span className="text-muted-foreground">Sources:</span>
                      <div className="flex gap-1">
                        {selectedArtifact.metadata.sources.map((source, i) => (
                          <Badge key={i} variant="secondary" className="text-xs">
                            {source}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {selectedArtifact.metadata.tags && (
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">Tags:</span>
                      <div className="flex gap-1">
                        {selectedArtifact.metadata.tags.map((tag, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Layers className="w-12 h-12 mx-auto mb-4 opacity-20" />
              <p>Select an artifact to view</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Artifact Card Component
function ArtifactCard({ 
  artifact, 
  isSelected, 
  onClick, 
  viewMode 
}: {
  artifact: Artifact;
  isSelected: boolean;
  onClick: () => void;
  viewMode: string;
}) {
  const getIcon = () => {
    switch (artifact.type) {
      case "value-model": return Target;
      case "roi-analysis": return TrendingUp;
      case "contract-terms": return FileText;
      case "implementation-plan": return GitBranch;
      case "progress-report": return BarChart3;
      case "executive-summary": return Briefcase;
      case "formula": return Calculator;
      case "data-table": return Table;
      case "visualization": return PieChart;
      case "document": return FileText;
      case "code": return Code;
      default: return FileText;
    }
  };

  const Icon = getIcon();

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <Card
        className={cn(
          "cursor-pointer transition-all",
          isSelected && "ring-2 ring-primary bg-primary/5"
        )}
        onClick={onClick}
      >
        <CardContent className="p-3">
          <div className="flex items-start gap-3">
            <div className={cn(
              "w-8 h-8 rounded flex items-center justify-center",
              isSelected ? "bg-primary text-white" : "bg-muted"
            )}>
              <Icon className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm truncate">{artifact.title}</p>
              <p className="text-xs text-muted-foreground truncate">
                {artifact.agent} • {new Date(artifact.timestamp).toLocaleDateString()}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="secondary" className="text-xs px-1 py-0">
                  {artifact.type}
                </Badge>
                {artifact.metadata?.confidence && (
                  <span className="text-xs text-muted-foreground">
                    {(artifact.metadata.confidence * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// Artifact Renderer - Routes to appropriate component
function ArtifactRenderer({ artifact }: { artifact: Artifact }) {
  const Component = ARTIFACT_COMPONENTS[artifact.type];
  
  if (!Component) {
    return <div>Unknown artifact type: {artifact.type}</div>;
  }
  
  return <Component artifact={artifact} />;
}

// Individual Artifact Components

function ValueModelArtifact({ artifact }: { artifact: Artifact }) {
  const content = artifact.content;
  
  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Value</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              ${(content.totalValue / 1000000).toFixed(1)}M
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>ROI</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {((content.totalValue - content.investment) / content.investment * 100).toFixed(0)}%
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Timeline</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {content.timeline}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Value Drivers */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Value Drivers</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {content.drivers.map((driver: any, index: number) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{driver.name}</span>
                    <span className="text-sm text-muted-foreground">
                      ${(driver.impact / 1000).toFixed(0)}K
                    </span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full"
                      style={{ width: `${driver.confidence * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Investment vs Return */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Investment Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm">Initial Investment</span>
              <span className="text-sm font-medium">
                ${(content.investment / 1000).toFixed(0)}K
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm">Total Return</span>
              <span className="text-sm font-medium text-green-600">
                ${(content.totalValue / 1000).toFixed(0)}K
              </span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="text-sm font-medium">Net Value</span>
              <span className="text-sm font-bold text-green-600">
                ${((content.totalValue - content.investment) / 1000).toFixed(0)}K
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ROIAnalysisArtifact({ artifact }: { artifact: Artifact }) {
  const content = artifact.content;
  
  return (
    <div className="space-y-6">
      {/* Scenario Comparison */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Scenario Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(content.scenarios).map(([scenario, data]: [string, any]) => (
              <div key={scenario} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium capitalize">{scenario}</span>
                  <div className="flex gap-4">
                    <Badge variant="secondary">
                      {data.roi}% ROI
                    </Badge>
                    <Badge variant="outline">
                      {data.payback} mo payback
                    </Badge>
                  </div>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className={cn(
                      "h-2 rounded-full",
                      scenario === "conservative" && "bg-blue-500",
                      scenario === "realistic" && "bg-green-500",
                      scenario === "optimistic" && "bg-purple-500"
                    )}
                    style={{ width: `${Math.min(data.roi / 4, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Yearly Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">3-Year Value Progression</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {content.yearlyBreakdown.map((year: any) => (
              <div key={year.year} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <span className="text-sm font-medium">Year {year.year}</span>
                <div className="flex gap-4">
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">Value</p>
                    <p className="text-sm font-medium text-green-600">
                      ${(year.value / 1000).toFixed(0)}K
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">Cost</p>
                    <p className="text-sm font-medium text-red-600">
                      ${(year.cost / 1000).toFixed(0)}K
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">Net</p>
                    <p className="text-sm font-bold">
                      ${((year.value - year.cost) / 1000).toFixed(0)}K
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ExecutiveSummaryArtifact({ artifact }: { artifact: Artifact }) {
  const content = artifact.content;
  
  return (
    <div className="space-y-6">
      {/* Headline */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-lg bg-white flex items-center justify-center">
              <Lightbulb className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h3 className="text-xl font-bold mb-2">{content.headline}</h3>
              <p className="text-sm text-muted-foreground">
                Executive value proposition for C-suite presentation
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Points */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Key Value Points</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {content.keyPoints.map((point: string, index: number) => (
              <div key={index} className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Check className="w-3 h-3 text-green-600" />
                </div>
                <p className="text-sm">{point}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Call to Action */}
      <Card className="border-primary">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-primary" />
            Recommended Action
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm font-medium">{content.callToAction}</p>
        </CardContent>
      </Card>
    </div>
  );
}

// Placeholder components for other artifact types
function ContractTermsArtifact({ artifact }: { artifact: Artifact }) {
  return <div>Contract Terms Content</div>;
}

function ImplementationPlanArtifact({ artifact }: { artifact: Artifact }) {
  return <div>Implementation Plan Content</div>;
}

function ProgressReportArtifact({ artifact }: { artifact: Artifact }) {
  return <div>Progress Report Content</div>;
}

function FormulaArtifact({ artifact }: { artifact: Artifact }) {
  return <div>Formula Content</div>;
}

function DataTableArtifact({ artifact }: { artifact: Artifact }) {
  return <div>Data Table Content</div>;
}

function VisualizationArtifact({ artifact }: { artifact: Artifact }) {
  return <div>Visualization Content</div>;
}

function DocumentArtifact({ artifact }: { artifact: Artifact }) {
  return <div>Document Content</div>;
}

function CodeArtifact({ artifact }: { artifact: Artifact }) {
  return (
    <SyntaxHighlighter language="python" style={oneDark}>
      {artifact.content}
    </SyntaxHighlighter>
  );
}

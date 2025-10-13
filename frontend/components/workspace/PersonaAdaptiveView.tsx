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
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  BarChart3,
  TrendingUp,
  Users,
  Target,
  Calculator,
  FileText,
  Settings,
  HelpCircle,
  ChevronRight,
  Sparkles,
  Zap,
  Shield,
  Eye,
  Code,
  Layers,
  BookOpen,
  Wand2,
  AlertCircle,
  CheckCircle,
  DollarSign,
  Activity,
  PieChart,
  LineChart,
  Briefcase,
  UserCheck,
  GraduationCap,
} from "lucide-react";
import { cn } from "@/lib/utils";

// User Personas
type UserRole = "sales" | "analyst" | "csm" | "executive";
type ExpertiseLevel = "beginner" | "intermediate" | "expert";

interface PersonaConfig {
  role: UserRole;
  level: ExpertiseLevel;
  preferences: {
    dataGranularity: "summary" | "detailed" | "custom";
    showFormulas: boolean;
    enableCustomization: boolean;
    proactiveAssistance: boolean;
    keyboardShortcuts: boolean;
    batchOperations: boolean;
    apiAccess: boolean;
  };
}

// Role-specific dashboard configurations
const ROLE_DASHBOARDS = {
  sales: {
    title: "Sales Dashboard",
    icon: Briefcase,
    color: "text-blue-600",
    description: "High-level ROI insights and talking points",
    primaryMetrics: ["Total Value", "ROI %", "Payback Period"],
    features: {
      showTalkingPoints: true,
      quickScenarios: true,
      executiveSummary: true,
      hideComplexFormulas: true,
    },
  },
  analyst: {
    title: "Analyst Workspace",
    icon: Calculator,
    color: "text-purple-600",
    description: "Detailed formulas and deep customization",
    primaryMetrics: ["Value Drivers", "Confidence Score", "Variance Analysis"],
    features: {
      showFormulas: true,
      deepCustomization: true,
      dataExport: true,
      advancedFilters: true,
    },
  },
  csm: {
    title: "Customer Success Hub",
    icon: UserCheck,
    color: "text-green-600",
    description: "Realization tracking and QBR generation",
    primaryMetrics: ["Realization %", "Health Score", "Next Milestone"],
    features: {
      showRealizationMetrics: true,
      enableQBRGeneration: true,
      riskAlerts: true,
      customerTimeline: true,
    },
  },
  executive: {
    title: "Executive Overview",
    icon: Target,
    color: "text-orange-600",
    description: "Strategic insights and portfolio view",
    primaryMetrics: ["Portfolio Value", "Success Rate", "Strategic Alignment"],
    features: {
      portfolioView: true,
      strategicMetrics: true,
      executiveReporting: true,
      minimalDetail: true,
    },
  },
};

// Progressive disclosure configurations
const EXPERTISE_LEVELS = {
  beginner: {
    title: "Guided Mode",
    icon: GraduationCap,
    description: "Step-by-step workflows with helpful tooltips",
    features: {
      wizardWorkflow: true,
      extensiveTooltips: true,
      proactiveSuggestions: true,
      simplifiedControls: true,
    },
  },
  intermediate: {
    title: "Hybrid Mode",
    icon: Layers,
    description: "Balance of guidance and flexibility",
    features: {
      standardControls: true,
      optionalGuidance: true,
      advancedFilters: true,
      customization: true,
    },
  },
  expert: {
    title: "Power User Mode",
    icon: Zap,
    description: "Full control with keyboard shortcuts and API access",
    features: {
      denseLayout: true,
      keyboardShortcuts: true,
      batchOperations: true,
      apiAccess: true,
      customScripting: true,
    },
  },
};

interface PersonaAdaptiveViewProps {
  initialRole?: UserRole;
  initialLevel?: ExpertiseLevel;
  onConfigChange?: (config: PersonaConfig) => void;
}

export function PersonaAdaptiveView({
  initialRole = "sales",
  initialLevel = "intermediate",
  onConfigChange,
}: PersonaAdaptiveViewProps) {
  const [config, setConfig] = useState<PersonaConfig>({
    role: initialRole,
    level: initialLevel,
    preferences: {
      dataGranularity: "summary",
      showFormulas: false,
      enableCustomization: false,
      proactiveAssistance: true,
      keyboardShortcuts: false,
      batchOperations: false,
      apiAccess: false,
    },
  });

  const [showWizard, setShowWizard] = useState(false);
  const [wizardStep, setWizardStep] = useState(0);

  // Update preferences based on role and level changes
  useEffect(() => {
    const newPreferences = {
      ...config.preferences,
      // Role-based defaults
      showFormulas: config.role === "analyst",
      dataGranularity: config.role === "analyst" ? "detailed" : 
                      config.role === "executive" ? "summary" : "custom",
      // Level-based defaults
      proactiveAssistance: config.level === "beginner",
      keyboardShortcuts: config.level === "expert",
      batchOperations: config.level === "expert",
      apiAccess: config.level === "expert" && config.role === "analyst",
      enableCustomization: config.level !== "beginner",
    };

    const newConfig = { ...config, preferences: newPreferences };
    setConfig(newConfig);
    onConfigChange?.(newConfig);
  }, [config.role, config.level]);

  const currentDashboard = ROLE_DASHBOARDS[config.role];
  const currentLevel = EXPERTISE_LEVELS[config.level];

  // Sample metrics data
  const metricsData = {
    "Total Value": "$2.3M",
    "ROI %": "285%",
    "Payback Period": "8 months",
    "Value Drivers": "12 active",
    "Confidence Score": "87%",
    "Variance Analysis": "+5.2%",
    "Realization %": "78%",
    "Health Score": "Good",
    "Next Milestone": "Q2 Review",
    "Portfolio Value": "$45.6M",
    "Success Rate": "92%",
    "Strategic Alignment": "High",
  };

  return (
    <div className="space-y-6">
      {/* Configuration Header */}
      <Card className="border-2">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={cn(
                "w-10 h-10 rounded-lg flex items-center justify-center",
                "bg-gradient-to-br from-slate-100 to-slate-200"
              )}>
                <currentDashboard.icon className={cn("w-5 h-5", currentDashboard.color)} />
              </div>
              <div>
                <CardTitle>{currentDashboard.title}</CardTitle>
                <CardDescription>{currentDashboard.description}</CardDescription>
              </div>
            </div>
            
            {/* Settings Button */}
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                  <Settings className="w-4 h-4 mr-2" />
                  Customize View
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Customize Your Experience</DialogTitle>
                  <DialogDescription>
                    Adjust the interface to match your role and expertise level
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-6 py-4">
                  {/* Role Selection */}
                  <div className="space-y-3">
                    <Label>Your Role</Label>
                    <div className="grid grid-cols-2 gap-3">
                      {(Object.keys(ROLE_DASHBOARDS) as UserRole[]).map((role) => {
                        const dashboard = ROLE_DASHBOARDS[role];
                        return (
                          <Card
                            key={role}
                            className={cn(
                              "cursor-pointer transition-all",
                              config.role === role && "ring-2 ring-primary"
                            )}
                            onClick={() => setConfig({ ...config, role })}
                          >
                            <CardContent className="p-4">
                              <div className="flex items-center gap-3">
                                <dashboard.icon className={cn("w-5 h-5", dashboard.color)} />
                                <div>
                                  <p className="font-medium capitalize">{role}</p>
                                  <p className="text-xs text-muted-foreground">
                                    {dashboard.description}
                                  </p>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })}
                    </div>
                  </div>
                  
                  {/* Expertise Level */}
                  <div className="space-y-3">
                    <Label>Expertise Level</Label>
                    <div className="grid grid-cols-3 gap-3">
                      {(Object.keys(EXPERTISE_LEVELS) as ExpertiseLevel[]).map((level) => {
                        const levelConfig = EXPERTISE_LEVELS[level];
                        return (
                          <Card
                            key={level}
                            className={cn(
                              "cursor-pointer transition-all",
                              config.level === level && "ring-2 ring-primary"
                            )}
                            onClick={() => setConfig({ ...config, level })}
                          >
                            <CardContent className="p-4">
                              <div className="flex flex-col items-center text-center gap-2">
                                <levelConfig.icon className="w-5 h-5" />
                                <p className="font-medium text-sm capitalize">{level}</p>
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })}
                    </div>
                  </div>
                  
                  {/* Advanced Preferences */}
                  <div className="space-y-3">
                    <Label>Advanced Preferences</Label>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="formulas" className="text-sm font-normal">
                          Show Formulas
                        </Label>
                        <Switch
                          id="formulas"
                          checked={config.preferences.showFormulas}
                          onCheckedChange={(checked) =>
                            setConfig({
                              ...config,
                              preferences: { ...config.preferences, showFormulas: checked },
                            })
                          }
                        />
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <Label htmlFor="assistance" className="text-sm font-normal">
                          Proactive Assistance
                        </Label>
                        <Switch
                          id="assistance"
                          checked={config.preferences.proactiveAssistance}
                          onCheckedChange={(checked) =>
                            setConfig({
                              ...config,
                              preferences: { ...config.preferences, proactiveAssistance: checked },
                            })
                          }
                        />
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <Label htmlFor="shortcuts" className="text-sm font-normal">
                          Keyboard Shortcuts
                        </Label>
                        <Switch
                          id="shortcuts"
                          checked={config.preferences.keyboardShortcuts}
                          onCheckedChange={(checked) =>
                            setConfig({
                              ...config,
                              preferences: { ...config.preferences, keyboardShortcuts: checked },
                            })
                          }
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
      </Card>

      {/* Expertise Level Indicator */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Badge variant="outline" className="px-3 py-1">
            <currentLevel.icon className="w-3 h-3 mr-2" />
            {currentLevel.title}
          </Badge>
          <span className="text-sm text-muted-foreground">
            {currentLevel.description}
          </span>
        </div>
        
        {config.level === "beginner" && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowWizard(true)}
          >
            <Wand2 className="w-4 h-4 mr-2" />
            Start Guided Workflow
          </Button>
        )}
      </div>

      {/* Role-Specific Dashboard */}
      <div className="grid gap-4 md:grid-cols-3">
        {currentDashboard.primaryMetrics.map((metric) => (
          <Card key={metric}>
            <CardHeader className="pb-2">
              <CardDescription>{metric}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metricsData[metric as keyof typeof metricsData]}
              </div>
              {config.preferences.showFormulas && (
                <p className="text-xs text-muted-foreground mt-2">
                  Formula: f(x) = Σ(value_drivers × confidence)
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Feature-Specific Content */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
          <TabsTrigger value="actions">Actions</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Sales View: Talking Points */}
          {config.role === "sales" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Executive Talking Points
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600 mt-0.5" />
                    <span className="text-sm">
                      25% improvement in customer retention within 6 months
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600 mt-0.5" />
                    <span className="text-sm">
                      ROI payback in under 8 months with 285% total return
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600 mt-0.5" />
                    <span className="text-sm">
                      Proven success with 3 similar companies in your industry
                    </span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Analyst View: Formula Builder */}
          {config.role === "analyst" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calculator className="w-5 h-5" />
                  Formula Builder
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-3 bg-muted rounded-lg font-mono text-sm">
                    ROI = ((Total_Value - Investment) / Investment) × 100
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Total Value</Label>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-sm">Σ(Driver_i × Weight_i)</span>
                        <Badge variant="secondary">$2.3M</Badge>
                      </div>
                    </div>
                    <div>
                      <Label>Investment</Label>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-sm">Fixed + Variable</span>
                        <Badge variant="secondary">$580K</Badge>
                      </div>
                    </div>
                  </div>
                  {config.preferences.enableCustomization && (
                    <Button variant="outline" className="w-full">
                      <Code className="w-4 h-4 mr-2" />
                      Edit Formula
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* CSM View: Realization Tracker */}
          {config.role === "csm" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  Value Realization Progress
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Overall Progress</span>
                      <span className="text-sm text-muted-foreground">78%</span>
                    </div>
                    <Progress value={78} className="h-2" />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        Phase 1: Foundation
                      </span>
                      <Badge variant="secondary">Complete</Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                        Phase 2: Implementation
                      </span>
                      <Badge>In Progress</Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 text-orange-600" />
                        Phase 3: Optimization
                      </span>
                      <Badge variant="outline">Upcoming</Badge>
                    </div>
                  </div>
                  
                  <Button className="w-full">
                    Generate QBR Report
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Executive View: Portfolio Summary */}
          {config.role === "executive" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="w-5 h-5" />
                  Portfolio Overview
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-600">92%</div>
                      <p className="text-sm text-muted-foreground">Success Rate</p>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-600">$45.6M</div>
                      <p className="text-sm text-muted-foreground">Total Portfolio</p>
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t">
                    <p className="text-sm font-medium mb-2">Top Performers</p>
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span>TechCorp Solutions</span>
                        <Badge variant="secondary">+312% ROI</Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span>Global Industries</span>
                        <Badge variant="secondary">+287% ROI</Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span>Innovate Inc</span>
                        <Badge variant="secondary">+265% ROI</Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Guided Workflow Wizard (for beginners) */}
      <AnimatePresence>
        {showWizard && config.level === "beginner" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowWizard(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-lg p-6 max-w-lg w-full mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">
                    Step {wizardStep + 1} of 5: {
                      ["Define Objective", "Select Customer", "Input Data", "Review Model", "Generate Output"][wizardStep]
                    }
                  </h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowWizard(false)}
                  >
                    ×
                  </Button>
                </div>
                
                <Progress value={(wizardStep + 1) * 20} className="h-2" />
                
                <div className="py-8 text-center">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Sparkles className="w-8 h-8 text-primary" />
                  </div>
                  <p className="text-muted-foreground">
                    Wizard content for step {wizardStep + 1} would appear here
                  </p>
                </div>
                
                <div className="flex justify-between">
                  <Button
                    variant="outline"
                    onClick={() => setWizardStep(Math.max(0, wizardStep - 1))}
                    disabled={wizardStep === 0}
                  >
                    Previous
                  </Button>
                  <Button
                    onClick={() => {
                      if (wizardStep === 4) {
                        setShowWizard(false);
                        setWizardStep(0);
                      } else {
                        setWizardStep(wizardStep + 1);
                      }
                    }}
                  >
                    {wizardStep === 4 ? "Finish" : "Next"}
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Keyboard Shortcuts Helper (for experts) */}
      {config.level === "expert" && config.preferences.keyboardShortcuts && (
        <Card className="border-dashed">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Keyboard Shortcuts Active
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="flex items-center gap-2">
                <kbd className="px-2 py-1 bg-muted rounded">⌘K</kbd>
                <span>Quick Search</span>
              </div>
              <div className="flex items-center gap-2">
                <kbd className="px-2 py-1 bg-muted rounded">⌘N</kbd>
                <span>New Model</span>
              </div>
              <div className="flex items-center gap-2">
                <kbd className="px-2 py-1 bg-muted rounded">⌘S</kbd>
                <span>Save</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

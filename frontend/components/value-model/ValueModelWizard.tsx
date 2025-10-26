"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Target,
  TrendingUp,
  DollarSign,
  Users,
  Clock,
  AlertCircle,
  CheckCircle,
  ChevronRight,
  ChevronLeft,
  Plus,
  Trash2,
  Save,
  Play,
  BarChart3,
  Calculator,
  Sparkles,
  Settings,
  FileText,
  Download,
  Upload,
} from "lucide-react";
import { cn } from "@/utils/cn";

// Value Model Types
interface ValueDriver {
  id: string;
  name: string;
  category: string;
  description: string;
  baselineValue: number;
  targetValue: number;
  unit: string;
  weight: number;
  impact: "high" | "medium" | "low";
}

interface ValueModel {
  id?: string;
  name: string;
  description: string;
  company: string;
  industry: string;
  drivers: ValueDriver[];
  timeline: number; // months
  totalValue: number;
  confidence: number;
  assumptions: string[];
  risks: string[];
  createdAt?: Date;
  updatedAt?: Date;
}

interface ValueModelWizardProps {
  onComplete: (model: ValueModel) => void;
  onCancel: () => void;
  initialModel?: ValueModel;
}

const STEPS = [
  { id: 1, name: "Basic Information", icon: FileText },
  { id: 2, name: "Value Drivers", icon: Target },
  { id: 3, name: "Calculations", icon: Calculator },
  { id: 4, name: "Assumptions & Risks", icon: AlertCircle },
  { id: 5, name: "Review & Test", icon: CheckCircle },
];

const DRIVER_CATEGORIES = [
  "Cost Reduction",
  "Revenue Growth",
  "Efficiency Gains",
  "Risk Mitigation",
  "Customer Satisfaction",
  "Employee Productivity",
];

const DRIVER_UNITS = [
  "USD",
  "EUR",
  "Percentage",
  "Hours",
  "Days",
  "FTE",
  "Units",
  "Custom",
];

export default function ValueModelWizard({
  onComplete,
  onCancel,
  initialModel,
}: ValueModelWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [model, setModel] = useState<ValueModel>(
    initialModel || {
      name: "",
      description: "",
      company: "",
      industry: "",
      drivers: [],
      timeline: 12,
      totalValue: 0,
      confidence: 70,
      assumptions: [],
      risks: [],
    }
  );
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [testResults, setTestResults] = useState<any>(null);

  // Validation
  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};

    switch (step) {
      case 1:
        if (!model.name) newErrors.name = "Name is required";
        if (!model.company) newErrors.company = "Company is required";
        if (!model.industry) newErrors.industry = "Industry is required";
        break;
      case 2:
        if (model.drivers.length === 0) {
          newErrors.drivers = "At least one value driver is required";
        }
        break;
      case 3:
        if (model.timeline <= 0) {
          newErrors.timeline = "Timeline must be positive";
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Navigation
  const handleNext = () => {
    if (validateStep(currentStep)) {
      if (currentStep === STEPS.length) {
        onComplete(model);
      } else {
        setCurrentStep(currentStep + 1);
      }
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Value Driver Management
  const addDriver = () => {
    const newDriver: ValueDriver = {
      id: Date.now().toString(),
      name: "",
      category: DRIVER_CATEGORIES[0],
      description: "",
      baselineValue: 0,
      targetValue: 0,
      unit: "USD",
      weight: 1,
      impact: "medium",
    };
    setModel({ ...model, drivers: [...model.drivers, newDriver] });
  };

  const updateDriver = (id: string, updates: Partial<ValueDriver>) => {
    setModel({
      ...model,
      drivers: model.drivers.map((d) => (d.id === id ? { ...d, ...updates } : d)),
    });
  };

  const removeDriver = (id: string) => {
    setModel({
      ...model,
      drivers: model.drivers.filter((d) => d.id !== id),
    });
  };

  // Calculations
  const calculateTotalValue = () => {
    const total = model.drivers.reduce((sum, driver) => {
      const improvement = driver.targetValue - driver.baselineValue;
      return sum + improvement * driver.weight;
    }, 0);
    setModel({ ...model, totalValue: total });
  };

  const testModel = () => {
    // Simulate model testing
    const results = {
      totalValue: model.totalValue,
      roi: ((model.totalValue / 100000) * 100).toFixed(1), // Mock investment
      paybackPeriod: (100000 / (model.totalValue / model.timeline)).toFixed(1),
      confidence: model.confidence,
      topDrivers: model.drivers
        .sort((a, b) => b.weight - a.weight)
        .slice(0, 3)
        .map((d) => d.name),
    };
    setTestResults(results);
  };

  // Render Steps
  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Model Name *</Label>
              <Input
                id="name"
                value={model.name}
                onChange={(e) => setModel({ ...model, name: e.target.value })}
                placeholder="e.g., Digital Transformation ROI Model"
                className={errors.name ? "border-red-500" : ""}
              />
              {errors.name && (
                <p className="text-sm text-red-500 mt-1">{errors.name}</p>
              )}
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={model.description}
                onChange={(e) => setModel({ ...model, description: e.target.value })}
                placeholder="Describe the purpose and scope of this value model..."
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="company">Company *</Label>
                <Input
                  id="company"
                  value={model.company}
                  onChange={(e) => setModel({ ...model, company: e.target.value })}
                  placeholder="e.g., Acme Corporation"
                  className={errors.company ? "border-red-500" : ""}
                />
                {errors.company && (
                  <p className="text-sm text-red-500 mt-1">{errors.company}</p>
                )}
              </div>

              <div>
                <Label htmlFor="industry">Industry *</Label>
                <Select
                  value={model.industry}
                  onValueChange={(value: string) => setModel({ ...model, industry: value })}
                >
                  <SelectTrigger className={errors.industry ? "border-red-500" : ""}>
                    <SelectValue placeholder="Select industry" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="technology">Technology</SelectItem>
                    <SelectItem value="healthcare">Healthcare</SelectItem>
                    <SelectItem value="finance">Finance</SelectItem>
                    <SelectItem value="retail">Retail</SelectItem>
                    <SelectItem value="manufacturing">Manufacturing</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
                {errors.industry && (
                  <p className="text-sm text-red-500 mt-1">{errors.industry}</p>
                )}
              </div>
            </div>

            <div>
              <Label htmlFor="timeline">Timeline (months)</Label>
              <div className="flex items-center gap-4">
                <Slider
                  id="timeline"
                  min={1}
                  max={60}
                  step={1}
                  value={[model.timeline]}
                  onValueChange={(value: number[]) => setModel({ ...model, timeline: value[0] })}
                  className="flex-1"
                />
                <span className="w-16 text-right font-medium">
                  {model.timeline} mo
                </span>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Value Drivers</h3>
              <Button onClick={addDriver} size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Add Driver
              </Button>
            </div>

            {errors.drivers && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{errors.drivers}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-4 max-h-96 overflow-y-auto">
              {model.drivers.map((driver, index) => (
                <Card key={driver.id}>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <Input
                          value={driver.name}
                          onChange={(e) =>
                            updateDriver(driver.id, { name: e.target.value })
                          }
                          placeholder="Driver name"
                          className="font-medium"
                        />
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeDriver(driver.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label>Category</Label>
                        <Select
                          value={driver.category}
                          onValueChange={(value: string) =>
                            updateDriver(driver.id, { category: value })
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {DRIVER_CATEGORIES.map((cat) => (
                              <SelectItem key={cat} value={cat}>
                                {cat}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Unit</Label>
                        <Select
                          value={driver.unit}
                          onValueChange={(value: string) =>
                            updateDriver(driver.id, { unit: value })
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {DRIVER_UNITS.map((unit) => (
                              <SelectItem key={unit} value={unit}>
                                {unit}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label>Baseline Value</Label>
                        <Input
                          type="number"
                          value={driver.baselineValue}
                          onChange={(e) =>
                            updateDriver(driver.id, {
                              baselineValue: parseFloat(e.target.value) || 0,
                            })
                          }
                        />
                      </div>

                      <div>
                        <Label>Target Value</Label>
                        <Input
                          type="number"
                          value={driver.targetValue}
                          onChange={(e) =>
                            updateDriver(driver.id, {
                              targetValue: parseFloat(e.target.value) || 0,
                            })
                          }
                        />
                      </div>
                    </div>

                    <div>
                      <Label>Impact Level</Label>
                      <div className="flex gap-2 mt-1">
                        {["low", "medium", "high"].map((level) => (
                          <Button
                            key={level}
                            size="sm"
                            variant={driver.impact === level ? "default" : "outline"}
                            onClick={() =>
                              updateDriver(driver.id, { impact: level as any })
                            }
                            className="flex-1"
                          >
                            {level}
                          </Button>
                        ))}
                      </div>
                    </div>

                    <div>
                      <Label>Weight (1-10)</Label>
                      <Slider
                        min={1}
                        max={10}
                        step={1}
                        value={[driver.weight]}
                        onValueChange={(value: string) =>
                          updateDriver(driver.id, { weight: value[0] })
                        }
                      />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Value Calculations</CardTitle>
                <CardDescription>
                  Review and adjust the calculated values
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button onClick={calculateTotalValue} className="w-full">
                  <Calculator className="h-4 w-4 mr-2" />
                  Calculate Total Value
                </Button>

                <div className="grid grid-cols-2 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-2xl font-bold">
                        ${model.totalValue.toLocaleString()}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Total Value
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-2xl font-bold">
                        {model.confidence}%
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Confidence
                      </p>
                    </CardContent>
                  </Card>
                </div>

                <div>
                  <Label>Confidence Level</Label>
                  <Slider
                    min={0}
                    max={100}
                    step={5}
                    value={[model.confidence]}
                    onValueChange={(value: string) =>
                      setModel({ ...model, confidence: value[0] })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <h4 className="font-medium">Value Breakdown by Driver</h4>
                  {model.drivers.map((driver) => {
                    const value = (driver.targetValue - driver.baselineValue) * driver.weight;
                    const percentage = model.totalValue > 0 ? (value / model.totalValue) * 100 : 0;
                    return (
                      <div key={driver.id} className="flex items-center justify-between">
                        <span className="text-sm">{driver.name}</span>
                        <div className="flex items-center gap-2">
                          <Progress value={percentage} className="w-24" />
                          <span className="text-sm font-medium">
                            ${value.toLocaleString()}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        );

      case 4:
        return (
          <div className="space-y-4">
            <div>
              <Label>Key Assumptions</Label>
              <div className="space-y-2">
                {model.assumptions.map((assumption, index) => (
                  <div key={index} className="flex gap-2">
                    <Input
                      value={assumption}
                      onChange={(e) => {
                        const newAssumptions = [...model.assumptions];
                        newAssumptions[index] = e.target.value;
                        setModel({ ...model, assumptions: newAssumptions });
                      }}
                      placeholder="Enter assumption..."
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        const newAssumptions = model.assumptions.filter(
                          (_, i) => i !== index
                        );
                        setModel({ ...model, assumptions: newAssumptions });
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setModel({ ...model, assumptions: [...model.assumptions, ""] })
                  }
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Assumption
                </Button>
              </div>
            </div>

            <div>
              <Label>Identified Risks</Label>
              <div className="space-y-2">
                {model.risks.map((risk, index) => (
                  <div key={index} className="flex gap-2">
                    <Input
                      value={risk}
                      onChange={(e) => {
                        const newRisks = [...model.risks];
                        newRisks[index] = e.target.value;
                        setModel({ ...model, risks: newRisks });
                      }}
                      placeholder="Enter risk..."
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        const newRisks = model.risks.filter((_, i) => i !== index);
                        setModel({ ...model, risks: newRisks });
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setModel({ ...model, risks: [...model.risks, ""] })}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Risk
                </Button>
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Model Summary</CardTitle>
                <CardDescription>Review your value model before saving</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Model Name</p>
                    <p className="font-medium">{model.name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Company</p>
                    <p className="font-medium">{model.company}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Industry</p>
                    <p className="font-medium">{model.industry}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Timeline</p>
                    <p className="font-medium">{model.timeline} months</p>
                  </div>
                </div>

                <Separator />

                <div>
                  <p className="text-sm text-muted-foreground mb-2">Value Drivers</p>
                  <div className="space-y-1">
                    {model.drivers.map((driver) => (
                      <div key={driver.id} className="flex items-center justify-between">
                        <span className="text-sm">{driver.name}</span>
                        <Badge variant="outline">{driver.impact}</Badge>
                      </div>
                    ))}
                  </div>
                </div>

                <Separator />

                <div className="grid grid-cols-2 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-3xl font-bold text-green-600">
                        ${model.totalValue.toLocaleString()}
                      </div>
                      <p className="text-sm text-muted-foreground">Total Value</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-3xl font-bold text-blue-600">
                        {model.confidence}%
                      </div>
                      <p className="text-sm text-muted-foreground">Confidence</p>
                    </CardContent>
                  </Card>
                </div>

                <Button onClick={testModel} className="w-full">
                  <Play className="h-4 w-4 mr-2" />
                  Test Model
                </Button>

                {testResults && (
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      <div className="space-y-1">
                        <p>ROI: {testResults.roi}%</p>
                        <p>Payback Period: {testResults.paybackPeriod} months</p>
                        <p>Top Drivers: {testResults.topDrivers.join(", ")}</p>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          {STEPS.map((step, index) => (
            <div
              key={step.id}
              className={cn(
                "flex items-center",
                index < STEPS.length - 1 && "flex-1"
              )}
            >
              <div
                className={cn(
                  "flex items-center justify-center w-10 h-10 rounded-full border-2",
                  currentStep >= step.id
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-background border-muted-foreground"
                )}
              >
                {currentStep > step.id ? (
                  <CheckCircle className="h-5 w-5" />
                ) : (
                  <step.icon className="h-5 w-5" />
                )}
              </div>
              {index < STEPS.length - 1 && (
                <div
                  className={cn(
                    "flex-1 h-1 mx-2",
                    currentStep > step.id ? "bg-primary" : "bg-muted"
                  )}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between">
          {STEPS.map((step) => (
            <div
              key={step.id}
              className={cn(
                "text-xs",
                currentStep >= step.id ? "text-primary" : "text-muted-foreground"
              )}
            >
              {step.name}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <Card>
        <CardHeader>
          <CardTitle>{STEPS[currentStep - 1].name}</CardTitle>
          <CardDescription>
            Step {currentStep} of {STEPS.length}
          </CardDescription>
        </CardHeader>
        <CardContent>{renderStep()}</CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between mt-6">
        <Button
          variant="outline"
          onClick={currentStep === 1 ? onCancel : handlePrevious}
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          {currentStep === 1 ? "Cancel" : "Previous"}
        </Button>
        <Button onClick={handleNext}>
          {currentStep === STEPS.length ? (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save Model
            </>
          ) : (
            <>
              Next
              <ChevronRight className="h-4 w-4 ml-2" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

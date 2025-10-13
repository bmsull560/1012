"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Lock,
  Unlock,
  Info,
  AlertCircle,
  Calculator,
  Sliders as SlidersIcon
} from "lucide-react";
import { VALUE_DRIVERS, calculateTotalValue, calculateNPV, calculatePayback, calculateAdoptionFactor } from "@/utils/valueDrivers";

interface SliderInput {
  id: string;
  name: string;
  category: string;
  currentValue: number;
  defaultValue: number;
  minValue: number;
  maxValue: number;
  step: number;
  unit: string;
  format: (value: number) => string;
  impact: 'high' | 'medium' | 'low';
  description?: string;
}

interface WhatIfSlidersProps {
  inputs: Map<string, number>;
  selectedDrivers: string[];
  onInputChange: (inputId: string, value: number) => void;
  onReset?: () => void;
  onApply?: (inputs: Map<string, number>) => void;
  currentMetrics?: {
    totalBenefits: number;
    netBenefit: number;
    npv: number;
    payback: number;
  };
}

export function WhatIfSliders({
  inputs,
  selectedDrivers,
  onInputChange,
  onReset,
  onApply,
  currentMetrics
}: WhatIfSlidersProps) {
  const [localInputs, setLocalInputs] = useState<Map<string, number>>(new Map(inputs));
  const [lockedInputs, setLockedInputs] = useState<Set<string>>(new Set());
  const [calculatedMetrics, setCalculatedMetrics] = useState(currentMetrics);
  const [showComparison, setShowComparison] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'revenue' | 'cost' | 'adoption'>('all');

  // Format functions
  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value.toFixed(0)}`;
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(0)}%`;
  const formatNumber = (value: number) => value.toFixed(0);

  // Build slider configurations based on selected drivers and their inputs
  const buildSliderConfigs = (): SliderInput[] => {
    const configs: SliderInput[] = [];
    
    // Get all unique inputs from selected drivers
    const processedInputs = new Set<string>();
    
    selectedDrivers.forEach(driverId => {
      const driver = VALUE_DRIVERS.find(d => d.id === driverId);
      if (driver) {
        driver.inputs.forEach(input => {
          if (!processedInputs.has(input.id)) {
            processedInputs.add(input.id);
            
            const currentValue = localInputs.get(input.id) || input.defaultValue;
            
            // Determine impact level based on typical contribution
            let impact: 'high' | 'medium' | 'low' = 'medium';
            if (input.id === 'reps' || input.id === 'adoption_rate' || input.id === 'new_surgeons_per_rep') {
              impact = 'high';
            } else if (input.id === 'weeks_per_year' || input.id === 'bad_demos_avoided') {
              impact = 'low';
            }
            
            // Determine category
            let category = 'other';
            if (['reps', 'new_surgeons_per_rep', 'cases_per_surgeon', 'target_procedures'].includes(input.id)) {
              category = 'revenue';
            } else if (['hours_saved_per_week', 'months_saved', 'bad_demos_avoided'].includes(input.id)) {
              category = 'cost';
            } else if (['adoption_rate', 'share_gain_pp', 'compliance_uplift'].includes(input.id)) {
              category = 'adoption';
            }
            
            configs.push({
              id: input.id,
              name: input.name,
              category: category,
              currentValue: currentValue,
              defaultValue: input.defaultValue,
              minValue: input.lowValue,
              maxValue: input.highValue,
              step: input.type === 'percentage' ? 0.01 : 1,
              unit: input.unit || '',
              format: input.type === 'percentage' ? formatPercent : 
                      input.type === 'currency' ? formatCurrency : 
                      formatNumber,
              impact: impact,
              description: input.description
            });
          }
        });
      }
    });
    
    // Add subscription cost if not present
    if (!processedInputs.has('annual_subscription')) {
      configs.push({
        id: 'annual_subscription',
        name: 'Annual Subscription',
        category: 'other',
        currentValue: localInputs.get('annual_subscription') || 450000,
        defaultValue: 450000,
        minValue: 100000,
        maxValue: 2000000,
        step: 50000,
        unit: '',
        format: formatCurrency,
        impact: 'high',
        description: 'Annual subscription cost for the solution'
      });
    }
    
    return configs.sort((a, b) => {
      // Sort by impact first, then by name
      const impactOrder = { high: 0, medium: 1, low: 2 };
      if (impactOrder[a.impact] !== impactOrder[b.impact]) {
        return impactOrder[a.impact] - impactOrder[b.impact];
      }
      return a.name.localeCompare(b.name);
    });
  };

  const sliderConfigs = buildSliderConfigs();

  // Filter sliders based on active tab
  const filteredSliders = activeTab === 'all' 
    ? sliderConfigs
    : sliderConfigs.filter(s => s.category === activeTab);

  // Calculate metrics when inputs change
  useEffect(() => {
    const selectedDriverObjects = VALUE_DRIVERS.filter(d => 
      selectedDrivers.includes(d.id)
    );
    
    const results = calculateTotalValue(selectedDriverObjects, localInputs);
    
    // Get costs
    const annualCost = localInputs.get('annual_subscription') || 450000;
    const onboardingCost = localInputs.get('onboarding_cost') || 75000;
    const totalCostsY1 = annualCost + onboardingCost;
    
    // Apply adoption ramp
    const adoptionFactor = calculateAdoptionFactor('standard');
    const realizedBenefitY1 = results.totalBenefits * adoptionFactor;
    const netBenefitY1 = realizedBenefitY1 - totalCostsY1;
    
    // Calculate steady state
    const netBenefitSteadyState = results.totalBenefits - annualCost;
    
    // Calculate 3-year NPV
    const npv = calculateNPV(
      [realizedBenefitY1, netBenefitSteadyState, netBenefitSteadyState],
      [totalCostsY1, annualCost, annualCost],
      0.12
    );
    
    // Calculate payback
    const monthlyBenefit = netBenefitY1 / 12;
    const payback = calculatePayback(totalCostsY1, monthlyBenefit);
    
    setCalculatedMetrics({
      totalBenefits: results.totalBenefits,
      netBenefit: netBenefitY1,
      npv: npv,
      payback: payback
    });
  }, [localInputs, selectedDrivers]);

  const handleSliderChange = (inputId: string, value: number) => {
    if (!lockedInputs.has(inputId)) {
      const newInputs = new Map(localInputs);
      newInputs.set(inputId, value);
      setLocalInputs(newInputs);
    }
  };

  const toggleLock = (inputId: string) => {
    const newLocked = new Set(lockedInputs);
    if (newLocked.has(inputId)) {
      newLocked.delete(inputId);
    } else {
      newLocked.add(inputId);
    }
    setLockedInputs(newLocked);
  };

  const resetToDefaults = () => {
    const newInputs = new Map<string, number>();
    sliderConfigs.forEach(config => {
      if (!lockedInputs.has(config.id)) {
        newInputs.set(config.id, config.defaultValue);
      } else {
        newInputs.set(config.id, localInputs.get(config.id) || config.defaultValue);
      }
    });
    setLocalInputs(newInputs);
    if (onReset) onReset();
  };

  const applyChanges = () => {
    if (onApply) {
      onApply(localInputs);
    }
    onInputChange('bulk_update', 0); // Trigger parent update
  };

  const getImpactColor = (impact: 'high' | 'medium' | 'low') => {
    switch (impact) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
    }
  };

  const getMetricChange = (current: number, original: number) => {
    const change = ((current - original) / original) * 100;
    const isPositive = change > 0;
    return {
      value: Math.abs(change).toFixed(1),
      isPositive,
      icon: isPositive ? TrendingUp : TrendingDown,
      color: isPositive ? 'text-green-600' : 'text-red-600'
    };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <SlidersIcon className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold">What-If Analysis</h3>
            <p className="text-sm text-gray-600">
              Adjust assumptions to see impact on ROI
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowComparison(!showComparison)}
          >
            <Calculator className="h-4 w-4 mr-1" />
            {showComparison ? 'Hide' : 'Show'} Comparison
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={resetToDefaults}
            disabled={lockedInputs.size === sliderConfigs.length}
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Reset
          </Button>
          <Button
            size="sm"
            onClick={applyChanges}
            className="bg-blue-600 hover:bg-blue-700"
          >
            Apply Changes
          </Button>
        </div>
      </div>

      {/* Current Metrics Summary */}
      {calculatedMetrics && showComparison && currentMetrics && (
        <Card className="bg-gradient-to-r from-blue-50 to-purple-50">
          <CardContent className="pt-6">
            <div className="grid grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-600">Total Benefits</p>
                <p className="text-lg font-bold">{formatCurrency(calculatedMetrics.totalBenefits)}</p>
                {currentMetrics.totalBenefits !== calculatedMetrics.totalBenefits && (
                  <div className="flex items-center gap-1 mt-1">
                    {(() => {
                      const change = getMetricChange(calculatedMetrics.totalBenefits, currentMetrics.totalBenefits);
                      return (
                        <>
                          <change.icon className={`h-3 w-3 ${change.color}`} />
                          <span className={`text-xs ${change.color}`}>{change.value}%</span>
                        </>
                      );
                    })()}
                  </div>
                )}
              </div>
              <div>
                <p className="text-xs text-gray-600">Net Benefit Y1</p>
                <p className="text-lg font-bold">{formatCurrency(calculatedMetrics.netBenefit)}</p>
                {currentMetrics.netBenefit !== calculatedMetrics.netBenefit && (
                  <div className="flex items-center gap-1 mt-1">
                    {(() => {
                      const change = getMetricChange(calculatedMetrics.netBenefit, currentMetrics.netBenefit);
                      return (
                        <>
                          <change.icon className={`h-3 w-3 ${change.color}`} />
                          <span className={`text-xs ${change.color}`}>{change.value}%</span>
                        </>
                      );
                    })()}
                  </div>
                )}
              </div>
              <div>
                <p className="text-xs text-gray-600">3-Year NPV</p>
                <p className="text-lg font-bold">{formatCurrency(calculatedMetrics.npv)}</p>
                {currentMetrics.npv !== calculatedMetrics.npv && (
                  <div className="flex items-center gap-1 mt-1">
                    {(() => {
                      const change = getMetricChange(calculatedMetrics.npv, currentMetrics.npv);
                      return (
                        <>
                          <change.icon className={`h-3 w-3 ${change.color}`} />
                          <span className={`text-xs ${change.color}`}>{change.value}%</span>
                        </>
                      );
                    })()}
                  </div>
                )}
              </div>
              <div>
                <p className="text-xs text-gray-600">Payback</p>
                <p className="text-lg font-bold">{calculatedMetrics.payback.toFixed(1)} Mo</p>
                {currentMetrics.payback !== calculatedMetrics.payback && (
                  <div className="flex items-center gap-1 mt-1">
                    {(() => {
                      const change = getMetricChange(calculatedMetrics.payback, currentMetrics.payback);
                      return (
                        <>
                          <change.icon className={`h-3 w-3 ${change.color === 'text-green-600' ? 'text-red-600' : 'text-green-600'}`} />
                          <span className={`text-xs ${change.color === 'text-green-600' ? 'text-red-600' : 'text-green-600'}`}>{change.value}%</span>
                        </>
                      );
                    })()}
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Category Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
        <TabsList className="grid grid-cols-4 w-full max-w-md">
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="revenue">Revenue</TabsTrigger>
          <TabsTrigger value="cost">Cost</TabsTrigger>
          <TabsTrigger value="adoption">Adoption</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Sliders Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredSliders.map((config) => {
          const isLocked = lockedInputs.has(config.id);
          const hasChanged = config.currentValue !== config.defaultValue;
          
          return (
            <motion.div
              key={config.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Card className={isLocked ? 'opacity-75' : ''}>
                <CardContent className="pt-4">
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Label className="text-sm font-medium">{config.name}</Label>
                          {config.description && (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger>
                                  <Info className="h-3 w-3 text-gray-400" />
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p className="text-xs max-w-xs">{config.description}</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline" className={`text-xs ${getImpactColor(config.impact)}`}>
                            {config.impact} impact
                          </Badge>
                          {hasChanged && (
                            <Badge variant="outline" className="text-xs">
                              Changed
                            </Badge>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-semibold">
                          {config.format(config.currentValue)}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleLock(config.id)}
                          className="h-6 w-6 p-0"
                        >
                          {isLocked ? (
                            <Lock className="h-3 w-3" />
                          ) : (
                            <Unlock className="h-3 w-3" />
                          )}
                        </Button>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Slider
                        value={[((config.currentValue - config.minValue) / (config.maxValue - config.minValue)) * 100]}
                        onValueChange={([percentage]) => {
                          if (!isLocked) {
                            const actualValue = config.minValue + (percentage / 100) * (config.maxValue - config.minValue);
                            handleSliderChange(config.id, actualValue);
                          }
                        }}
                        className={`w-full ${isLocked ? 'opacity-50 cursor-not-allowed' : ''}`}
                      />
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>{config.format(config.minValue)}</span>
                        <span className="font-medium">
                          Default: {config.format(config.defaultValue)}
                        </span>
                        <span>{config.format(config.maxValue)}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Impact Summary */}
      {showComparison && currentMetrics && calculatedMetrics && (
        <Card className="bg-yellow-50 border-yellow-200">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-yellow-600" />
              Impact Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-700">
              Your adjustments would change the 3-Year NPV by{' '}
              <span className="font-bold">
                {formatCurrency(Math.abs(calculatedMetrics.npv - currentMetrics.npv))}
              </span>
              {' '}({getMetricChange(calculatedMetrics.npv, currentMetrics.npv).value}%)
              {calculatedMetrics.npv > currentMetrics.npv ? ' improvement' : ' reduction'}.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

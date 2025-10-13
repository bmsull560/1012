"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  TrendingUp,
  DollarSign,
  Clock,
  Target,
  CheckCircle,
  AlertCircle,
  Download,
  Share2,
  Printer,
  FileText,
  PieChart,
  BarChart3,
  Activity,
  Users,
  Zap,
  Shield,
  ArrowUp,
  ArrowDown,
  ChevronRight,
  Calculator,
  Briefcase
} from "lucide-react";

export interface ValueModelData {
  company: {
    name: string;
    industry: string;
    size: string;
    analysisType: string;
  };
  keyMetrics: {
    totalBenefitsY1: number;
    netBenefitY1: number;
    npv3Year: number;
    paybackMonths: number;
    adoptionRamp: number;
  };
  executiveSummary: {
    roiYear1: number;
    paybackPeriod: number;
    roi3Year: number;
    keyRecommendation: string;
  };
  valueDrivers: Array<{
    name: string;
    value: number;
    percentOfTotal: number;
    confidence: number;
    category: "revenue" | "cost" | "risk";
  }>;
  financialDetails: {
    totalBenefitsY1: number;
    totalCostsY1: number;
    netBenefitRealized: number;
    netBenefitSteadyState: number;
    npv3Year: number;
    discountRate: number;
  };
  assumptions: {
    salesReps: number;
    aspPerCase: number;
    grossMargin: number;
    annualProcedures: number;
    adoptionRate: number;
    criticalFactor: string;
  };
  scenarios: {
    base: number;
    conservative: number;
    optimistic: number;
  };
  implementationNotes?: string[];
  keySuccessFactors?: string[];
}

interface ValueModelReportProps {
  data: ValueModelData;
  onExport?: (format: "pdf" | "ppt" | "excel") => void;
  onShare?: () => void;
  onScenarioChange?: (scenario: "base" | "conservative" | "optimistic") => void;
}

export function ValueModelReport({
  data,
  onExport,
  onShare,
  onScenarioChange,
}: ValueModelReportProps) {
  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value.toFixed(0)}`;
  };

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(0)}%`;
  };

  const formatPayback = (months: number) => {
    if (months < 1) {
      return `${(months * 30).toFixed(0)} days`;
    } else if (months === 1) {
      return "1 month";
    }
    return `${months.toFixed(1)} months`;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return "text-green-600";
    if (confidence >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  const getPaybackColor = (months: number) => {
    if (months <= 3) return "bg-green-500";
    if (months <= 12) return "bg-blue-500";
    return "bg-yellow-500";
  };

  // Separate value drivers by category
  const revenueDrivers = data.valueDrivers.filter(d => d.category === "revenue");
  const costDrivers = data.valueDrivers.filter(d => d.category === "cost");

  return (
    <div className="w-full max-w-7xl mx-auto p-6 space-y-6 bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 bg-white p-6 rounded-lg shadow-sm">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Calculator className="h-6 w-6 text-blue-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900">
              {data.company.name} Value Model
            </h1>
          </div>
          <p className="text-gray-600">
            {data.company.industry} • {data.company.analysisType}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onShare?.()}
          >
            <Share2 className="h-4 w-4 mr-1" />
            Share
          </Button>
          <Button
            size="sm"
            onClick={() => onExport?.("pdf")}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Download className="h-4 w-4 mr-1" />
            Load Scenario
          </Button>
        </div>
      </div>

      {/* Scenario Selector */}
      <div className="flex justify-center">
        <Tabs defaultValue="base" className="w-auto">
          <TabsList className="grid grid-cols-3 w-[400px] bg-white">
            <TabsTrigger 
              value="conservative"
              onClick={() => onScenarioChange?.("conservative")}
            >
              Low Case
            </TabsTrigger>
            <TabsTrigger 
              value="base"
              onClick={() => onScenarioChange?.("base")}
            >
              Base Case
            </TabsTrigger>
            <TabsTrigger 
              value="optimistic"
              onClick={() => onScenarioChange?.("optimistic")}
            >
              High Case
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Key Performance Indicators */}
      <div className="text-sm text-gray-600 mb-2">Key Performance Indicators</div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white border-0">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-white/80" />
                <CardTitle className="text-sm font-medium text-white/90">
                  Total Benefits (Y1)
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {formatCurrency(data.keyMetrics.totalBenefitsY1)}
              </div>
              <p className="text-xs text-white/70 mt-1">
                Revenue + Cost Savings
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-white/80" />
                <CardTitle className="text-sm font-medium text-white/90">
                  Net Benefit (Y1)
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {formatCurrency(data.keyMetrics.netBenefitY1)}
              </div>
              <p className="text-xs text-white/70 mt-1">
                After {formatPercent(data.keyMetrics.adoptionRamp)} Adoption Ramp
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-gradient-to-br from-yellow-500 to-yellow-600 text-white border-0">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-white/80" />
                <CardTitle className="text-sm font-medium text-white/90">
                  3-Year NPV
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {formatCurrency(data.keyMetrics.npv3Year)}
              </div>
              <p className="text-xs text-white/70 mt-1">
                at {formatPercent(data.financialDetails.discountRate)} Discount Rate
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card className={`text-white border-0 ${getPaybackColor(data.keyMetrics.paybackMonths)}`}>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-white/80" />
                <CardTitle className="text-sm font-medium text-white/90">
                  Payback
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {data.keyMetrics.paybackMonths.toFixed(1)} Mo
              </div>
              <p className="text-xs text-white/70 mt-1">
                Fast Recovery
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Executive Summary */}
      <div className="flex items-center gap-2 mt-8 mb-4">
        <BarChart3 className="h-5 w-5 text-gray-600" />
        <h2 className="text-lg font-semibold text-gray-900">Executive Summary</h2>
      </div>
      <div className="text-sm text-gray-600 mb-4">
        Key business outcomes and strategic recommendations
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-white border-green-200">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              <CardTitle className="text-sm font-medium text-gray-700">
                ROI (Year 1)
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-3xl font-bold text-green-600">
              {formatPercent(data.executiveSummary.roiYear1 / 100)}
            </div>
            <p className="text-xs text-gray-600">After adoption ramp</p>
            <div className="p-3 bg-green-50 rounded-md">
              <div className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                <p className="text-xs text-green-800">
                  Exceptional ROI - Strong business case for immediate investment
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white border-blue-200">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-blue-600" />
              <CardTitle className="text-sm font-medium text-gray-700">
                Payback Period
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-3xl font-bold text-blue-600">
              {data.executiveSummary.paybackPeriod.toFixed(1)}
            </div>
            <p className="text-xs text-gray-600">Months</p>
            <div className="p-3 bg-blue-50 rounded-md">
              <div className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5" />
                <p className="text-xs text-blue-800">
                  Fast payback - Investment recovers quickly, minimal financial risk
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white border-purple-200">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Target className="h-5 w-5 text-purple-600" />
              <CardTitle className="text-sm font-medium text-gray-700">
                3-Year ROI
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-3xl font-bold text-purple-600">
              {formatPercent(data.executiveSummary.roi3Year / 100)}
            </div>
            <p className="text-xs text-gray-600">NPV-based</p>
            <div className="p-3 bg-purple-50 rounded-md">
              <div className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-purple-600 mt-0.5" />
                <p className="text-xs text-purple-800">
                  Exceptional long-term value creation
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Strategic Insights */}
      <div className="flex items-center gap-2 mt-8 mb-4">
        <Activity className="h-5 w-5 text-gray-600" />
        <h2 className="text-lg font-semibold text-gray-900">Strategic Insights</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Revenue Uplifts */}
        <Card className="bg-white">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-green-600" />
                <CardTitle className="text-base">Revenue Uplifts</CardTitle>
              </div>
              <Badge variant="secondary" className="bg-green-100 text-green-700">
                {formatCurrency(revenueDrivers.reduce((sum, d) => sum + d.value, 0))}
              </Badge>
            </div>
            <CardDescription>Growth opportunities across key value levers</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {revenueDrivers.map((driver, i) => (
              <div key={i} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">{driver.name}</span>
                  <span className="text-sm font-medium">{formatCurrency(driver.value)}</span>
                </div>
                <Progress value={driver.percentOfTotal * 100} className="h-1.5" />
              </div>
            ))}
            {revenueDrivers.length > 0 && (
              <div className="pt-3 border-t">
                <div className="flex items-center gap-2 p-2 bg-green-50 rounded-md">
                  <Target className="h-4 w-4 text-green-600" />
                  <p className="text-xs text-green-800">
                    Top Driver: {revenueDrivers[0].name} ({formatCurrency(revenueDrivers[0].value)})
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Cost Savings */}
        <Card className="bg-white">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-blue-600" />
                <CardTitle className="text-base">Cost Savings</CardTitle>
              </div>
              <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                {formatCurrency(costDrivers.reduce((sum, d) => sum + d.value, 0))}
              </Badge>
            </div>
            <CardDescription>Operational efficiency improvements</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {costDrivers.map((driver, i) => (
              <div key={i} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">{driver.name}</span>
                  <span className="text-sm font-medium">{formatCurrency(driver.value)}</span>
                </div>
                <Progress value={driver.percentOfTotal * 100} className="h-1.5" />
              </div>
            ))}
            {costDrivers.length > 0 && (
              <div className="pt-3 border-t">
                <div className="flex items-center gap-2 p-2 bg-blue-50 rounded-md">
                  <Zap className="h-4 w-4 text-blue-600" />
                  <p className="text-xs text-blue-800">
                    Efficiency Focus: Rep time savings of 6 hrs/week = 1000+ hrs productivity gain per rep
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Implementation Roadmap */}
      {(data.keySuccessFactors || data.implementationNotes) && (
        <>
          <div className="flex items-center gap-2 mt-8 mb-4">
            <Target className="h-5 w-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Implementation Roadmap</h2>
          </div>
          <Card className="bg-white">
            <CardHeader>
              <CardTitle className="text-sm">Critical success factors and next steps</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {data.keySuccessFactors && data.keySuccessFactors.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Key Success Factors</h4>
                  <div className="space-y-2">
                    {data.keySuccessFactors.map((factor, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                        <p className="text-sm text-gray-600">{factor}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {data.implementationNotes && data.implementationNotes.length > 0 && (
                <div className="pt-4 border-t">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Implementation Notes</h4>
                  <div className="space-y-2">
                    {data.implementationNotes.map((note, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <ChevronRight className="h-4 w-4 text-gray-400 mt-0.5" />
                        <p className="text-sm text-gray-600">{note}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Financial Overview Table */}
      <div className="flex items-center gap-2 mt-8 mb-4">
        <Calculator className="h-5 w-5 text-gray-600" />
        <h2 className="text-lg font-semibold text-gray-900">Financial Overview</h2>
      </div>
      
      <Card className="bg-white">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <tbody>
                <tr className="border-b">
                  <td className="px-6 py-4 text-sm text-gray-700">Total Benefits (Y1)</td>
                  <td className="px-6 py-4 text-sm font-medium text-right">
                    ${data.financialDetails.totalBenefitsY1.toLocaleString()}
                  </td>
                </tr>
                <tr className="border-b">
                  <td className="px-6 py-4 text-sm text-gray-700">Total Costs (Y1)</td>
                  <td className="px-6 py-4 text-sm font-medium text-right">
                    ${data.financialDetails.totalCostsY1.toLocaleString()}
                  </td>
                </tr>
                <tr className="border-b bg-gray-50">
                  <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                    Net Benefit (Y1 Realized)
                  </td>
                  <td className="px-6 py-4 text-sm font-bold text-right text-green-600">
                    ${data.financialDetails.netBenefitRealized.toLocaleString()}
                  </td>
                </tr>
                <tr className="border-b">
                  <td className="px-6 py-4 text-sm text-gray-700">Net Benefit (Steady State)</td>
                  <td className="px-6 py-4 text-sm font-medium text-right">
                    ${data.financialDetails.netBenefitSteadyState.toLocaleString()}
                  </td>
                </tr>
                <tr className="bg-blue-50">
                  <td className="px-6 py-4 text-sm font-semibold text-blue-900">3-Year NPV</td>
                  <td className="px-6 py-4 text-sm font-bold text-right text-blue-600">
                    ${data.financialDetails.npv3Year.toLocaleString()}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="px-6 py-3 bg-gray-50 border-t">
            <p className="text-xs text-gray-600 text-center">
              Discounted at {formatPercent(data.financialDetails.discountRate)} cost of capital
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Key Assumptions */}
      <div className="flex items-center gap-2 mt-8 mb-4">
        <Briefcase className="h-5 w-5 text-gray-600" />
        <h2 className="text-lg font-semibold text-gray-900">Key Assumptions</h2>
      </div>

      <Card className="bg-white">
        <CardHeader>
          <CardTitle className="text-sm">Critical parameters driving the analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-600">Sales Reps</p>
              <p className="text-lg font-semibold">{data.assumptions.salesReps}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600">Rep Adoption</p>
              <p className="text-lg font-semibold">{formatPercent(data.assumptions.adoptionRate)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600">Gross Margin</p>
              <p className="text-lg font-semibold">{formatPercent(data.assumptions.grossMargin)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600">Adoption Ramp</p>
              <p className="text-lg font-semibold">{formatPercent(data.keyMetrics.adoptionRamp)}</p>
            </div>
          </div>
          {data.assumptions.criticalFactor && (
            <div className="mt-4 p-3 bg-yellow-50 rounded-md">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5" />
                <p className="text-xs text-yellow-800">
                  Critical Success Factor: {data.assumptions.criticalFactor}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

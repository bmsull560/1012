"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Users,
  DollarSign,
  Activity,
  Target,
  Calendar,
  Download,
  Filter,
  RefreshCw,
  ArrowUp,
  ArrowDown,
  Clock,
  CheckCircle,
  AlertCircle,
  PieChart,
  LineChart,
  FileText,
  Brain,
  Sparkles,
  Shield,
} from "lucide-react";
import {
  LineChart as RechartsLineChart,
  Line,
  BarChart,
  Bar,
  PieChart as RechartsPieChart,
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
} from "recharts";
import { cn } from "@/utils/cn";
import { useAuthStore } from "@/stores/authStore";

// Mock data for charts
const revenueData = [
  { month: "Jan", actual: 45000, target: 50000 },
  { month: "Feb", actual: 52000, target: 55000 },
  { month: "Mar", actual: 58000, target: 60000 },
  { month: "Apr", actual: 65000, target: 65000 },
  { month: "May", actual: 72000, target: 70000 },
  { month: "Jun", actual: 78000, target: 75000 },
];

const valueDriversData = [
  { name: "Cost Reduction", value: 35, color: "#3b82f6" },
  { name: "Revenue Growth", value: 28, color: "#10b981" },
  { name: "Efficiency Gains", value: 22, color: "#f59e0b" },
  { name: "Risk Mitigation", value: 15, color: "#ef4444" },
];

const agentActivityData = [
  { day: "Mon", architect: 12, committer: 8, executor: 15, amplifier: 5 },
  { day: "Tue", architect: 15, committer: 10, executor: 18, amplifier: 7 },
  { day: "Wed", architect: 18, committer: 12, executor: 20, amplifier: 8 },
  { day: "Thu", architect: 14, committer: 15, executor: 22, amplifier: 10 },
  { day: "Fri", architect: 20, committer: 18, executor: 25, amplifier: 12 },
];

const projectsData = [
  { name: "Digital Transformation", progress: 75, value: 2500000, status: "on-track" },
  { name: "Cloud Migration", progress: 60, value: 1800000, status: "on-track" },
  { name: "Process Automation", progress: 45, value: 950000, status: "at-risk" },
  { name: "Data Analytics", progress: 90, value: 3200000, status: "ahead" },
  { name: "Customer Experience", progress: 30, value: 1200000, status: "delayed" },
];

// KPI Card Component
interface KPICardProps {
  title: string;
  value: string | number;
  change: number;
  icon: React.ElementType;
  trend: "up" | "down" | "neutral";
  color?: string;
}

function KPICard({ title, value, change, icon: Icon, trend, color }: KPICardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">{title}</p>
            <div className="text-2xl font-bold">{value}</div>
            <div className="flex items-center gap-1">
              {trend === "up" ? (
                <ArrowUp className="h-4 w-4 text-green-500" />
              ) : trend === "down" ? (
                <ArrowDown className="h-4 w-4 text-red-500" />
              ) : null}
              <span
                className={cn(
                  "text-sm",
                  trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500" : "text-gray-500"
                )}
              >
                {Math.abs(change)}%
              </span>
              <span className="text-sm text-muted-foreground">vs last month</span>
            </div>
          </div>
          <div className={cn("p-3 rounded-lg", color || "bg-primary/10")}>
            <Icon className={cn("h-6 w-6", color ? "text-white" : "text-primary")} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuthStore() as { user: { email?: string; firstName?: string; lastName?: string } | null };
  const [dateRange, setDateRange] = useState("30d");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState("revenue");

  // Simulate data refresh
  const refreshData = () => {
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 1500);
  };

  // Calculate summary stats
  const totalValue = projectsData.reduce((sum, p) => sum + p.value, 0);
  const avgProgress = projectsData.reduce((sum, p) => sum + p.progress, 0) / projectsData.length;
  const onTrackProjects = projectsData.filter(p => p.status === "on-track" || p.status === "ahead").length;

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Welcome back, {user?.firstName || 'User'}! Here's your value realization overview.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-40">
              <Calendar className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
              <SelectItem value="1y">Last year</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={refreshData} disabled={isLoading}>
            <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
            Refresh
          </Button>
          <Button>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Value Realized"
          value={`$${(totalValue / 1000000).toFixed(1)}M`}
          change={23.5}
          icon={DollarSign}
          trend="up"
          color="bg-green-500"
        />
        <KPICard
          title="Active Projects"
          value={projectsData.length}
          change={-5.2}
          icon={Target}
          trend="down"
          color="bg-blue-500"
        />
        <KPICard
          title="Agent Interactions"
          value="1,284"
          change={18.7}
          icon={Brain}
          trend="up"
          color="bg-purple-500"
        />
        <KPICard
          title="Success Rate"
          value={`${Math.round(avgProgress)}%`}
          change={8.3}
          icon={CheckCircle}
          trend="up"
          color="bg-orange-500"
        />
      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Value Realization Trend</CardTitle>
            <CardDescription>Actual vs Target value over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="target"
                  stackId="1"
                  stroke="#94a3b8"
                  fill="#e2e8f0"
                  name="Target"
                />
                <Area
                  type="monotone"
                  dataKey="actual"
                  stackId="2"
                  stroke="#3b82f6"
                  fill="#93c5fd"
                  name="Actual"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Value Drivers Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Value Drivers Distribution</CardTitle>
            <CardDescription>Contribution by value driver category</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsPieChart>
                <Pie
                  data={valueDriversData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {valueDriversData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </RechartsPieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Tabs Section */}
      <Tabs defaultValue="projects" className="space-y-4">
        <TabsList>
          <TabsTrigger value="projects">Projects</TabsTrigger>
          <TabsTrigger value="agents">Agent Activity</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        {/* Projects Tab */}
        <TabsContent value="projects" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Active Projects</CardTitle>
              <CardDescription>Track progress and value across all projects</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {projectsData.map((project) => (
                  <div key={project.name} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <h4 className="font-medium">{project.name}</h4>
                        <Badge
                          variant={
                            project.status === "on-track"
                              ? "default"
                              : project.status === "ahead"
                              ? "outline"
                              : project.status === "at-risk"
                              ? "secondary"
                              : "destructive"
                          }
                          className={
                            project.status === "ahead"
                              ? "bg-green-100 text-green-800 border-green-200"
                              : project.status === "at-risk"
                              ? "bg-yellow-100 text-yellow-800 border-yellow-200"
                              : ""
                          }
                        >
                          {project.status}
                        </Badge>
                      </div>
                      <span className="text-sm font-medium">
                        ${(project.value / 1000000).toFixed(1)}M
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={project.progress} className="flex-1" />
                      <span className="text-sm text-muted-foreground w-12">
                        {project.progress}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Agent Activity Tab */}
        <TabsContent value="agents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Activity</CardTitle>
              <CardDescription>Interactions by agent type over the week</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={agentActivityData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="architect" fill="#8b5cf6" name="Architect" />
                  <Bar dataKey="committer" fill="#3b82f6" name="Committer" />
                  <Bar dataKey="executor" fill="#10b981" name="Executor" />
                  <Bar dataKey="amplifier" fill="#f59e0b" name="Amplifier" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Architect</p>
                    <p className="text-2xl font-bold">79</p>
                    <p className="text-xs text-green-500">+12% this week</p>
                  </div>
                  <Brain className="h-8 w-8 text-purple-500" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Committer</p>
                    <p className="text-2xl font-bold">63</p>
                    <p className="text-xs text-green-500">+8% this week</p>
                  </div>
                  <Shield className="h-8 w-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Executor</p>
                    <p className="text-2xl font-bold">100</p>
                    <p className="text-xs text-green-500">+15% this week</p>
                  </div>
                  <Target className="h-8 w-8 text-green-500" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Amplifier</p>
                    <p className="text-2xl font-bold">42</p>
                    <p className="text-xs text-green-500">+20% this week</p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-orange-500" />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>System Performance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">API Response Time</span>
                    <span className="text-sm font-medium">142ms</span>
                  </div>
                  <Progress value={85} />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">Database Queries</span>
                    <span className="text-sm font-medium">98% optimized</span>
                  </div>
                  <Progress value={98} />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">Cache Hit Rate</span>
                    <span className="text-sm font-medium">94%</span>
                  </div>
                  <Progress value={94} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>User Satisfaction</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-4xl font-bold text-green-500">4.8</div>
                  <div className="text-sm text-muted-foreground">out of 5.0</div>
                  <div className="flex justify-center mt-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Sparkles
                        key={star}
                        className={cn(
                          "h-5 w-5",
                          star <= 4.8 ? "text-yellow-400 fill-yellow-400" : "text-gray-300"
                        )}
                      />
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Ease of Use</span>
                    <span className="font-medium">4.9</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span>Value Delivered</span>
                    <span className="font-medium">4.7</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span>Support Quality</span>
                    <span className="font-medium">4.8</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>System Health</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Uptime</span>
                  <Badge variant="outline" className="bg-green-100 text-green-800 border-green-200">99.98%</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Error Rate</span>
                  <Badge variant="outline" className="bg-green-100 text-green-800 border-green-200">0.02%</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Active Users</span>
                  <Badge>1,284</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Avg Session</span>
                  <Badge>24 min</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Data Processed</span>
                  <Badge>2.4 TB</Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

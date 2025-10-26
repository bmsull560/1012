"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Progress } from "@/components/ui/index";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Building2,
  Users,
  Settings,
  CreditCard,
  Shield,
  Activity,
  Plus,
  Edit3,
  Trash2,
  MoreVertical,
  Search,
  Filter,
  Download,
  Upload,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Calendar,
  Globe,
  Lock,
  Unlock,
  Mail,
  Phone,
  MapPin,
  Briefcase,
  Database,
  Cpu,
  HardDrive,
  Zap,
  BarChart3,
  PieChart,
  FileText,
  Copy,
  ExternalLink,
  RefreshCw,
  Loader2,
} from "lucide-react";
import { useTenantStore } from "@/stores/tenantStore";
import { useAuthStore } from "@/stores/authStore";
import { useRouter } from "next/navigation";
import { cn } from "@/utils/cn";
import { Tenant, TenantStatus, TenantSubscription } from "@/types/tenant";

export default function TenantAdminPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const {
    tenants,
    currentTenant,
    isLoading,
    error,
    createTenant,
    updateTenant,
    deleteTenant,
    switchTenant,
    clearError,
  } = useTenantStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<TenantStatus | "all">("all");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

  // New tenant form state
  const [newTenantData, setNewTenantData] = useState({
    name: "",
    slug: "",
    subdomain: "",
    adminEmail: "",
    adminName: "",
    plan: "starter",
    industry: "",
    companySize: "",
  });

  // Check if user is super admin
  useEffect(() => {
    if (user?.role !== "admin") {
      router.push("/dashboard");
    }
  }, [user, router]);

  // Filter tenants based on search and status
  const filteredTenants = tenants.filter((tenant) => {
    const matchesSearch = 
      tenant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tenant.subdomain.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || tenant.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Calculate statistics
  const stats = {
    total: tenants.length,
    active: tenants.filter(t => t.status === "active").length,
    trial: tenants.filter(t => t.subscription.status === "trialing").length,
    revenue: tenants.reduce((sum, t) => {
      if (t.subscription.status === "active") {
        return sum + (t.subscription.monthlyPrice * t.subscription.seats);
      }
      return sum;
    }, 0),
  };

  const handleCreateTenant = async () => {
    try {
      const tenant = await createTenant({
        name: newTenantData.name,
        slug: newTenantData.slug,
        subdomain: newTenantData.subdomain,
        status: "active",
        subscription: {
          plan: newTenantData.plan as any,
          status: "trialing",
          currentPeriodStart: new Date(),
          currentPeriodEnd: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000), // 14 days trial
          trialEndsAt: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000),
          seats: 5,
          monthlyPrice: 0,
          billingEmail: newTenantData.adminEmail,
        },
        metadata: {
          industry: newTenantData.industry,
          companySize: newTenantData.companySize,
          onboardingCompleted: false,
        },
        settings: {
          allowSignup: true,
          requireEmailVerification: true,
          allowGoogleAuth: true,
          allowSAML: false,
          passwordPolicy: {
            minLength: 8,
            requireUppercase: true,
            requireLowercase: true,
            requireNumbers: true,
            requireSpecialChars: false,
            preventReuse: 3,
          },
          sessionTimeout: 60,
          mfaRequired: false,
          customBranding: false,
          features: {
            aiAgents: true,
            valueModeling: true,
            advancedAnalytics: newTenantData.plan !== "starter",
            customIntegrations: newTenantData.plan === "enterprise",
            apiAccess: newTenantData.plan !== "starter",
            whiteLabeling: newTenantData.plan === "enterprise",
            customReports: newTenantData.plan !== "starter",
            unlimitedUsers: newTenantData.plan === "enterprise",
          },
        },
        limits: {
          maxUsers: newTenantData.plan === "starter" ? 5 : newTenantData.plan === "professional" ? 25 : 999999,
          maxProjects: newTenantData.plan === "starter" ? 3 : newTenantData.plan === "professional" ? 10 : 999999,
          maxValueModels: newTenantData.plan === "starter" ? 10 : newTenantData.plan === "professional" ? 50 : 999999,
          maxApiCalls: newTenantData.plan === "starter" ? 1000 : newTenantData.plan === "professional" ? 10000 : 999999,
          maxStorageGB: newTenantData.plan === "starter" ? 5 : newTenantData.plan === "professional" ? 50 : 999999,
          maxMonthlyAgentCalls: newTenantData.plan === "starter" ? 100 : newTenantData.plan === "professional" ? 1000 : 999999,
          currentUsage: {
            users: 1,
            projects: 0,
            valueModels: 0,
            apiCalls: 0,
            storageGB: 0,
            agentCalls: 0,
          },
        },
      });

      setShowCreateDialog(false);
      setNewTenantData({
        name: "",
        slug: "",
        subdomain: "",
        adminEmail: "",
        adminName: "",
        plan: "starter",
        industry: "",
        companySize: "",
      });
    } catch (error) {
      console.error("Failed to create tenant:", error);
    }
  };

  const handleDeleteTenant = async () => {
    if (selectedTenant) {
      try {
        await deleteTenant(selectedTenant.id);
        setShowDeleteConfirm(false);
        setSelectedTenant(null);
      } catch (error) {
        console.error("Failed to delete tenant:", error);
      }
    }
  };

  const handleSuspendTenant = async (tenant: Tenant) => {
    try {
      await updateTenant(tenant.id, { status: "suspended" });
    } catch (error) {
      console.error("Failed to suspend tenant:", error);
    }
  };

  const handleActivateTenant = async (tenant: Tenant) => {
    try {
      await updateTenant(tenant.id, { status: "active" });
    } catch (error) {
      console.error("Failed to activate tenant:", error);
    }
  };

  const getStatusColor = (status: TenantStatus) => {
    switch (status) {
      case "active": return "text-green-600 bg-green-50";
      case "suspended": return "text-red-600 bg-red-50";
      case "pending": return "text-yellow-600 bg-yellow-50";
      case "deleted": return "text-gray-600 bg-gray-50";
      default: return "text-gray-600 bg-gray-50";
    }
  };

  const getPlanColor = (plan: string) => {
    switch (plan) {
      case "starter": return "text-blue-600 bg-blue-50";
      case "professional": return "text-purple-600 bg-purple-50";
      case "enterprise": return "text-orange-600 bg-orange-50";
      default: return "text-gray-600 bg-gray-50";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Tenant Management</h1>
              <p className="text-sm text-gray-500 mt-1">
                Manage all tenants, subscriptions, and configurations
              </p>
            </div>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="w-4 h-4 mr-2" />
              New Tenant
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="px-6 py-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Tenants</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
              <p className="text-xs text-muted-foreground mt-1">
                <TrendingUp className="w-3 h-3 inline mr-1" />
                +12% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Active Tenants</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.active}</div>
              <Progress value={(stats.active / stats.total) * 100} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Trial Accounts</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{stats.trial}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Converting at 68% rate
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Monthly Revenue</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                ${stats.revenue.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                <TrendingUp className="w-3 h-3 inline mr-1" />
                +23% from last month
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="px-6 pb-4">
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search tenants..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as any)}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="suspended">Suspended</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
            </SelectContent>
          </Select>

          <Button variant="outline">
            <Filter className="w-4 h-4 mr-2" />
            More Filters
          </Button>

          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Tenants Table */}
      <div className="px-6">
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tenant</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Plan</TableHead>
                  <TableHead>Users</TableHead>
                  <TableHead>Usage</TableHead>
                  <TableHead>Revenue</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTenants.map((tenant) => (
                  <TableRow key={tenant.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold">
                          {tenant.name.charAt(0)}
                        </div>
                        <div>
                          <div className="font-medium">{tenant.name}</div>
                          <div className="text-sm text-gray-500">{tenant.subdomain}.valueverse.ai</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={cn("capitalize", getStatusColor(tenant.status))}>
                        {tenant.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={cn("capitalize", getPlanColor(tenant.subscription.plan))}>
                        {tenant.subscription.plan}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Users className="w-4 h-4 text-gray-400" />
                        <span>{tenant.limits.currentUsage.users}/{tenant.limits.maxUsers}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Database className="w-3 h-3 text-gray-400" />
                          <div className="w-20 bg-gray-200 rounded-full h-1.5">
                            <div 
                              className="bg-blue-600 h-1.5 rounded-full" 
                              style={{ width: `${(tenant.limits.currentUsage.storageGB / tenant.limits.maxStorageGB) * 100}%` }}
                            />
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Zap className="w-3 h-3 text-gray-400" />
                          <div className="w-20 bg-gray-200 rounded-full h-1.5">
                            <div 
                              className="bg-green-600 h-1.5 rounded-full" 
                              style={{ width: `${(tenant.limits.currentUsage.apiCalls / tenant.limits.maxApiCalls) * 100}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">
                        ${(tenant.subscription.monthlyPrice * tenant.subscription.seats).toLocaleString()}/mo
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm text-gray-500">
                        {new Date(tenant.createdAt).toLocaleDateString()}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => router.push(`/admin/tenants/${tenant.id}`)}>
                            <Edit3 className="w-4 h-4 mr-2" />
                            Edit Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => switchTenant(tenant.id)}>
                            <ExternalLink className="w-4 h-4 mr-2" />
                            Switch to Tenant
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => router.push(`/admin/tenants/${tenant.id}/users`)}>
                            <Users className="w-4 h-4 mr-2" />
                            Manage Users
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => router.push(`/admin/tenants/${tenant.id}/billing`)}>
                            <CreditCard className="w-4 h-4 mr-2" />
                            Billing
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {tenant.status === "active" ? (
                            <DropdownMenuItem 
                              onClick={() => handleSuspendTenant(tenant)}
                              className="text-yellow-600"
                            >
                              <Lock className="w-4 h-4 mr-2" />
                              Suspend
                            </DropdownMenuItem>
                          ) : (
                            <DropdownMenuItem 
                              onClick={() => handleActivateTenant(tenant)}
                              className="text-green-600"
                            >
                              <Unlock className="w-4 h-4 mr-2" />
                              Activate
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem 
                            onClick={() => {
                              setSelectedTenant(tenant);
                              setShowDeleteConfirm(true);
                            }}
                            className="text-red-600"
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Create Tenant Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create New Tenant</DialogTitle>
            <DialogDescription>
              Set up a new tenant account with initial configuration
            </DialogDescription>
          </DialogHeader>

          <div className="grid grid-cols-2 gap-4 py-4">
            <div>
              <Label htmlFor="name">Company Name</Label>
              <Input
                id="name"
                value={newTenantData.name}
                onChange={(e) => setNewTenantData({ ...newTenantData, name: e.target.value })}
                placeholder="Acme Corporation"
              />
            </div>
            <div>
              <Label htmlFor="subdomain">Subdomain</Label>
              <div className="flex">
                <Input
                  id="subdomain"
                  value={newTenantData.subdomain}
                  onChange={(e) => setNewTenantData({ ...newTenantData, subdomain: e.target.value })}
                  placeholder="acme"
                  className="rounded-r-none"
                />
                <div className="px-3 py-2 bg-gray-100 border border-l-0 rounded-r-md text-sm text-gray-500">
                  .valueverse.ai
                </div>
              </div>
            </div>
            <div>
              <Label htmlFor="adminEmail">Admin Email</Label>
              <Input
                id="adminEmail"
                type="email"
                value={newTenantData.adminEmail}
                onChange={(e) => setNewTenantData({ ...newTenantData, adminEmail: e.target.value })}
                placeholder="admin@acme.com"
              />
            </div>
            <div>
              <Label htmlFor="adminName">Admin Name</Label>
              <Input
                id="adminName"
                value={newTenantData.adminName}
                onChange={(e) => setNewTenantData({ ...newTenantData, adminName: e.target.value })}
                placeholder="John Doe"
              />
            </div>
            <div>
              <Label htmlFor="plan">Subscription Plan</Label>
              <Select
                value={newTenantData.plan}
                onValueChange={(value) => setNewTenantData({ ...newTenantData, plan: value })}
              >
                <SelectTrigger id="plan">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="starter">Starter - $99/mo</SelectItem>
                  <SelectItem value="professional">Professional - $299/mo</SelectItem>
                  <SelectItem value="enterprise">Enterprise - Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="industry">Industry</Label>
              <Select
                value={newTenantData.industry}
                onValueChange={(value) => setNewTenantData({ ...newTenantData, industry: value })}
              >
                <SelectTrigger id="industry">
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
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateTenant} disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Tenant"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Tenant</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete {selectedTenant?.name}? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <Alert className="border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              All data associated with this tenant will be permanently deleted, including:
              <ul className="list-disc list-inside mt-2">
                <li>All users and their data</li>
                <li>All projects and value models</li>
                <li>All analytics and reports</li>
                <li>All billing history</li>
              </ul>
            </AlertDescription>
          </Alert>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteConfirm(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteTenant} disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                "Delete Tenant"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

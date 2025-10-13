"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Building2,
  Search,
  Plus,
  ArrowRight,
  Users,
  Sparkles,
  Clock,
  CheckCircle,
  AlertCircle,
  LogOut,
  Settings,
  TrendingUp,
  Calendar,
  Globe,
  Shield,
  Loader2,
} from "lucide-react";
import { useTenantStore } from "@/stores/tenantStore";
import { useAuthStore } from "@/stores/authStore";
import { useRouter } from "next/navigation";
import { cn } from "@/utils/cn";

export default function SelectTenantPage() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const { tenants, currentTenant, setCurrentTenant, isLoading, error } = useTenantStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);

  // Load user's tenants on mount
  useEffect(() => {
    // In a real app, this would fetch tenants the user has access to
    // For now, we'll use mock data or existing tenants
    if (currentTenant) {
      router.push("/dashboard");
    }
  }, [currentTenant, router]);

  // Filter tenants based on search
  const filteredTenants = tenants.filter(
    (tenant) =>
      tenant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tenant.subdomain.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSelectTenant = (tenantId: string) => {
    setSelectedTenantId(tenantId);
  };

  const handleContinue = () => {
    if (selectedTenantId) {
      const tenant = tenants.find((t) => t.id === selectedTenantId);
      if (tenant) {
        setCurrentTenant(tenant);
        router.push("/dashboard");
      }
    }
  };

  const handleCreateTenant = () => {
    router.push("/create-tenant");
  };

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  const getPlanColor = (plan: string) => {
    switch (plan) {
      case "starter":
        return "bg-blue-100 text-blue-700";
      case "professional":
        return "bg-purple-100 text-purple-700";
      case "enterprise":
        return "bg-orange-100 text-orange-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "trialing":
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case "suspended":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-blue-50">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading workspaces...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold">ValueVerse</span>
            </div>
            
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                {user?.email}
              </span>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="w-4 h-4 mr-2" />
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Title Section */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Select Your Workspace
            </h1>
            <p className="text-gray-600">
              Choose a workspace to continue or create a new one
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert className="mb-6 border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">{error}</AlertDescription>
            </Alert>
          )}

          {/* Search Bar */}
          {tenants.length > 3 && (
            <div className="mb-6">
              <div className="relative max-w-md mx-auto">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <Input
                  placeholder="Search workspaces..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
          )}

          {/* Tenant Cards */}
          {filteredTenants.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {filteredTenants.map((tenant) => (
                <motion.div
                  key={tenant.id}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Card
                    className={cn(
                      "cursor-pointer transition-all",
                      selectedTenantId === tenant.id && "ring-2 ring-primary"
                    )}
                    onClick={() => handleSelectTenant(tenant.id)}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold text-lg">
                            {tenant.name.charAt(0)}
                          </div>
                          <div>
                            <CardTitle className="text-lg">{tenant.name}</CardTitle>
                            <CardDescription className="text-xs">
                              {tenant.subdomain}.valueverse.ai
                            </CardDescription>
                          </div>
                        </div>
                        {getStatusIcon(tenant.subscription.status)}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {/* Plan Badge */}
                        <div className="flex items-center justify-between">
                          <Badge className={cn("text-xs", getPlanColor(tenant.subscription.plan))}>
                            {tenant.subscription.plan}
                          </Badge>
                          {tenant.subscription.status === "trialing" && (
                            <span className="text-xs text-muted-foreground">
                              Trial ends {new Date(tenant.subscription.trialEndsAt!).toLocaleDateString()}
                            </span>
                          )}
                        </div>

                        {/* Stats */}
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="flex items-center gap-1">
                            <Users className="w-3 h-3 text-muted-foreground" />
                            <span>{tenant.limits.currentUsage.users} users</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <TrendingUp className="w-3 h-3 text-muted-foreground" />
                            <span>{tenant.limits.currentUsage.valueModels} models</span>
                          </div>
                        </div>

                        {/* Last Activity */}
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Clock className="w-3 h-3" />
                          <span>
                            Last active{" "}
                            {tenant.metadata.lastActivityAt
                              ? new Date(tenant.metadata.lastActivityAt).toLocaleDateString()
                              : "Never"}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Building2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No Workspaces Found
              </h3>
              <p className="text-gray-600 mb-6">
                {searchQuery
                  ? "No workspaces match your search"
                  : "You don't have access to any workspaces yet"}
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-center gap-4">
            {selectedTenantId && (
              <Button size="lg" onClick={handleContinue}>
                Continue to Workspace
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            )}
            
            <Button
              size="lg"
              variant={selectedTenantId ? "outline" : "default"}
              onClick={handleCreateTenant}
            >
              <Plus className="w-4 h-4 mr-2" />
              Create New Workspace
            </Button>
          </div>

          {/* Help Section */}
          <div className="mt-12 text-center">
            <p className="text-sm text-muted-foreground mb-4">
              Need help accessing your workspace?
            </p>
            <div className="flex items-center justify-center gap-4">
              <Button variant="link" size="sm">
                <Shield className="w-4 h-4 mr-2" />
                Contact Admin
              </Button>
              <Button variant="link" size="sm">
                <Settings className="w-4 h-4 mr-2" />
                Account Settings
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

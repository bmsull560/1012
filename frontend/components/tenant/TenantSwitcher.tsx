"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Building2,
  ChevronDown,
  Plus,
  Check,
  Settings,
  Users,
  CreditCard,
  LogOut,
  Sparkles,
  Search,
  ExternalLink,
} from "lucide-react";
import { useTenantStore } from "@/stores/tenantStore";
import { useAuthStore } from "@/stores/authStore";
import { useTenant } from "@/hooks/useTenant";
import { useRouter } from "next/navigation";
import { cn } from "@/utils/cn";

export function TenantSwitcher() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { currentTenant, tenants, switchTenant, createTenant } = useTenantStore();
  const { isSuperAdmin } = useTenant();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [newTenantName, setNewTenantName] = useState("");
  const [newTenantSubdomain, setNewTenantSubdomain] = useState("");

  // Filter tenants based on search
  const filteredTenants = tenants.filter(
    (tenant) =>
      tenant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tenant.subdomain.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSwitchTenant = async (tenantId: string) => {
    await switchTenant(tenantId);
    router.push("/dashboard");
  };

  const handleCreateTenant = async () => {
    try {
      await createTenant({
        name: newTenantName,
        subdomain: newTenantSubdomain,
        status: "active",
      });
      setShowCreateDialog(false);
      setNewTenantName("");
      setNewTenantSubdomain("");
    } catch (error) {
      console.error("Failed to create tenant:", error);
    }
  };

  const getPlanBadge = (plan: string) => {
    const colors: Record<string, string> = {
      starter: "bg-blue-100 text-blue-700",
      professional: "bg-purple-100 text-purple-700",
      enterprise: "bg-orange-100 text-orange-700",
    };
    return colors[plan] || "bg-gray-100 text-gray-700";
  };

  if (!currentTenant) {
    return (
      <Button variant="outline" size="sm" disabled>
        <Building2 className="w-4 h-4 mr-2" />
        No Tenant Selected
      </Button>
    );
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="min-w-[200px] justify-between">
            <div className="flex items-center gap-2">
              <Avatar className="w-5 h-5">
                <AvatarImage src={currentTenant.logo} />
                <AvatarFallback className="text-xs">
                  {currentTenant.name.charAt(0)}
                </AvatarFallback>
              </Avatar>
              <span className="truncate max-w-[150px]">{currentTenant.name}</span>
            </div>
            <ChevronDown className="w-4 h-4 ml-2 opacity-50" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-[300px]">
          <DropdownMenuLabel>
            <div className="flex items-center justify-between">
              <span>Current Workspace</span>
              <Badge className={cn("text-xs", getPlanBadge(currentTenant.subscription.plan))}>
                {currentTenant.subscription.plan}
              </Badge>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          
          {/* Current tenant info */}
          <div className="px-2 py-2">
            <div className="flex items-center gap-3">
              <Avatar>
                <AvatarImage src={currentTenant.logo} />
                <AvatarFallback>{currentTenant.name.charAt(0)}</AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{currentTenant.name}</p>
                <p className="text-xs text-muted-foreground truncate">
                  {currentTenant.subdomain}.valueverse.ai
                </p>
              </div>
            </div>
            
            {/* Quick stats */}
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-1">
                <Users className="w-3 h-3 text-muted-foreground" />
                <span>{currentTenant.limits.currentUsage.users} users</span>
              </div>
              <div className="flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-muted-foreground" />
                <span>{currentTenant.limits.currentUsage.valueModels} models</span>
              </div>
            </div>
          </div>
          
          <DropdownMenuSeparator />
          
          {/* Quick actions */}
          <DropdownMenuItem onClick={() => router.push("/settings/workspace")}>
            <Settings className="w-4 h-4 mr-2" />
            Workspace Settings
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => router.push("/settings/billing")}>
            <CreditCard className="w-4 h-4 mr-2" />
            Billing & Usage
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => router.push("/settings/users")}>
            <Users className="w-4 h-4 mr-2" />
            Manage Users
          </DropdownMenuItem>
          
          {/* Tenant switcher for users with access to multiple tenants */}
          {(tenants.length > 1 || isSuperAdmin) && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuLabel>Switch Workspace</DropdownMenuLabel>
              
              {/* Search for tenants */}
              {tenants.length > 5 && (
                <div className="px-2 pb-2">
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="Search workspaces..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-8 h-9"
                    />
                  </div>
                </div>
              )}
              
              <div className="max-h-[200px] overflow-y-auto">
                {filteredTenants.map((tenant) => (
                  <DropdownMenuItem
                    key={tenant.id}
                    onClick={() => handleSwitchTenant(tenant.id)}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <Avatar className="w-5 h-5">
                        <AvatarImage src={tenant.logo} />
                        <AvatarFallback className="text-xs">
                          {tenant.name.charAt(0)}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="text-sm">{tenant.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {tenant.subdomain}.valueverse.ai
                        </p>
                      </div>
                    </div>
                    {tenant.id === currentTenant.id && (
                      <Check className="w-4 h-4 text-primary" />
                    )}
                  </DropdownMenuItem>
                ))}
              </div>
            </>
          )}
          
          {/* Create new tenant (super admin only) */}
          {isSuperAdmin && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setShowCreateDialog(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Create New Workspace
              </DropdownMenuItem>
            </>
          )}
          
          {/* Admin portal link */}
          {isSuperAdmin && (
            <DropdownMenuItem onClick={() => router.push("/admin/tenants")}>
              <ExternalLink className="w-4 h-4 mr-2" />
              Admin Portal
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Create Tenant Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Workspace</DialogTitle>
            <DialogDescription>
              Set up a new workspace for your organization
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="name">Workspace Name</Label>
              <Input
                id="name"
                value={newTenantName}
                onChange={(e) => setNewTenantName(e.target.value)}
                placeholder="Acme Corporation"
              />
            </div>
            <div>
              <Label htmlFor="subdomain">Subdomain</Label>
              <div className="flex">
                <Input
                  id="subdomain"
                  value={newTenantSubdomain}
                  onChange={(e) => setNewTenantSubdomain(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
                  placeholder="acme"
                  className="rounded-r-none"
                />
                <div className="px-3 py-2 bg-muted border border-l-0 rounded-r-md text-sm text-muted-foreground">
                  .valueverse.ai
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                This will be your workspace URL
              </p>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateTenant}>
              Create Workspace
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

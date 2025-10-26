"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
import { useTenant } from "@/hooks/useTenant";
import { Loader2 } from "lucide-react";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: {
    resource: string;
    action: string;
  };
  requiredRole?: string;
  requireAdmin?: boolean;
  requireSuperAdmin?: boolean;
}

export function ProtectedRoute({
  children,
  requiredPermission,
  requiredRole,
  requireAdmin,
  requireSuperAdmin,
}: ProtectedRouteProps) {
  const router = useRouter();
  const { isAuthenticated, user, isLoading: authLoading } = useAuthStore();
  const { tenant, hasPermission, isAdmin, isSuperAdmin } = useTenant();

  useEffect(() => {
    // Check authentication
    if (!authLoading && !isAuthenticated) {
      router.push("/auth/login");
      return;
    }

    // Check tenant context
    if (!authLoading && isAuthenticated && !tenant) {
      router.push("/select-tenant");
      return;
    }

    // Check role requirements
    if (requiredRole && user?.role !== requiredRole) {
      router.push("/unauthorized");
      return;
    }

    // Check admin requirements
    if (requireAdmin && !isAdmin) {
      router.push("/unauthorized");
      return;
    }

    // Check super admin requirements
    if (requireSuperAdmin && !isSuperAdmin) {
      router.push("/unauthorized");
      return;
    }

    // Check specific permissions
    if (requiredPermission) {
      const hasRequiredPermission = hasPermission(
        requiredPermission.resource,
        requiredPermission.action
      );
      if (!hasRequiredPermission) {
        router.push("/unauthorized");
        return;
      }
    }
  }, [
    authLoading,
    isAuthenticated,
    tenant,
    user,
    requiredPermission,
    requiredRole,
    requireAdmin,
    requireSuperAdmin,
    hasPermission,
    isAdmin,
    isSuperAdmin,
    router,
  ]);

  // Show loading state
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render children until all checks pass
  if (!isAuthenticated || !tenant) {
    return null;
  }

  // Check permissions
  if (requiredPermission) {
    const hasRequiredPermission = hasPermission(
      requiredPermission.resource,
      requiredPermission.action
    );
    if (!hasRequiredPermission) {
      return null;
    }
  }

  if (requireAdmin && !isAdmin) {
    return null;
  }

  if (requireSuperAdmin && !isSuperAdmin) {
    return null;
  }

  return <>{children}</>;
}

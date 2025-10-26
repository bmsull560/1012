"use client";

import type { ReactNode } from "react";
import { useMonitoring } from "@/lib/monitoring";

export function MonitoringProvider({ children }: { children: ReactNode }) {
  useMonitoring();

  return <>{children}</>;
}

export default MonitoringProvider;

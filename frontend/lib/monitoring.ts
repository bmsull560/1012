"use client";

import { useEffect } from "react";
import type { Metric } from "web-vitals";
import { onCLS, onFID, onINP, onLCP, onTTFB } from "web-vitals/attribution";

const MONITORING_EVENT_NAME = "monitoring:event";

interface TrackingPayload {
  [key: string]: unknown;
}

type ErrorInput = Error | string | unknown;

declare global {
  interface Window {
    analytics?: {
      track?: (eventName: string, payload?: TrackingPayload) => void;
    };
    dataLayer?: Array<Record<string, unknown>>;
    __monitoringEvents?: Array<{ event: string; payload: TrackingPayload; timestamp: number }>;
  }
}

let monitoringInitialized = false;

const recordEventLocally = (event: string, payload: TrackingPayload) => {
  if (typeof window === "undefined") {
    return;
  }

  if (!window.__monitoringEvents) {
    window.__monitoringEvents = [];
  }

  window.__monitoringEvents.push({ event, payload, timestamp: Date.now() });

  window.dispatchEvent(new CustomEvent(MONITORING_EVENT_NAME, { detail: { event, payload } }));
};

export const trackEvent = (event: string, payload: TrackingPayload = {}) => {
  if (typeof window === "undefined") {
    return;
  }

  recordEventLocally(event, payload);

  if (window.analytics?.track) {
    window.analytics.track(event, payload);
  } else if (Array.isArray(window.dataLayer)) {
    window.dataLayer.push({ event, ...payload });
  } else if (process.env.NODE_ENV !== "production") {
    // eslint-disable-next-line no-console
    console.info(`[monitoring] ${event}`, payload);
  }
};

const normalizeError = (error: ErrorInput): { message: string; stack?: string } => {
  if (error instanceof Error) {
    return { message: error.message, stack: error.stack };
  }

  if (typeof error === "string") {
    return { message: error };
  }

  try {
    return { message: JSON.stringify(error) };
  } catch {
    return { message: "Unknown error" };
  }
};

export const reportError = (error: ErrorInput, context: TrackingPayload = {}) => {
  const normalized = normalizeError(error);

  trackEvent("ui.error", {
    ...context,
    ...normalized,
  });

  if (process.env.NODE_ENV !== "production") {
    // eslint-disable-next-line no-console
    console.error("Captured UI error", normalized, context);
  }
};

const registerGlobalErrorListeners = () => {
  if (typeof window === "undefined") {
    return;
  }

  window.addEventListener("error", event => {
    reportError(event.error ?? event.message, {
      source: "window.error",
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    });
  });

  window.addEventListener("unhandledrejection", event => {
    reportError(event.reason ?? "Unhandled rejection", {
      source: "window.unhandledrejection",
    });
  });
};

const registerWebVitals = () => {
  const handlers: Array<(onReport: (metric: Metric) => void) => void> = [
    onCLS,
    onFID,
    onINP,
    onLCP,
    onTTFB,
  ];

  const reportMetric = (metric: Metric) => {
    const { name, value, rating, id } = metric;
    const payload: TrackingPayload = {
      name,
      value: Number(value.toFixed(2)),
      rating,
      id,
    };

    const attribution = (metric as Metric & { attribution?: Record<string, unknown> }).attribution;
    if (attribution) {
      payload.attribution = attribution;
    }

    trackEvent("web-vital", payload);
  };

  handlers.forEach(handler => handler(reportMetric));
};

const enableAccessibilityChecks = async () => {
  if (process.env.NODE_ENV === "production") {
    return;
  }

  try {
    const [{ default: React }, { default: ReactDOM }, { default: axe }] = await Promise.all([
      import("react"),
      import("react-dom"),
      import("@axe-core/react"),
    ]);

    axe(React, ReactDOM, 1000);
    trackEvent("accessibility.audit_enabled");
  } catch (error) {
    // eslint-disable-next-line no-console
    console.warn("Failed to initialize accessibility auditing", error);
  }
};

export const initMonitoring = () => {
  if (monitoringInitialized || typeof window === "undefined") {
    return;
  }

  monitoringInitialized = true;

  registerGlobalErrorListeners();
  registerWebVitals();
  enableAccessibilityChecks();
};

export const useMonitoring = () => {
  useEffect(() => {
    initMonitoring();
  }, []);
};


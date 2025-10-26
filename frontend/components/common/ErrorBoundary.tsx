"use client";

import React from "react";
import type { ErrorInfo, ReactNode } from "react";
import { reportError } from "@/lib/monitoring";

type FallbackRenderArgs = {
  error: Error;
  resetErrorBoundary: () => void;
};

type ErrorBoundaryProps = {
  children: ReactNode;
  fallback?: ReactNode;
  fallbackRender?: (args: FallbackRenderArgs) => ReactNode;
  onReset?: () => void;
  onError?: (error: Error, info: ErrorInfo) => void;
  resetKeys?: Array<unknown>;
};

type ErrorBoundaryState = {
  hasError: boolean;
  error?: Error;
};

const arraysAreDifferent = (a: Array<unknown> = [], b: Array<unknown> = []) => {
  if (a.length !== b.length) {
    return true;
  }

  return a.some((item, index) => !Object.is(item, b[index]));
};

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    reportError(error, {
      boundary: this.constructor.name,
      componentStack: info.componentStack,
    });

    if (this.props.onError) {
      this.props.onError(error, info);
    }
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    if (this.state.hasError && this.props.resetKeys && prevProps.resetKeys) {
      if (arraysAreDifferent(this.props.resetKeys, prevProps.resetKeys)) {
        this.resetErrorBoundary();
      }
    }
  }

  private resetErrorBoundary = () => {
    this.setState({ hasError: false, error: undefined });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render(): ReactNode {
    if (this.state.hasError) {
      const { fallback, fallbackRender } = this.props;
      const error = this.state.error ?? new Error("Unknown error");

      if (fallbackRender) {
        return fallbackRender({ error, resetErrorBoundary: this.resetErrorBoundary });
      }

      if (fallback) {
        return fallback;
      }

      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 p-6 text-center text-slate-700">
          <div className="text-lg font-semibold text-slate-900">Something went wrong</div>
          <p className="max-w-md text-sm">
            An unexpected error occurred. Try refreshing the page or contact support if the issue persists.
          </p>
          <button
            type="button"
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-slate-700"
            onClick={this.resetErrorBoundary}
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

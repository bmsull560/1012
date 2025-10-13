// frontend/src/app/layout.test.tsx

import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react";
import { RouterContext } from "next/dist/shared/lib/router-context";
import { createMockRouter } from "next-router-mock";
import { AuthProvider } from "../hooks/useAuth";
import Layout from "./layout";

jest.mock("../components/layout/Sidebar", () => () => <div>Sidebar</div>);
jest.mock("../components/layout/Header", () => () => <div>Header</div>);
jest.mock("../components/layout/Footer", () => () => <div>Footer</div>);

describe("Layout component", () => {
  const router = createMockRouter();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders loading message when user is loading", () => {
    const { getByText } = render(
      <RouterContext.Provider value={router}>
        <AuthProvider value={{ user: null, isLoading: true }}>
          <Layout>
            <div>Children</div>
          </Layout>
        </AuthProvider>
      </RouterContext.Provider>,
    );

    expect(getByText("Loading...")).toBeInTheDocument();
  });

  it("renders not authenticated message when user is not authenticated", () => {
    const { getByText } = render(
      <RouterContext.Provider value={router}>
        <AuthProvider value={{ user: null, isLoading: false }}>
          <Layout>
            <div>Children</div>
          </Layout>
        </AuthProvider>
      </RouterContext.Provider>,
    );

    expect(getByText("You are not authenticated.")).toBeInTheDocument();
  });

  it("renders layout with sidebar, header, and footer when user is authenticated", () => {
    const { getByText } = render(
      <RouterContext.Provider value={router}>
        <AuthProvider value={{ user: { id: 1 }, isLoading: false }}>
          <Layout>
            <div>Children</div>
          </Layout>
        </AuthProvider>
      </RouterContext.Provider>,
    );

    expect(getByText("Sidebar")).toBeInTheDocument();
    expect(getByText("Header")).toBeInTheDocument();
    expect(getByText("Footer")).toBeInTheDocument();
    expect(getByText("Children")).toBeInTheDocument();
  });

  it("closes sidebar when route changes", async () => {
    const setIsSidebarOpen = jest.fn();
    const { rerender } = render(
      <RouterContext.Provider value={router}>
        <AuthProvider value={{ user: { id: 1 }, isLoading: false }}>
          <Layout>
            <div>Children</div>
          </Layout>
        </AuthProvider>
      </RouterContext.Provider>,
    );

    rerender(
      <RouterContext.Provider value={router}>
        <AuthProvider value={{ user: { id: 1 }, isLoading: false }}>
          <Layout>
            <div>Children</div>
          </Layout>
        </AuthProvider>
      </RouterContext.Provider>,
    );

    await waitFor(() => {
      expect(setIsSidebarOpen).toHaveBeenCalledTimes(1);
      expect(setIsSidebarOpen).toHaveBeenCalledWith(false);
    });
  });

  it("calls handleRouteChange when route changes", async () => {
    const handleRouteChange = jest.fn();
    router.events.on = jest.fn((event, callback) => {
      if (event === "routeChangeStart") {
        handleRouteChange();
      }
    });

    const { rerender } = render(
      <RouterContext.Provider value={router}>
        <AuthProvider value={{ user: { id: 1 }, isLoading: false }}>
          <Layout>
            <div>Children</div>
          </Layout>
        </AuthProvider>
      </RouterContext.Provider>,
    );

    rerender(
      <RouterContext.Provider value={router}>
        <AuthProvider value={{ user: { id: 1 }, isLoading: false }}>
          <Layout>
            <div>Children</div>
          </Layout>
        </AuthProvider>
      </RouterContext.Provider>,
    );

    await waitFor(() => {
      expect(handleRouteChange).toHaveBeenCalledTimes(1);
    });
  });

  it("renders head with title, description, and favicon", () => {
    const { getByText } = render(
      <RouterContext.Provider value={router}>
        <AuthProvider value={{ user: { id: 1 }, isLoading: false }}>
          <Layout>
            <div>Children</div>
          </Layout>
        </AuthProvider>
      </RouterContext.Provider>,
    );

    expect(
      getByText("ValueVerse B2B Value Realization Platform"),
    ).toBeInTheDocument();
    expect(
      getByText("ValueVerse B2B Value Realization Platform"),
    ).toBeInTheDocument();
    expect(getByText("/favicon.ico")).toBeInTheDocument();
  });
});

import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react";
import { NextRouter } from "next/router";
import { DashboardPage } from "./page";
import { useAuth } from "../hooks/useAuth";
import { useOrganizations } from "../hooks/useOrganizations";
import { Layout } from "../components/layout/DashboardLayout";
import { DashboardHeader } from "../components/layout/DashboardHeader";
import { DashboardContent } from "../components/layout/DashboardContent";
import { DashboardFooter } from "../components/layout/DashboardFooter";
import { OrganizationCard } from "../components/ui/OrganizationCard";
import { Spinner } from "../components/ui/Spinner";
import { ErrorAlert } from "../components/ui/ErrorAlert";

jest.mock("next/router", () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

jest.mock("../hooks/useAuth", () => ({
  useAuth: () => ({
    user: { id: 1, name: "John Doe", email: "johndoe@example.com" },
  }),
}));

jest.mock("../hooks/useOrganizations", () => ({
  useOrganizations: () => ({
    organizations: [
      { id: 1, name: "Organization 1" },
      { id: 2, name: "Organization 2" },
    ],
    isLoading: false,
    isError: false,
  }),
}));

describe("DashboardPage", () => {
  it("renders correctly when loading", () => {
    jest.mock("../hooks/useOrganizations", () => ({
      useOrganizations: () => ({
        organizations: [],
        isLoading: true,
        isError: false,
      }),
    }));

    const { getByText } = render(<DashboardPage />);

    expect(getByText("Loading...")).toBeInTheDocument();
    expect(getByText("Dashboard")).toBeInTheDocument();
  });

  it("renders correctly when error occurs", () => {
    jest.mock("../hooks/useOrganizations", () => ({
      useOrganizations: () => ({
        organizations: [],
        isLoading: false,
        isError: true,
      }),
    }));

    const { getByText } = render(<DashboardPage />);

    expect(getByText("Failed to load organizations")).toBeInTheDocument();
    expect(getByText("Dashboard")).toBeInTheDocument();
  });

  it("renders correctly when organizations are loaded", () => {
    const { getByText } = render(<DashboardPage />);

    expect(getByText("Your Organizations")).toBeInTheDocument();
    expect(getByText("Organization 1")).toBeInTheDocument();
    expect(getByText("Organization 2")).toBeInTheDocument();
  });

  it("renders OrganizationCard components correctly", () => {
    const { getAllByTestId } = render(<DashboardPage />);

    const organizationCards = getAllByTestId("organization-card");

    expect(organizationCards.length).toBe(2);
    expect(organizationCards[0]).toHaveTextContent("Organization 1");
    expect(organizationCards[1]).toHaveTextContent("Organization 2");
  });

  it("renders Layout, DashboardHeader, DashboardContent, and DashboardFooter components correctly", () => {
    const { getByText } = render(<DashboardPage />);

    expect(getByText("Dashboard")).toBeInTheDocument();
    expect(getByText("Your Organizations")).toBeInTheDocument();
  });

  it("renders Spinner component correctly when loading", () => {
    jest.mock("../hooks/useOrganizations", () => ({
      useOrganizations: () => ({
        organizations: [],
        isLoading: true,
        isError: false,
      }),
    }));

    const { getByTestId } = render(<DashboardPage />);

    expect(getByTestId("spinner")).toBeInTheDocument();
  });

  it("renders ErrorAlert component correctly when error occurs", () => {
    jest.mock("../hooks/useOrganizations", () => ({
      useOrganizations: () => ({
        organizations: [],
        isLoading: false,
        isError: true,
      }),
    }));

    const { getByTestId } = render(<DashboardPage />);

    expect(getByTestId("error-alert")).toBeInTheDocument();
  });
});

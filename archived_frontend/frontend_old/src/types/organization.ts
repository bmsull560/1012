// frontend/src/types/organization.test.ts

import { OrganizationStatus } from "./organization";

describe("OrganizationStatus enum", () => {
  it("should have the correct values", () => {
    expect(OrganizationStatus.ACTIVE).toBe("active");
    expect(OrganizationStatus.INACTIVE).toBe("inactive");
    expect(OrganizationStatus.PENDING).toBe("pending");
  });
});

describe("Organization interface", () => {
  it("should have the correct properties", () => {
    const organization: any = {
      id: "123",
      name: "Test Organization",
      description: "This is a test organization",
      status: OrganizationStatus.ACTIVE,
      createdAt: new Date(),
      updatedAt: new Date(),
      users: [],
    };

    expect(organization).toHaveProperty("id");
    expect(organization).toHaveProperty("name");
    expect(organization).toHaveProperty("description");
    expect(organization).toHaveProperty("status");
    expect(organization).toHaveProperty("createdAt");
    expect(organization).toHaveProperty("updatedAt");
    expect(organization).toHaveProperty("users");
  });

  it("should throw an error if the status is not a valid OrganizationStatus", () => {
    expect(() => {
      const organization: any = {
        id: "123",
        name: "Test Organization",
        description: "This is a test organization",
        status: "invalid-status",
        createdAt: new Date(),
        updatedAt: new Date(),
        users: [],
      };
    }).toThrowError(
      "Type 'invalid-status' is not a valid enum value for type 'OrganizationStatus'.",
    );
  });
});

describe("OrganizationCreate interface", () => {
  it("should have the correct properties", () => {
    const organizationCreate: any = {
      name: "Test Organization",
      description: "This is a test organization",
    };

    expect(organizationCreate).toHaveProperty("name");
    expect(organizationCreate).toHaveProperty("description");
  });

  it("should throw an error if the name is missing", () => {
    expect(() => {
      const organizationCreate: any = {
        description: "This is a test organization",
      };
    }).toThrowError("Type 'undefined' is not assignable to type 'string'.");
  });

  it("should throw an error if the description is missing", () => {
    expect(() => {
      const organizationCreate: any = {
        name: "Test Organization",
      };
    }).toThrowError("Type 'undefined' is not assignable to type 'string'.");
  });
});

describe("OrganizationUpdate interface", () => {
  it("should have the correct properties", () => {
    const organizationUpdate: any = {
      name: "Test Organization",
      description: "This is a test organization",
      status: OrganizationStatus.ACTIVE,
    };

    expect(organizationUpdate).toHaveProperty("name");
    expect(organizationUpdate).toHaveProperty("description");
    expect(organizationUpdate).toHaveProperty("status");
  });

  it("should not throw an error if the name is missing", () => {
    expect(() => {
      const organizationUpdate: any = {
        description: "This is a test organization",
        status: OrganizationStatus.ACTIVE,
      };
    }).not.toThrowError();
  });

  it("should not throw an error if the description is missing", () => {
    expect(() => {
      const organizationUpdate: any = {
        name: "Test Organization",
        status: OrganizationStatus.ACTIVE,
      };
    }).not.toThrowError();
  });

  it("should throw an error if the status is not a valid OrganizationStatus", () => {
    expect(() => {
      const organizationUpdate: any = {
        name: "Test Organization",
        description: "This is a test organization",
        status: "invalid-status",
      };
    }).toThrowError(
      "Type 'invalid-status' is not a valid enum value for type 'OrganizationStatus'.",
    );
  });
});

describe("OrganizationResponse interface", () => {
  it("should have the correct properties", () => {
    const organizationResponse: any = {
      id: "123",
      name: "Test Organization",
      description: "This is a test organization",
      status: OrganizationStatus.ACTIVE,
      createdAt: new Date(),
      updatedAt: new Date(),
      users: [],
    };

    expect(organizationResponse).toHaveProperty("id");
    expect(organizationResponse).toHaveProperty("name");
    expect(organizationResponse).toHaveProperty("description");
    expect(organizationResponse).toHaveProperty("status");
    expect(organizationResponse).toHaveProperty("createdAt");
    expect(organizationResponse).toHaveProperty("updatedAt");
    expect(organizationResponse).toHaveProperty("users");
  });

  it("should throw an error if the status is not a valid OrganizationStatus", () => {
    expect(() => {
      const organizationResponse: any = {
        id: "123",
        name: "Test Organization",
        description: "This is a test organization",
        status: "invalid-status",
        createdAt: new Date(),
        updatedAt: new Date(),
        users: [],
      };
    }).toThrowError(
      "Type 'invalid-status' is not a valid enum value for type 'OrganizationStatus'.",
    );
  });
});

describe("OrganizationsResponse interface", () => {
  it("should have the correct properties", () => {
    const organizationsResponse: any = {
      organizations: [],
      totalCount: 0,
    };

    expect(organizationsResponse).toHaveProperty("organizations");
    expect(organizationsResponse).toHaveProperty("totalCount");
  });

  it("should throw an error if the organizations property is missing", () => {
    expect(() => {
      const organizationsResponse: any = {
        totalCount: 0,
      };
    }).toThrowError(
      "Type 'undefined' is not assignable to type 'OrganizationResponse[]'.",
    );
  });

  it("should throw an error if the totalCount property is missing", () => {
    expect(() => {
      const organizationsResponse: any = {
        organizations: [],
      };
    }).toThrowError("Type 'undefined' is not assignable to type 'number'.");
  });
});

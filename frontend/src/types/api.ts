// frontend/src/types/api.test.ts

import { 
  ApiErrorResponse, 
  ApiSuccessResponse, 
  ApiResponse, 
  AuthApiResponse, 
  OrganizationsApiResponse, 
  OrganizationApiResponse, 
  UserApiResponse 
} from './api';

describe('API Response Type Definitions', () => {
  describe('ApiErrorResponse', () => {
    it('should have required properties', () => {
      const errorResponse: ApiErrorResponse = {
        error: 'Error',
        message: 'Error message',
        statusCode: 400,
      };

      expect(errorResponse).toHaveProperty('error');
      expect(errorResponse).toHaveProperty('message');
      expect(errorResponse).toHaveProperty('statusCode');
    });

    it('should throw an error if required properties are missing', () => {
      expect(() => {
        const errorResponse: ApiErrorResponse = {
          error: 'Error',
        };
      }).toThrowError();
    });
  });

  describe('ApiSuccessResponse', () => {
    it('should have required properties', () => {
      const successResponse: ApiSuccessResponse<{ id: number }> = {
        data: { id: 1 },
        message: 'Success message',
        statusCode: 200,
      };

      expect(successResponse).toHaveProperty('data');
      expect(successResponse).toHaveProperty('message');
      expect(successResponse).toHaveProperty('statusCode');
    });

    it('should throw an error if required properties are missing', () => {
      expect(() => {
        const successResponse: ApiSuccessResponse<{ id: number }> = {
          data: { id: 1 },
        };
      }).toThrowError();
    });
  });

  describe('ApiResponse', () => {
    it('should be either ApiErrorResponse or ApiSuccessResponse', () => {
      const errorResponse: ApiResponse<{ id: number }> = {
        error: 'Error',
        message: 'Error message',
        statusCode: 400,
      };

      const successResponse: ApiResponse<{ id: number }> = {
        data: { id: 1 },
        message: 'Success message',
        statusCode: 200,
      };

      expect(errorResponse).toBeInstanceOf(Object);
      expect(successResponse).toBeInstanceOf(Object);
    });
  });

  describe('AuthApiResponse', () => {
    it('should have required properties', () => {
      const authResponse: AuthApiResponse = {
        token: 'token',
        user: { id: 1, name: 'John Doe' },
      };

      expect(authResponse).toHaveProperty('token');
      expect(authResponse).toHaveProperty('user');
    });

    it('should throw an error if required properties are missing', () => {
      expect(() => {
        const authResponse: AuthApiResponse = {
          token: 'token',
        };
      }).toThrowError();
    });
  });

  describe('OrganizationsApiResponse', () => {
    it('should have required properties', () => {
      const organizationsResponse: OrganizationsApiResponse = {
        organizations: [{ id: 1, name: 'Organization 1' }],
      };

      expect(organizationsResponse).toHaveProperty('organizations');
    });

    it('should throw an error if required properties are missing', () => {
      expect(() => {
        const organizationsResponse: OrganizationsApiResponse = {};
      }).toThrowError();
    });
  });

  describe('OrganizationApiResponse', () => {
    it('should have required properties', () => {
      const organizationResponse: OrganizationApiResponse = {
        organization: { id: 1, name: 'Organization 1' },
      };

      expect(organizationResponse).toHaveProperty('organization');
    });

    it('should throw an error if required properties are missing', () => {
      expect(() => {
        const organizationResponse: OrganizationApiResponse = {};
      }).toThrowError();
    });
  });

  describe('UserApiResponse', () => {
    it('should have required properties', () => {
      const userResponse: UserApiResponse = {
        user: { id: 1, name: 'John Doe' },
      };

      expect(userResponse).toHaveProperty('user');
    });

    it('should throw an error if required properties are missing', () => {
      expect(() => {
        const userResponse: UserApiResponse = {};
      }).toThrowError();
    });
  });
});
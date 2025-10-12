// frontend/src/types/user.test.ts

import { z } from 'zod';
import { User, userSchema, UserResponse, userResponseSchema } from './user';

describe('User type definitions', () => {
  describe('User interface', () => {
    it('should have required properties', () => {
      const user: User = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(user).toHaveProperty('id');
      expect(user).toHaveProperty('email');
      expect(user).toHaveProperty('username');
      expect(user).toHaveProperty('firstName');
      expect(user).toHaveProperty('lastName');
      expect(user).toHaveProperty('role');
      expect(user).toHaveProperty('createdAt');
      expect(user).toHaveProperty('updatedAt');
    });
  });

  describe('User schema', () => {
    it('should validate a valid user', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({ success: true, data: user });
    });

    it('should not validate an invalid user', () => {
      const user = {
        id: 'invalid-id',
        email: 'invalid-email',
        username: 'a', // too short
        firstName: '', // empty
        lastName: '', // empty
        role: 'invalid-role',
        createdAt: 'invalid-date',
        updatedAt: 'invalid-date',
      };

      expect(userSchema.safeParse(user)).toEqual({
        success: false,
        error: expect.any(z.ZodError),
      });
    });

    it('should validate a user with a valid UUID', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({ success: true, data: user });
    });

    it('should not validate a user with an invalid UUID', () => {
      const user = {
        id: 'invalid-id',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({
        success: false,
        error: expect.any(z.ZodError),
      });
    });

    it('should validate a user with a valid email', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({ success: true, data: user });
    });

    it('should not validate a user with an invalid email', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'invalid-email',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({
        success: false,
        error: expect.any(z.ZodError),
      });
    });

    it('should validate a user with a valid username', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({ success: true, data: user });
    });

    it('should not validate a user with an invalid username', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'a', // too short
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({
        success: false,
        error: expect.any(z.ZodError),
      });
    });

    it('should validate a user with a valid first name', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({ success: true, data: user });
    });

    it('should not validate a user with an invalid first name', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: '', // empty
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({
        success: false,
        error: expect.any(z.ZodError),
      });
    });

    it('should validate a user with a valid last name', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({ success: true, data: user });
    });

    it('should not validate a user with an invalid last name', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: '', // empty
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({
        success: false,
        error: expect.any(z.ZodError),
      });
    });

    it('should validate a user with a valid role', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({ success: true, data: user });
    });

    it('should not validate a user with an invalid role', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'invalid-role',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({
        success: false,
        error: expect.any(z.ZodError),
      });
    });

    it('should validate a user with a valid created at date', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({ success: true, data: user });
    });

    it('should not validate a user with an invalid created at date', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: 'invalid-date',
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({
        success: false,
        error: expect.any(z.ZodError),
      });
    });

    it('should validate a user with a valid updated at date', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      expect(userSchema.safeParse(user)).toEqual({ success: true, data: user });
    });

    it('should not validate a user with an invalid updated at date', () => {
      const user = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'john.doe@example.com',
        username: 'johndoe',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user',
        createdAt: new Date(),
        updatedAt: 'invalid-date',
      };

      expect(userSchema.safeParse(user)).toEqual({
        success: false,
        error: expect.any(z.ZodError),
      });
    });
  });

  describe('UserResponse interface', () => {
    it('should have required properties', () => {
      const userResponse: UserResponse = {
        user: {
          id: '123e4567-e89b-12d3-a456-426614174000',
          email: 'john.doe@example.com',
          username: 'johndoe',
          firstName: 'John',
          lastName: 'Doe',
          role: 'user',
          createdAt: new Date(),
          updatedAt: new Date(),
        },
        token: 'example-token',
      };

      expect(userResponse).toHaveProperty('user');
      expect(userResponse).toHaveProperty('token');
    });
  });

  describe('UserResponse schema', () => {
    it('should validate a valid user response', () => {
      const userResponse = {
        user: {
          id: '123e4567-e89b-12d3-a456-426614174000',
          email: 'john.doe@example.com',
          username: 'johndoe',
          firstName: 'John',
          lastName: 'Doe',
          role: 'user',
          createdAt: new Date(),
          updatedAt: new Date(),
        },
        token: 'example-token',
      };

      expect(userResponseSchema.safeParse(userResponse)).toEqual({
        success: true,
        data: userResponse,
      });
    });

    it('should not validate an invalid user response', () => {
      const userResponse = {
        user: {
          id: 'invalid-id',
          email: 'invalid-email',
          username: 'a', // too short
          firstName: '', // empty
          lastName: '', // empty
          role: 'invalid-role',
          createdAt: 'invalid-date',
          updatedAt: 'invalid-date',
        },
        token: '', // empty
      };

      expect(userResponseSchema.safeParse(userResponse)).toEqual({
        success: false,
        error: expect.any(z.ZodError),
      });
    });
  });
});
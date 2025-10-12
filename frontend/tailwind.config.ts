// frontend/tailwind.config.test.ts

import tailwindConfig from './tailwind.config';
import { Config } from 'tailwindcss';
import { renderHook } from '@testing-library/react-hooks';
import { act } from 'react-dom/test-utils';

jest.mock('tailwindcss', () => ({
  __esModule: true,
  default: jest.fn().mockImplementation(() => ({})),
}));

describe('tailwind.config', () => {
  it('should have a prefix', () => {
    expect(tailwindConfig.prefix).toBe('tw-');
  });

  it('should have a theme', () => {
    expect(tailwindConfig.theme).toBeDefined();
  });

  it('should have a theme with extend property', () => {
    expect(tailwindConfig.theme.extend).toBeDefined();
  });

  it('should have a theme with extend colors property', () => {
    expect(tailwindConfig.theme.extend.colors).toBeDefined();
  });

  it('should have a theme with extend spacing property', () => {
    expect(tailwindConfig.theme.extend.spacing).toBeDefined();
  });

  it('should have a theme with extend typography property', () => {
    expect(tailwindConfig.theme.extend.typography).toBeDefined();
  });

  it('should have a variants property', () => {
    expect(tailwindConfig.variants).toBeDefined();
  });

  it('should have a variants with extend property', () => {
    expect(tailwindConfig.variants.extend).toBeDefined();
  });

  it('should have a plugins property', () => {
    expect(tailwindConfig.plugins).toBeDefined();
  });

  it('should have a plugins with @tailwindcss/forms', () => {
    expect(tailwindConfig.plugins.includes(require('@tailwindcss/forms'))).toBe(true);
  });

  it('should have a plugins with @tailwindcss/typography', () => {
    expect(tailwindConfig.plugins.includes(require('@tailwindcss/typography'))).toBe(true);
  });

  it('should be of type Config', () => {
    expect(tailwindConfig).toBeInstanceOf(Config);
  });

  it('should throw an error if theme is not defined', () => {
    const invalidConfig = { ...tailwindConfig };
    delete invalidConfig.theme;
    expect(() => (invalidConfig as Config)).toThrowError();
  });

  it('should throw an error if variants is not defined', () => {
    const invalidConfig = { ...tailwindConfig };
    delete invalidConfig.variants;
    expect(() => (invalidConfig as Config)).toThrowError();
  });

  it('should throw an error if plugins is not defined', () => {
    const invalidConfig = { ...tailwindConfig };
    delete invalidConfig.plugins;
    expect(() => (invalidConfig as Config)).toThrowError();
  });

  it('should handle edge case where theme is an empty object', () => {
    const edgeCaseConfig = { ...tailwindConfig, theme: {} };
    expect(() => (edgeCaseConfig as Config)).not.toThrowError();
  });

  it('should handle edge case where variants is an empty object', () => {
    const edgeCaseConfig = { ...tailwindConfig, variants: {} };
    expect(() => (edgeCaseConfig as Config)).not.toThrowError();
  });

  it('should handle edge case where plugins is an empty array', () => {
    const edgeCaseConfig = { ...tailwindConfig, plugins: [] };
    expect(() => (edgeCaseConfig as Config)).not.toThrowError();
  });
});
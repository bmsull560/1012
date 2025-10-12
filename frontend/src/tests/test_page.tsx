import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import { RouterContext } from 'next/dist/shared/lib/router-context';
import { createMockRouter } from './__mocks__/next-router-mock';
import { useAuth } from '../hooks/useAuth';
import { Layout } from './layout';
import HomePage from './page';

jest.mock('../hooks/useAuth');
jest.mock('./layout');

describe('HomePage', () => {
  const router = createMockRouter({ pathname: '/' });
  const user = { id: 1, name: 'John Doe' };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state when user is loading', () => {
    (useAuth as jest.Mock).mockReturnValue({ user: null, isLoading: true });
    const { getByText } = render(
      <RouterContext.Provider value={router}>
        <HomePage />
      </RouterContext.Provider>
    );
    expect(getByText('Loading...')).toBeInTheDocument();
  });

  it('redirects to login page when user is not authenticated', () => {
    (useAuth as jest.Mock).mockReturnValue({ user: null, isLoading: false });
    render(
      <RouterContext.Provider value={router}>
        <HomePage />
      </RouterContext.Provider>
    );
    expect(router.push).toHaveBeenCalledTimes(1);
    expect(router.push).toHaveBeenCalledWith('/auth/login');
  });

  it('renders home page when user is authenticated', () => {
    (useAuth as jest.Mock).mockReturnValue({ user, isLoading: false });
    const { getByText } = render(
      <RouterContext.Provider value={router}>
        <HomePage />
      </RouterContext.Provider>
    );
    expect(getByText('Welcome to ValueVerse')).toBeInTheDocument();
    expect(getByText('Your B2B Value Realization Platform')).toBeInTheDocument();
  });

  it('renders layout component', () => {
    (useAuth as jest.Mock).mockReturnValue({ user, isLoading: false });
    const layoutMock = jest.fn();
    Layout.mockImplementation(layoutMock);
    render(
      <RouterContext.Provider value={router}>
        <HomePage />
      </RouterContext.Provider>
    );
    expect(layoutMock).toHaveBeenCalledTimes(1);
  });

  it('renders head component with title', () => {
    (useAuth as jest.Mock).mockReturnValue({ user, isLoading: false });
    const { getByText } = render(
      <RouterContext.Provider value={router}>
        <HomePage />
      </RouterContext.Provider>
    );
    expect(getByText('ValueVerse B2B Value Realization Platform')).toBeInTheDocument();
  });

  it('handles error when useAuth hook throws an error', () => {
    (useAuth as jest.Mock).mockImplementation(() => {
      throw new Error('Mocked error');
    });
    const consoleErrorMock = jest.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <RouterContext.Provider value={router}>
        <HomePage />
      </RouterContext.Provider>
    );
    expect(consoleErrorMock).toHaveBeenCalledTimes(1);
    consoleErrorMock.mockRestore();
  });
});
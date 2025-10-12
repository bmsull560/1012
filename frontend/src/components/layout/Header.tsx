// frontend/src/components/layout/Header.test.tsx

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import { RouterContext } from 'next/dist/shared/lib/router-context';
import { createMockRouter } from '../../__mocks__/next-router';
import { useAuth } from '../../hooks/useAuth';
import Header from './Header';

jest.mock('../../hooks/useAuth');

describe('Header component', () => {
  const mockRouter = createMockRouter({ pathname: '/' });
  const mockLogout = jest.fn();

  beforeEach(() => {
    (useAuth as jest.Mock).mockReturnValue({ user: null, logout: mockLogout });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders the header with login and signup links when user is not logged in', () => {
    const { getByText } = render(
      <RouterContext.Provider value={mockRouter}>
        <Header />
      </RouterContext.Provider>
    );

    expect(getByText('Login')).toBeInTheDocument();
    expect(getByText('Signup')).toBeInTheDocument();
  });

  it('renders the header with dashboard and logout links when user is logged in', () => {
    (useAuth as jest.Mock).mockReturnValue({ user: { id: 1, name: 'John Doe' }, logout: mockLogout });

    const { getByText } = render(
      <RouterContext.Provider value={mockRouter}>
        <Header />
      </RouterContext.Provider>
    );

    expect(getByText('Dashboard')).toBeInTheDocument();
    expect(getByText('Logout')).toBeInTheDocument();
  });

  it('calls the logout function and redirects to login page when logout button is clicked', async () => {
    (useAuth as jest.Mock).mockReturnValue({ user: { id: 1, name: 'John Doe' }, logout: mockLogout });

    const { getByText } = render(
      <RouterContext.Provider value={mockRouter}>
        <Header />
      </RouterContext.Provider>
    );

    const logoutButton = getByText('Logout');
    fireEvent.click(logoutButton);

    await waitFor(() => expect(mockLogout).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(mockRouter.push).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(mockRouter.push).toHaveBeenCalledWith('/auth/login'));
  });

  it('handles error when logout function fails', async () => {
    (useAuth as jest.Mock).mockReturnValue({ user: { id: 1, name: 'John Doe' }, logout: jest.fn(() => Promise.reject(new Error('Logout failed'))) });

    const { getByText } = render(
      <RouterContext.Provider value={mockRouter}>
        <Header />
      </RouterContext.Provider>
    );

    const logoutButton = getByText('Logout');
    fireEvent.click(logoutButton);

    await waitFor(() => expect(console.error).toHaveBeenCalledTimes(1));
  });

  it('renders the header with custom class name', () => {
    const { getByText } = render(
      <RouterContext.Provider value={mockRouter}>
        <Header className="custom-class" />
      </RouterContext.Provider>
    );

    expect(getByText('ValueVerse')).toHaveClass('custom-class');
  });
});
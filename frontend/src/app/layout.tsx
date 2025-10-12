// frontend/src/app/layout.tsx

import type { NextPage, NextPageContext } from 'next';
import type { ReactNode } from 'react';
import { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useAuth } from '../hooks/useAuth';
import Sidebar from '../components/layout/Sidebar';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import styles from '../styles/Layout.module.css';

interface LayoutProps {
  children: ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    const handleRouteChange = () => {
      setIsSidebarOpen(false);
    };

    router.events.on('routeChangeStart', handleRouteChange);

    return () => {
      router.events.off('routeChangeStart', handleRouteChange);
    };
  }, [router.events]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <div>You are not authenticated.</div>;
  }

  return (
    <div className={styles.container}>
      <Head>
        <title>ValueVerse B2B Value Realization Platform</title>
        <meta name="description" content="ValueVerse B2B Value Realization Platform" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Sidebar isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen} />
      <div className={styles.main}>
        <Header setIsSidebarOpen={setIsSidebarOpen} />
        <main className={styles.content}>{children}</main>
        <Footer />
      </div>
    </div>
  );
};

export default Layout;
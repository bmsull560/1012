import type { NextPage } from 'next';
import Head from 'next/head';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../hooks/useAuth';
import { Layout } from './layout';

const HomePage: NextPage = () => {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/auth/login');
    }
  }, [isLoading, user, router]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return null;
  }

  return (
    <Layout>
      <Head>
        <title>ValueVerse B2B Value Realization Platform</title>
      </Head>
      <div className="container mx-auto p-4 pt-6">
        <h1 className="text-3xl font-bold mb-4">Welcome to ValueVerse</h1>
        <p className="text-lg mb-4">Your B2B Value Realization Platform</p>
      </div>
    </Layout>
  );
};

export default HomePage;
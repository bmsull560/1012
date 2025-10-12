import type { NextPage } from 'next';
import Head from 'next/head';
import { useAuth } from '../hooks/useAuth';
import { useOrganizations } from '../hooks/useOrganizations';
import { Layout } from '../components/layout/DashboardLayout';
import { DashboardHeader } from '../components/layout/DashboardHeader';
import { DashboardContent } from '../components/layout/DashboardContent';
import { DashboardFooter } from '../components/layout/DashboardFooter';
import { OrganizationCard } from '../components/ui/OrganizationCard';
import { Spinner } from '../components/ui/Spinner';
import { ErrorAlert } from '../components/ui/ErrorAlert';

const DashboardPage: NextPage = () => {
  const { user } = useAuth();
  const { organizations, isLoading, isError } = useOrganizations();

  if (isLoading) {
    return (
      <Layout>
        <DashboardHeader />
        <DashboardContent>
          <Spinner />
        </DashboardContent>
        <DashboardFooter />
      </Layout>
    );
  }

  if (isError) {
    return (
      <Layout>
        <DashboardHeader />
        <DashboardContent>
          <ErrorAlert message="Failed to load organizations" />
        </DashboardContent>
        <DashboardFooter />
      </Layout>
    );
  }

  return (
    <Layout>
      <Head>
        <title>Dashboard - ValueVerse</title>
      </Head>
      <DashboardHeader />
      <DashboardContent>
        <h2 className="text-2xl font-bold mb-4">Your Organizations</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {organizations.map((organization) => (
            <OrganizationCard key={organization.id} organization={organization} />
          ))}
        </div>
      </DashboardContent>
      <DashboardFooter />
    </Layout>
  );
};

export default DashboardPage;
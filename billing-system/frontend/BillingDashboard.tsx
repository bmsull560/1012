/**
 * ValueVerse Billing Dashboard - Customer Portal
 * Real-time usage tracking, billing history, and self-service management
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  CreditCard,
  TrendingUp,
  AlertTriangle,
  Download,
  Settings,
  Calendar,
  DollarSign,
  Activity,
  Zap,
  Database,
  Server,
  Clock,
  FileText,
  CheckCircle,
  XCircle,
  Info,
  RefreshCw,
} from 'lucide-react';
import { format, startOfMonth, endOfMonth, subMonths } from 'date-fns';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useWebSocket } from '@/hooks/useWebSocket';

// ==================== TypeScript Interfaces ====================

interface Organization {
  id: string;
  name: string;
  billing_email: string;
  status: 'active' | 'suspended' | 'deleted';
}

interface Subscription {
  id: string;
  plan_name: string;
  status: 'trialing' | 'active' | 'past_due' | 'canceled' | 'paused';
  current_period_start: string;
  current_period_end: string;
  trial_end?: string;
  cancel_at_period_end: boolean;
}

interface UsageMetric {
  metric_name: string;
  current_usage: number;
  limit?: number;
  unit: string;
  cost: number;
  trend: number; // percentage change
}

interface Invoice {
  id: string;
  invoice_number: string;
  status: 'draft' | 'open' | 'paid' | 'void' | 'uncollectible';
  total: number;
  currency: string;
  due_date: string;
  created_at: string;
  line_items: LineItem[];
}

interface LineItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

interface PaymentMethod {
  id: string;
  type: 'card' | 'bank_account' | 'paypal' | 'wire';
  brand?: string;
  last_four?: string;
  exp_month?: number;
  exp_year?: number;
  is_default: boolean;
}

interface BillingAlert {
  id: string;
  type: 'warning' | 'error' | 'info';
  message: string;
  timestamp: string;
}

// ==================== API Service ====================

const billingAPI = {
  // Subscription endpoints
  getSubscription: async (): Promise<Subscription> => {
    const response = await fetch('/api/v1/billing/subscription', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    return response.json();
  },

  // Usage endpoints
  getUsageSummary: async (startDate: Date, endDate: Date) => {
    const params = new URLSearchParams({
      start_date: startDate.toISOString(),
      end_date: endDate.toISOString(),
    });
    const response = await fetch(`/api/v1/billing/usage/summary?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    return response.json();
  },

  // Invoice endpoints
  getInvoices: async () => {
    const response = await fetch('/api/v1/billing/invoices', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    return response.json();
  },

  // Payment method endpoints
  getPaymentMethods: async () => {
    const response = await fetch('/api/v1/billing/payment-methods', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    return response.json();
  },

  updatePaymentMethod: async (id: string, data: any) => {
    const response = await fetch(`/api/v1/billing/payment-methods/${id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  // Plan management
  changePlan: async (newPlanId: string) => {
    const response = await fetch('/api/v1/billing/subscription/change-plan', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ plan_id: newPlanId }),
    });
    return response.json();
  },
};

// ==================== Main Dashboard Component ====================

export const BillingDashboard: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<'current' | 'previous'>('current');
  const [alerts, setAlerts] = useState<BillingAlert[]>([]);
  const queryClient = useQueryClient();

  // WebSocket connection for real-time updates
  const { data: realtimeData } = useWebSocket('/ws/billing', {
    onMessage: (event) => {
      // Update relevant data based on event type
      if (event.type === 'usage.updated') {
        queryClient.invalidateQueries('usage-summary');
      } else if (event.type === 'invoice.created') {
        queryClient.invalidateQueries('invoices');
        setAlerts(prev => [...prev, {
          id: Date.now().toString(),
          type: 'info',
          message: `New invoice generated: ${event.data.invoice_number}`,
          timestamp: new Date().toISOString(),
        }]);
      }
    },
  });

  // Queries
  const { data: subscription, isLoading: subscriptionLoading } = useQuery(
    'subscription',
    billingAPI.getSubscription
  );

  const { data: usageSummary, isLoading: usageLoading } = useQuery(
    ['usage-summary', selectedPeriod],
    () => {
      const now = new Date();
      const startDate = selectedPeriod === 'current'
        ? startOfMonth(now)
        : startOfMonth(subMonths(now, 1));
      const endDate = selectedPeriod === 'current'
        ? endOfMonth(now)
        : endOfMonth(subMonths(now, 1));
      return billingAPI.getUsageSummary(startDate, endDate);
    },
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const { data: invoices } = useQuery('invoices', billingAPI.getInvoices);
  const { data: paymentMethods } = useQuery('payment-methods', billingAPI.getPaymentMethods);

  // Calculate current charges
  const currentCharges = useMemo(() => {
    if (!usageSummary?.data?.metrics) return 0;
    return usageSummary.data.metrics.reduce(
      (sum: number, metric: any) => sum + (metric.cost || 0),
      0
    );
  }, [usageSummary]);

  // Mock usage trend data (replace with actual API data)
  const usageTrendData = [
    { date: '2024-01-01', api_calls: 45000, storage_gb: 120, compute_hours: 850 },
    { date: '2024-01-02', api_calls: 48000, storage_gb: 125, compute_hours: 920 },
    { date: '2024-01-03', api_calls: 52000, storage_gb: 128, compute_hours: 890 },
    { date: '2024-01-04', api_calls: 49000, storage_gb: 130, compute_hours: 950 },
    { date: '2024-01-05', api_calls: 55000, storage_gb: 135, compute_hours: 980 },
    { date: '2024-01-06', api_calls: 58000, storage_gb: 138, compute_hours: 1020 },
    { date: '2024-01-07', api_calls: 62000, storage_gb: 140, compute_hours: 1050 },
  ];

  // Cost breakdown for pie chart
  const costBreakdown = [
    { name: 'API Calls', value: 450, color: '#8884d8' },
    { name: 'Storage', value: 280, color: '#82ca9d' },
    { name: 'Compute', value: 620, color: '#ffc658' },
    { name: 'Bandwidth', value: 150, color: '#ff7c7c' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Billing & Usage
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">
              Monitor usage, manage subscriptions, and view billing history
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export Report
            </Button>
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>

        {/* Alerts */}
        {alerts.length > 0 && (
          <div className="space-y-2">
            {alerts.map((alert) => (
              <Alert key={alert.id} variant={alert.type === 'error' ? 'destructive' : 'default'}>
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>{alert.type === 'error' ? 'Alert' : 'Notice'}</AlertTitle>
                <AlertDescription>{alert.message}</AlertDescription>
              </Alert>
            ))}
          </div>
        )}

        {/* Current Subscription Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Current Subscription</CardTitle>
              <CardDescription>
                {subscription?.plan_name || 'Loading...'}
              </CardDescription>
            </div>
            <Badge
              variant={
                subscription?.status === 'active' ? 'default' :
                subscription?.status === 'trialing' ? 'secondary' :
                'destructive'
              }
            >
              {subscription?.status}
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-500">Billing Period</p>
                <p className="text-lg font-semibold">
                  {subscription && format(new Date(subscription.current_period_start), 'MMM dd')} -
                  {subscription && format(new Date(subscription.current_period_end), 'MMM dd, yyyy')}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Current Charges</p>
                <p className="text-2xl font-bold">${currentCharges.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Next Invoice</p>
                <p className="text-lg font-semibold">
                  {subscription && format(new Date(subscription.current_period_end), 'MMM dd, yyyy')}
                </p>
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <Button size="sm" variant="outline">
                Change Plan
              </Button>
              <Button size="sm" variant="outline">
                Update Billing Info
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Usage Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">API Calls</CardTitle>
              <Zap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">1.2M</div>
              <p className="text-xs text-muted-foreground">
                +20.1% from last month
              </p>
              <Progress value={65} className="mt-2" />
              <p className="text-xs text-gray-500 mt-1">65% of 2M limit</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Storage</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">458 GB</div>
              <p className="text-xs text-muted-foreground">
                +5.2% from last month
              </p>
              <Progress value={46} className="mt-2" />
              <p className="text-xs text-gray-500 mt-1">46% of 1TB limit</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Compute Hours</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">2,847</div>
              <p className="text-xs text-muted-foreground">
                +12.5% from last month
              </p>
              <Progress value={71} className="mt-2" />
              <p className="text-xs text-gray-500 mt-1">71% of 4,000 limit</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Bandwidth</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">3.2 TB</div>
              <p className="text-xs text-muted-foreground">
                +8.3% from last month
              </p>
              <Progress value={32} className="mt-2" />
              <p className="text-xs text-gray-500 mt-1">32% of 10TB limit</p>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Analytics Tabs */}
        <Tabs defaultValue="usage" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="usage">Usage Trends</TabsTrigger>
            <TabsTrigger value="costs">Cost Analysis</TabsTrigger>
            <TabsTrigger value="invoices">Invoices</TabsTrigger>
            <TabsTrigger value="payments">Payment Methods</TabsTrigger>
          </TabsList>

          {/* Usage Trends Tab */}
          <TabsContent value="usage">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>Usage Trends</CardTitle>
                  <Select value={selectedPeriod} onValueChange={(v: any) => setSelectedPeriod(v)}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="current">This Month</SelectItem>
                      <SelectItem value="previous">Last Month</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={350}>
                  <LineChart data={usageTrendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(value) => format(new Date(value), 'MMM dd')}
                    />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="api_calls" 
                      stroke="#8884d8" 
                      name="API Calls"
                      strokeWidth={2}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="compute_hours" 
                      stroke="#82ca9d" 
                      name="Compute Hours"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Cost Analysis Tab */}
          <TabsContent value="costs">
            <Card>
              <CardHeader>
                <CardTitle>Cost Breakdown</CardTitle>
                <CardDescription>
                  Current billing period cost distribution
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={costBreakdown}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(entry) => `${entry.name}: $${entry.value}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {costBreakdown.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                  
                  <div className="space-y-4">
                    <h3 className="font-semibold">Projected Monthly Cost</h3>
                    <div className="text-3xl font-bold">${(currentCharges * 1.1).toFixed(2)}</div>
                    <div className="space-y-2">
                      {costBreakdown.map((item) => (
                        <div key={item.name} className="flex justify-between">
                          <div className="flex items-center gap-2">
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: item.color }}
                            />
                            <span className="text-sm">{item.name}</span>
                          </div>
                          <span className="text-sm font-medium">${item.value}</span>
                        </div>
                      ))}
                    </div>
                    <Button className="w-full" variant="outline">
                      View Detailed Report
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Invoices Tab */}
          <TabsContent value="invoices">
            <Card>
              <CardHeader>
                <CardTitle>Invoice History</CardTitle>
                <CardDescription>
                  Download invoices and view payment history
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Invoice Number</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoices?.data?.map((invoice: Invoice) => (
                      <TableRow key={invoice.id}>
                        <TableCell className="font-medium">
                          {invoice.invoice_number}
                        </TableCell>
                        <TableCell>
                          {format(new Date(invoice.created_at), 'MMM dd, yyyy')}
                        </TableCell>
                        <TableCell>
                          ${invoice.total.toFixed(2)} {invoice.currency}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              invoice.status === 'paid' ? 'success' :
                              invoice.status === 'open' ? 'warning' :
                              'default'
                            }
                          >
                            {invoice.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button size="sm" variant="outline">
                              <FileText className="h-4 w-4 mr-1" />
                              View
                            </Button>
                            <Button size="sm" variant="outline">
                              <Download className="h-4 w-4 mr-1" />
                              PDF
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Payment Methods Tab */}
          <TabsContent value="payments">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>Payment Methods</CardTitle>
                    <CardDescription>
                      Manage your payment methods and billing information
                    </CardDescription>
                  </div>
                  <Button>
                    <CreditCard className="h-4 w-4 mr-2" />
                    Add Payment Method
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {paymentMethods?.data?.map((method: PaymentMethod) => (
                    <div
                      key={method.id}
                      className="flex items-center justify-between p-4 border rounded-lg"
                    >
                      <div className="flex items-center gap-4">
                        <CreditCard className="h-8 w-8 text-gray-400" />
                        <div>
                          <p className="font-medium">
                            {method.brand} ending in {method.last_four}
                          </p>
                          <p className="text-sm text-gray-500">
                            Expires {method.exp_month}/{method.exp_year}
                          </p>
                        </div>
                        {method.is_default && (
                          <Badge variant="secondary">Default</Badge>
                        )}
                      </div>
                      <div className="flex gap-2">
                        {!method.is_default && (
                          <Button size="sm" variant="outline">
                            Set as Default
                          </Button>
                        )}
                        <Button size="sm" variant="outline">
                          Edit
                        </Button>
                        <Button size="sm" variant="outline" className="text-red-600">
                          Remove
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Usage Alerts Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>Usage Alerts</CardTitle>
            <CardDescription>
              Configure alerts to monitor your usage and avoid overage charges
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">API Calls Alert</p>
                  <p className="text-sm text-gray-500">Alert when usage exceeds 80% of limit</p>
                </div>
                <Button size="sm" variant="outline">Configure</Button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Cost Threshold Alert</p>
                  <p className="text-sm text-gray-500">Alert when monthly cost exceeds $5,000</p>
                </div>
                <Button size="sm" variant="outline">Configure</Button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Storage Limit Alert</p>
                  <p className="text-sm text-gray-500">Alert when storage usage exceeds 90% of limit</p>
                </div>
                <Button size="sm" variant="outline">Configure</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

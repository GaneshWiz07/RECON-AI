/**
 * Dashboard Page - Complete Implementation with Analytics
 * 
 * Features:
 * - Real-time statistics cards
 * - Risk score trend chart
 * - Asset distribution pie chart
 * - Top risky assets table
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Navigation from '../components/ui/Navigation';
import {
  LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const Dashboard = () => {
  const { user, signOut } = useAuth();
  const [stats, setStats] = useState(null);
  const [riskTrend, setRiskTrend] = useState([]);
  const [topAssets, setTopAssets] = useState([]);
  const [allAssets, setAllAssets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Only fetch data if user is authenticated
    if (user) {
      fetchDashboardData();
    }
  }, [user]);

  const fetchDashboardData = async () => {
    // Don't fetch if user is not logged in
    if (!user) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      
      // Small delay to ensure Firebase auth token is ready
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Fetch dashboard stats
      const statsResponse = await api.get('/api/analytics/dashboard');
      setStats(statsResponse.data);

      // Fetch risk trend (last 30 days)
      const trendResponse = await api.get('/api/analytics/risk-trend?days=30');
      setRiskTrend(trendResponse.data.trend);

      // Fetch top risky assets
      const assetsResponse = await api.get('/api/analytics/top-risky-assets?limit=5');
      setTopAssets(assetsResponse.data.assets);

      // Fetch all assets for the main table
      const allAssetsResponse = await api.get('/api/assets/?limit=100');
      const assetsData = allAssetsResponse.data.data || allAssetsResponse.data;
      setAllAssets(assetsData.assets || []);

    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      // Don't show error if it's just unauthorized (user not fully logged in yet)
      if (error.status !== 401) {
        console.error('Dashboard fetch error:', error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'critical': return 'text-red-500';
      case 'high': return 'text-orange-500';
      case 'medium': return 'text-yellow-500';
      case 'low': return 'text-green-500';
      default: return 'text-gray-500';
    }
  };

  const getRiskBadgeVariant = (level) => {
    switch (level) {
      case 'critical': return 'danger';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  // Pie chart colors
  const RISK_COLORS = {
    low: '#10b981',      // green
    medium: '#f59e0b',  // yellow
    high: '#f97316',     // orange
    critical: '#ef4444' // red
  };

  // Prepare pie chart data
  const pieData = stats ? [
    { name: 'Low', value: stats.assets_by_risk.low, color: RISK_COLORS.low },
    { name: 'Medium', value: stats.assets_by_risk.medium, color: RISK_COLORS.medium },
    { name: 'High', value: stats.assets_by_risk.high, color: RISK_COLORS.high },
    { name: 'Critical', value: stats.assets_by_risk.critical, color: RISK_COLORS.critical },
  ].filter(item => item.value > 0) : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900">
        <Navigation />
        <div className="flex items-center justify-center" style={{ height: 'calc(100vh - 4rem)' }}>
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500"></div>
            <p className="text-gray-400 mt-4">Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Navigation />
      
      <div className="max-w-7xl mx-auto p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 mt-1">Welcome back, {user?.email}</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <Card>
            <div className="flex flex-col">
              <span className="text-gray-400 text-sm mb-2">Overall Risk Score</span>
              <div className={`text-4xl font-bold ${
                getRiskColor(stats?.overall_risk_level || 'low')
              }`}>
                {stats?.overall_risk_score || 0}
              </div>
              <span className="text-xs text-gray-500 mt-2 uppercase">
                {stats?.overall_risk_level || 'low'} risk
              </span>
            </div>
          </Card>

          <Card>
            <div className="flex flex-col">
              <span className="text-gray-400 text-sm mb-2">Discovered Assets</span>
              <div className="text-4xl font-bold text-blue-500">
                {stats?.discovered_assets || 0}
              </div>
              <span className="text-xs text-gray-500 mt-2">
                {stats?.assets_change_7d >= 0 ? '+' : ''}{stats?.assets_change_7d || 0}% this week
              </span>
            </div>
          </Card>

          <Card>
            <div className="flex flex-col">
              <span className="text-gray-400 text-sm mb-2">Total Scans</span>
              <div className="text-4xl font-bold text-purple-500">
                {stats?.total_scans || 0}
              </div>
              <span className="text-xs text-gray-500 mt-2">
                {stats?.scans_change_7d >= 0 ? '+' : ''}{stats?.scans_change_7d || 0}% this week
              </span>
            </div>
          </Card>

          <Card>
            <div className="flex flex-col">
              <span className="text-gray-400 text-sm mb-2">Critical Alerts</span>
              <div className="text-4xl font-bold text-red-500">
                {stats?.new_critical_alerts || 0}
              </div>
              <span className="text-xs text-gray-500 mt-2">Last 7 days</span>
            </div>
          </Card>

          <Card>
            <div className="flex flex-col">
              <span className="text-gray-400 text-sm mb-2">Open Vulnerabilities</span>
              <div className="text-4xl font-bold text-orange-500">
                {stats?.open_vulnerabilities || 0}
              </div>
              <span className="text-xs text-gray-500 mt-2">Requires attention</span>
            </div>
          </Card>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Risk Trend Chart */}
          <Card title="Risk Score Trend (30 Days)">
            {riskTrend.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={riskTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#9ca3af"
                    tick={{ fill: '#9ca3af' }}
                  />
                  <YAxis 
                    stroke="#9ca3af"
                    tick={{ fill: '#9ca3af' }}
                    domain={[0, 100]}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1f2937', 
                      border: '1px solid #374151',
                      borderRadius: '8px'
                    }}
                    labelStyle={{ color: '#f3f4f6' }}
                  />
                  <Legend wrapperStyle={{ color: '#9ca3af' }} />
                  <Line 
                    type="monotone" 
                    dataKey="risk_score" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6', r: 4 }}
                    name="Risk Score"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-500">
                No data available. Start scanning to see trends.
              </div>
            )}
          </Card>

          {/* Asset Distribution Pie Chart */}
          <Card title="Assets by Risk Level">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1f2937', 
                      border: '1px solid #374151',
                      borderRadius: '8px'
                    }}
                  />
                  <Legend wrapperStyle={{ color: '#9ca3af' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-500">
                No assets discovered yet.
              </div>
            )}
          </Card>
        </div>

        {/* All Discovered Assets */}
        <Card title="Discovered Assets">
          {allAssets.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Asset</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Type</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Risk Score</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Risk Level</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Open Ports</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Status</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Last Seen</th>
                  </tr>
                </thead>
                <tbody>
                  {allAssets.map((asset, index) => (
                    <tr key={asset._id || index} className="border-b border-gray-800 hover:bg-gray-800">
                      <td className="py-3 px-4 text-white font-mono text-sm">
                        {asset.asset_value}
                      </td>
                      <td className="py-3 px-4 text-gray-400 capitalize">
                        {asset.asset_type?.replace('_', ' ')}
                      </td>
                      <td className={`py-3 px-4 font-bold ${
                        getRiskColor(asset.risk_level)
                      }`}>
                        {asset.risk_score}
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant={getRiskBadgeVariant(asset.risk_level)}>
                          {asset.risk_level?.toUpperCase() || 'UNKNOWN'}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-gray-400 text-sm">
                        {asset.open_ports && asset.open_ports.length > 0 
                          ? asset.open_ports.slice(0, 3).join(', ') + (asset.open_ports.length > 3 ? '...' : '')
                          : 'None'}
                      </td>
                      <td className="py-3 px-4">
                        {asset.http_status ? (
                          <span className={`text-sm ${
                            asset.http_status >= 200 && asset.http_status < 300 
                              ? 'text-green-500' 
                              : asset.http_status >= 400 
                              ? 'text-red-500' 
                              : 'text-yellow-500'
                          }`}>
                            {asset.http_status}
                          </span>
                        ) : (
                          <span className="text-gray-500 text-sm">N/A</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-gray-400 text-sm">
                        {asset.last_scanned_at 
                          ? new Date(asset.last_scanned_at).toLocaleDateString()
                          : 'Never'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <p className="mb-4">No assets discovered yet.</p>
              <Button onClick={() => window.location.href = '/assets'}>
                Start Your First Scan
              </Button>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;

import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Navigation from '../components/ui/Navigation';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const Analytics = () => {
  const { user } = useAuth();
  const [riskTrend, setRiskTrend] = useState([]);
  const [assetDistribution, setAssetDistribution] = useState([]);
  const [riskFactors, setRiskFactors] = useState([]);
  const [totalAssets, setTotalAssets] = useState(0);
  const [securityInsights, setSecurityInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30');

  useEffect(() => {
    fetchAnalyticsData();
  }, [timeRange]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      
      // Fetch risk trend
      const trendResponse = await api.get(`/api/analytics/risk-trend?days=${timeRange}`);
      const trendData = trendResponse.data.data || trendResponse.data;
      setRiskTrend(trendData.trend || []);
      
      // Fetch asset distribution
      const distributionResponse = await api.get('/api/analytics/asset-distribution');
      const distData = distributionResponse.data.data || distributionResponse.data;
      setAssetDistribution(distData.distribution || []);
      
      // Fetch risk factors
      const factorsResponse = await api.get('/api/analytics/risk-factors');
      const factorsData = factorsResponse.data.data || factorsResponse.data;
      setRiskFactors(factorsData.factors || []);
      setTotalAssets(factorsData.total_assets || 0);
      
      // Fetch security insights
      const insightsResponse = await api.get('/api/analytics/security-insights');
      const insightsData = insightsResponse.data.data || insightsResponse.data;
      setSecurityInsights(insightsData.insights || []);
      
    } catch (error) {
      console.error('Failed to fetch analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Colors for charts
  const RISK_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#10b981'];
  const ASSET_COLORS = ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900">
      <Navigation />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 sm:mb-8 fade-in">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white">Risk Analytics</h1>
            <p className="text-sm sm:text-base text-gray-400 mt-1">Security insights and risk trends</p>
          </div>
          
          <div className="mt-4 md:mt-0">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="w-full md:w-auto px-3 py-2 glass-card rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
            >
              <option value="7" className="bg-gray-800">Last 7 days</option>
              <option value="30" className="bg-gray-800">Last 30 days</option>
              <option value="90" className="bg-gray-800">Last 90 days</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="glass-card p-8 rounded-2xl flex flex-col items-center gap-4">
              <div className="relative w-12 h-12">
                <div className="absolute inset-0 rounded-full border-4 border-blue-500/20"></div>
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-500 animate-spin"></div>
              </div>
              <p className="text-white font-medium">Loading analytics...</p>
            </div>
          </div>
        ) : (
          <>
            {/* Risk Trend Chart */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
              <Card title="Risk Score Trend">
                {riskTrend.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={riskTrend}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis 
                        dataKey="date" 
                        stroke="#9ca3af"
                        tick={{ fill: '#9ca3af', fontSize: 12 }}
                        tickFormatter={(value) => {
                          const date = new Date(value);
                          return `${date.getMonth() + 1}/${date.getDate()}`;
                        }}
                      />
                      <YAxis 
                        stroke="#9ca3af"
                        tick={{ fill: '#9ca3af' }}
                        domain={[0, 100]}
                        label={{ value: 'Risk Score', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#1f2937', 
                          border: '1px solid #374151',
                          borderRadius: '8px'
                        }}
                        labelStyle={{ color: '#f3f4f6' }}
                        formatter={(value) => [`${value}`, 'Risk Score']}
                        labelFormatter={(label) => {
                          const date = new Date(label);
                          return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                        }}
                      />
                      <Legend wrapperStyle={{ color: '#9ca3af' }} />
                      <Line 
                        type="monotone" 
                        dataKey="risk_score" 
                        stroke="#3b82f6" 
                        strokeWidth={3}
                        dot={{ fill: '#3b82f6', r: 5, strokeWidth: 2, stroke: '#1f2937' }}
                        activeDot={{ r: 7 }}
                        name="Risk Score"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                    <svg className="w-16 h-16 mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                    </svg>
                    <p className="text-center">No risk trend data yet.<br />Complete a scan to start tracking.</p>
                  </div>
                )}
              </Card>

              {/* Asset Distribution */}
              <Card title="Assets by Type">
                {assetDistribution.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={assetDistribution}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis 
                        dataKey="type" 
                        stroke="#9ca3af"
                        tick={{ fill: '#9ca3af' }}
                      />
                      <YAxis 
                        stroke="#9ca3af"
                        tick={{ fill: '#9ca3af' }}
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
                      <Bar 
                        dataKey="count" 
                        name="Asset Count"
                      >
                        {assetDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={ASSET_COLORS[index % ASSET_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-64 text-gray-500">
                    No data available.
                  </div>
                )}
              </Card>
            </div>

            {/* Risk Factors */}
            <Card title="Risk Factors Analysis" className="mb-8">
              {riskFactors.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {riskFactors.map((factor, index) => (
                    <div key={index} className="bg-gray-800 rounded-lg p-6">
                      <div className="flex items-center justify-between mb-3">
                        <div className="text-lg font-semibold text-white">
                          {factor.name}
                        </div>
                        <div className={`text-2xl font-bold ${
                          factor.percentage > 50 ? 'text-red-500' :
                          factor.percentage > 25 ? 'text-orange-500' :
                          'text-yellow-500'
                        }`}>
                          {factor.percentage}%
                        </div>
                      </div>
                      <div className="text-sm text-gray-400 mb-3">
                        {factor.count} of {totalAssets} assets affected
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            factor.percentage > 50 ? 'bg-red-500' :
                            factor.percentage > 25 ? 'bg-orange-500' :
                            'bg-yellow-500'
                          }`}
                          style={{ width: `${factor.percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No risk factors detected. Your assets are well secured!
                </div>
              )}
            </Card>

            {/* Security Insights */}
            <Card title="Security Insights">
              {securityInsights.length > 0 ? (
                <div className="space-y-4">
                  {securityInsights.map((insight, index) => {
                    const getInsightColor = (type) => {
                      switch (type) {
                        case 'critical': return 'bg-red-500';
                        case 'warning': return 'bg-orange-500';
                        case 'success': return 'bg-green-500';
                        case 'info': return 'bg-blue-500';
                        default: return 'bg-gray-500';
                      }
                    };

                    const getInsightIcon = (type) => {
                      switch (type) {
                        case 'critical': return '⚠️';
                        case 'warning': return '⚡';
                        case 'success': return '✓';
                        case 'info': return 'ℹ';
                        default: return '•';
                      }
                    };

                    return (
                      <div key={index} className="flex items-start">
                        <div className="flex-shrink-0 mt-1">
                          <div className={`w-3 h-3 rounded-full ${getInsightColor(insight.type)}`}></div>
                        </div>
                        <div className="ml-3 flex-1">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h3 className="text-white font-medium flex items-center gap-2">
                                <span>{getInsightIcon(insight.type)}</span>
                                {insight.title}
                                {insight.priority === 'critical' && (
                                  <span className="px-2 py-0.5 text-xs bg-red-900 text-red-200 rounded-full">
                                    Critical
                                  </span>
                                )}
                              </h3>
                              <p className="text-gray-400 text-sm mt-1">
                                {insight.message}
                              </p>
                              {insight.recommendation && (
                                <div className="mt-3 p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
                                  <div className="flex items-start gap-2">
                                    <svg className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                                    </svg>
                                    <div className="flex-1">
                                      <div className="text-xs font-semibold text-blue-300 mb-1">AI Recommendation</div>
                                      <p className="text-sm text-blue-200">{insight.recommendation}</p>
                                    </div>
                                  </div>
                                </div>
                              )}
                              {insight.stats && (
                                <div className="mt-2 text-xs text-gray-500">
                                  {Object.entries(insight.stats).map(([key, value]) => (
                                    <span key={key} className="mr-3">
                                      {key}: {value}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-start">
                    <div className="flex-shrink-0 mt-1">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-white font-medium">Start Monitoring</h3>
                      <p className="text-gray-400 text-sm mt-1">
                        Run your first scan to receive personalized security insights based on your assets.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </Card>
          </>
        )}
      </div>
    </div>
  );
};

export default Analytics;
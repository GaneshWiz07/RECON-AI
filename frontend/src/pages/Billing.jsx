import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Navigation from '../components/ui/Navigation';
import LoadingSpinner from '../components/ui/LoadingSpinner';

const Billing = () => {
  const { user } = useAuth();
  const [subscription, setSubscription] = useState(null);
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBillingData();
  }, []);

  const fetchBillingData = async () => {
    try {
      setLoading(true);
      
      // Fetch subscription data
      const subscriptionResponse = await api.get('/api/billing/subscription');
      setSubscription(subscriptionResponse.data);
      
      // Fetch usage data
      const usageResponse = await api.get('/api/billing/usage');
      setUsage(usageResponse.data);
      
    } catch (error) {
      console.error('Failed to fetch billing data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (plan) => {
    try {
      const response = await api.post('/api/billing/create-checkout', { plan });
      window.location.href = response.data.checkout_url;
    } catch (error) {
      console.error('Upgrade failed:', error);
    }
  };

  const handleCancel = async () => {
    try {
      await api.post('/api/billing/cancel-subscription');
      await fetchBillingData(); // Refresh data
    } catch (error) {
      console.error('Cancellation failed:', error);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-green-900/20 to-gray-900">
      <Navigation />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 sm:mb-8 fade-in">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white">Billing & Subscription</h1>
            <p className="text-sm sm:text-base text-gray-400 mt-1">Manage your subscription and usage</p>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="glass-card p-8 rounded-2xl flex flex-col items-center gap-4">
              <LoadingSpinner size="lg" />
              <p className="text-white font-medium">Loading billing information...</p>
            </div>
          </div>
        ) : (
          <>
            {/* Current Plan */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
              <Card className="lg:col-span-2">
                <h2 className="text-xl font-semibold text-white mb-4">Current Plan</h2>
                
                {subscription ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-medium text-white capitalize">
                          {subscription.plan} Plan
                        </h3>
                        <p className="text-gray-400">
                          {subscription.status === 'active' ? 'Active' : 'Inactive'}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-white">
                          {subscription.plan === 'pro' ? '$29' : '$0'}
                          <span className="text-lg font-normal text-gray-400">/month</span>
                        </p>
                      </div>
                    </div>
                    
                    {subscription.current_period_end && (
                      <div className="pt-4 border-t border-gray-700">
                        <p className="text-gray-400">
                          {subscription.cancel_at_period_end 
                            ? `Subscription will cancel on ${formatDate(subscription.current_period_end)}`
                            : `Renews on ${formatDate(subscription.current_period_end)}`
                          }
                        </p>
                      </div>
                    )}
                    
                    <div className="pt-4 flex gap-3">
                      {subscription.plan === 'free' ? (
                        <Button onClick={() => handleUpgrade('pro')}>
                          Upgrade to Pro
                        </Button>
                      ) : (
                        <>
                          {!subscription.cancel_at_period_end && (
                            <Button variant="outline" onClick={handleCancel}>
                              Cancel Subscription
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-400">No subscription data available.</p>
                  </div>
                )}
              </Card>

              {/* Usage Stats */}
              <Card>
                <h2 className="text-xl font-semibold text-white mb-4">Usage This Month</h2>
                
                {usage ? (
                  <div className="space-y-6">
                    {/* Show scan credits only for Free users */}
                    {subscription?.plan === 'free' && (
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-gray-400">Manual Scan Credits</span>
                          <span className="text-white">
                            {usage.scan_credits_used} / {usage.scan_credits_limit}
                          </span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div 
                            className="bg-green-500 h-2 rounded-full" 
                            style={{ 
                              width: `${Math.min((usage.scan_credits_used / usage.scan_credits_limit) * 100, 100)}%` 
                            }}
                          ></div>
                        </div>
                        <div className="text-right text-sm text-gray-400 mt-1">
                          {Math.round((usage.scan_credits_used / usage.scan_credits_limit) * 100)}%
                        </div>
                      </div>
                    )}
                    
                    {/* Show Pro status for Pro users */}
                    {subscription?.plan === 'pro' && (
                      <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-500 rounded-lg p-4">
                        <div className="flex items-center gap-3 mb-2">
                          <svg className="w-6 h-6 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <h3 className="text-lg font-semibold text-white">Pro Plan Active</h3>
                        </div>
                        <ul className="space-y-2 text-sm text-gray-300">
                          <li className="flex items-center gap-2">
                            <span className="text-green-400">✓</span>
                            <span>Unlimited manual scans</span>
                          </li>
                          <li className="flex items-center gap-2">
                            <span className="text-green-400">✓</span>
                            <span>Continuous asset monitoring</span>
                          </li>
                          <li className="flex items-center gap-2">
                            <span className="text-green-400">✓</span>
                            <span>Real-time threat detection</span>
                          </li>
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-400">No usage data available.</p>
                  </div>
                )}
              </Card>
            </div>

            {/* Plan Comparison */}
            <Card title="Plan Comparison">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Free Plan */}
                <div className="border border-gray-700 rounded-lg p-6">
                  <h3 className="text-xl font-bold text-white mb-2">Free Plan</h3>
                  <div className="text-3xl font-bold text-white mb-4">
                    $0<span className="text-lg font-normal text-gray-400">/month</span>
                  </div>
                  
                  <ul className="space-y-3 mb-6">
                    <li className="flex items-center">
                      <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-gray-300">10 Manual Scans/month</span>
                    </li>
                    <li className="flex items-center">
                      <svg className="h-5 w-5 text-red-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                      <span className="text-gray-500">No Continuous Monitoring</span>
                    </li>
                    <li className="flex items-center">
                      <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-gray-300">Basic Asset Discovery</span>
                    </li>
                    <li className="flex items-center">
                      <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-gray-300">Email Support</span>
                    </li>
                  </ul>
                  
                  {subscription?.plan === 'free' ? (
                    <Button disabled className="w-full">
                      Current Plan
                    </Button>
                  ) : (
                    <Button variant="outline" onClick={() => handleUpgrade('free')} className="w-full">
                      Downgrade
                    </Button>
                  )}
                </div>

                {/* Pro Plan */}
                <div className="border border-blue-500 rounded-lg p-6 relative">
                  <div className="absolute top-0 right-0 bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg rounded-tr-lg">
                    POPULAR
                  </div>
                  
                  <h3 className="text-xl font-bold text-white mb-2">Pro Plan</h3>
                  <div className="text-3xl font-bold text-white mb-4">
                    $29<span className="text-lg font-normal text-gray-400">/month</span>
                  </div>
                  
                  <ul className="space-y-3 mb-6">
                    <li className="flex items-center">
                      <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-gray-300">Unlimited Manual Scans</span>
                    </li>
                    <li className="flex items-center">
                      <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-gray-300 font-semibold">Continuous Asset Monitoring</span>
                    </li>
                    <li className="flex items-center">
                      <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-gray-300">Real-time Threat Detection</span>
                    </li>
                    <li className="flex items-center">
                      <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-gray-300">Advanced Asset Discovery</span>
                    </li>
                    <li className="flex items-center">
                      <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-gray-300">Priority Support</span>
                    </li>
                    <li className="flex items-center">
                      <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-gray-300">Custom Email Alerts</span>
                    </li>
                  </ul>
                  
                  {subscription?.plan === 'pro' ? (
                    <Button disabled className="w-full">
                      Current Plan
                    </Button>
                  ) : (
                    <Button onClick={() => handleUpgrade('pro')} className="w-full">
                      Upgrade to Pro
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          </>
        )}
      </div>
    </div>
  );
};

export default Billing;
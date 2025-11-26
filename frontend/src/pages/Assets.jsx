import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Navigation from '../components/ui/Navigation';
import LoadingSpinner from '../components/ui/LoadingSpinner';

const Assets = () => {
  const { user } = useAuth();
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [domain, setDomain] = useState('');
  const [scanSubdomains, setScanSubdomains] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [scanNotification, setScanNotification] = useState(null);
  const [scannedDomain, setScannedDomain] = useState('');
  const [userPlan, setUserPlan] = useState('free');
  const [misconfigurationRecommendations, setMisconfigurationRecommendations] = useState({});
  const [summaryRecommendation, setSummaryRecommendation] = useState(null);
  const [loadingRecommendations, setLoadingRecommendations] = useState({});
  const [loadingSummaryRecommendation, setLoadingSummaryRecommendation] = useState(false);
  const [securityTerms, setSecurityTerms] = useState([]);
  const [loadingSecurityTerms, setLoadingSecurityTerms] = useState(false);

  useEffect(() => {
    fetchAssets();
    fetchUserPlan();

    // Auto-refresh every 15 seconds to show new assets from scans
    const interval = setInterval(() => {
      fetchAssets();
    }, 15000);

    return () => clearInterval(interval);
  }, [currentPage, searchTerm]);

  const fetchUserPlan = async () => {
    try {
      const response = await api.get('/api/billing/subscription');
      setUserPlan(response.data.data?.plan || 'free');
    } catch (error) {
      console.error('Failed to fetch user plan:', error);
    }
  };

  const fetchAssets = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/assets/?page=${currentPage}&search=${searchTerm}`);
      console.log('Assets response:', response.data); // Debug log
      const assetsData = response.data.data || response.data;
      const fetchedAssets = assetsData.assets || [];
      setAssets(fetchedAssets);
      setTotalPages(assetsData.pagination?.total_pages || assetsData.total_pages || 1);
      
      // Fetch security terms when assets are loaded
      if (fetchedAssets.length > 0 && securityTerms.length === 0) {
        fetchSecurityTerms();
      }
    } catch (error) {
      console.error('Failed to fetch assets:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMisconfigurationRecommendation = async (assetId) => {
    if (!assetId) {
      console.error('Asset ID is missing');
      return;
    }
    
    // Check if already fetched or currently loading
    if (misconfigurationRecommendations[assetId] || loadingRecommendations[assetId]) {
      console.log('Recommendation already fetched or loading for:', assetId);
      return;
    }
    
    try {
      console.log('Starting to fetch recommendation for asset:', assetId);
      setLoadingRecommendations(prev => {
        const updated = { ...prev, [assetId]: true };
        console.log('Updated loading state:', updated);
        return updated;
      });
      
      const response = await api.post('/api/assets/misconfiguration-recommendation', {
        asset_id: assetId
      });
      
      console.log('Recommendation response received:', response.data);
      console.log('Full response structure:', JSON.stringify(response.data, null, 2));
      
      // Handle different response structures
      const recommendation = response.data?.data?.recommendation 
        || response.data?.recommendation 
        || response.data?.data?.data?.recommendation
        || null;
      
      console.log('Extracted recommendation:', recommendation);
      console.log('Recommendation type:', typeof recommendation);
      console.log('Recommendation length:', recommendation?.length);
      
      // Check if recommendation exists and is not empty
      if (recommendation && recommendation.trim().length > 0) {
        setMisconfigurationRecommendations(prev => {
          const updated = { ...prev, [assetId]: recommendation.trim() };
          console.log('Updated recommendations state:', updated);
          return updated;
        });
      } else {
        console.warn('No recommendation in response or recommendation is empty');
        console.warn('Response data:', response.data);
        setMisconfigurationRecommendations(prev => ({
          ...prev,
          [assetId]: 'Unable to generate AI recommendations. Please check console for details.'
        }));
      }
    } catch (error) {
      console.error(`Failed to fetch recommendation for asset ${assetId}:`, error);
      console.error('Error details:', error.response?.data || error.message);
      setMisconfigurationRecommendations(prev => ({
        ...prev,
        [assetId]: error.response?.data?.detail || 'Unable to load AI recommendations at this time.'
      }));
    } finally {
      setLoadingRecommendations(prev => {
        const updated = { ...prev, [assetId]: false };
        console.log('Cleared loading state for:', assetId, updated);
        return updated;
      });
    }
  };

  const fetchSummaryRecommendation = async () => {
    if (loadingSummaryRecommendation) {
      console.log('Summary recommendation already loading');
      return; // Already loading
    }
    
    try {
      console.log('Starting to fetch summary recommendation');
      setLoadingSummaryRecommendation(true);
      
      const response = await api.post('/api/assets/summary-recommendation', {});
      console.log('Summary recommendation response received:', response.data);
      console.log('Full response structure:', JSON.stringify(response.data, null, 2));
      
      // Handle different response structures
      const recommendation = response.data?.data?.recommendation 
        || response.data?.recommendation 
        || response.data?.data?.data?.recommendation
        || null;
      
      console.log('Extracted summary recommendation:', recommendation);
      console.log('Recommendation type:', typeof recommendation);
      console.log('Recommendation length:', recommendation?.length);
      
      // Check if recommendation exists and is not empty
      if (recommendation && recommendation.trim().length > 0) {
        setSummaryRecommendation(recommendation.trim());
      } else {
        console.warn('No recommendation in response or recommendation is empty');
        console.warn('Response data:', response.data);
        setSummaryRecommendation('Unable to generate AI recommendations. Please check console for details.');
      }
    } catch (error) {
      console.error('Failed to fetch summary recommendation:', error);
      console.error('Error details:', error.response?.data || error.message);
      setSummaryRecommendation(error.response?.data?.detail || 'Unable to load AI recommendations at this time.');
    } finally {
      setLoadingSummaryRecommendation(false);
    }
  };

  const fetchSecurityTerms = async () => {
    if (loadingSecurityTerms || securityTerms.length > 0) {
      return; // Already loading or fetched
    }
    
    try {
      console.log('Starting to fetch security terms');
      setLoadingSecurityTerms(true);
      
      const response = await api.post('/api/assets/security-terms', {});
      console.log('Security terms response received:', response.data);
      
      const terms = response.data?.data?.terms || [];
      console.log('Extracted security terms:', terms);
      
      if (terms && terms.length > 0) {
        setSecurityTerms(terms);
      } else {
        // Fallback to default terms if AI generation fails
        setSecurityTerms([
          ['Phishing', 'Fake Message'],
          ['Smishing', 'Fake SMS'],
          ['Vishing', 'Fake Call'],
          ['Malware', 'Harmful File'],
          ['Ransomware', 'Lock Attack'],
          ['Data Leak', 'Info Spill'],
        ]);
      }
    } catch (error) {
      console.error('Failed to fetch security terms:', error);
      // Fallback to default terms on error
      setSecurityTerms([
        ['Phishing', 'Fake Message'],
        ['Smishing', 'Fake SMS'],
        ['Vishing', 'Fake Call'],
        ['Malware', 'Harmful File'],
        ['Ransomware', 'Lock Attack'],
        ['Data Leak', 'Info Spill'],
      ]);
    } finally {
      setLoadingSecurityTerms(false);
    }
  };

  const handleScan = async (e) => {
    e.preventDefault();
    if (!domain) return;

    try {
      setLoading(true);
      setScanNotification(null);
      const scanDomain = domain;
      setScannedDomain(scanDomain);

      const response = await api.post('/api/assets/scan', {
        domain: scanDomain,
        scan_subdomains: scanSubdomains
      });

      const scanId = response.data.scan_id;

      // Show initial scanning message
      setScanNotification({
        type: 'info',
        message: `Scanning "${scanDomain}"... This may take a few seconds.`
      });

      // Wait for scan to complete (check every 15 seconds for up to 5 minutes)
      let attempts = 0;
      const maxAttempts = 20;
      let scanCompleted = false;
      let foundAssets = false;
      const initialAssetCount = assets.length;

      while (attempts < maxAttempts && !scanCompleted) {
        await new Promise(resolve => setTimeout(resolve, 15000));

        // Fetch updated assets
        const assetsResponse = await api.get(`/api/assets/?page=1&limit=100`);
        const assetsData = assetsResponse.data.data || assetsResponse.data;
        const currentAssets = assetsData.assets || [];

        // Check if assets were found for this domain
        const domainAssets = currentAssets.filter(asset => {
          const assetValue = asset.asset_value || '';
          const parentDomain = asset.parent_domain || '';
          // Clean the domain for comparison
          const cleanScanDomain = scanDomain.replace(/^https?:\/\//, '').replace(/\/$/, '');
          const cleanAssetValue = assetValue.replace(/^https?:\/\//, '').replace(/\/$/, '');
          const cleanParentDomain = parentDomain.replace(/^https?:\/\//, '').replace(/\/$/, '');

          return cleanAssetValue.includes(cleanScanDomain) ||
            cleanParentDomain.includes(cleanScanDomain) ||
            cleanAssetValue === cleanScanDomain ||
            cleanParentDomain === cleanScanDomain;
        });

        // If we found new assets, scan is complete
        if (domainAssets.length > 0 && currentAssets.length > initialAssetCount) {
          scanCompleted = true;
          foundAssets = true;
          setScanNotification({
            type: 'success',
            message: `Scan completed! Found ${domainAssets.length} asset(s) for "${scanDomain}".`
          });
          setAssets(currentAssets);
          setTotalPages(assetsData.pagination?.total_pages || assetsData.total_pages || 1);
          break;
        }

        // After 4 attempts (60 seconds), check if scan finished with 0 assets
        if (attempts >= 4) {
          // Refresh assets one more time
          await fetchAssets();
          const finalCheck = assets.filter(asset => {
            const assetValue = asset.asset_value || '';
            const parentDomain = asset.parent_domain || '';
            const cleanScanDomain = scanDomain.replace(/^https?:\/\//, '').replace(/\/$/, '');
            return assetValue.includes(cleanScanDomain) || parentDomain.includes(cleanScanDomain);
          });

          if (finalCheck.length === 0) {
            scanCompleted = true;
            foundAssets = false;
            setScanNotification({
              type: 'warning',
              message: `No assets found for "${scanDomain}".`
            });
            break;
          }
        }

        attempts++;
      }

      if (!scanCompleted) {
        await fetchAssets();
        foundAssets = false;
        setScanNotification({
          type: 'warning',
          message: `No assets found for "${scanDomain}".`
        });
      }

      // Only reset form if assets were found
      if (foundAssets) {
        setDomain('');
        setScanSubdomains(false);
      }

      // Auto-hide notification after 10 seconds
      setTimeout(() => setScanNotification(null), 10000);

    } catch (error) {
      console.error('Scan failed:', error);
      setScanNotification({
        type: 'error',
        message: `Scan failed: ${error.response?.data?.detail || error.message}`
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClearAssets = async () => {
    if (!window.confirm('Are you sure you want to clear all scanned records? This action cannot be undone.')) {
      return;
    }

    try {
      setLoading(true);
      const response = await api.delete('/api/assets/');
      const deletedCount = response.data?.deleted_count || 0;
      
      setScanNotification({
        type: 'success',
        message: `Successfully cleared ${deletedCount} scanned record(s).`
      });

      // Refresh assets list
      await fetchAssets();
      setCurrentPage(1);
      setSearchTerm('');

      // Auto-hide notification after 5 seconds
      setTimeout(() => setScanNotification(null), 5000);
    } catch (error) {
      console.error('Failed to clear assets:', error);
      setScanNotification({
        type: 'error',
        message: `Failed to clear assets: ${error.message || 'Unknown error'}`
      });
    } finally {
      setLoading(false);
    }
  };

  const filteredAssets = assets.filter(asset =>
    asset.asset_value.toLowerCase().includes(searchTerm.toLowerCase()) ||
    asset.asset_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Filter assets with real breach history from database
  const assetsWithBreaches = filteredAssets.filter(asset => (asset.breach_history_count || 0) > 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-indigo-900/20 to-gray-900">
      <Navigation />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 sm:mb-8 fade-in">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white">Asset Discovery</h1>
            <p className="text-sm sm:text-base text-gray-400 mt-1">Discover and manage your internet assets</p>
          </div>

        </div>

        {/* Notification */}
        {scanNotification && (
          <div className={`mb-6 p-4 rounded-lg glass-card border scale-in ${scanNotification.type === 'success' ? 'bg-green-900/20 border-green-500 text-green-200' :
            scanNotification.type === 'warning' ? 'bg-yellow-900/20 border-yellow-500 text-yellow-200' :
              scanNotification.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' :
                'bg-blue-900/20 border-blue-500 text-blue-200'
            }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {scanNotification.type === 'success' && (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                )}
                {scanNotification.type === 'warning' && (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                )}
                {scanNotification.type === 'error' && (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                )}
                {scanNotification.type === 'info' && (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                )}
                <p className="text-sm font-medium">{scanNotification.message}</p>
              </div>
              <button
                onClick={() => setScanNotification(null)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Pro User Continuous Monitoring Banner */}
        {userPlan === 'pro' && (
          <div className="mb-6 bg-gradient-to-r from-blue-900/40 to-purple-900/40 border border-blue-500 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">Pro Plan Active - Continuous Monitoring Enabled</h3>
                  <p className="text-sm text-gray-300">Your assets are being monitored continuously. New threats will be detected automatically.</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-green-400 font-medium">Live</span>
              </div>
            </div>
          </div>
        )}

        {/* Free User Upgrade Prompt */}
        {userPlan === 'free' && (
          <div className="mb-6 bg-gray-800 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-700 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">Manual Scans Only</h3>
                  <p className="text-sm text-gray-400">Upgrade to Pro for unlimited manual scans and continuous asset monitoring.</p>
                </div>
              </div>
              <Button onClick={() => window.location.href = '/billing'}>
                Upgrade to Pro
              </Button>
            </div>
          </div>
        )}

        {/* Scan Form */}
        <Card className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Start New Scan</h2>
          <form onSubmit={handleScan} className="space-y-4">
            <div>
              <label htmlFor="domain" className="block text-sm font-medium text-gray-300 mb-1">
                Domain to Scan
              </label>
              <input
                type="text"
                id="domain"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="example.com"
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="scanSubdomains"
                checked={scanSubdomains}
                onChange={(e) => setScanSubdomains(e.target.checked)}
                className="h-4 w-4 text-blue-600 bg-gray-800 border-gray-700 rounded focus:ring-blue-500"
                disabled={loading}
              />
              <label htmlFor="scanSubdomains" className="ml-2 block text-sm text-gray-300">
                Scan subdomains
              </label>
            </div>

            <Button type="submit" disabled={loading || !domain}>
              {loading ? 'Scanning...' : 'Start Scan'}
            </Button>
          </form>
        </Card>

        {/* Search and Filters */}
        <div className="mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="flex-1">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search assets..."
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Assets Table */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Discovered Assets</h2>
            {assets.length > 0 && (
              <Button
                variant="danger"
                size="sm"
                onClick={handleClearAssets}
                disabled={loading}
              >
                Clear All Records
              </Button>
            )}
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          ) : filteredAssets.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-400">No assets found. Start a scan to discover assets.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Asset</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Type</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Risk Score</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Status</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">Last Seen</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAssets.map((asset, index) => (
                    <tr key={index} className="border-b border-gray-800 hover:bg-gray-800">
                      <td className="py-3 px-4 text-white font-mono text-sm">
                        {asset.asset_value}
                      </td>
                      <td className="py-3 px-4 text-gray-400 capitalize">
                        {asset.asset_type}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`font-bold ${asset.risk_score >= 80 ? 'text-red-500' :
                          asset.risk_score >= 60 ? 'text-orange-500' :
                            asset.risk_score >= 30 ? 'text-yellow-500' : 'text-green-500'
                          }`}>
                          {asset.risk_score}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${asset.http_status >= 200 && asset.http_status < 300 ? 'bg-green-900 text-green-300' :
                          asset.http_status >= 400 ? 'bg-red-900 text-red-300' : 'bg-gray-700 text-gray-300'
                          }`}>
                          {asset.http_status ? `HTTP ${asset.http_status}` : 'N/A'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-400 text-sm">
                        {asset.last_scanned_at ? new Date(asset.last_scanned_at).toLocaleDateString() : 'Never'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6">
              <Button
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
              >
                Previous
              </Button>

              <span className="text-gray-400">
                Page {currentPage} of {totalPages}
              </span>

              <Button
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
              >
                Next
              </Button>
            </div>
          )}
        </Card>

        {/* Misconfigurations & Vulnerabilities Section */}
        {filteredAssets.some(asset => asset.misconfigurations?.total_issues > 0) && (
          <Card className="mt-8">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-white">Security Misconfigurations Detected</h2>
              <p className="text-sm text-gray-400 mt-1">
                Found {filteredAssets.filter(a => a.misconfigurations?.total_issues > 0).length} asset(s) with security misconfigurations
              </p>
            </div>

            <div className="space-y-6">
              {filteredAssets.filter(asset => asset.misconfigurations?.total_issues > 0).map((asset, index) => {
                const misc = asset.misconfigurations;
                if (!misc || misc.total_issues === 0) return null;

                return (
                  <div key={index} className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    {/* Asset Header */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${misc.severity === 'critical' ? 'bg-red-900/30 border border-red-500' :
                          misc.severity === 'high' ? 'bg-orange-900/30 border border-orange-500' :
                            misc.severity === 'medium' ? 'bg-yellow-900/30 border border-yellow-500' :
                              'bg-blue-900/30 border border-blue-500'
                          }`}>
                          <svg className={`w-5 h-5 ${misc.severity === 'critical' ? 'text-red-500' :
                            misc.severity === 'high' ? 'text-orange-500' :
                              misc.severity === 'medium' ? 'text-yellow-500' :
                                'text-blue-500'
                            }`} fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-white font-semibold font-mono">{asset.asset_value}</h3>
                          <p className="text-sm text-gray-400">{misc.total_issues} issue(s) detected</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-400">Severity</div>
                        <div className={`text-lg font-bold uppercase ${misc.severity === 'critical' ? 'text-red-500' :
                          misc.severity === 'high' ? 'text-orange-500' :
                            misc.severity === 'medium' ? 'text-yellow-500' :
                              'text-blue-500'
                          }`}>
                          {misc.severity}
                        </div>
                      </div>
                    </div>

                    {/* Issue Categories Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {/* Web Headers */}
                      {misc.web_headers?.has_issues && (
                        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold text-white text-sm">HTTP Headers</h4>
                            <span className="px-2 py-0.5 bg-red-900/50 text-red-200 rounded-full text-xs">
                              {misc.web_headers.missing_headers?.length || 0}
                            </span>
                          </div>
                          <ul className="space-y-1 text-xs text-gray-400">
                            {misc.web_headers.missing_headers?.slice(0, 3).map((h, i) => (
                              <li key={i} className="flex items-start gap-1">
                                <span className="text-red-400">•</span>
                                <span className="truncate">{h.header}</span>
                              </li>
                            ))}
                            {misc.web_headers.missing_headers?.length > 3 && (
                              <li className="text-gray-500">+{misc.web_headers.missing_headers.length - 3} more</li>
                            )}
                          </ul>
                        </div>
                      )}

                      {/* SSL/TLS */}
                      {misc.ssl?.has_issues && (
                        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold text-white text-sm">SSL/TLS</h4>
                            <span className="px-2 py-0.5 bg-red-900/50 text-red-200 rounded-full text-xs">
                              {misc.ssl.issues?.length || 0}
                            </span>
                          </div>
                          <ul className="space-y-1 text-xs text-gray-400">
                            {misc.ssl.issues?.slice(0, 3).map((issue, i) => (
                              <li key={i} className="flex items-start gap-1">
                                <span className="text-red-400">•</span>
                                <span className="truncate">{issue.type?.replace(/_/g, ' ')}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* DNS */}
                      {misc.dns?.has_issues && (
                        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold text-white text-sm">DNS Config</h4>
                            <span className="px-2 py-0.5 bg-red-900/50 text-red-200 rounded-full text-xs">
                              {misc.dns.issues?.length || 0}
                            </span>
                          </div>
                          <ul className="space-y-1 text-xs text-gray-400">
                            {misc.dns.issues?.slice(0, 3).map((issue, i) => (
                              <li key={i} className="flex items-start gap-1">
                                <span className="text-red-400">•</span>
                                <span className="truncate">{issue.type?.replace(/_/g, ' ')}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Cloud Buckets */}
                      {misc.cloud_buckets?.has_issues && (
                        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold text-white text-sm">Cloud Storage</h4>
                            <span className="px-2 py-0.5 bg-red-900/50 text-red-200 rounded-full text-xs">
                              {misc.cloud_buckets.buckets?.length || 0}
                            </span>
                          </div>
                          <ul className="space-y-1 text-xs text-gray-400">
                            {misc.cloud_buckets.buckets?.slice(0, 3).map((bucket, i) => (
                              <li key={i} className="flex items-start gap-1">
                                <span className="text-red-400">•</span>
                                <span className="truncate">{bucket.type}: {bucket.bucket}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Security Files */}
                      {misc.security_files?.has_issues && (
                        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold text-white text-sm">Exposed Files</h4>
                            <span className="px-2 py-0.5 bg-red-900/50 text-red-200 rounded-full text-xs">
                              {misc.security_files.sensitive_exposed?.length || 0}
                            </span>
                          </div>
                          <ul className="space-y-1 text-xs text-gray-400">
                            {misc.security_files.sensitive_exposed?.slice(0, 3).map((file, i) => (
                              <li key={i} className="flex items-start gap-1">
                                <span className="text-red-400">•</span>
                                <span className="truncate">{file.path}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Open Directories */}
                      {misc.open_directories?.has_issues && (
                        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold text-white text-sm">Open Directories</h4>
                            <span className="px-2 py-0.5 bg-red-900/50 text-red-200 rounded-full text-xs">
                              {misc.open_directories.open_directories?.length || 0}
                            </span>
                          </div>
                          <ul className="space-y-1 text-xs text-gray-400">
                            {misc.open_directories.open_directories?.slice(0, 3).map((dir, i) => (
                              <li key={i} className="flex items-start gap-1">
                                <span className="text-red-400">•</span>
                                <span className="truncate">{dir.path}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* AI-Powered Security Recommendations */}
                    {(() => {
                      // Use asset_id if available, otherwise use asset_value as fallback identifier
                      // IMPORTANT: This must match what we send to the API
                      const assetId = asset.asset_id || asset.asset_value;
                      
                      // Only show if we have a valid asset identifier
                      if (!assetId) {
                        return null;
                      }
                      
                      const recommendation = misconfigurationRecommendations[assetId];
                      const isLoading = loadingRecommendations[assetId];
                      
                      return (
                        <div className="mt-6 bg-gradient-to-r from-blue-900/20 to-purple-900/20 border border-blue-500 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-blue-200 font-semibold flex items-center gap-2">
                              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                              </svg>
                              AI Security Recommendations
                              <span className="text-xs bg-purple-500/30 text-purple-200 px-2 py-0.5 rounded-full ml-2">AI-Powered</span>
                            </h4>
                            {!recommendation && !isLoading && (
                              <button
                                onClick={() => {
                                  console.log('Generating recommendation for asset:', {
                                    assetId,
                                    asset_id: asset.asset_id,
                                    asset_value: asset.asset_value,
                                    currentRecommendations: misconfigurationRecommendations,
                                    currentLoading: loadingRecommendations
                                  });
                                  fetchMisconfigurationRecommendation(assetId);
                                }}
                                className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-full transition-colors"
                              >
                                Generate
                              </button>
                            )}
                          </div>
                          {isLoading ? (
                            <div className="flex items-center gap-2 text-blue-300 text-sm">
                              <LoadingSpinner size="sm" />
                              <span>Generating AI recommendations...</span>
                            </div>
                          ) : recommendation ? (
                            <div className="text-sm text-blue-300 leading-relaxed whitespace-pre-line">
                              <p className="mt-2">{recommendation}</p>
                            </div>
                          ) : (
                            <div className="text-sm text-gray-400 italic">
                              Click "Generate" to get AI-powered security recommendations for this asset.
                            </div>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                );
              })}
            </div>
          </Card>
        )}

        {/* Data Breaches for Discovered Assets */}
        {assetsWithBreaches.length > 0 && (
          <Card className="mt-8">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-white">Data Breaches Detected</h2>
              <p className="text-sm text-gray-400 mt-1">
                Found {assetsWithBreaches.length} asset(s) with breach history
              </p>
            </div>

            <div className="space-y-6">
              {assetsWithBreaches.map((asset, index) => {
                const breachCount = asset.breach_history_count || 0;
                if (breachCount === 0) return null;

                return (
                  <div key={index} className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    {/* Asset Header */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-red-900/30 border border-red-500 rounded-lg flex items-center justify-center">
                          <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-white font-semibold font-mono">{asset.asset_value}</h3>
                          <p className="text-sm text-gray-400">{breachCount} breach(es) detected via Have I Been Pwned</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-400">Risk Score</div>
                        <div className={`text-2xl font-bold ${asset.risk_score >= 80 ? 'text-red-500' :
                          asset.risk_score >= 60 ? 'text-orange-500' :
                            asset.risk_score >= 30 ? 'text-yellow-500' : 'text-green-500'
                          }`}>
                          {asset.risk_score}
                        </div>
                      </div>
                    </div>

                    {/* Breach Info */}
                    <div className="bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center gap-2 text-sm text-gray-300">
                        <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                        </svg>
                        <span>
                          This domain has been involved in <strong className="text-red-400">{breachCount}</strong> known data breach(es) according to Have I Been Pwned database.
                          Review security practices and consider password rotation for affected accounts.
                        </span>
                      </div>
                    </div>

                  </div>
                );
              })}
            </div>

            {/* Security Warning */}
            <div className="mt-6 bg-blue-900/20 border border-blue-500 rounded-lg p-4">
              <h4 className="text-blue-200 font-semibold mb-2 flex items-center gap-2">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
                Security Recommendations
              </h4>
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-blue-300">
                <li className="flex items-start gap-2">
                  <span className="text-blue-400 mt-0.5">•</span>
                  <span>Rotate credentials for affected domains</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-400 mt-0.5">•</span>
                  <span>Enable 2FA on all accounts</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-400 mt-0.5">•</span>
                  <span>Monitor for suspicious activity</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-400 mt-0.5">•</span>
                  <span>Use unique passwords per service</span>
                </li>
              </ul>
            </div>
          </Card>
        )}

        {/* Summary Report Section */}
        {assets.length > 0 && (
          <Card className="mt-8">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white">📊 Security Summary Report</h2>
                <p className="text-sm text-gray-400 mt-1">
                  Comprehensive overview of your assets, vulnerabilities, and security status
                </p>
              </div>
              <button
                onClick={async () => {
                  try {
                    const response = await api.get('/api/assets/export-detailed-report', {
                      responseType: 'blob',
                      headers: {
                        'Accept': 'application/pdf'
                      }
                    });
                    
                    // When responseType is 'blob', the interceptor returns the full response
                    // So response is the full axios response, and response.data is the Blob
                    const blob = response.data || response;
                    
                    // Verify blob is not empty
                    if (!blob || (blob.size !== undefined && blob.size === 0)) {
                      console.error('PDF blob is empty or invalid:', blob);
                      throw new Error('PDF file is empty');
                    }
                    
                    // Create download link
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', `detailed_security_report_${new Date().toISOString().split('T')[0]}.pdf`);
                    document.body.appendChild(link);
                    link.click();
                    link.remove();
                    window.URL.revokeObjectURL(url);
                  } catch (error) {
                    console.error('Failed to export detailed report:', error);
                    console.error('Error details:', error.response || error);
                    alert(`Failed to export detailed report: ${error.message || 'Unknown error'}. Please try again.`);
                  }
                }}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Export Detailed PDF Report
              </button>
            </div>

            {/* SME-Friendly Terms Section */}
            <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-500/50 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                Easy Terms for Business Owners
              </h3>
              {loadingSecurityTerms ? (
                <div className="flex items-center justify-center gap-2 text-blue-300 py-8">
                  <LoadingSpinner size="sm" />
                  <span className="text-sm">Generating relevant security terms based on your scan...</span>
                </div>
              ) : securityTerms.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {securityTerms.map(([tech, simple], idx) => (
                    <div key={idx} className="bg-gray-800/50 rounded-lg p-3">
                      <div className="text-sm font-semibold text-blue-300">{tech}</div>
                      <div className="text-xs text-gray-400 mt-1">→ {simple}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-400 italic py-4">
                  Loading security terms based on your scan results...
                </div>
              )}
            </div>

            {/* Overall Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">Total Assets</div>
                <div className="text-3xl font-bold text-white">{assets.length}</div>
              </div>
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">High Risk</div>
                <div className="text-3xl font-bold text-red-500">
                  {assets.filter(a => a.risk_level === 'high' || a.risk_level === 'critical').length}
                </div>
              </div>
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">Medium Risk</div>
                <div className="text-3xl font-bold text-yellow-500">
                  {assets.filter(a => a.risk_level === 'medium').length}
                </div>
              </div>
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">Low Risk</div>
                <div className="text-3xl font-bold text-green-500">
                  {assets.filter(a => a.risk_level === 'low').length}
                </div>
              </div>
            </div>

            {/* Security Misconfigurations Summary */}
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-white mb-4">🔒 Security Issues Found</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-2">Missing Security Headers</div>
                  <div className="text-2xl font-bold text-orange-400">
                    {assets.reduce((sum, a) => sum + (((a.misconfigurations || {}).web_headers || {}).missing_headers || []).length, 0)}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Headers protect against attacks</div>
                </div>
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-2">SSL/TLS Issues</div>
                  <div className="text-2xl font-bold text-red-400">
                    {assets.reduce((sum, a) => sum + (((a.misconfigurations || {}).ssl || {}).issues || []).length, 0)}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Certificate problems</div>
                </div>
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-2">DNS Problems</div>
                  <div className="text-2xl font-bold text-yellow-400">
                    {assets.reduce((sum, a) => sum + (((a.misconfigurations || {}).dns || {}).issues || []).length, 0)}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">DNS configuration errors</div>
                </div>
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-2">Exposed Cloud Storage</div>
                  <div className="text-2xl font-bold text-red-400">
                    {assets.reduce((sum, a) => sum + (((a.misconfigurations || {}).cloud_buckets || {}).buckets || []).length, 0)}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Public cloud buckets</div>
                </div>
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-2">Sensitive Files Exposed</div>
                  <div className="text-2xl font-bold text-red-400">
                    {assets.reduce((sum, a) => sum + (((a.misconfigurations || {}).security_files || {}).sensitive_exposed || []).length, 0)}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Config files visible</div>
                </div>
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-2">Open Directories</div>
                  <div className="text-2xl font-bold text-orange-400">
                    {assets.reduce((sum, a) => sum + (((a.misconfigurations || {}).open_directories || {}).open_directories || []).length, 0)}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Directory listings enabled</div>
                </div>
              </div>
            </div>

            {/* Data Breaches Summary */}
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-white mb-4">🚨 Data Breach Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
                  <div className="text-sm text-red-300 mb-2">Total Breaches</div>
                  <div className="text-3xl font-bold text-red-400">
                    {assets.reduce((sum, a) => sum + (a.breach_history_count || 0), 0)}
                  </div>
                </div>
                <div className="bg-orange-900/20 border border-orange-500 rounded-lg p-4">
                  <div className="text-sm text-orange-300 mb-2">Assets with Breaches</div>
                  <div className="text-3xl font-bold text-orange-400">
                    {assets.filter(a => (a.breach_history_count || 0) > 0).length}
                  </div>
                </div>
                <div className="bg-yellow-900/20 border border-yellow-500 rounded-lg p-4">
                  <div className="text-sm text-yellow-300 mb-2">Breach Risk Level</div>
                  <div className="text-2xl font-bold text-yellow-400">
                    {assets.reduce((sum, a) => sum + (a.breach_history_count || 0), 0) > 10 ? 'HIGH' :
                      assets.reduce((sum, a) => sum + (a.breach_history_count || 0), 0) > 3 ? 'MEDIUM' : 'LOW'}
                  </div>
                </div>
              </div>
            </div>

            {/* AI-Powered Strategic Recommendations */}
            <div className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 border border-blue-500 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-blue-200 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Strategic Security Recommendations
                  <span className="text-xs bg-purple-500/30 text-purple-200 px-2 py-0.5 rounded-full ml-2">AI-Powered</span>
                </h3>
                {!summaryRecommendation && !loadingSummaryRecommendation && (
                  <button
                    onClick={() => {
                      console.log('Generate button clicked for summary recommendation');
                      fetchSummaryRecommendation();
                    }}
                    className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-full transition-colors"
                  >
                    Generate
                  </button>
                )}
              </div>
              {loadingSummaryRecommendation ? (
                <div className="flex items-center gap-2 text-blue-300 text-sm">
                  <LoadingSpinner size="sm" />
                  <span>Generating AI strategic recommendations...</span>
                </div>
              ) : summaryRecommendation ? (
                <div className="text-sm text-blue-300 leading-relaxed whitespace-pre-line">
                  {summaryRecommendation}
                </div>
              ) : (
                <div className="text-sm text-gray-400 italic">
                  Click "Generate" to get AI-powered strategic recommendations based on your security scan results.
                </div>
              )}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Assets;
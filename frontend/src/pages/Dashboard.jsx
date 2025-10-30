/**
 * Dashboard Page - Placeholder
 * Will be completed in Phase 4
 */

import { useAuth } from '../context/AuthContext';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

const Dashboard = () => {
  const { user, signOut } = useAuth();

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Dashboard</h1>
            <p className="text-gray-400 mt-1">Welcome back, {user?.email}</p>
          </div>
          <Button variant="ghost" onClick={signOut}>
            Sign Out
          </Button>
        </div>

        <Card title="Dashboard Overview" className="mb-6">
          <p className="text-gray-400">
            Dashboard components will be implemented in Phase 4.
          </p>
          <p className="text-gray-500 mt-2">
            Current Phase: Core Infrastructure Complete ✓
          </p>
        </Card>

        <div className="grid grid-cols-3 gap-6">
          <Card title="Assets">
            <div className="text-4xl font-bold text-primary">0</div>
            <p className="text-gray-400 mt-2">Discovered Assets</p>
          </Card>

          <Card title="Risk Score">
            <div className="text-4xl font-bold text-warning">0</div>
            <p className="text-gray-400 mt-2">Overall Risk</p>
          </Card>

          <Card title="Scans">
            <div className="text-4xl font-bold text-success">0</div>
            <p className="text-gray-400 mt-2">Total Scans</p>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

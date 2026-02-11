import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Plus, Database, Trash2, Play, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { connections } from '../services/api';
import type { Connection, ConnectionCreate } from '../types';

const DB_TYPES = [
  { value: 'postgresql', label: 'PostgreSQL', defaultPort: 5432 },
  { value: 'sqlserver', label: 'SQL Server', defaultPort: 1433 },
  { value: 'db2', label: 'IBM DB2', defaultPort: 50000 },
] as const;

export default function ConnectionsPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({});
  
  const { data: connectionList = [], isLoading } = useQuery({
    queryKey: ['connections'],
    queryFn: connections.list,
  });
  
  const createMutation = useMutation({
    mutationFn: connections.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connections'] });
      setShowForm(false);
    },
  });
  
  const deleteMutation = useMutation({
    mutationFn: connections.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['connections'] }),
  });
  
  const testConnection = async (id: string) => {
    setTestResults((prev) => ({ ...prev, [id]: { success: false, message: 'Testing...' } }));
    try {
      const result = await connections.test(id);
      setTestResults((prev) => ({ ...prev, [id]: result }));
    } catch (error) {
      setTestResults((prev) => ({ ...prev, [id]: { success: false, message: 'Test failed' } }));
    }
  };
  
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data: ConnectionCreate = {
      name: formData.get('name') as string,
      db_type: formData.get('db_type') as ConnectionCreate['db_type'],
      host: formData.get('host') as string,
      port: parseInt(formData.get('port') as string, 10),
      database_name: formData.get('database_name') as string,
      username: formData.get('username') as string,
      password: formData.get('password') as string,
    };
    createMutation.mutate(data);
  };
  
  if (isLoading) {
    return <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-primary-500" /></div>;
  }
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Database Connections</h1>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary">
          <Plus className="h-4 w-4 mr-2" /> Add Connection
        </button>
      </div>
      
      {showForm && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">New Connection</h2>
          <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
            <div><label className="input-label">Name</label><input name="name" className="input" required /></div>
            <div>
              <label className="input-label">Database Type</label>
              <select name="db_type" className="select" required>
                {DB_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div><label className="input-label">Host</label><input name="host" className="input" defaultValue="localhost" required /></div>
            <div><label className="input-label">Port</label><input name="port" type="number" className="input" defaultValue={5432} required /></div>
            <div><label className="input-label">Database Name</label><input name="database_name" className="input" required /></div>
            <div><label className="input-label">Username</label><input name="username" className="input" required /></div>
            <div className="col-span-2"><label className="input-label">Password</label><input name="password" type="password" className="input" required /></div>
            <div className="col-span-2 flex justify-end space-x-3">
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
              <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Creating...' : 'Create Connection'}
              </button>
            </div>
          </form>
        </div>
      )}
      
      <div className="grid gap-4">
        {connectionList.map((conn: Connection) => (
          <div key={conn.id} className="card flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Database className="h-10 w-10 text-primary-500" />
              <div>
                <h3 className="font-semibold text-gray-900">{conn.name}</h3>
                <p className="text-sm text-gray-500">{conn.db_type} • {conn.host}:{conn.port}/{conn.database_name}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              {testResults[conn.id] && (
                <span className={`text-sm ${testResults[conn.id].success ? 'text-green-600' : 'text-red-600'}`}>
                  {testResults[conn.id].success ? <CheckCircle className="h-4 w-4 inline mr-1" /> : <XCircle className="h-4 w-4 inline mr-1" />}
                  {testResults[conn.id].message}
                </span>
              )}
              <button onClick={() => testConnection(conn.id)} className="btn-ghost"><Play className="h-4 w-4" /></button>
              <Link to={`/schema/${conn.id}`} className="btn-secondary">View Schema</Link>
              <Link to={`/intent/${conn.id}`} className="btn-primary">Create Intent</Link>
              <button onClick={() => deleteMutation.mutate(conn.id)} className="btn-ghost text-red-500"><Trash2 className="h-4 w-4" /></button>
            </div>
          </div>
        ))}
        {connectionList.length === 0 && (
          <div className="card text-center py-12 text-gray-500">No connections yet. Add one to get started.</div>
        )}
      </div>
    </div>
  );
}


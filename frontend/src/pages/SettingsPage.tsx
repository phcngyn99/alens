import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Key, Plus, Loader2, CheckCircle, Cloud, Lock, Users, UserPlus, Trash2 } from 'lucide-react';
import { ai, users } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import type { AICredentialCreate, AIProviderType, UserCreate } from '../types';

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI', models: ['gpt-4-turbo-preview', 'gpt-4', 'gpt-3.5-turbo'], isAzure: false },
  { value: 'anthropic', label: 'Anthropic', models: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'], isAzure: false },
  { value: 'azure_openai', label: 'Azure OpenAI', models: ['gpt-4', 'gpt-4-turbo', 'gpt-35-turbo'], isAzure: true },
  { value: 'azure_anthropic', label: 'Azure Anthropic', models: ['claude-opus-4-5', 'claude-sonnet-4', 'claude-haiku'], isAzure: true },
] as const;

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { isAdmin, username } = useAuth();
  const [showForm, setShowForm] = useState(false);
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [showUserForm, setShowUserForm] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<AIProviderType>('openai');
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  const { data: credentials = [], isLoading } = useQuery({
    queryKey: ['ai-credentials'],
    queryFn: ai.getCredentials,
  });

  const { data: usersList = [], isLoading: usersLoading } = useQuery({
    queryKey: ['users'],
    queryFn: users.list,
    enabled: isAdmin(),
  });

  const createMutation = useMutation({
    mutationFn: ai.createCredential,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-credentials'] });
      setShowForm(false);
    },
  });

  const changePasswordMutation = useMutation({
    mutationFn: users.changePassword,
    onSuccess: () => {
      setPasswordSuccess(true);
      setShowPasswordForm(false);
      setTimeout(() => setPasswordSuccess(false), 3000);
    },
    onError: (error: unknown) => {
      setPasswordError(error instanceof Error ? error.message : 'Failed to change password');
    },
  });

  const createUserMutation = useMutation({
    mutationFn: users.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowUserForm(false);
    },
  });

  const deleteUserMutation = useMutation({
    mutationFn: users.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  const handlePasswordSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setPasswordError(null);
    const formData = new FormData(e.currentTarget);
    const newPassword = formData.get('new_password') as string;
    const confirmPassword = formData.get('confirm_password') as string;

    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }

    changePasswordMutation.mutate({
      current_password: formData.get('current_password') as string,
      new_password: newPassword,
    });
  };

  const handleUserSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const userData: UserCreate = {
      username: formData.get('username') as string,
      password: formData.get('password') as string,
      role: formData.get('role') as 'admin' | 'user',
      is_active: true,
    };
    createUserMutation.mutate(userData);
  };
  
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const provider = formData.get('provider') as AIProviderType;
    const isAzure = provider === 'azure_openai' || provider === 'azure_anthropic';

    const data: AICredentialCreate = {
      provider,
      api_key: formData.get('api_key') as string,
      model_name: formData.get('model_name') as string,
      max_tokens: parseInt(formData.get('max_tokens') as string, 10),
      // Azure-specific fields
      ...(isAzure && {
        endpoint_url: formData.get('endpoint_url') as string,
        deployment_name: formData.get('deployment_name') as string || undefined,
        api_version: formData.get('api_version') as string,
      }),
    };
    createMutation.mutate(data);
  };

  const currentProvider = PROVIDERS.find((p) => p.value === selectedProvider);
  const isAzureProvider = currentProvider?.isAzure ?? false;
  
  if (isLoading) {
    return <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-primary-500" /></div>;
  }
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500">Manage AI credentials and preferences</p>
        </div>
      </div>
      
      {/* AI Credentials */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">AI Credentials</h2>
          <button onClick={() => setShowForm(!showForm)} className="btn-secondary">
            <Plus className="h-4 w-4 mr-2" /> Add Credential
          </button>
        </div>
        
        {showForm && (
          <form onSubmit={handleSubmit} className="mb-6 p-4 bg-gray-50 rounded-lg space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="input-label">Provider</label>
                <select
                  name="provider"
                  className="select"
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value as AIProviderType)}
                >
                  {PROVIDERS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
              </div>
              <div>
                <label className="input-label">Model {isAzureProvider ? '/ Deployment Name' : ''}</label>
                <select name="model_name" className="select">
                  {currentProvider?.models.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <div className="col-span-2">
                <label className="input-label">API Key</label>
                <input name="api_key" type="password" className="input" placeholder={isAzureProvider ? 'Azure API key' : 'sk-...'} required />
              </div>

              {/* Azure-specific fields */}
              {isAzureProvider && (
                <>
                  <div className="col-span-2">
                    <label className="input-label">Endpoint URL</label>
                    <input name="endpoint_url" type="url" className="input" placeholder="https://your-resource.openai.azure.com" required />
                    <p className="text-xs text-gray-500 mt-1">Your Azure endpoint URL</p>
                  </div>
                  <div>
                    <label className="input-label">Deployment Name (optional)</label>
                    <input name="deployment_name" type="text" className="input" placeholder="my-deployment" />
                    <p className="text-xs text-gray-500 mt-1">Defaults to model name if empty</p>
                  </div>
                  <div>
                    <label className="input-label">API Version</label>
                    <input name="api_version" type="text" className="input"
                      defaultValue={selectedProvider === 'azure_openai' ? '2024-02-15-preview' : '2023-06-01'}
                      required
                    />
                  </div>
                </>
              )}

              <div>
                <label className="input-label">Max Tokens</label>
                <input name="max_tokens" type="number" className="input" defaultValue={4096} required />
              </div>
            </div>
            <div className="flex justify-end space-x-3">
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
              <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Saving...' : 'Save Credential'}
              </button>
            </div>
          </form>
        )}
        
        {credentials.length > 0 ? (
          <div className="space-y-3">
            {credentials.map((cred) => {
              const isAzure = cred.provider === 'azure_openai' || cred.provider === 'azure_anthropic';
              return (
                <div key={cred.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {isAzure ? (
                      <Cloud className="h-5 w-5 text-blue-500" />
                    ) : (
                      <Key className="h-5 w-5 text-primary-500" />
                    )}
                    <div>
                      <p className="font-medium">
                        {PROVIDERS.find(p => p.value === cred.provider)?.label || cred.provider}
                      </p>
                      <p className="text-sm text-gray-500">
                        {cred.model_name} • Max {cred.max_tokens} tokens
                      </p>
                      {isAzure && cred.endpoint_url && (
                        <p className="text-xs text-gray-400 truncate max-w-md">{cred.endpoint_url}</p>
                      )}
                    </div>
                  </div>
                  <CheckCircle className="h-5 w-5 text-green-500" />
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No AI credentials configured. Add one to enable model generation.</p>
        )}
      </div>
      
      {/* Account Settings */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Account Settings</h2>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <Lock className="h-5 w-5 text-gray-500" />
              <div>
                <p className="font-medium">Logged in as: {username}</p>
                <p className="text-sm text-gray-500">Change your password</p>
              </div>
            </div>
            <button onClick={() => setShowPasswordForm(!showPasswordForm)} className="btn-secondary">
              Change Password
            </button>
          </div>

          {passwordSuccess && (
            <div className="p-3 bg-green-50 text-green-800 rounded-lg">Password changed successfully!</div>
          )}

          {showPasswordForm && (
            <form onSubmit={handlePasswordSubmit} className="p-4 bg-gray-50 rounded-lg space-y-4">
              {passwordError && (
                <div className="p-3 bg-red-50 text-red-800 rounded-lg">{passwordError}</div>
              )}
              <div className="grid grid-cols-1 gap-4 max-w-md">
                <div>
                  <label className="input-label">Current Password</label>
                  <input name="current_password" type="password" className="input" required />
                </div>
                <div>
                  <label className="input-label">New Password</label>
                  <input name="new_password" type="password" className="input" minLength={6} required />
                </div>
                <div>
                  <label className="input-label">Confirm New Password</label>
                  <input name="confirm_password" type="password" className="input" minLength={6} required />
                </div>
              </div>
              <div className="flex justify-end space-x-3">
                <button type="button" onClick={() => setShowPasswordForm(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-primary" disabled={changePasswordMutation.isPending}>
                  {changePasswordMutation.isPending ? 'Saving...' : 'Update Password'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* User Management (Admin Only) */}
      {isAdmin() && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold flex items-center">
              <Users className="h-5 w-5 mr-2" />
              User Management
            </h2>
            <button onClick={() => setShowUserForm(!showUserForm)} className="btn-secondary">
              <UserPlus className="h-4 w-4 mr-2" /> Add User
            </button>
          </div>

          {showUserForm && (
            <form onSubmit={handleUserSubmit} className="mb-6 p-4 bg-gray-50 rounded-lg space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="input-label">Username</label>
                  <input name="username" type="text" className="input" minLength={3} required />
                </div>
                <div>
                  <label className="input-label">Password</label>
                  <input name="password" type="password" className="input" minLength={6} required />
                </div>
                <div>
                  <label className="input-label">Role</label>
                  <select name="role" className="select">
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end space-x-3">
                <button type="button" onClick={() => setShowUserForm(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-primary" disabled={createUserMutation.isPending}>
                  {createUserMutation.isPending ? 'Creating...' : 'Create User'}
                </button>
              </div>
            </form>
          )}

          {usersLoading ? (
            <div className="flex justify-center py-4"><Loader2 className="h-6 w-6 animate-spin text-primary-500" /></div>
          ) : usersList.length > 0 ? (
            <div className="space-y-3">
              {usersList.map((user) => (
                <div key={user.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">{user.username}</p>
                    <p className="text-sm text-gray-500">
                      Role: <span className={user.role === 'admin' ? 'text-primary-600 font-medium' : ''}>{user.role}</span>
                      {' • '}
                      Status: <span className={user.is_active ? 'text-green-600' : 'text-red-600'}>{user.is_active ? 'Active' : 'Inactive'}</span>
                    </p>
                  </div>
                  {user.username !== username && (
                    <button
                      onClick={() => deleteUserMutation.mutate(user.id)}
                      className="text-red-500 hover:text-red-700"
                      disabled={deleteUserMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">No users found.</p>
          )}
        </div>
      )}

      {/* Info */}
      <div className="card bg-blue-50 border border-blue-100">
        <h3 className="font-semibold text-blue-900 mb-2">About Alens</h3>
        <p className="text-sm text-blue-800">
          Alens (Analytics Lens) connects to relational databases, introspects schema metadata,
          and uses AI to propose dimensional models for data warehousing. All database access is read-only.
        </p>
        <p className="text-xs text-blue-600 mt-2">Version 0.1.0</p>
      </div>
    </div>
  );
}


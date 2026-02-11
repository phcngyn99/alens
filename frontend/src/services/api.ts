/**
 * API service for communicating with the Alens backend.
 */
import axios from 'axios';
import type {
  TokenWithUser,
  Connection,
  ConnectionCreate,
  DriverStatus,
  Schema,
  Table,
  TableDataPreview,
  Intent,
  IntentCreate,
  AIOutput,
  AICredential,
  AICredentialCreate,
  User,
  UserCreate,
  UserUpdate,
  ChangePasswordRequest,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const auth = {
  login: async (username: string, password: string): Promise<TokenWithUser> => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    const { data } = await api.post<TokenWithUser>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return data;
  },
};

// Users
export const users = {
  getMe: async (): Promise<User> => {
    const { data } = await api.get<User>('/users/me');
    return data;
  },

  changePassword: async (request: ChangePasswordRequest): Promise<{ message: string }> => {
    const { data } = await api.post<{ message: string }>('/users/me/change-password', request);
    return data;
  },

  list: async (): Promise<User[]> => {
    const { data } = await api.get<User[]>('/users');
    return data;
  },

  create: async (user: UserCreate): Promise<User> => {
    const { data } = await api.post<User>('/users', user);
    return data;
  },

  get: async (id: string): Promise<User> => {
    const { data } = await api.get<User>(`/users/${id}`);
    return data;
  },

  update: async (id: string, updates: UserUpdate): Promise<User> => {
    const { data } = await api.patch<User>(`/users/${id}`, updates);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/users/${id}`);
  },
};

// Connections
export const connections = {
  list: async (): Promise<Connection[]> => {
    const { data } = await api.get<Connection[]>('/connections');
    return data;
  },
  
  get: async (id: string): Promise<Connection> => {
    const { data } = await api.get<Connection>(`/connections/${id}`);
    return data;
  },
  
  create: async (connection: ConnectionCreate): Promise<Connection> => {
    const { data } = await api.post<Connection>('/connections', connection);
    return data;
  },
  
  delete: async (id: string): Promise<void> => {
    await api.delete(`/connections/${id}`);
  },
  
  test: async (id: string): Promise<{ success: boolean; message: string }> => {
    const { data } = await api.post(`/connections/${id}/test`);
    return data;
  },
  
  getDrivers: async (): Promise<Record<string, DriverStatus>> => {
    const { data } = await api.get<Record<string, DriverStatus>>('/connections/drivers');
    return data;
  },
};

// Introspection
export const introspection = {
  getSchemas: async (connectionId: string): Promise<string[]> => {
    const { data } = await api.get<string[]>(`/introspect/${connectionId}/schemas`);
    return data;
  },
  
  getTables: async (connectionId: string, schemaName: string): Promise<string[]> => {
    const { data } = await api.get<string[]>(`/introspect/${connectionId}/schemas/${schemaName}/tables`);
    return data;
  },
  
  getSchema: async (connectionId: string, schemaName: string, includeStats = false): Promise<Schema> => {
    const { data } = await api.get<Schema>(
      `/introspect/${connectionId}/schemas/${schemaName}`,
      { params: { include_stats: includeStats } }
    );
    return data;
  },
  
  getTable: async (connectionId: string, schemaName: string, tableName: string): Promise<Table> => {
    const { data } = await api.get<Table>(
      `/introspect/${connectionId}/schemas/${schemaName}/tables/${tableName}`
    );
    return data;
  },

  getTablePreview: async (
    connectionId: string,
    schemaName: string,
    tableName: string,
    limit = 20
  ): Promise<TableDataPreview> => {
    const { data } = await api.get<TableDataPreview>(
      `/introspect/${connectionId}/schemas/${schemaName}/tables/${tableName}/preview`,
      { params: { limit } }
    );
    return data;
  },
};

// Intents
export const intents = {
  list: async (connectionId?: string): Promise<Intent[]> => {
    const { data } = await api.get<Intent[]>('/intents', {
      params: connectionId ? { connection_id: connectionId } : undefined,
    });
    return data;
  },
  
  get: async (id: string): Promise<Intent> => {
    const { data } = await api.get<Intent>(`/intents/${id}`);
    return data;
  },
  
  create: async (intent: IntentCreate): Promise<Intent> => {
    const { data } = await api.post<Intent>('/intents', intent);
    return data;
  },
  
  delete: async (id: string): Promise<void> => {
    await api.delete(`/intents/${id}`);
  },
};

// AI
export const ai = {
  getCredentials: async (): Promise<AICredential[]> => {
    const { data } = await api.get<AICredential[]>('/ai/credentials');
    return data;
  },
  
  createCredential: async (credential: AICredentialCreate): Promise<AICredential> => {
    const { data } = await api.post<AICredential>('/ai/credentials', credential);
    return data;
  },
  
  generate: async (intentId: string, includeStatistics = false): Promise<AIOutput> => {
    const { data } = await api.post<AIOutput>('/ai/generate', {
      intent_id: intentId,
      include_statistics: includeStatistics,
    });
    return data;
  },
};

export default api;


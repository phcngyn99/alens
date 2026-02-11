import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Table2, Key, Link as LinkIcon, Loader2, ChevronDown, ChevronRight } from 'lucide-react';
import { connections, introspection } from '../services/api';
import type { Table, Column } from '../types';

export default function SchemaPage() {
  const { connectionId } = useParams<{ connectionId: string }>();
  const [selectedSchema, setSelectedSchema] = useState<string | null>(null);
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());
  
  const { data: connection } = useQuery({
    queryKey: ['connection', connectionId],
    queryFn: () => connections.get(connectionId!),
    enabled: !!connectionId,
  });
  
  const { data: schemas = [], isLoading: loadingSchemas, error: schemasError, isError: isSchemasError } = useQuery({
    queryKey: ['schemas', connectionId],
    queryFn: () => introspection.getSchemas(connectionId!),
    enabled: !!connectionId,
    retry: 1, // Only retry once for connection errors
    retryDelay: 500, // Short delay between retries
  });

  const { data: schemaData, isLoading: loadingSchema, error: schemaError } = useQuery({
    queryKey: ['schema', connectionId, selectedSchema],
    queryFn: () => introspection.getSchema(connectionId!, selectedSchema!, true),
    enabled: !!connectionId && !!selectedSchema,
  });
  
  const toggleTable = (tableName: string) => {
    setExpandedTables((prev) => {
      const next = new Set(prev);
      if (next.has(tableName)) next.delete(tableName);
      else next.add(tableName);
      return next;
    });
  };
  
  const getHintBadge = (table: Table) => {
    if (table.hint === 'event-like') return <span className="badge-info">Event-like</span>;
    if (table.hint === 'reference-like') return <span className="badge-gray">Reference-like</span>;
    return null;
  };
  
  if (loadingSchemas) {
    return <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-primary-500" /></div>;
  }

  // Extract error message from axios error
  const getErrorMessage = (error: unknown): string => {
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as { response?: { data?: { detail?: string } } };
      return axiosError.response?.data?.detail || 'Unknown error occurred';
    }
    if (error instanceof Error) return error.message;
    return 'Unknown error occurred';
  };

  // Check for both error and isError for comprehensive error handling
  if (isSchemasError || schemasError) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Schema Browser</h1>
          <p className="text-gray-500">{connection?.name} - {connection?.db_type}</p>
        </div>
        <div className="card bg-red-50 border border-red-200">
          <h3 className="text-red-800 font-semibold flex items-center">
            <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            Connection Error
          </h3>
          <p className="text-red-600 mt-2">{getErrorMessage(schemasError || isSchemasError)}</p>
          <p className="text-red-500 text-sm mt-2">
            Unable to connect to the database. Please verify:
          </p>
          <ul className="text-red-500 text-sm mt-1 list-disc list-inside">
            <li>The database server is running and accessible</li>
            <li>The connection credentials are correct</li>
            <li>Network/firewall settings allow the connection</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Schema Browser</h1>
        <p className="text-gray-500">{connection?.name} - {connection?.db_type}</p>
      </div>
      
      <div className="flex space-x-4">
        <div className="w-48">
          <label className="input-label">Schema</label>
          <select
            className="select"
            value={selectedSchema || ''}
            onChange={(e) => setSelectedSchema(e.target.value || null)}
          >
            <option value="">Select schema...</option>
            {schemas.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>
      
      {loadingSchema && <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin text-primary-500" /></div>}

      {schemaError && (
        <div className="card bg-yellow-50 border border-yellow-200">
          <h3 className="text-yellow-800 font-semibold">Error Loading Schema</h3>
          <p className="text-yellow-600 mt-2">{getErrorMessage(schemaError)}</p>
        </div>
      )}

      {schemaData && (
        <div className="space-y-3">
          {schemaData.tables.map((table: Table) => (
            <div key={table.name} className="card p-0 overflow-hidden">
              <button
                onClick={() => toggleTable(table.name)}
                className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  {expandedTables.has(table.name) ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                  <Table2 className="h-5 w-5 text-primary-500" />
                  <span className="font-medium">{table.name}</span>
                  {getHintBadge(table)}
                </div>
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>{table.columns.length} columns</span>
                  {table.fk_count > 0 && <span><LinkIcon className="h-3 w-3 inline" /> {table.fk_count} FKs</span>}
                  {table.approximate_row_count !== null && <span>~{table.approximate_row_count.toLocaleString()} rows</span>}
                </div>
              </button>
              
              {expandedTables.has(table.name) && (
                <div className="border-t border-gray-100 p-4 bg-gray-50">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-500">
                        <th className="pb-2 font-medium">Column</th>
                        <th className="pb-2 font-medium">Type</th>
                        <th className="pb-2 font-medium">Nullable</th>
                        <th className="pb-2 font-medium">Keys</th>
                      </tr>
                    </thead>
                    <tbody>
                      {table.columns.map((col: Column) => (
                        <tr key={col.name} className="border-t border-gray-100">
                          <td className="py-2 font-mono">{col.name}</td>
                          <td className="py-2 text-gray-600">{col.data_type}</td>
                          <td className="py-2">{col.nullable ? 'Yes' : 'No'}</td>
                          <td className="py-2">
                            {col.is_primary_key && <span title="Primary Key"><Key className="h-3 w-3 inline text-yellow-500 mr-1" /></span>}
                            {col.is_foreign_key && <span title="Foreign Key"><LinkIcon className="h-3 w-3 inline text-blue-500" /></span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  
                  {table.foreign_keys.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Foreign Keys</h4>
                      {table.foreign_keys.map((fk) => (
                        <div key={fk.name} className="text-sm text-gray-600">
                          {fk.columns.join(', ')} → {fk.referenced_schema}.{fk.referenced_table}({fk.referenced_columns.join(', ')})
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          {schemaData.tables.length === 0 && (
            <div className="card text-center py-8 text-gray-500">No tables found in this schema.</div>
          )}
        </div>
      )}
    </div>
  );
}


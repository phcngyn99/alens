import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, Key, Link2, Check, X as XIcon, Table as TableIcon, Database } from 'lucide-react';
import { introspection } from '../services/api';
import type { Table } from '../types';

interface TableDetailsPanelProps {
  connectionId: string;
  table: Table;
}

type TabType = 'columns' | 'preview';

export default function TableDetailsPanel({ connectionId, table }: TableDetailsPanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>('columns');

  const { data: preview, isLoading: previewLoading, error: previewError } = useQuery({
    queryKey: ['tablePreview', connectionId, table.schema_name, table.name],
    queryFn: () => introspection.getTablePreview(connectionId, table.schema_name, table.name, 20),
    enabled: activeTab === 'preview',
    staleTime: 60000, // Cache for 1 minute
  });

  return (
    <div className="border rounded-lg bg-white overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b">
        <div className="flex items-center space-x-2">
          <TableIcon className="h-5 w-5 text-indigo-600" />
          <span className="font-semibold text-gray-800">{table.schema_name}.{table.name}</span>
          {table.approximate_row_count !== null && (
            <span className="text-sm text-gray-500">~{table.approximate_row_count.toLocaleString()} rows</span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {table.hint && (
            <span className={`px-2 py-1 text-xs rounded-full ${
              table.hint === 'event-like' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
            }`}>
              {table.hint}
            </span>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        <button
          onClick={() => setActiveTab('columns')}
          className={`px-4 py-2 text-sm font-medium ${
            activeTab === 'columns' 
              ? 'text-indigo-600 border-b-2 border-indigo-600' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <Database className="h-4 w-4 inline mr-1" />
          Columns ({table.columns.length})
        </button>
        <button
          onClick={() => setActiveTab('preview')}
          className={`px-4 py-2 text-sm font-medium ${
            activeTab === 'preview' 
              ? 'text-indigo-600 border-b-2 border-indigo-600' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <TableIcon className="h-4 w-4 inline mr-1" />
          Data Preview
        </button>
      </div>

      {/* Content */}
      <div className="max-h-80 overflow-auto">
        {activeTab === 'columns' && (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Column</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">PK</th>
                <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">FK</th>
                <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Nullable</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Comment</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {table.columns.map((col, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-sm font-medium text-gray-900 flex items-center">
                    {col.is_primary_key && <Key className="h-3 w-3 text-amber-500 mr-1" />}
                    {col.is_foreign_key && <Link2 className="h-3 w-3 text-indigo-500 mr-1" />}
                    {col.name}
                  </td>
                  <td className="px-4 py-2 text-sm text-gray-500 font-mono">{col.data_type}</td>
                  <td className="px-4 py-2 text-center">
                    {col.is_primary_key ? <Check className="h-4 w-4 text-green-500 mx-auto" /> : null}
                  </td>
                  <td className="px-4 py-2 text-center">
                    {col.is_foreign_key ? <Check className="h-4 w-4 text-indigo-500 mx-auto" /> : null}
                  </td>
                  <td className="px-4 py-2 text-center">
                    {col.nullable 
                      ? <span className="text-gray-400 text-xs">NULL</span> 
                      : <XIcon className="h-4 w-4 text-red-400 mx-auto" />}
                  </td>
                  <td className="px-4 py-2 text-sm text-gray-500">{col.comment || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {activeTab === 'preview' && (
          <div className="p-4">
            {previewLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-indigo-600" />
                <span className="ml-2 text-gray-500">Loading data preview...</span>
              </div>
            ) : previewError ? (
              <div className="text-center py-8 text-red-500">
                Error loading preview: {(previewError as Error).message}
              </div>
            ) : preview && preview.rows.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      {preview.columns.map((col, idx) => (
                        <th key={idx} className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {preview.rows.map((row, ridx) => (
                      <tr key={ridx} className="hover:bg-gray-50">
                        {row.map((val, cidx) => (
                          <td key={cidx} className="px-3 py-2 text-gray-700 whitespace-nowrap max-w-xs truncate">
                            {val === null ? <span className="text-gray-400 italic">NULL</span> : String(val)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="mt-2 text-xs text-gray-500">Showing {preview.row_count} rows</p>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">No data available</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}


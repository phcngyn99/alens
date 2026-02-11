import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Loader2, X, Eye, Edit2, ChevronDown, ChevronUp } from 'lucide-react';
import { connections, introspection, intents } from '../services/api';
import type { IntentCreate, TableOfInterest } from '../types';
import TableERD from '../components/TableERD';
import TableDetailsPanel from '../components/TableDetailsPanel';

interface ExtendedTableOfInterest extends TableOfInterest {
  notes?: string;
}

export default function IntentPage() {
  const { connectionId } = useParams<{ connectionId: string }>();
  const navigate = useNavigate();

  const [selectedSchema, setSelectedSchema] = useState<string | null>(null);
  const [selectedTableName, setSelectedTableName] = useState<string | null>(null);
  const [showDetailsPanel, setShowDetailsPanel] = useState(true);
  const [editingDescription, setEditingDescription] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    business_domain: '',
    analytical_goal: 'reporting' as const,
    time_grain: 'daily' as const,
    key_metrics: '',
    exclusions: '',
  });
  const [tablesOfInterest, setTablesOfInterest] = useState<ExtendedTableOfInterest[]>([]);

  const { data: connection } = useQuery({
    queryKey: ['connection', connectionId],
    queryFn: () => connections.get(connectionId!),
    enabled: !!connectionId,
  });

  const { data: schemas = [], isLoading: schemasLoading, error: schemasError } = useQuery({
    queryKey: ['schemas', connectionId],
    queryFn: () => introspection.getSchemas(connectionId!),
    enabled: !!connectionId,
  });

  const { data: schemaData, isLoading: schemaLoading } = useQuery({
    queryKey: ['schema', connectionId, selectedSchema],
    queryFn: () => introspection.getSchema(connectionId!, selectedSchema!),
    enabled: !!connectionId && !!selectedSchema,
  });

  const createMutation = useMutation({
    mutationFn: intents.create,
    onSuccess: (data) => navigate(`/generate/${data.id}`),
  });

  useEffect(() => {
    if (schemas.length > 0 && !selectedSchema) setSelectedSchema(schemas[0]);
  }, [schemas, selectedSchema]);

  // Find the selected table object
  const selectedTable = useMemo(() =>
    schemaData?.tables.find(t => t.name === selectedTableName) || null,
    [schemaData, selectedTableName]
  );

  // Find related tables (tables with FK relationships to selected table)
  const relatedTables = useMemo(() => {
    if (!selectedTable || !schemaData) return [];
    const related = new Set<string>();
    // Tables this table references (outgoing FKs)
    selectedTable.foreign_keys.forEach(fk => related.add(fk.referenced_table));
    // Tables that reference this table (incoming FKs)
    schemaData.tables.forEach(t => {
      t.foreign_keys.forEach(fk => {
        if (fk.referenced_table === selectedTable.name) related.add(t.name);
      });
    });
    return schemaData.tables.filter(t => related.has(t.name));
  }, [selectedTable, schemaData]);

  const addTable = (tableName: string) => {
    if (!tablesOfInterest.find((t) => t.name === tableName)) {
      setTablesOfInterest([...tablesOfInterest, {
        name: tableName,
        is_likely_fact: false,
        is_likely_dimension: false,
        description: '',
        notes: ''
      }]);
      setSelectedTableName(tableName);
    }
  };

  const removeTable = (tableName: string) => {
    setTablesOfInterest(tablesOfInterest.filter((t) => t.name !== tableName));
    if (selectedTableName === tableName) {
      setSelectedTableName(tablesOfInterest.length > 1 ? tablesOfInterest[0].name : null);
    }
  };

  const updateTable = (tableName: string, field: keyof ExtendedTableOfInterest, value: boolean | string) => {
    setTablesOfInterest(tablesOfInterest.map((t) => t.name === tableName ? { ...t, [field]: value } : t));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const intent: IntentCreate = {
      connection_id: connectionId!,
      business_domain: formData.business_domain,
      analytical_goal: formData.analytical_goal,
      time_grain: formData.time_grain,
      key_metrics: formData.key_metrics.split(',').map((s) => s.trim()).filter(Boolean),
      tables_of_interest: tablesOfInterest.map(t => ({
        name: t.name,
        is_likely_fact: t.is_likely_fact,
        is_likely_dimension: t.is_likely_dimension,
        description: t.description || t.notes || undefined,
      })),
      exclusions: formData.exclusions.split(',').map((s) => s.trim()).filter(Boolean),
    };
    createMutation.mutate(intent);
  };
  
  // Show connection error if schemas failed to load
  if (schemasError) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Define Analytical Intent</h1>
          <p className="text-gray-500">{connection?.name}</p>
        </div>
        <div className="card bg-red-50 border-red-200">
          <h3 className="text-red-800 font-semibold">Connection Error</h3>
          <p className="text-red-600 mt-2">{(schemasError as Error).message}</p>
          <p className="text-red-500 text-sm mt-2">Please check your database connection settings and try again.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Define Analytical Intent</h1>
        <p className="text-gray-500">{connection?.name}</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* STEP 1: Tables of Interest - Now at the top */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Step 1: Select Tables of Interest</h2>
          <p className="text-sm text-gray-500 mb-4">Choose the tables you want to include in your dimensional model. You can mark tables as likely fact or dimension tables.</p>

          <div className="flex space-x-4 mb-4">
            <select
              className="select w-48"
              value={selectedSchema || ''}
              onChange={(e) => setSelectedSchema(e.target.value)}
              disabled={schemasLoading}
            >
              {schemasLoading ? (
                <option>Loading schemas...</option>
              ) : schemas.length === 0 ? (
                <option>No schemas found</option>
              ) : (
                schemas.map((s) => <option key={s} value={s}>{s}</option>)
              )}
            </select>
            <select
              className="select flex-1"
              onChange={(e) => { if (e.target.value) addTable(e.target.value); e.target.value = ''; }}
              disabled={schemaLoading}
            >
              <option value="">{schemaLoading ? 'Loading tables...' : 'Add table...'}</option>
              {schemaData?.tables.map((t) => (
                <option key={t.name} value={t.name} disabled={tablesOfInterest.some(toi => toi.name === t.name)}>
                  {t.name} {tablesOfInterest.some(toi => toi.name === t.name) ? '(added)' : ''}
                </option>
              ))}
            </select>
          </div>

          {tablesOfInterest.length > 0 ? (
            <div className="space-y-2">
              {tablesOfInterest.map((t) => (
                <div
                  key={t.name}
                  className={`p-3 rounded-lg border-2 transition-colors cursor-pointer ${
                    selectedTableName === t.name
                      ? 'bg-indigo-50 border-indigo-300'
                      : 'bg-gray-50 border-transparent hover:border-gray-200'
                  }`}
                  onClick={() => setSelectedTableName(t.name)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium">{t.name}</span>
                      {selectedTableName === t.name && (
                        <span className="text-xs text-indigo-600 bg-indigo-100 px-2 py-0.5 rounded">Selected</span>
                      )}
                    </div>
                    <div className="flex items-center space-x-4">
                      <label className="flex items-center space-x-2 text-sm" onClick={(e) => e.stopPropagation()}>
                        <input type="checkbox" checked={t.is_likely_fact}
                          onChange={(e) => updateTable(t.name, 'is_likely_fact', e.target.checked)} />
                        <span className={t.is_likely_fact ? 'text-blue-700 font-medium' : ''}>Fact</span>
                      </label>
                      <label className="flex items-center space-x-2 text-sm" onClick={(e) => e.stopPropagation()}>
                        <input type="checkbox" checked={t.is_likely_dimension}
                          onChange={(e) => updateTable(t.name, 'is_likely_dimension', e.target.checked)} />
                        <span className={t.is_likely_dimension ? 'text-green-700 font-medium' : ''}>Dim</span>
                      </label>
                      <button type="button" onClick={(e) => { e.stopPropagation(); setSelectedTableName(t.name); }}
                        className="text-gray-500 hover:text-indigo-600"><Eye className="h-4 w-4" /></button>
                      <button type="button" onClick={(e) => { e.stopPropagation(); removeTable(t.name); }}
                        className="text-red-500 hover:text-red-700"><X className="h-4 w-4" /></button>
                    </div>
                  </div>

                  {/* Table notes/description */}
                  {editingDescription === t.name ? (
                    <div className="mt-2" onClick={(e) => e.stopPropagation()}>
                      <textarea
                        className="input text-sm w-full"
                        placeholder="Add notes about this table (e.g., business purpose, transformation notes)..."
                        value={t.notes || ''}
                        onChange={(e) => updateTable(t.name, 'notes', e.target.value)}
                        rows={2}
                        autoFocus
                        onBlur={() => setEditingDescription(null)}
                      />
                    </div>
                  ) : t.notes ? (
                    <div className="mt-2 text-sm text-gray-600 flex items-start space-x-1" onClick={(e) => e.stopPropagation()}>
                      <span className="flex-1">{t.notes}</span>
                      <button type="button" onClick={() => setEditingDescription(t.name)} className="text-gray-400 hover:text-gray-600">
                        <Edit2 className="h-3 w-3" />
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      className="mt-2 text-xs text-gray-400 hover:text-indigo-600"
                      onClick={(e) => { e.stopPropagation(); setEditingDescription(t.name); }}
                    >
                      + Add notes
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">Add tables from the dropdown above to get started</p>
          )}
        </div>

        {/* ERD Visualization */}
        {selectedTable && tablesOfInterest.length > 0 && (
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Table Relationships (ERD)</h2>
              <button type="button" onClick={() => setShowDetailsPanel(!showDetailsPanel)} className="text-gray-500 hover:text-indigo-600 flex items-center text-sm">
                {showDetailsPanel ? <ChevronUp className="h-4 w-4 mr-1" /> : <ChevronDown className="h-4 w-4 mr-1" />}
                {showDetailsPanel ? 'Hide' : 'Show'} Details
              </button>
            </div>
            <TableERD
              selectedTable={selectedTable}
              relatedTables={relatedTables}
              onTableClick={(name) => {
                if (!tablesOfInterest.find(t => t.name === name)) {
                  addTable(name);
                }
                setSelectedTableName(name);
              }}
            />
          </div>
        )}

        {/* Table Details Panel */}
        {selectedTable && showDetailsPanel && (
          <TableDetailsPanel connectionId={connectionId!} table={selectedTable} />
        )}

        {/* STEP 2: Business Context */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Step 2: Define Business Context</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="input-label">Business Domain</label>
              <input className="input" placeholder="e.g., E-commerce, Healthcare, Finance" value={formData.business_domain}
                onChange={(e) => setFormData({ ...formData, business_domain: e.target.value })} required />
            </div>
            <div>
              <label className="input-label">Analytical Goal</label>
              <select className="select" value={formData.analytical_goal}
                onChange={(e) => setFormData({ ...formData, analytical_goal: e.target.value as typeof formData.analytical_goal })}>
                <option value="reporting">Reporting</option>
                <option value="bi">Business Intelligence</option>
                <option value="ad-hoc">Ad-hoc Analysis</option>
              </select>
            </div>
            <div>
              <label className="input-label">Time Grain</label>
              <select className="select" value={formData.time_grain}
                onChange={(e) => setFormData({ ...formData, time_grain: e.target.value as typeof formData.time_grain })}>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
            <div className="col-span-2">
              <label className="input-label">Key Metrics (comma-separated)</label>
              <input className="input" placeholder="e.g., revenue, order_count, avg_order_value" value={formData.key_metrics}
                onChange={(e) => setFormData({ ...formData, key_metrics: e.target.value })} />
            </div>
          </div>
        </div>

        {/* Exclusions */}
        <div className="card">
          <label className="input-label">Exclusions (comma-separated table names to exclude from analysis)</label>
          <input className="input" placeholder="e.g., audit_log, temp_data" value={formData.exclusions}
            onChange={(e) => setFormData({ ...formData, exclusions: e.target.value })} />
        </div>

        {/* Submit */}
        <div className="flex justify-end">
          <button type="submit" className="btn-primary" disabled={createMutation.isPending || tablesOfInterest.length === 0}>
            {createMutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin mr-2" />Creating...</> : 'Create Intent & Generate Model'}
          </button>
        </div>
      </form>
    </div>
  );
}


import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Loader2, Sparkles, Download, Copy, Check } from 'lucide-react';
import { intents, ai } from '../services/api';
import type { AIOutput } from '../types';

export default function GeneratePage() {
  const { intentId } = useParams<{ intentId: string }>();
  const [output, setOutput] = useState<AIOutput | null>(null);
  const [copied, setCopied] = useState(false);
  const [includeStats, setIncludeStats] = useState(false);
  
  const { data: intent, isLoading: loadingIntent } = useQuery({
    queryKey: ['intent', intentId],
    queryFn: () => intents.get(intentId!),
    enabled: !!intentId,
  });
  
  const generateMutation = useMutation({
    mutationFn: () => ai.generate(intentId!, includeStats),
    onSuccess: (data) => setOutput(data),
  });
  
  const copyDbml = () => {
    if (output?.dimensional_dbml) {
      navigator.clipboard.writeText(output.dimensional_dbml);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };
  
  const downloadDbml = () => {
    if (output?.dimensional_dbml) {
      const blob = new Blob([output.dimensional_dbml], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dimensional_model_v${output.version}.dbml`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };
  
  if (loadingIntent) {
    return <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-primary-500" /></div>;
  }
  
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Generate Dimensional Model</h1>
        <p className="text-gray-500">Intent v{intent?.version} - {intent?.business_domain}</p>
      </div>
      
      {/* Intent Summary */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Intent Summary</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-gray-500">Goal:</span> <span className="font-medium">{intent?.analytical_goal}</span></div>
          <div><span className="text-gray-500">Time Grain:</span> <span className="font-medium">{intent?.time_grain}</span></div>
          <div><span className="text-gray-500">Key Metrics:</span> <span className="font-medium">{intent?.key_metrics.join(', ') || 'None specified'}</span></div>
          <div><span className="text-gray-500">Tables:</span> <span className="font-medium">{intent?.tables_of_interest.length} selected</span></div>
        </div>
      </div>
      
      {/* Generate Button */}
      {!output && (
        <div className="card text-center py-8">
          <Sparkles className="h-12 w-12 text-primary-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Ready to Generate</h3>
          <p className="text-gray-500 mb-6">The AI will analyze your schema and intent to propose a dimensional model.</p>
          <div className="flex items-center justify-center space-x-4 mb-4">
            <label className="flex items-center space-x-2 text-sm">
              <input type="checkbox" checked={includeStats} onChange={(e) => setIncludeStats(e.target.checked)} />
              <span>Include table statistics (slower)</span>
            </label>
          </div>
          <button onClick={() => generateMutation.mutate()} className="btn-primary" disabled={generateMutation.isPending}>
            {generateMutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin mr-2" />Generating...</> : <><Sparkles className="h-4 w-4 mr-2" />Generate Model</>}
          </button>
          {generateMutation.isError && (
            <p className="text-red-500 mt-4">Error: {(generateMutation.error as Error).message}. Make sure AI credentials are configured in Settings.</p>
          )}
        </div>
      )}
      
      {/* Output */}
      {output && (
        <div className="space-y-6">
          <div className="card">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Model Explanation</h2>
              <span className="badge-info">{output.ai_provider} / {output.ai_model}</span>
            </div>
            <div className="prose prose-sm max-w-none">
              <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">
                {output.model_explanation}
              </pre>
            </div>
            {output.prompt_tokens && (
              <p className="text-xs text-gray-400 mt-4">Tokens: {output.prompt_tokens} prompt + {output.completion_tokens} completion</p>
            )}
          </div>
          
          {output.dimensional_dbml && (
            <div className="card">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Dimensional DBML</h2>
                <div className="flex space-x-2">
                  <button onClick={copyDbml} className="btn-ghost">
                    {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                  </button>
                  <button onClick={downloadDbml} className="btn-secondary"><Download className="h-4 w-4 mr-2" />Download</button>
                </div>
              </div>
              <pre className="text-sm font-mono bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto max-h-96">
                {output.dimensional_dbml}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


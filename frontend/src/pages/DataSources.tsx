import React, { useState, useEffect } from 'react';
import { Plus, Database, RefreshCw, Trash2, Upload, Globe, Webhook, FileText, CheckCircle, XCircle } from 'lucide-react';
import { api } from '../lib/api';

interface DataSource {
  id: string;
  name: string;
  type: string;
  description?: string;
  enabled: boolean;
  last_refresh?: string;
  records_cached: number;
}

export default function DataSources() {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [refreshing, setRefreshing] = useState<string | null>(null);

  useEffect(() => {
    loadDataSources();
  }, []);

  const loadDataSources = async () => {
    try {
      const response = await api.get('/data-sources/');
      setSources(response.data);
    } catch (error) {
      console.error('Failed to load data sources:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshSource = async (sourceId: string) => {
    setRefreshing(sourceId);
    try {
      await api.post(`/data-sources/${sourceId}/refresh`);
      await loadDataSources();
    } catch (error) {
      console.error('Failed to refresh:', error);
    } finally {
      setRefreshing(null);
    }
  };

  const deleteSource = async (sourceId: string) => {
    if (!confirm('Are you sure you want to delete this data source?')) return;
    
    try {
      await api.delete(`/data-sources/${sourceId}`);
      await loadDataSources();
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'api': return <Globe className="w-5 h-5" />;
      case 'webhook': return <Webhook className="w-5 h-5" />;
      case 'database': return <Database className="w-5 h-5" />;
      case 'file': return <FileText className="w-5 h-5" />;
      default: return <Database className="w-5 h-5" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Data Sources</h1>
            <p className="text-gray-400">Connect your data to the AI platform</p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <Plus className="w-5 h-5" />
            Add Data Source
          </button>
        </div>

        {/* Data Sources Grid */}
        {sources.length === 0 ? (
          <div className="text-center py-16">
            <Database className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-400 mb-2">No data sources yet</h3>
            <p className="text-gray-500 mb-6">Connect your first data source to get started</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              Add Data Source
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sources.map((source) => (
              <div
                key={source.id}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 hover:border-blue-500 transition-colors"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-600/20 rounded-lg text-blue-400">
                      {getTypeIcon(source.type)}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white">{source.name}</h3>
                      <span className="text-sm text-gray-400 capitalize">{source.type}</span>
                    </div>
                  </div>
                  {source.enabled ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500" />
                  )}
                </div>

                {source.description && (
                  <p className="text-gray-400 text-sm mb-4">{source.description}</p>
                )}

                <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                  <span>{source.records_cached} records</span>
                  {source.last_refresh && (
                    <span>Updated {new Date(source.last_refresh).toLocaleTimeString()}</span>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => refreshSource(source.id)}
                    disabled={refreshing === source.id}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 rounded-lg transition-colors disabled:opacity-50"
                  >
                    <RefreshCw className={`w-4 h-4 ${refreshing === source.id ? 'animate-spin' : ''}`} />
                    Refresh
                  </button>
                  <button
                    onClick={() => deleteSource(source.id)}
                    className="px-3 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Add Modal */}
        {showAddModal && (
          <AddDataSourceModal
            onClose={() => setShowAddModal(false)}
            onSuccess={() => {
              setShowAddModal(false);
              loadDataSources();
            }}
          />
        )}
      </div>
    </div>
  );
}

interface AddDataSourceModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

function AddDataSourceModal({ onClose, onSuccess }: AddDataSourceModalProps) {
  const [type, setType] = useState<'api' | 'file' | 'webhook' | 'database'>('api');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    api_url: '',
    api_method: 'GET',
    api_auth_type: 'none',
    api_auth_value: '',
    enable_rag: true,
    generate_mcp_tool: true,
  });
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      if (type === 'file' && file) {
        const formDataObj = new FormData();
        formDataObj.append('file', file);
        formDataObj.append('name', formData.name);
        formDataObj.append('description', formData.description);
        formDataObj.append('file_format', file.name.endsWith('.json') ? 'json' : 'csv');
        formDataObj.append('enable_rag', String(formData.enable_rag));
        formDataObj.append('generate_mcp_tool', String(formData.generate_mcp_tool));

        await api.post('/data-sources/upload', formDataObj, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } else {
        await api.post('/data-sources/', {
          ...formData,
          type,
        });
      }

      onSuccess();
    } catch (error) {
      console.error('Failed to add data source:', error);
      alert('Failed to add data source. Please check your configuration.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-700">
          <h2 className="text-2xl font-bold text-white">Add Data Source</h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Data Source Type</label>
            <div className="grid grid-cols-2 gap-3">
              {(['api', 'file', 'webhook', 'database'] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setType(t)}
                  className={`p-4 rounded-lg border-2 transition-colors capitalize ${
                    type === t
                      ? 'border-blue-500 bg-blue-600/20 text-blue-400'
                      : 'border-gray-700 bg-gray-900/50 text-gray-400 hover:border-gray-600'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Common Fields */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Name</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:outline-none"
              placeholder="My Data Source"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:outline-none"
              rows={2}
              placeholder="Optional description"
            />
          </div>

          {/* Type-specific Fields */}
          {type === 'api' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">API URL</label>
                <input
                  type="url"
                  required
                  value={formData.api_url}
                  onChange={(e) => setFormData({ ...formData, api_url: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                  placeholder="https://api.example.com/data"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Method</label>
                  <select
                    value={formData.api_method}
                    onChange={(e) => setFormData({ ...formData, api_method: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                  >
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Auth Type</label>
                  <select
                    value={formData.api_auth_type}
                    onChange={(e) => setFormData({ ...formData, api_auth_type: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                  >
                    <option value="none">None</option>
                    <option value="bearer">Bearer Token</option>
                    <option value="api_key">API Key</option>
                  </select>
                </div>
              </div>

              {formData.api_auth_type !== 'none' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Auth Value</label>
                  <input
                    type="password"
                    value={formData.api_auth_value}
                    onChange={(e) => setFormData({ ...formData, api_auth_value: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                    placeholder="Your API key or token"
                  />
                </div>
              )}
            </>
          )}

          {type === 'file' && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Upload File</label>
              <input
                type="file"
                accept=".json,.csv"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:outline-none"
              />
              <p className="text-sm text-gray-500 mt-1">Supported formats: JSON, CSV</p>
            </div>
          )}

          {type === 'webhook' && (
            <div className="p-4 bg-blue-600/10 border border-blue-600/30 rounded-lg">
              <p className="text-sm text-blue-400">
                After creating the webhook, you'll receive a unique URL to send data to.
              </p>
            </div>
          )}

          {type === 'database' && (
            <div className="p-4 bg-yellow-600/10 border border-yellow-600/30 rounded-lg">
              <p className="text-sm text-yellow-400">
                Database connections coming soon. Use API or file upload for now.
              </p>
            </div>
          )}

          {/* Options */}
          <div className="space-y-3">
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={formData.enable_rag}
                onChange={(e) => setFormData({ ...formData, enable_rag: e.target.checked })}
                className="w-4 h-4 rounded border-gray-700 bg-gray-900 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-300">Index in RAG for AI retrieval</span>
            </label>

            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={formData.generate_mcp_tool}
                onChange={(e) => setFormData({ ...formData, generate_mcp_tool: e.target.checked })}
                className="w-4 h-4 rounded border-gray-700 bg-gray-900 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-300">Generate MCP tool for agents</span>
            </label>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || (type === 'file' && !file) || (type === 'database')}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Adding...' : 'Add Data Source'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

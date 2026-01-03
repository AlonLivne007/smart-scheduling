// frontend/src/pages/Admin/OptimizationConfigPage.jsx
import React, { useState, useEffect } from 'react';
import { Settings, Plus, Edit2, Trash2, Star, Loader2, Save, X } from 'lucide-react';
import toast from 'react-hot-toast';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import { 
  getAllConfigs, 
  getDefaultConfig,
  createConfig, 
  updateConfig, 
  deleteConfig,
  WEIGHT_FIELDS
} from '../../api/optimizationConfig';

export default function OptimizationConfigPage() {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [formData, setFormData] = useState(getInitialFormData());

  useEffect(() => {
    loadConfigs();
  }, []);

  function getInitialFormData() {
    return {
      config_name: '',
      weight_fairness: 0.3,
      weight_preferences: 0.4,
      weight_coverage: 0.2,
      weight_cost: 0.1,
      max_runtime_seconds: 300,
      mip_gap: 0.01,
      is_default: false
    };
  }

  async function loadConfigs() {
    setLoading(true);
    try {
      const data = await getAllConfigs();
      setConfigs(data || []);
    } catch (error) {
      console.error('Failed to load configurations:', error);
      toast.error('Failed to load optimization configurations');
    } finally {
      setLoading(false);
    }
  }

  function handleAddNew() {
    setEditingConfig(null);
    setFormData(getInitialFormData());
    setShowForm(true);
  }

  function handleEdit(config) {
    setEditingConfig(config);
    setFormData({
      config_name: config.config_name,
      weight_fairness: config.weight_fairness,
      weight_preferences: config.weight_preferences,
      weight_coverage: config.weight_coverage,
      weight_cost: config.weight_cost,
      max_runtime_seconds: config.max_runtime_seconds,
      mip_gap: config.mip_gap,
      is_default: config.is_default
    });
    setShowForm(true);
  }

  function calculateWeightTotal() {
    return (
      parseFloat(formData.weight_fairness || 0) +
      parseFloat(formData.weight_preferences || 0) +
      parseFloat(formData.weight_coverage || 0) +
      parseFloat(formData.weight_cost || 0)
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    
    if (!formData.config_name?.trim()) {
      toast.error('Please enter a configuration name');
      return;
    }

    const total = calculateWeightTotal();
    if (Math.abs(total - 1.0) > 0.001) {
      toast.error(`Weights must sum to 1.0 (currently ${total.toFixed(2)})`);
      return;
    }

    try {
      const payload = {
        config_name: formData.config_name.trim(),
        weight_fairness: parseFloat(formData.weight_fairness),
        weight_preferences: parseFloat(formData.weight_preferences),
        weight_coverage: parseFloat(formData.weight_coverage),
        weight_cost: parseFloat(formData.weight_cost),
        max_runtime_seconds: parseInt(formData.max_runtime_seconds),
        mip_gap: parseFloat(formData.mip_gap),
        is_default: formData.is_default
      };

      if (editingConfig) {
        await updateConfig(editingConfig.config_id, payload);
        toast.success('Configuration updated successfully');
      } else {
        await createConfig(payload);
        toast.success('Configuration created successfully');
      }

      setShowForm(false);
      setEditingConfig(null);
      await loadConfigs();
    } catch (error) {
      console.error('Failed to save configuration:', error);
      const msg = error?.response?.data?.detail || 'Failed to save configuration';
      toast.error(msg);
    }
  }

  async function handleDelete(config) {
    if (config.is_default) {
      toast.error('Cannot delete the default configuration');
      return;
    }

    if (!window.confirm(`Are you sure you want to delete "${config.config_name}"?`)) {
      return;
    }

    try {
      await deleteConfig(config.config_id);
      toast.success('Configuration deleted successfully');
      await loadConfigs();
    } catch (error) {
      console.error('Failed to delete configuration:', error);
      const msg = error?.response?.data?.detail || 'Failed to delete configuration';
      toast.error(msg);
    }
  }

  function handleWeightChange(field, value) {
    setFormData({ ...formData, [field]: value });
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center">
                <Settings className="w-8 h-8 text-blue-600 mr-3" />
                <h1 className="text-4xl font-bold text-blue-700">Optimization Configurations</h1>
              </div>
              <p className="text-lg text-blue-500 font-light mt-2">
                Manage solver settings and objective function weights
              </p>
            </div>
            <Button onClick={handleAddNew} variant="primary">
              <Plus className="w-4 h-4 mr-2" />
              New Configuration
            </Button>
          </div>
        </div>

        {/* Configuration Form */}
        {showForm && (
          <Card className="mb-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  {editingConfig ? 'Edit Configuration' : 'New Configuration'}
                </h3>
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setEditingConfig(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Basic Settings */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Configuration Name *
                  </label>
                  <input
                    type="text"
                    value={formData.config_name}
                    onChange={(e) => setFormData({ ...formData, config_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Balanced Schedule, Preference-Heavy, etc."
                    required
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_default"
                    checked={formData.is_default}
                    onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="is_default" className="ml-2 text-sm text-gray-700 flex items-center">
                    <Star className="w-4 h-4 mr-1 text-yellow-500" />
                    Set as default configuration
                  </label>
                </div>
              </div>

              {/* Objective Weights */}
              <div className="border-t pt-6">
                <h4 className="text-md font-semibold text-gray-900 mb-4">
                  Objective Function Weights
                  <span className="ml-2 text-sm font-normal text-gray-600">
                    (Must sum to 1.0, currently: {calculateWeightTotal().toFixed(2)})
                  </span>
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(WEIGHT_FIELDS).map(([field, meta]) => (
                    <div key={field}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {meta.label}
                      </label>
                      <p className="text-xs text-gray-500 mb-2">{meta.description}</p>
                      <div className="flex items-center space-x-3">
                        <input
                          type="range"
                          min={meta.min}
                          max={meta.max}
                          step={meta.step}
                          value={formData[field]}
                          onChange={(e) => handleWeightChange(field, e.target.value)}
                          className="flex-1"
                        />
                        <input
                          type="number"
                          min={meta.min}
                          max={meta.max}
                          step={meta.step}
                          value={formData[field]}
                          onChange={(e) => handleWeightChange(field, e.target.value)}
                          className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Solver Parameters */}
              <div className="border-t pt-6">
                <h4 className="text-md font-semibold text-gray-900 mb-4">Solver Parameters</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Runtime (seconds) *
                    </label>
                    <p className="text-xs text-gray-500 mb-2">
                      Maximum time allowed for optimization (1-3600)
                    </p>
                    <input
                      type="number"
                      min="1"
                      max="3600"
                      value={formData.max_runtime_seconds}
                      onChange={(e) => setFormData({ ...formData, max_runtime_seconds: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      MIP Gap *
                    </label>
                    <p className="text-xs text-gray-500 mb-2">
                      Optimality tolerance (0.01 = 1%)
                    </p>
                    <input
                      type="number"
                      min="0.001"
                      max="1.0"
                      step="0.001"
                      value={formData.mip_gap}
                      onChange={(e) => setFormData({ ...formData, mip_gap: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end space-x-3 pt-4 border-t">
                <Button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setEditingConfig(null);
                  }}
                  variant="outline"
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary">
                  <Save className="w-4 h-4 mr-2" />
                  {editingConfig ? 'Update' : 'Create'} Configuration
                </Button>
              </div>
            </form>
          </Card>
        )}

        {/* Configurations List */}
        {configs.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <Settings className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Configurations</h3>
              <p className="text-gray-600 mb-6">
                Create your first optimization configuration to get started
              </p>
              <Button onClick={handleAddNew} variant="primary">
                <Plus className="w-4 h-4 mr-2" />
                Create Configuration
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {configs.map((config) => (
              <Card key={config.config_id} className={`hover:shadow-lg transition-shadow ${
                config.is_default ? 'ring-2 ring-yellow-400' : ''
              }`}>
                <div className="space-y-4">
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {config.config_name}
                        </h3>
                        {config.is_default && (
                          <Star className="w-5 h-5 ml-2 text-yellow-500 fill-yellow-500" />
                        )}
                      </div>
                      {config.is_default && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          Default Configuration
                        </span>
                      )}
                    </div>
                    <div className="flex space-x-2 ml-4">
                      <button
                        onClick={() => handleEdit(config)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        title="Edit configuration"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(config)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete configuration"
                        disabled={config.is_default}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Weights */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold text-gray-700">Objective Weights</h4>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(WEIGHT_FIELDS).map(([field, meta]) => (
                        <div key={field} className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">{meta.label}:</span>
                          <span className="font-semibold text-gray-900">
                            {(config[field] * 100).toFixed(0)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Solver Parameters */}
                  <div className="space-y-2 pt-3 border-t">
                    <h4 className="text-sm font-semibold text-gray-700">Solver Settings</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Max Runtime:</span>
                        <span className="font-semibold text-gray-900">
                          {config.max_runtime_seconds}s
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">MIP Gap:</span>
                        <span className="font-semibold text-gray-900">
                          {(config.mip_gap * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

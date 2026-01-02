// frontend/src/api/optimizationConfig.js
import api from '../lib/axios';

/**
 * Get all optimization configurations
 */
export async function getAllConfigs() {
  const { data } = await api.get('/optimization-configs/');
  return data;
}

/**
 * Get default optimization configuration
 */
export async function getDefaultConfig() {
  const { data } = await api.get('/optimization-configs/default');
  return data;
}

/**
 * Get a single optimization configuration by ID
 */
export async function getConfig(configId) {
  const { data } = await api.get(`/optimization-configs/${configId}`);
  return data;
}

/**
 * Create a new optimization configuration
 */
export async function createConfig(payload) {
  const { data } = await api.post('/optimization-configs/', payload);
  return data;
}

/**
 * Update an optimization configuration
 */
export async function updateConfig(configId, payload) {
  const { data } = await api.put(`/optimization-configs/${configId}`, payload);
  return data;
}

/**
 * Delete an optimization configuration
 */
export async function deleteConfig(configId) {
  const { data } = await api.delete(`/optimization-configs/${configId}`);
  return data;
}

/**
 * Weight configuration metadata for UI labels and validation
 */
export const WEIGHT_FIELDS = {
  weight_fairness: {
    label: 'Fairness',
    description: 'Balances workload distribution among employees',
    min: 0,
    max: 1,
    step: 0.05,
  },
  weight_preferences: {
    label: 'Preferences',
    description: 'Satisfies employee shift preferences',
    min: 0,
    max: 1,
    step: 0.05,
  },
  weight_coverage: {
    label: 'Coverage',
    description: 'Ensures all shifts are filled',
    min: 0,
    max: 1,
    step: 0.05,
  },
  weight_cost: {
    label: 'Cost',
    description: 'Minimizes labor costs (future use)',
    min: 0,
    max: 1,
    step: 0.05,
  },
};

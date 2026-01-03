// frontend/src/pages/Admin/SystemConstraintsPage.jsx
import React, { useState, useEffect } from 'react';
import { Shield, Plus, Edit2, Trash2, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import { 
  getAllConstraints, 
  createConstraint, 
  updateConstraint, 
  deleteConstraint,
  CONSTRAINT_TYPES 
} from '../../api/constraints';

export default function SystemConstraintsPage() {
  const [constraints, setConstraints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingConstraint, setEditingConstraint] = useState(null);
  const [formData, setFormData] = useState({
    constraint_type: '',
    constraint_value: '',
    is_hard_constraint: true
  });

  useEffect(() => {
    loadConstraints();
  }, []);

  async function loadConstraints() {
    setLoading(true);
    try {
      const data = await getAllConstraints();
      setConstraints(data || []);
    } catch (error) {
      console.error('Failed to load constraints:', error);
      toast.error('Failed to load system constraints');
    } finally {
      setLoading(false);
    }
  }

  function handleAddNew() {
    setEditingConstraint(null);
    setFormData({
      constraint_type: '',
      constraint_value: '',
      is_hard_constraint: true
    });
    setShowForm(true);
  }

  function handleEdit(constraint) {
    setEditingConstraint(constraint);
    setFormData({
      constraint_type: constraint.constraint_type,
      constraint_value: constraint.constraint_value,
      is_hard_constraint: constraint.is_hard_constraint
    });
    setShowForm(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    
    if (!formData.constraint_type || !formData.constraint_value) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      const payload = {
        constraint_type: formData.constraint_type,
        constraint_value: parseFloat(formData.constraint_value),
        is_hard_constraint: formData.is_hard_constraint
      };

      if (editingConstraint) {
        await updateConstraint(editingConstraint.constraint_id, payload);
        toast.success('Constraint updated successfully');
      } else {
        await createConstraint(payload);
        toast.success('Constraint created successfully');
      }

      setShowForm(false);
      setEditingConstraint(null);
      await loadConstraints();
    } catch (error) {
      console.error('Failed to save constraint:', error);
      const msg = error?.response?.data?.detail || 'Failed to save constraint';
      toast.error(msg);
    }
  }

  async function handleDelete(constraint) {
    if (!window.confirm(`Are you sure you want to delete this constraint?\n\n${getConstraintLabel(constraint.constraint_type)}`)) {
      return;
    }

    try {
      await deleteConstraint(constraint.constraint_id);
      toast.success('Constraint deleted successfully');
      await loadConstraints();
    } catch (error) {
      console.error('Failed to delete constraint:', error);
      toast.error('Failed to delete constraint');
    }
  }

  function getConstraintLabel(type) {
    return CONSTRAINT_TYPES[type]?.label || type;
  }

  function getConstraintUnit(type) {
    return CONSTRAINT_TYPES[type]?.unit || '';
  }

  function getAvailableTypes() {
    const existingTypes = constraints.map(c => c.constraint_type);
    return Object.values(CONSTRAINT_TYPES).filter(
      type => !existingTypes.includes(type.value) || editingConstraint?.constraint_type === type.value
    );
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
                <Shield className="w-8 h-8 text-blue-600 mr-3" />
                <h1 className="text-4xl font-bold text-blue-700">System Constraints</h1>
              </div>
              <p className="text-lg text-blue-500 font-light mt-2">
                Manage global work rules and restrictions
              </p>
            </div>
            <Button onClick={handleAddNew} variant="primary">
              <Plus className="w-4 h-4 mr-2" />
              Add Constraint
            </Button>
          </div>
        </div>

        {/* Constraint Form */}
        {showForm && (
          <Card className="mb-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                {editingConstraint ? 'Edit Constraint' : 'New Constraint'}
              </h3>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Constraint Type *
                </label>
                <select
                  value={formData.constraint_type}
                  onChange={(e) => setFormData({ ...formData, constraint_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={!!editingConstraint}
                  required
                >
                  <option value="">Select a constraint type</option>
                  {getAvailableTypes().map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label} - {type.description}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Value * {formData.constraint_type && `(${getConstraintUnit(formData.constraint_type)})`}
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.constraint_value}
                  onChange={(e) => setFormData({ ...formData, constraint_value: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter numeric value"
                  required
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_hard"
                  checked={formData.is_hard_constraint}
                  onChange={(e) => setFormData({ ...formData, is_hard_constraint: e.target.checked })}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="is_hard" className="ml-2 text-sm text-gray-700">
                  Hard Constraint (must be satisfied)
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <Button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setEditingConstraint(null);
                  }}
                  variant="outline"
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary">
                  {editingConstraint ? 'Update' : 'Create'} Constraint
                </Button>
              </div>
            </form>
          </Card>
        )}

        {/* Constraints List */}
        {constraints.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <Shield className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Constraints Defined</h3>
              <p className="text-gray-600 mb-6">
                Start by adding system-wide work rules and constraints
              </p>
              <Button onClick={handleAddNew} variant="primary">
                <Plus className="w-4 h-4 mr-2" />
                Add First Constraint
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {constraints.map((constraint) => (
              <Card key={constraint.constraint_id} className="hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      {constraint.is_hard_constraint ? (
                        <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                      ) : (
                        <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                      )}
                      <h3 className="text-lg font-semibold text-gray-900">
                        {getConstraintLabel(constraint.constraint_type)}
                      </h3>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">
                      {CONSTRAINT_TYPES[constraint.constraint_type]?.description || ''}
                    </p>
                    <div className="flex items-baseline space-x-2">
                      <span className="text-3xl font-bold text-blue-600">
                        {constraint.constraint_value}
                      </span>
                      <span className="text-sm text-gray-500">
                        {getConstraintUnit(constraint.constraint_type)}
                      </span>
                    </div>
                    <div className="mt-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        constraint.is_hard_constraint 
                          ? 'bg-red-100 text-red-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {constraint.is_hard_constraint ? 'Hard Constraint' : 'Soft Constraint'}
                      </span>
                    </div>
                  </div>
                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={() => handleEdit(constraint)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Edit constraint"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(constraint)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete constraint"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
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

// frontend/src/pages/Admin/Employees/EmployeesPage.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import api from "../../../lib/axios";
import Button from "../../../components/ui/Button";
import Skeleton from "../../../components/ui/Skeleton";
import ConfirmDialog from "../../../components/ui/ConfirmDialog";

export default function EmployeesPage() {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const navigate = useNavigate();
  
  // Search and filter state
  const [searchTerm, setSearchTerm] = useState("");
  const [filterRole, setFilterRole] = useState("ALL");
  const [sortBy, setSortBy] = useState("name"); // name, email, joined
  const [sortOrder, setSortOrder] = useState("asc"); // asc, desc
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  
  // Delete dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  async function load() {
    setLoading(true);
    setErr("");
    try {
      const [usersRes, rolesRes] = await Promise.all([
        api.get("/users"),
        api.get("/roles")
      ]);
      setUsers(usersRes.data || []);
      setRoles(rolesRes.data || []);
    } catch (e) {
      const m = e?.response?.data?.detail || e.message || "Failed to load data";
      setErr(m);
      toast.error(m);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const handleDeleteClick = (user) => {
    setUserToDelete(user);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!userToDelete) return;
    
    setDeleting(true);
    try {
      await api.delete(`/users/${userToDelete.user_id}`);
      setUsers((prev) => prev.filter((u) => u.user_id !== userToDelete.user_id));
      toast.success(`Employee ${userToDelete.user_full_name} deleted successfully`);
      setDeleteDialogOpen(false);
      setUserToDelete(null);
    } catch (e) {
      const m = e?.response?.data?.detail || e.message || "Delete failed";
      toast.error(m);
    } finally {
      setDeleting(false);
    }
  };

  function onAdd() {
    navigate("/admin/add-user");
  }

  function onEdit(userId) {
    navigate(`/employees/edit/${userId}`);
  }

  function onViewProfile(userId) {
    navigate(`/employees/${userId}`);
  }

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
    setCurrentPage(1); // Reset to first page on sort
  };

  const SortIcon = ({ field }) => {
    if (sortBy !== field) return <span className="text-gray-400 ml-1">↕</span>;
    return <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>;
  };

  // Filter and sort users
  const filteredAndSortedUsers = users
    .filter(user => {
      // Search filter (name or email)
      const searchLower = searchTerm.toLowerCase();
      const nameMatch = user.user_full_name?.toLowerCase().includes(searchLower);
      const emailMatch = user.user_email?.toLowerCase().includes(searchLower);
      if (searchTerm && !nameMatch && !emailMatch) return false;

      // Role filter
      if (filterRole !== 'ALL') {
        const hasRole = user.roles?.some(r => r.role_name === filterRole);
        if (!hasRole) return false;
      }

      return true;
    })
    .sort((a, b) => {
      let comparison = 0;
      
      if (sortBy === 'name') {
        comparison = (a.user_full_name || '').localeCompare(b.user_full_name || '');
      } else if (sortBy === 'email') {
        comparison = (a.user_email || '').localeCompare(b.user_email || '');
      } else if (sortBy === 'joined') {
        comparison = new Date(a.created_at || 0) - new Date(b.created_at || 0);
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedUsers.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedUsers = filteredAndSortedUsers.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Employee Directory</h1>
          <p className="text-gray-600 mt-1">Manage your team members and their roles</p>
        </div>
        <Button onClick={onAdd}>
          Add New Employee
        </Button>
      </div>

      {err && (
        <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {err}
        </div>
      )}

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex gap-4 flex-wrap">
          {/* Search Box */}
          <div className="flex-1 min-w-[250px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <input
              type="text"
              placeholder="Search by name or email..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1); // Reset to first page on search
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Role Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Role
            </label>
            <select
              value={filterRole}
              onChange={(e) => {
                setFilterRole(e.target.value);
                setCurrentPage(1); // Reset to first page on filter
              }}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">All Roles</option>
              {roles.map(role => (
                <option key={role.role_id} value={role.role_name}>
                  {role.role_name}
                </option>
              ))}
            </select>
          </div>

          {/* Results Count */}
          <div className="flex items-end">
            <p className="text-sm text-gray-600">
              Showing {paginatedUsers.length} of {filteredAndSortedUsers.length} employees
              {filteredAndSortedUsers.length !== users.length && ` (${users.length} total)`}
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="bg-white rounded-lg shadow p-6 space-y-3">
          <Skeleton height={50} />
          <Skeleton height={50} />
          <Skeleton height={50} />
        </div>
      ) : paginatedUsers.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <p className="mt-2">
            {searchTerm || filterRole !== 'ALL' 
              ? 'No employees match your filters' 
              : 'No employees found'}
          </p>
          {(searchTerm || filterRole !== 'ALL') && (
            <Button 
              variant="outline" 
              className="mt-4"
              onClick={() => {
                setSearchTerm('');
                setFilterRole('ALL');
              }}
            >
              Clear Filters
            </Button>
          )}
        </div>
      ) : (
        <>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50 text-gray-700 border-b border-gray-200">
                  <tr>
                    <th 
                      className="px-4 py-3 cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort('name')}
                    >
                      <div className="flex items-center font-semibold">
                        Name <SortIcon field="name" />
                      </div>
                    </th>
                    <th 
                      className="px-4 py-3 cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort('email')}
                    >
                      <div className="flex items-center font-semibold">
                        Email <SortIcon field="email" />
                      </div>
                    </th>
                    <th className="px-4 py-3 font-semibold">Manager</th>
                    <th className="px-4 py-3 font-semibold">Roles</th>
                    <th 
                      className="px-4 py-3 cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort('joined')}
                    >
                      <div className="flex items-center font-semibold">
                        Joined <SortIcon field="joined" />
                      </div>
                    </th>
                    <th className="px-4 py-3 text-right font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {paginatedUsers.map((u) => (
                    <tr 
                      key={u.user_id} 
                      className="hover:bg-gray-50 cursor-pointer"
                      onClick={() => onViewProfile(u.user_id)}
                    >
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900">{u.user_full_name}</div>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{u.user_email}</td>
                      <td className="px-4 py-3">
                        {u.is_manager ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            Manager
                          </span>
                        ) : (
                          <span className="text-gray-500">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {u.roles?.length ? (
                          <div className="flex flex-wrap gap-1">
                            {u.roles.map((r) => (
                              <span 
                                key={r.role_id}
                                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                              >
                                {r.role_name}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-gray-500">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-600 text-sm">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onEdit(u.user_id)}
                            title="Edit employee"
                          >
                            Edit
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeleteClick(u)}
                            className="border-red-300 text-red-700 hover:bg-red-50"
                            title="Delete employee"
                          >
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between bg-white rounded-lg shadow px-4 py-3">
              <div className="text-sm text-gray-700">
                Page {currentPage} of {totalPages}
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                
                {/* Page numbers */}
                <div className="flex gap-1">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                    <button
                      key={page}
                      onClick={() => handlePageChange(page)}
                      className={`px-3 py-1 rounded text-sm ${
                        currentPage === page
                          ? 'bg-blue-600 text-white'
                          : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      {page}
                    </button>
                  ))}
                </div>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Employee"
        message={`Are you sure you want to delete ${userToDelete?.user_full_name}? This action cannot be undone.`}
        confirmText="Delete Employee"
        variant="danger"
        isLoading={deleting}
      />
    </div>
  );
}

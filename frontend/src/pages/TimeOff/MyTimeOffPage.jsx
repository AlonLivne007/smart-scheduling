import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { fetchMyTimeOffRequests, deleteTimeOffRequest } from '../../api/timeOff';
import Button from '../../components/ui/Button';
import Skeleton from '../../components/ui/Skeleton';
import ConfirmDialog from '../../components/ui/ConfirmDialog';

export default function MyTimeOffPage() {
  const navigate = useNavigate();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [requestToDelete, setRequestToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const statusOptions = ['ALL', 'PENDING', 'APPROVED', 'REJECTED'];

  useEffect(() => {
    loadRequests();
  }, []);

  const loadRequests = async () => {
    setLoading(true);
    try {
      const data = await fetchMyTimeOffRequests();
      setRequests(data);
    } catch (error) {
      console.error('Failed to load time-off requests:', error);
      toast.error('Failed to load your requests');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (request) => {
    setRequestToDelete(request);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!requestToDelete) return;

    setDeleting(true);
    try {
      const requestId = requestToDelete.request_id ?? requestToDelete.time_off_request_id;
      await deleteTimeOffRequest(requestId);
      toast.success('Request deleted successfully');
      setDeleteDialogOpen(false);
      setRequestToDelete(null);
      await loadRequests(); // Reload to get updated data
    } catch (error) {
      console.error('Failed to delete request:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete request');
    } finally {
      setDeleting(false);
    }
  };

  const handleNewRequest = () => {
    navigate('/time-off/request');
  };

  // Filter requests
  const filteredRequests = requests.filter(req => {
    if (filterStatus !== 'ALL' && req.status !== filterStatus) return false;
    return true;
  });

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'PENDING':
        return 'bg-yellow-100 text-yellow-800';
      case 'APPROVED':
        return 'bg-green-100 text-green-800';
      case 'REJECTED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeBadgeClass = (type) => {
    switch (type) {
      case 'VACATION':
        return 'bg-blue-100 text-blue-800';
      case 'SICK':
        return 'bg-purple-100 text-purple-800';
      case 'PERSONAL':
        return 'bg-indigo-100 text-indigo-800';
      case 'OTHER':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Time-Off Requests</h1>
          <p className="text-gray-600 mt-1">View and manage your time-off requests</p>
        </div>
        <Button onClick={handleNewRequest}>
          New Request
        </Button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex gap-4 flex-wrap items-center">
          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Status
            </label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {statusOptions.map(status => (
                <option key={status} value={status}>
                  {status === 'ALL' ? 'All Statuses' : status}
                </option>
              ))}
            </select>
          </div>

          {/* Results Count */}
          <div className="flex items-end">
            <p className="text-sm text-gray-600">
              Showing {filteredRequests.length} of {requests.length} requests
            </p>
          </div>
        </div>
      </div>

      {/* Requests Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-6 space-y-3">
            <Skeleton height={50} />
            <Skeleton height={50} />
            <Skeleton height={50} />
          </div>
        ) : filteredRequests.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="mt-2">No time-off requests found</p>
            <Button onClick={handleNewRequest} className="mt-4">
              Create Your First Request
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Start Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    End Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Days
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Submitted
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredRequests.map((request) => {
                  const requestId = request.request_id ?? request.time_off_request_id;
                  const days = Math.ceil((new Date(request.end_date) - new Date(request.start_date)) / (1000 * 60 * 60 * 24)) + 1;
                  const isPending = request.status === 'PENDING';

                  return (
                    <tr key={requestId} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getTypeBadgeClass(request.request_type)}`}>
                          {request.request_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(request.start_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(request.end_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {days} day{days !== 1 ? 's' : ''}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeClass(request.status)}`}>
                          {request.status}
                        </span>
                        {request.status === 'APPROVED' && request.approved_by && (
                          <div className="text-xs text-gray-500 mt-1">
                            Approved by {request.approved_by.user_full_name}
                          </div>
                        )}
                        {request.status === 'REJECTED' && request.approved_by && (
                          <div className="text-xs text-gray-500 mt-1">
                            Rejected by {request.approved_by.user_full_name}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDateTime(request.requested_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {isPending ? (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeleteClick(request)}
                            className="border-red-300 text-red-700 hover:bg-red-50"
                          >
                            Delete
                          </Button>
                        ) : (
                          <span className="text-gray-400">No actions</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Time-Off Request"
        message={`Are you sure you want to delete this ${requestToDelete?.request_type.toLowerCase()} request for ${requestToDelete ? formatDate(requestToDelete.start_date) : ''} to ${requestToDelete ? formatDate(requestToDelete.end_date) : ''}?`}
        confirmText="Delete Request"
        variant="danger"
        isLoading={deleting}
      />
    </div>
  );
}

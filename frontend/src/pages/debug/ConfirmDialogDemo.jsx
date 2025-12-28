/**
 * ConfirmDialog Demo Page
 * 
 * Demonstrates all features of the ConfirmDialog component including:
 * - Basic confirmation dialogs
 * - Danger variant for destructive actions
 * - Side effects display
 * - Loading states
 * - Different use cases
 * 
 * @component
 */
import { useState } from 'react';
import Button from '../../components/ui/Button.jsx';
import Card from '../../components/ui/Card.jsx';
import ConfirmDialog from '../../components/ui/ConfirmDialog.jsx';
import PageLayout from '../../layouts/PageLayout.jsx';
import { showSuccess, showError, showInfo } from '../../lib/notifications.jsx';
import { Trash2, UserX, Calendar, FileX } from 'lucide-react';

export default function ConfirmDialogDemo() {
  const [showBasic, setShowBasic] = useState(false);
  const [showDanger, setShowDanger] = useState(false);
  const [showWithEffects, setShowWithEffects] = useState(false);
  const [showLoading, setShowLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showDeleteUser, setShowDeleteUser] = useState(false);
  const [showDeleteSchedule, setShowDeleteSchedule] = useState(false);
  const [showRemoveAssignment, setShowRemoveAssignment] = useState(false);

  // Simulate async deletion with loading state
  const handleAsyncDelete = async () => {
    setIsLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsLoading(false);
    setShowLoading(false);
    showSuccess('Item deleted successfully');
  };

  const handleDeleteUser = () => {
    setShowDeleteUser(false);
    showSuccess('User "John Doe" has been deleted');
  };

  const handleDeleteSchedule = () => {
    setShowDeleteSchedule(false);
    showSuccess('Weekly schedule deleted successfully');
  };

  const handleRemoveAssignment = () => {
    setShowRemoveAssignment(false);
    showSuccess('Shift assignment removed');
  };

  return (
    <PageLayout>
      <div className="max-w-5xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            ConfirmDialog Component Demo
          </h1>
          <p className="text-gray-600">
            US-009: Confirmation dialogs for critical actions
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Demo Buttons */}
          <div className="space-y-6">
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Basic Dialogs
              </h2>
              <div className="space-y-3">
                <Button
                  variant="primary"
                  onClick={() => setShowBasic(true)}
                  className="w-full"
                >
                  Show Basic Confirmation
                </Button>

                <Button
                  variant="danger"
                  onClick={() => setShowDanger(true)}
                  className="w-full"
                >
                  Show Danger Confirmation
                </Button>

                <Button
                  variant="primarySubtle"
                  onClick={() => setShowWithEffects(true)}
                  className="w-full"
                >
                  Show with Side Effects
                </Button>

                <Button
                  variant="outline"
                  onClick={() => setShowLoading(true)}
                  className="w-full"
                >
                  Show with Loading State
                </Button>
              </div>
            </Card>

            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Real-World Use Cases
              </h2>
              <p className="text-sm text-gray-600 mb-4">
                Examples of confirmation dialogs in actual application scenarios
              </p>
              <div className="space-y-3">
                <Button
                  variant="danger"
                  onClick={() => setShowDeleteUser(true)}
                  className="w-full flex items-center justify-center gap-2"
                >
                  <UserX className="w-4 h-4" />
                  Delete User
                </Button>

                <Button
                  variant="danger"
                  onClick={() => setShowDeleteSchedule(true)}
                  className="w-full flex items-center justify-center gap-2"
                >
                  <Calendar className="w-4 h-4" />
                  Delete Weekly Schedule
                </Button>

                <Button
                  variant="outline"
                  onClick={() => setShowRemoveAssignment(true)}
                  className="w-full flex items-center justify-center gap-2"
                >
                  <FileX className="w-4 h-4" />
                  Remove Shift Assignment
                </Button>
              </div>
            </Card>
          </div>

          {/* Right Column - Features Checklist */}
          <div className="space-y-6">
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Features Implemented
              </h2>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Modal appears before delete operations</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Modal shows what will be deleted</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>"Cancel" and "Confirm" buttons</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Confirmation for: Delete user, Delete schedule, Remove assignment</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Shows side effects (e.g., related data impacts)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Styled consistently with app theme</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Keyboard support (Esc to cancel, Enter to confirm)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Focus management and accessibility</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Loading states during async operations</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Backdrop click to dismiss</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Prevents background scroll when open</span>
                </li>
              </ul>
            </Card>

            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Keyboard Shortcuts
              </h2>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between py-2 border-b border-gray-200">
                  <span className="text-gray-600">Close dialog</span>
                  <kbd className="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-xs font-mono">
                    Esc
                  </kbd>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-gray-200">
                  <span className="text-gray-600">Confirm action</span>
                  <kbd className="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-xs font-mono">
                    Enter
                  </kbd>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-gray-600">Navigate buttons</span>
                  <kbd className="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-xs font-mono">
                    Tab
                  </kbd>
                </div>
              </div>
            </Card>

            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Usage Example
              </h2>
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-xs overflow-x-auto">
{`<ConfirmDialog
  isOpen={showConfirm}
  onClose={() => setShowConfirm(false)}
  onConfirm={handleDelete}
  title="Delete User"
  message="Are you sure you want to delete John Doe?"
  confirmText="Delete User"
  variant="danger"
  sideEffects={[
    "All shift assignments will be removed",
    "Time-off requests will be retained"
  ]}
/>`}
              </pre>
            </Card>
          </div>
        </div>
      </div>

      {/* Dialog Components */}
      <ConfirmDialog
        isOpen={showBasic}
        onClose={() => setShowBasic(false)}
        onConfirm={() => {
          setShowBasic(false);
          showSuccess('Action confirmed!');
        }}
        title="Confirm Action"
        message="Are you sure you want to proceed with this action?"
        confirmText="Yes, Continue"
      />

      <ConfirmDialog
        isOpen={showDanger}
        onClose={() => setShowDanger(false)}
        onConfirm={() => {
          setShowDanger(false);
          showSuccess('Item deleted successfully');
        }}
        title="Delete Item"
        message="This action cannot be undone. Are you sure you want to delete this item?"
        confirmText="Delete"
        variant="danger"
      />

      <ConfirmDialog
        isOpen={showWithEffects}
        onClose={() => setShowWithEffects(false)}
        onConfirm={() => {
          setShowWithEffects(false);
          showSuccess('Record deleted with all related data');
        }}
        title="Delete Record"
        message="Deleting this record will affect related data."
        confirmText="Delete Anyway"
        variant="danger"
        sideEffects={[
          'Delete 5 associated planned shifts',
          'Remove 12 shift assignments',
          'Archive time-off requests (not deleted)',
        ]}
      />

      <ConfirmDialog
        isOpen={showLoading}
        onClose={() => !isLoading && setShowLoading(false)}
        onConfirm={handleAsyncDelete}
        title="Delete with Async Operation"
        message="This will perform a server request. Click confirm to see loading state."
        confirmText="Delete"
        variant="danger"
        isLoading={isLoading}
      />

      {/* Real-world use cases */}
      <ConfirmDialog
        isOpen={showDeleteUser}
        onClose={() => setShowDeleteUser(false)}
        onConfirm={handleDeleteUser}
        title="Delete User"
        message='Are you sure you want to delete "John Doe"? This action cannot be undone.'
        confirmText="Delete User"
        variant="danger"
        icon={<UserX className="w-5 h-5 text-red-600" />}
        sideEffects={[
          'Remove all shift assignments for this user',
          'Time-off requests will be retained for records',
          'User login credentials will be revoked',
        ]}
      />

      <ConfirmDialog
        isOpen={showDeleteSchedule}
        onClose={() => setShowDeleteSchedule(false)}
        onConfirm={handleDeleteSchedule}
        title="Delete Weekly Schedule"
        message="Are you sure you want to delete the schedule for the week of January 15-21, 2025?"
        confirmText="Delete Schedule"
        variant="danger"
        icon={<Calendar className="w-5 h-5 text-red-600" />}
        sideEffects={[
          'This will delete 24 planned shifts',
          'All shift assignments will be removed',
          'Employee notifications will be sent',
        ]}
      />

      <ConfirmDialog
        isOpen={showRemoveAssignment}
        onClose={() => setShowRemoveAssignment(false)}
        onConfirm={handleRemoveAssignment}
        title="Remove Shift Assignment"
        message='Remove "Jane Smith" from the Morning Shift on January 20, 2025?'
        confirmText="Remove Assignment"
        icon={<FileX className="w-5 h-5 text-blue-600" />}
        sideEffects={[
          'This position will become unassigned',
          'Employee will be notified of the change',
        ]}
      />
    </PageLayout>
  );
}

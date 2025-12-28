/**
 * ConfirmDialog Component
 * 
 * A modal dialog for confirming critical actions like deletions.
 * Provides clear messaging about what will be affected and requires
 * explicit user confirmation.
 * 
 * Features:
 * - Customizable title and message
 * - Optional side effects/warnings display
 * - Danger variant (red) for destructive actions
 * - Cancel and Confirm buttons
 * - Keyboard support (Escape to cancel, Enter to confirm)
 * - Focus management and accessibility
 * 
 * @component
 * @example
 * // Delete user confirmation
 * <ConfirmDialog
 *   isOpen={showConfirm}
 *   onClose={() => setShowConfirm(false)}
 *   onConfirm={handleDeleteUser}
 *   title="Delete User"
 *   message="Are you sure you want to delete John Doe?"
 *   confirmText="Delete User"
 *   variant="danger"
 *   sideEffects={["This will remove all shift assignments", "Time-off requests will remain"]}
 * />
 * 
 * @example
 * // Simple confirmation
 * <ConfirmDialog
 *   isOpen={showConfirm}
 *   onClose={() => setShowConfirm(false)}
 *   onConfirm={handleAction}
 *   title="Confirm Action"
 *   message="Are you sure you want to proceed?"
 * />
 */
import { useEffect, useRef } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import Button from './Button.jsx';

const ConfirmDialog = ({
  isOpen = false,
  onClose,
  onConfirm,
  title = 'Confirm Action',
  message = 'Are you sure you want to proceed?',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'default', // 'default' | 'danger'
  sideEffects = [], // Array of strings describing side effects
  isLoading = false,
  icon = null, // Custom icon component
}) => {
  const confirmButtonRef = useRef(null);
  const dialogRef = useRef(null);

  // Focus management
  useEffect(() => {
    if (isOpen && confirmButtonRef.current) {
      confirmButtonRef.current.focus();
    }
  }, [isOpen]);

  // Keyboard handling
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      } else if (e.key === 'Enter' && !isLoading) {
        e.preventDefault();
        onConfirm();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, onConfirm, isLoading]);

  // Prevent background scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const isDanger = variant === 'danger';

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleConfirmClick = () => {
    if (!isLoading) {
      onConfirm();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-sm transition-opacity"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
    >
      <div
        ref={dialogRef}
        className="bg-white rounded-2xl shadow-2xl max-w-md w-full transform transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`px-6 py-4 border-b ${isDanger ? 'border-red-200' : 'border-gray-200'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Icon */}
              <div
                className={`p-2 rounded-full ${
                  isDanger ? 'bg-red-100' : 'bg-blue-100'
                }`}
              >
                {icon || (
                  isDanger ? (
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-blue-600" />
                  )
                )}
              </div>
              
              {/* Title */}
              <h3
                id="confirm-dialog-title"
                className={`text-lg font-semibold ${
                  isDanger ? 'text-red-900' : 'text-gray-900'
                }`}
              >
                {title}
              </h3>
            </div>

            {/* Close button */}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-4">
          {/* Main message */}
          <p
            id="confirm-dialog-description"
            className="text-gray-700 text-base leading-relaxed"
          >
            {message}
          </p>

          {/* Side effects warning */}
          {sideEffects.length > 0 && (
            <div className={`mt-4 p-3 rounded-lg ${isDanger ? 'bg-red-50 border border-red-200' : 'bg-yellow-50 border border-yellow-200'}`}>
              <p className={`text-sm font-semibold mb-2 ${isDanger ? 'text-red-800' : 'text-yellow-800'}`}>
                This action will also:
              </p>
              <ul className="space-y-1">
                {sideEffects.map((effect, index) => (
                  <li
                    key={index}
                    className={`text-sm flex items-start gap-2 ${isDanger ? 'text-red-700' : 'text-yellow-700'}`}
                  >
                    <span className="mt-1">•</span>
                    <span>{effect}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 rounded-b-2xl flex gap-3 justify-end">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isLoading}
          >
            {cancelText}
          </Button>
          <Button
            ref={confirmButtonRef}
            variant={isDanger ? 'danger' : 'primary'}
            onClick={handleConfirmClick}
            disabled={isLoading}
            isLoading={isLoading}
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;

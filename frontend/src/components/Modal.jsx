import React, { useEffect } from 'react';

const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  showCancel = true,
  showConfirm = true,
  size = 'md',
  className = '',
  ...props
}) => {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  const getSizeClass = () => {
    switch (size) {
      case 'sm':
        return 'modal-sm';
      case 'lg':
        return 'modal-lg';
      case 'xl':
        return 'modal-xl';
      case 'md':
      default:
        return '';
    }
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleConfirm = () => {
    if (onConfirm) {
      onConfirm();
    } else {
      onClose();
    }
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="modal fade show d-block" 
      tabIndex="-1" 
      role="dialog"
      aria-modal="true"
      onClick={handleBackdropClick}
      style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
    >
      <div className={`modal-dialog ${getSizeClass()} ${className}`} role="document">
        <div className="modal-content">
          {title && (
            <div className="modal-header">
              <h5 className="modal-title">{title}</h5>
              <button
                type="button"
                className="btn-close"
                aria-label="Close"
                onClick={onClose}
              ></button>
            </div>
          )}
          <div className="modal-body">
            {children}
          </div>
          {(showConfirm || showCancel) && (
            <div className="modal-footer">
              {showCancel && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleCancel}
                >
                  {cancelText}
                </button>
              )}
              {showConfirm && (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleConfirm}
                >
                  {confirmText}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Modal;
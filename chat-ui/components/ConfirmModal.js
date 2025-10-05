/**
 * Confirmation modal component for delete actions
 */

;(function(){
const { useEffect } = React;

function ConfirmModal({ title, bodyText, confirmText = 'Confirm', onConfirm, onCancel }) {
  useEffect(() => {
    const onKey = (e) => { 
      if (e.key === 'Escape') onCancel && onCancel(); 
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onCancel]);

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal">
        <div className="modal-title">{title}</div>
        <div className="modal-body">{bodyText}</div>
        <div className="modal-actions">
          <button className="btn" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn btn-danger" onClick={onConfirm}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

// Export for use in main HTML file
window.ConfirmModal = ConfirmModal;
})();

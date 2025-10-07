/** Simple toast utility without React state */

(function(){
  const containerId = 'chem-toast-container';
  function ensureContainer(){
    let el = document.getElementById(containerId);
    if (!el) {
      el = document.createElement('div');
      el.id = containerId;
      el.style.position = 'fixed';
      el.style.top = '12px';
      el.style.right = '12px';
      el.style.zIndex = '10000';
      el.style.display = 'flex';
      el.style.flexDirection = 'column';
      el.style.gap = '8px';
      document.body.appendChild(el);
    }
    return el;
  }
  function show(message, type = 'info', durationMs = 4000){
    const container = ensureContainer();
    const toast = document.createElement('div');
    toast.style.padding = '10px 14px';
    toast.style.borderRadius = '8px';
    toast.style.fontFamily = 'Arial, sans-serif';
    toast.style.fontSize = '14px';
    toast.style.boxShadow = '0 2px 8px rgba(0,0,0,0.12)';
    toast.style.border = '1px solid #e5e7eb';
    if (type === 'error') {
      toast.style.background = '#fee2e2';
      toast.style.color = '#991b1b';
      toast.style.borderColor = '#fecaca';
    } else if (type === 'success') {
      toast.style.background = '#dcfce7';
      toast.style.color = '#14532d';
      toast.style.borderColor = '#bbf7d0';
    } else if (type === 'warning') {
      toast.style.background = '#fef3c7';
      toast.style.color = '#92400e';
      toast.style.borderColor = '#fde68a';
    } else {
      toast.style.background = '#f8fafc';
      toast.style.color = '#111827';
      toast.style.borderColor = '#e5e7eb';
    }

    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      if (toast.parentElement) toast.parentElement.removeChild(toast);
    }, durationMs);
  }
  window.toast = { show };
})();



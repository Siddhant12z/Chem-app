/**
 * StatusBar component - Shows system health status
 */

;(function(){
const { useState, useEffect } = React;

function StatusBar() {
  const [status, setStatus] = useState({
    rag: { status: 'checking', available: false },
    ollama: { status: 'checking', available: false },
    openai_voice: { status: 'checking', available: false }
  });
  const [overallStatus, setOverallStatus] = useState('checking');
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch('http://localhost:8000/api/health');
        const data = await res.json();
        
        setStatus({
          rag: data.components?.rag || { status: 'offline', available: false },
          ollama: data.components?.ollama || { status: 'offline', available: false },
          openai_voice: data.components?.openai_voice || { status: 'offline', available: false }
        });
        setOverallStatus(data.status || 'degraded');
      } catch (error) {
        console.error('Health check failed:', error);
        setStatus({
          rag: { status: 'offline', available: false },
          ollama: { status: 'offline', available: false },
          openai_voice: { status: 'offline', available: false }
        });
        setOverallStatus('offline');
      }
    }

    // Check immediately
    checkHealth();
    
    // Check every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (componentStatus) => {
    if (componentStatus === 'online' || componentStatus === 'configured') return '#10b981';
    if (componentStatus === 'checking') return '#f59e0b';
    return '#ef4444';
  };

  const getStatusIcon = (componentStatus) => {
    if (componentStatus === 'online' || componentStatus === 'configured') return '✓';
    if (componentStatus === 'checking') return '⋯';
    return '✕';
  };

  const getOverallColor = () => {
    if (overallStatus === 'healthy') return '#10b981';
    if (overallStatus === 'checking') return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="status-bar" onClick={() => setIsExpanded(!isExpanded)}>
      <div className="status-summary">
        <span 
          className="status-indicator" 
          style={{ 
            backgroundColor: getOverallColor(),
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            display: 'inline-block',
            marginRight: '8px',
            animation: overallStatus === 'checking' ? 'pulse 2s infinite' : 'none'
          }}
        />
        <span style={{ fontSize: '12px', color: '#6b7280', cursor: 'pointer' }}>
          System: {overallStatus === 'healthy' ? 'All Systems Online' : overallStatus === 'checking' ? 'Checking...' : 'Service Degraded'}
          {' '}
          <span style={{ fontSize: '10px' }}>{isExpanded ? '▼' : '▶'}</span>
        </span>
      </div>
      
      {isExpanded && (
        <div className="status-details" style={{ 
          marginTop: '8px',
          padding: '8px',
          background: '#f9fafb',
          borderRadius: '4px',
          fontSize: '11px'
        }}>
          <StatusBadge 
            icon="📚" 
            label="Knowledge Base" 
            status={status.rag.status}
            available={status.rag.available}
          />
          <StatusBadge 
            icon="🤖" 
            label="LLM (Ollama)" 
            status={status.ollama.status}
            available={status.ollama.available}
          />
          <StatusBadge 
            icon="🎤" 
            label="Voice (OpenAI)" 
            status={status.openai_voice.status}
            available={status.openai_voice.available}
          />
        </div>
      )}
    </div>
  );
}

function StatusBadge({ icon, label, status, available }) {
  const getStatusColor = () => {
    if (status === 'online' || status === 'configured') return '#10b981';
    if (status === 'checking') return '#f59e0b';
    return '#ef4444';
  };

  const getStatusText = () => {
    if (status === 'online') return 'Online';
    if (status === 'configured') return 'Ready';
    if (status === 'checking') return 'Checking...';
    if (status === 'not_configured') return 'Not Configured';
    return 'Offline';
  };

  return (
    <div style={{ 
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '4px 0',
      borderBottom: '1px solid #e5e7eb'
    }}>
      <span>
        <span style={{ marginRight: '6px' }}>{icon}</span>
        <span style={{ color: '#374151' }}>{label}</span>
      </span>
      <span style={{ 
        color: getStatusColor(),
        fontWeight: '600',
        fontSize: '10px'
      }}>
        {getStatusText()}
      </span>
    </div>
  );
}

// Export for use in main HTML file
window.StatusBar = StatusBar;
window.StatusBadge = StatusBadge;
})();


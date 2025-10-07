/**
 * TTS Mode Selector Component
 * Allows switching between OpenAI TTS and Browser TTS
 */

;(function(){
const { useState, useEffect } = React;

function TTSModeSelector({ currentMode, onModeChange, isOpenAIAvailable, isBrowserAvailable }) {
  const [isOpen, setIsOpen] = useState(false);
  
  const modes = [
    {
      id: 'openai',
      name: 'OpenAI TTS',
      description: 'High quality, supports Nepali',
      available: isOpenAIAvailable,
      icon: '🎤'
    },
    {
      id: 'browser',
      name: 'Browser TTS',
      description: 'Free, offline, basic quality',
      available: isBrowserAvailable,
      icon: '🌐'
    }
  ];
  
  const currentModeInfo = modes.find(m => m.id === currentMode);
  
  const handleModeChange = (modeId) => {
    onModeChange(modeId);
    setIsOpen(false);
  };
  
  return (
    <div className="tts-mode-selector">
      <button 
        className="tts-mode-button"
        onClick={() => setIsOpen(!isOpen)}
        title={`Current: ${currentModeInfo?.name || 'Unknown'}`}
      >
        <span className="tts-mode-icon">{currentModeInfo?.icon || '🎤'}</span>
        <span className="tts-mode-name">{currentModeInfo?.name || 'TTS'}</span>
        <span className="tts-mode-arrow">{isOpen ? '▲' : '▼'}</span>
      </button>
      
      {isOpen && (
        <div className="tts-mode-dropdown">
          {modes.map(mode => (
            <button
              key={mode.id}
              className={`tts-mode-option ${mode.id === currentMode ? 'active' : ''} ${!mode.available ? 'disabled' : ''}`}
              onClick={() => mode.available && handleModeChange(mode.id)}
              disabled={!mode.available}
            >
              <span className="tts-mode-option-icon">{mode.icon}</span>
              <div className="tts-mode-option-content">
                <div className="tts-mode-option-name">{mode.name}</div>
                <div className="tts-mode-option-desc">{mode.description}</div>
              </div>
              {mode.id === currentMode && (
                <span className="tts-mode-option-check">✓</span>
              )}
            </button>
          ))}
          
          {!isOpenAIAvailable && !isBrowserAvailable && (
            <div className="tts-mode-error">
              <span>⚠️ No TTS available</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Export globally
window.TTSModeSelector = TTSModeSelector;
})();

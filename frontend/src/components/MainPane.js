/**
 * Main pane component with SSE-based chat
 * Updated to use new streaming architecture
 */

;(function(){
const { useState, useEffect } = React;

function MainPane({ 
  activeChat, 
  onSendMessage, 
  ttsMode, 
  onTTSModeChange, 
  isOpenAIAvailable, 
  isBrowserAvailable 
}) {
  const [prefill, setPrefill] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  // Use new streaming voice hook
  const {
    isSpeaking,
    isMuted,
    isRecording,
    playAudio,
    stopSpeaking,
    handleVoiceInput,
    setIsMuted
  } = window.useStreamingVoice();
  
  // Use browser TTS hook
  const {
    isSpeaking: browserIsSpeaking,
    isMuted: browserIsMuted,
    speakText: browserSpeakText,
    stopSpeaking: browserStopSpeaking,
    setIsMuted: setBrowserIsMuted
  } = window.useBrowserTTS();

  const handleSend = () => {
    const text = prefill.trim();
    if (!text) return;
    
    console.log('[MainPane] Sending message');
    setIsLoading(true);
    
    // Unmute based on current TTS mode
    if (ttsMode === 'openai') {
      setIsMuted(false);
    } else if (ttsMode === 'browser') {
      setBrowserIsMuted(false);
    }
    
    Promise.resolve(onSendMessage(text)).finally(() => {
      setIsLoading(false);
      console.log('[MainPane] Message sent');
    });
    
    setPrefill("");
  };
  
  
  // Get current TTS state based on mode
  const currentIsSpeaking = ttsMode === 'openai' ? isSpeaking : browserIsSpeaking;
  const currentIsMuted = ttsMode === 'openai' ? isMuted : browserIsMuted;
  const currentStopSpeaking = ttsMode === 'openai' ? stopSpeaking : browserStopSpeaking;

  // Listen to STT transcript events
  useEffect(() => {
    const onTranscript = (e) => {
      setPrefill(e.detail.transcript || '');
    };
    
    window.addEventListener('stt:transcript', onTranscript);
    return () => window.removeEventListener('stt:transcript', onTranscript);
  }, []);

  return (
    <main className="main-pane">
      <AppHeader
        title="Organic Chemistry Tutor"
        subtitle="Ask me anything about organic chemistry! I can explain concepts and draw molecular structures."
      />

      <div className="content-area">
        {!activeChat || (activeChat.messages?.length || 0) === 0 ? (
          <EmptyState />
        ) : (
          <MessageList 
            messages={activeChat.messages}
          />
        )}
      </div>

      <ComposerArea
        prefill={prefill}
        setPrefill={setPrefill}
        onSend={handleSend}
        isRecording={isRecording}
        onVoiceInput={handleVoiceInput}
        isSpeaking={currentIsSpeaking}
        onStopSpeaking={currentStopSpeaking}
        isMuted={currentIsMuted}
        ttsMode={ttsMode}
        onTTSModeChange={onTTSModeChange}
        isOpenAIAvailable={isOpenAIAvailable}
        isBrowserAvailable={isBrowserAvailable}
      />
    </main>
  );
}

function AppHeader({ title, subtitle }) {
  return (
    <header className="app-header">
      <h1 className="app-title">{title}</h1>
      <p className="app-subtitle">{subtitle}</p>
    </header>
  );
}

function EmptyState() {
  return (
    <section className="empty-state">
      <div className="empty-illustration">🧪</div>
      <h2 className="empty-title">Welcome to ChemTutor!</h2>
      <p className="empty-subtext">
        Ask chemistry questions via voice or text.
      </p>
      <p className="empty-hint">
        Try: "What is benzene?" or "Show me the structure of water"
      </p>
    </section>
  );
}

// Export for use in main HTML file
window.MainPane = MainPane;
window.AppHeader = AppHeader;
window.EmptyState = EmptyState;
})();


/**
 * Main pane component with chat interface and composer
 */

;(function(){
const { useState, useRef, useEffect } = React;

function MainPane({ activeChat, onSendMessage }) {
  const [prefill, setPrefill] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const {
    isRecording, isSpeaking, isMuted,
    currentAudio, spokenMessageIds, currentSpeakingMessageId,
    lastProcessedMessageRef,
    handleVoiceInput, speakText, stopSpeaking,
    setIsMuted, setCurrentSpeakingMessageId, setSpokenMessageIds
  } = window.useVoice();

  const handleSend = () => {
    const text = prefill.trim();
    if (!text) return;
    setIsLoading(true);
    setIsMuted(false);
    setCurrentSpeakingMessageId(null);
    lastProcessedMessageRef.current = null;
    Promise.resolve(onSendMessage(text)).finally(() => setIsLoading(false));
    setPrefill("");
  };

  // Listen to STT transcript events to prefill input
  useEffect(() => {
    const onTranscript = (e) => setPrefill(e.detail.transcript || '');
    const onPartial = (e) => {
      const t = (e.detail && e.detail.transcript) || '';
      if (!t) return;
      // Only update if user hasn't typed over it
      setPrefill((prev) => {
        if (!prev || prev.length < t.length) return t;
        return prev;
      });
    };
    window.addEventListener('stt:transcript', onTranscript);
    window.addEventListener('stt:transcript_partial', onPartial);
    return () => window.removeEventListener('stt:transcript', onTranscript);
  }, []);

  // speakText provided by useVoice()

  // stopSpeaking handled by hook

  // Streaming TTS effect
  useEffect(() => {
    if (!activeChat || !activeChat.messages || isLoading || isMuted) return;
    
    const lastMessage = activeChat.messages[activeChat.messages.length - 1];
    if (lastMessage && lastMessage.role === 'assistant' && lastMessage.text && lastMessage.id) {
      const messageId = lastMessage.id;
      const textToSpeak = lastMessage.text.trim();
      
      const lastProcessed = lastProcessedMessageRef.current;
      const isNewMessage = !lastProcessed || lastProcessed.id !== messageId;
      const hasSignificantGrowth = lastProcessed && lastProcessed.id === messageId && 
                                 textToSpeak.length > (lastProcessed.textLength || 0) + 50;
      
      if ((isNewMessage || hasSignificantGrowth) && 
          textToSpeak.length > 20 && 
          !spokenMessageIds.has(messageId) && 
          currentSpeakingMessageId !== messageId) {
        
        const cleanText = textToSpeak
          .replace(/#{1,6}\s+/g, '')
          .replace(/\*\*(.*?)\*\*/g, '$1')
          .replace(/\*(.*?)\*/g, '$1')
          .replace(/`(.*?)`/g, '$1')
          .replace(/\[(.*?)\]\(.*?\)/g, '$1')
          .replace(/\n+/g, ' ')
          .trim();
        
        if (cleanText.length > 20) {
          lastProcessedMessageRef.current = {
            id: messageId,
            textLength: textToSpeak.length
          };
          
          setCurrentSpeakingMessageId(messageId);
          const speak = () => speakText(cleanText, messageId);
          const timer = setTimeout(speak, 1000);
          return () => clearTimeout(timer);
        }
      }
    }
  }, [activeChat?.messages, isLoading, isMuted]);

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
            onSpeak={(text, messageId) => speakText(text, messageId)} 
          />
        )}
      </div>

      <ComposerArea
        prefill={prefill}
        setPrefill={setPrefill}
        onSend={handleSend}
        isRecording={isRecording}
        onVoiceInput={handleVoiceInput}
        isSpeaking={isSpeaking}
        onStopSpeaking={stopSpeaking}
        isMuted={isMuted}
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
      <h2 className="empty-title">Welcome to Chem Tutor!</h2>
      <p className="empty-subtext">
        Click the microphone to start asking chemistry questions.
      </p>
      <p className="empty-hint">
        Try asking: "What is benzene?" or "Show me the structure of water"
      </p>
    </section>
  );
}

// Export for use in main HTML file
window.MainPane = MainPane;
window.AppHeader = AppHeader;
window.EmptyState = EmptyState;
})();

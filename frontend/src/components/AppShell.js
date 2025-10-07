/**
 * Main application shell component - Updated for SSE
 * Manages global state with new streaming architecture
 */

;(function(){
const { useState } = React;

function AppShell() {
  const { chats, setChats, selectedChatId, setSelectedChatId, createChat, deleteChat } = window.useChatContext();
  const [deleteTargetId, setDeleteTargetId] = useState(null);
  const [ttsMode, setTTSMode] = useState('openai'); // 'openai' or 'browser'

  // Get streaming voice hook
  const voiceHook = window.useStreamingVoice();
  
  // Get browser TTS hook
  const browserTTSHook = window.useBrowserTTS();
  
  // Create chat hook with audio event handler
  const { sendMessage } = window.useSSEChat({ 
    chats, 
    setChats, 
    selectedChatId,
    ttsMode,
    onAudioEvent: (audioEvent) => {
      // Audio event from backend - play it (only in OpenAI mode)
      console.log('[AppShell] Audio event received, sentence:', audioEvent.sentenceId);
      voiceHook.playAudio(audioEvent.audio);
    },
    onTextEvent: (textEvent) => {
      // Text event - use browser TTS if in browser mode
      if (ttsMode === 'browser' && textEvent.content) {
        console.log('[AppShell] Text event for browser TTS:', textEvent.content.substring(0, 50) + '...');
        browserTTSHook.speakText(textEvent.content);
      }
    }
  });

  const handleNewChat = () => createChat();
  const handleSelectChat = (id) => setSelectedChatId(id);
  
  const requestDeleteChat = (id) => setDeleteTargetId(id);
  const cancelDeleteChat = () => setDeleteTargetId(null);
  const confirmDeleteChat = () => {
    if (deleteTargetId == null) return;
    deleteChat(deleteTargetId);
    setDeleteTargetId(null);
  };

  const handleSendMessage = async (text) => {
    await sendMessage(text);
  };

  const handleTTSModeChange = (mode) => {
    console.log('[AppShell] TTS mode changed to:', mode);
    setTTSMode(mode);
    
    // Stop any current speech when switching modes
    if (voiceHook.isSpeaking) voiceHook.stopSpeaking();
    if (browserTTSHook.isSpeaking) browserTTSHook.stopSpeaking();
  };

  const activeChat = chats.find((c) => c.id === selectedChatId) || chats[0];

  return (
    <div className="app-shell">
      <Sidebar
        chats={chats}
        selectedChatId={selectedChatId}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        onDeleteChat={requestDeleteChat}
      />
      <MainPane
        activeChat={activeChat}
        onSendMessage={handleSendMessage}
        ttsMode={ttsMode}
        onTTSModeChange={handleTTSModeChange}
        isOpenAIAvailable={true} // TODO: Check actual availability
        isBrowserAvailable={browserTTSHook.isAvailable}
      />
      {deleteTargetId != null && (
        <ConfirmModal
          title="Delete chat?"
          bodyText="This will permanently remove the conversation. This action cannot be undone."
          confirmText="Delete"
          onConfirm={confirmDeleteChat}
          onCancel={cancelDeleteChat}
        />
      )}
    </div>
  );
}

// Export globally
window.AppShell = AppShell;
})();


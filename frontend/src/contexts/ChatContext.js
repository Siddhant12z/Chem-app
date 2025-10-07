/**
 * ChatContext - central store for chats and selection
 */

;(function(){
const { createContext, useContext, useState, useEffect, useMemo, useCallback } = React;

const ChatContext = createContext(null);

function ChatProvider({ children }) {
  const [chats, setChats] = useState(() => {
    try {
      const raw = localStorage.getItem('chemTutor.chats');
      if (raw) return JSON.parse(raw);
    } catch (_) {}
    const seed = [{ id: Date.now(), title: 'New Chat', messages: [], updatedAt: Date.now() }];
    return seed;
  });

  const [selectedChatId, setSelectedChatId] = useState(() => {
    try {
      const raw = localStorage.getItem('chemTutor.selectedChatId');
      if (raw) return JSON.parse(raw);
    } catch (_) {}
    return null;
  });

  useEffect(() => {
    try { localStorage.setItem('chemTutor.chats', JSON.stringify(chats)); } catch (_) {}
  }, [chats]);

  useEffect(() => {
    // Initialize selection if absent
    if (selectedChatId == null && chats[0]?.id) {
      setSelectedChatId(chats[0].id);
    }
    try { localStorage.setItem('chemTutor.selectedChatId', JSON.stringify(selectedChatId)); } catch (_) {}
  }, [selectedChatId, chats]);

  const createChat = useCallback(() => {
    const newChat = { id: Date.now(), title: 'New Chat', messages: [], updatedAt: Date.now() };
    setChats(prev => [newChat, ...prev]);
    setSelectedChatId(newChat.id);
  }, []);

  const deleteChat = useCallback((chatId) => {
    setChats(prev => {
      const remaining = prev.filter(c => c.id !== chatId);
      let nextSelected = selectedChatId;
      if (selectedChatId === chatId) {
        nextSelected = remaining[0]?.id || null;
      }
      setSelectedChatId(nextSelected);
      return remaining;
    });
  }, [selectedChatId]);

  const value = useMemo(() => ({
    chats, setChats, selectedChatId, setSelectedChatId,
    createChat, deleteChat
  }), [chats, selectedChatId, createChat, deleteChat]);

  return (
    <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
  );
}

function useChatContext() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error('useChatContext must be used within ChatProvider');
  return ctx;
}

// Expose globally for non-bundled usage
window.ChatProvider = ChatProvider;
window.useChatContext = useChatContext;
})();

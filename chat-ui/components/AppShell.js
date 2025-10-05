/**
 * Main application shell component
 * Manages global state and layout structure
 */

;(function(){
const { useState, useEffect } = React;

function AppShell() {
  const { chats, setChats, selectedChatId, setSelectedChatId, createChat, deleteChat } = window.useChatContext();
  const [deleteTargetId, setDeleteTargetId] = useState(null);

  const handleNewChat = () => createChat();

  const handleSelectChat = (id) => setSelectedChatId(id);

  const requestDeleteChat = (id) => setDeleteTargetId(id);
  const cancelDeleteChat = () => setDeleteTargetId(null);
  const confirmDeleteChat = () => {
    if (deleteTargetId == null) return;
    deleteChat(deleteTargetId);
    setDeleteTargetId(null);
  };

  // Use centralized streaming hook
  const { sendMessage } = window.useChatStream({ chats, setChats, selectedChatId });
  const handleSendMessage = async (text) => {
    await sendMessage(text);
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

// Helper function to process streaming chunks
function processStreamChunk(buffer, selectedChatId, setChats) {
  try {
    // Detect fenced tool JSON blocks and convert to attachments
    const toolRegex = /```(?:json)?\s*(\{[^}]*"tool"[^}]*\})\s*```/g;
    let m;
    const toAttach = [];
    while ((m = toolRegex.exec(buffer)) !== null) {
      try {
        const obj = JSON.parse(m[1]);
        if (obj.tool === 'draw_molecule') {
          if (Array.isArray(obj.items)) {
            for (const it of obj.items) {
              if (it.name && it.smiles) {
                toAttach.push({ kind: 'molecule', name: it.name, smiles: it.smiles });
              }
            }
          } else if (obj.name && obj.smiles) {
            toAttach.push({ kind: 'molecule', name: obj.name, smiles: obj.smiles });
          }
          buffer = buffer.replace(m[0], '');
        }
      } catch (e) {
        console.log('JSON parse error:', e, m[1]);
      }
    }
    
    if (toAttach.length > 0) {
      setChats(prev => prev.map(c => {
        if (c.id !== selectedChatId) return c;
        const lastIndex = c.messages.length - 1;
        const last = c.messages[lastIndex];
        if (!last || last.role !== 'assistant') return c;
        const attachments = Array.isArray(last.attachments) ? last.attachments.slice() : [];
        attachments.push(...toAttach);
        const updated = { ...last, attachments };
        const newMsgs = [...c.messages.slice(0, lastIndex), updated];
        return { ...c, messages: newMsgs };
      }));
    }

    // Parse tool events embedded as [EVENT]{json}
    const eventMatches = [...buffer.matchAll(/\[EVENT\](\{[^\n]+\})/g)];
    for (const m of eventMatches) {
      try {
        const evt = JSON.parse(m[1]);
        if (evt.type === 'molecule') {
          setChats(prev => prev.map(c => {
            if (c.id !== selectedChatId) return c;
            const lastIndex = c.messages.length - 1;
            const last = c.messages[lastIndex];
            if (!last || last.role !== 'assistant') return c;
            const attachments = Array.isArray(last.attachments) ? last.attachments.slice() : [];
            if (evt.items && Array.isArray(evt.items)) {
              for (const it of evt.items) {
                if (it.name && it.smiles) {
                  attachments.push({ kind: 'molecule', name: it.name, smiles: it.smiles });
                }
              }
            } else if (evt.name && evt.smiles) {
              attachments.push({ kind: 'molecule', name: evt.name, smiles: evt.smiles });
            }
            const updated = { ...last, attachments };
            const newMsgs = [...c.messages.slice(0, lastIndex), updated];
            return { ...c, messages: newMsgs };
          }));
        }
      } catch (_) {}
    }
  } catch (_) {}
}

// Export for use in main HTML file
window.AppShell = AppShell;
})();

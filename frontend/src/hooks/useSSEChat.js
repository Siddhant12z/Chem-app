/**
 * useSSEChat - Server-Sent Events chat hook
 * Simplified replacement for useChatStream.js
 * Consumes SSE events from backend streaming endpoint
 */

;(function(){
const { useCallback, useRef } = React;

function useSSEChat({ chats, setChats, selectedChatId, onAudioEvent, onTextEvent, ttsMode = 'openai' }) {
  const eventSourceRef = useRef(null);
  const currentMessageIdRef = useRef(null);
  
  const sendMessage = useCallback(async (text) => {
    console.log('[SSE Chat] Sending message:', text.substring(0, 50) + '...');
    
    // Optimistically add user message
    setChats((prev) => {
      const next = prev.map((c) => {
        if (c.id !== selectedChatId) return c;
        const userMsg = { id: Date.now(), role: 'user', text };
        const botMsg = { id: Date.now() + 1, role: 'assistant', text: '' };
        const msgs = [...c.messages, userMsg, botMsg];
        const title = c.title === 'New Chat' && text ? text.slice(0, 40) : c.title;
        return { ...c, messages: msgs, updatedAt: Date.now(), title };
      });
      return [...next].sort((a, b) => b.updatedAt - a.updatedAt);
    });
    
    // Close any existing connection
    if (eventSourceRef.current) {
      console.log('[SSE Chat] Closing existing connection');
      eventSourceRef.current.close();
    }
    
    try {
      // Get current chat messages for context
      const current = chats.find((c) => c.id === selectedChatId);
      const msgs = [];
      (current?.messages || []).forEach(m => msgs.push({ role: m.role, content: m.text }));
      msgs.push({ role: 'user', content: text });
      
      // Store the assistant message ID for tracking
      const assistantMsgId = Date.now() + 1;
      currentMessageIdRef.current = assistantMsgId;
      
      // Make SSE connection via POST with body
      const response = await fetch('http://localhost:8000/api/stream-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: msgs,
          chat_id: selectedChatId.toString(),
          enable_tts: true,
          tts_mode: ttsMode
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Read SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          console.log('[SSE Chat] Stream complete');
          break;
        }
        
        buffer += decoder.decode(value, { stream: true });
        
        // Process complete SSE events (separated by \n\n)
        const events = buffer.split('\n\n');
        buffer = events.pop() || ''; // Keep incomplete event in buffer
        
        for (const eventBlock of events) {
          if (!eventBlock.trim()) continue;
          
          const parsedEvent = parseSSEEvent(eventBlock);
          if (parsedEvent) {
            handleSSEEvent(parsedEvent, setChats, selectedChatId, onAudioEvent, onTextEvent);
          }
        }
      }
      
    } catch (err) {
      console.error('[SSE Chat] Error:', err);
      
      // Show error in chat
      setChats(prev => prev.map(c => {
        if (c.id !== selectedChatId) return c;
        const lastIndex = c.messages.length - 1;
        const last = c.messages[lastIndex];
        if (last && last.role === 'assistant') {
          const updated = { ...last, text: (last.text || '') + `\n[Error: ${String(err)}]` };
          const newMsgs = [...c.messages.slice(0, lastIndex), updated];
          return { ...c, messages: newMsgs };
        }
        return c;
      }));
    }
  }, [chats, selectedChatId, setChats, onAudioEvent, ttsMode]);
  
  return { sendMessage };
}

/**
 * Parse SSE event block into event object
 */
function parseSSEEvent(eventBlock) {
  const lines = eventBlock.split('\n');
  let eventType = 'message'; // default
  let data = null;
  
  for (const line of lines) {
    if (line.startsWith('event:')) {
      eventType = line.substring(6).trim();
    } else if (line.startsWith('data:')) {
      const dataStr = line.substring(5).trim();
      try {
        data = JSON.parse(dataStr);
      } catch (e) {
        console.warn('[SSE Parse] Failed to parse data:', dataStr);
        data = { raw: dataStr };
      }
    }
  }
  
  if (data) {
    return { type: eventType, ...data };
  }
  
  return null;
}

/**
 * Handle different SSE event types
 */
function handleSSEEvent(event, setChats, selectedChatId, onAudioEvent, onTextEvent) {
  const eventType = event.type;
  
  console.log('[SSE Event]', eventType, event);
  
  switch (eventType) {
    case 'text':
      // Append text to current assistant message
      const content = event.content || '';
      setChats(prev => prev.map(c => {
        if (c.id !== selectedChatId) return c;
        const lastIndex = c.messages.length - 1;
        const last = c.messages[lastIndex];
        if (last && last.role === 'assistant') {
          const updated = { ...last, text: (last.text || '') + content };
          const newMsgs = [...c.messages.slice(0, lastIndex), updated];
          return { ...c, messages: newMsgs };
        }
        return c;
      }));
      
      // Trigger text event for browser TTS
      if (onTextEvent && content.trim()) {
        onTextEvent(event);
      }
      break;
    
    case 'audio':
      // Trigger audio playback
      if (onAudioEvent && event.audio_base64) {
        console.log('[SSE Event] Triggering audio playback, sentence:', event.sentence_id);
        onAudioEvent({
          audio: event.audio_base64,
          sentenceId: event.sentence_id,
          text: event.text
        });
      }
      break;
    
    case 'molecule':
      // Add molecule attachment
      setChats(prev => prev.map(c => {
        if (c.id !== selectedChatId) return c;
        const lastIndex = c.messages.length - 1;
        const last = c.messages[lastIndex];
        if (last && last.role === 'assistant') {
          const attachments = Array.isArray(last.attachments) ? last.attachments.slice() : [];
          attachments.push({ kind: 'molecule', name: event.name, smiles: event.smiles });
          const updated = { ...last, attachments };
          const newMsgs = [...c.messages.slice(0, lastIndex), updated];
          return { ...c, messages: newMsgs };
        }
        return c;
      }));
      break;
    
    case 'complete':
    case 'done':
      console.log('[SSE Event] Stream complete');
      break;
    
    case 'error':
      console.error('[SSE Event] Error:', event.message);
      const errorMsg = `\n[Error: ${event.message}]`;
      setChats(prev => prev.map(c => {
        if (c.id !== selectedChatId) return c;
        const lastIndex = c.messages.length - 1;
        const last = c.messages[lastIndex];
        if (last && last.role === 'assistant') {
          const updated = { ...last, text: (last.text || '') + errorMsg };
          const newMsgs = [...c.messages.slice(0, lastIndex), updated];
          return { ...c, messages: newMsgs };
        }
        return c;
      }));
      break;
    
    default:
      console.warn('[SSE Event] Unknown event type:', eventType);
  }
}

// Export globally
window.useSSEChat = useSSEChat;
})();


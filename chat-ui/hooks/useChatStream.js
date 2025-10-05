/**
 * useChatStream - centralized streaming chat state manager
 * Handles: sending, streaming updates, tool/event parsing, and error handling
 */

const { useCallback, useRef } = React;

function useChatStream({ chats, setChats, selectedChatId }) {
  // Track how much of the stream we've already processed per chat to compute deltas
  const lastProcessedLenRef = useRef(new Map());
  // Track seen fenced tool blocks per chat to avoid duplicate attachments
  const seenToolMatchesRef = useRef(new Map());
  const processStreamChunk = useCallback((buffer, selectedId) => {
    try {
      const toolRegex = /```(?:json)?\s*(\{[^}]*"tool"[^}]*\})\s*```/g;
      let m;
      const toAttach = [];
      while ((m = toolRegex.exec(buffer)) !== null) {
        try {
          const fullMatch = m[0];
          const seenSet = seenToolMatchesRef.current.get(selectedId) || new Set();
          if (seenSet.has(fullMatch)) continue;
          const obj = JSON.parse(m[1]);
          if (obj.tool === 'draw_molecule') {
            if (Array.isArray(obj.items)) {
              for (const it of obj.items) {
                if (it && it.name) toAttach.push({ kind: 'molecule', name: it.name, smiles: it.smiles });
              }
            } else if (obj.name) {
              toAttach.push({ kind: 'molecule', name: obj.name, smiles: obj.smiles });
            }
            seenSet.add(fullMatch);
            seenToolMatchesRef.current.set(selectedId, seenSet);
          }
        } catch (_) {}
      }

      if (toAttach.length > 0) {
        setChats(prev => prev.map(c => {
          if (c.id !== selectedId) return c;
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

      // EVENTS: [EVENT]{json}
      const eventMatches = [...buffer.matchAll(/\[EVENT\](\{[^\n]+\})/g)];
      for (const m2 of eventMatches) {
        try {
          const evt = JSON.parse(m2[1]);
          if (evt.type === 'molecule') {
            setChats(prev => prev.map(c => {
              if (c.id !== selectedId) return c;
              const lastIndex = c.messages.length - 1;
              const last = c.messages[lastIndex];
              if (!last || last.role !== 'assistant') return c;
            const attachments = Array.isArray(last.attachments) ? last.attachments.slice() : [];
            if (evt.items && Array.isArray(evt.items)) {
              for (const it of evt.items) {
                if (it && it.name) attachments.push({ kind: 'molecule', name: it.name, smiles: it.smiles });
              }
            } else if (evt.name) {
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
  }, [setChats]);

  const sendMessage = useCallback(async (text) => {
    // optimistic add
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

    try {
      const current = chats.find((c) => c.id === selectedChatId);
      const msgs = [];
      (current?.messages || []).forEach(m => msgs.push({ role: m.role, content: m.text }));
      msgs.push({ role: 'user', content: text });

      const res = await apiService.sendRagMessage(msgs, selectedChatId.toString());
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let accumulated = '';

      const streamStartTs = performance.now();
      while (!done) {
        const { value, done: doneRead } = await reader.read();
        done = doneRead;
        let chunk = decoder.decode(value || new Uint8Array(), { stream: !done });
        if (!chunk) continue;
        accumulated += chunk;
        // Compute delta relative to what we've already processed for this chat
        const prevLen = lastProcessedLenRef.current.get(selectedChatId) || 0;
        const delta = accumulated.slice(prevLen);
        lastProcessedLenRef.current.set(selectedChatId, accumulated.length);
        // Parse tools/events from the accumulated buffer to allow cross-chunk detection
        if (accumulated && accumulated.length > 0) {
          processStreamChunk(accumulated, selectedChatId);
        }
        if (!delta) continue;
        const now = performance.now();
        if (window && window.console) {
          try {
            console.debug('[LLM stream]', {
              dtMs: Math.round(now - streamStartTs),
              deltaLen: delta.length
            });
          } catch(_){}
        }
        // Strip tool fences and event markers from the visible text
        const displayDelta = delta
          .replace(/```(?:json)?\s*\{[^}]*"tool"[^}]*\}\s*```/g, '')
          .replace(/\[EVENT\]\{[^\n]+\}\n?/g, '');
        if (!displayDelta) continue;
        setChats(prev => prev.map(c => {
          if (c.id !== selectedChatId) return c;
          const lastIndex = c.messages.length - 1;
          const last = c.messages[lastIndex];
          if (last && last.role === 'assistant') {
            const updated = { ...last, text: (last.text || '') + displayDelta };
            const newMsgs = [...c.messages.slice(0, lastIndex), updated];
            return { ...c, messages: newMsgs };
          }
          return c;
        }));
      }
    } catch (err) {
      try { window.toast && window.toast.show(String(err), 'error'); } catch(_){}
      setChats(prev => prev.map(c => {
        if (c.id !== selectedChatId) return c;
        const lastIndex = c.messages.length - 1;
        const last = c.messages[lastIndex];
        const updated = { ...last, text: (last.text || '') + `\n[Error: ${String(err)}]` };
        const newMsgs = [...c.messages.slice(0, lastIndex), updated];
        return { ...c, messages: newMsgs };
      }));
    }
  }, [chats, selectedChatId, setChats, processStreamChunk]);

  return { sendMessage };
}

// Export for global use
window.useChatStream = useChatStream;



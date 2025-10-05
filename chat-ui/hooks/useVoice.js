/**
 * useVoice - centralized STT/TTS state and actions
 */

(function(){
const { useState, useRef, useCallback } = React;

function useVoice() {
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentAudio, setCurrentAudio] = useState(null);
  const [spokenMessageIds, setSpokenMessageIds] = useState(new Set());
  const [currentSpeakingMessageId, setCurrentSpeakingMessageId] = useState(null);
  const lastProcessedMessageRef = useRef(null);
  // Maintain an audio job queue for incremental speech
  const ttsQueueRef = useRef([]);
  const isTtsBusyRef = useRef(false);
  // Track last spoken character index per message
  const lastSpokenIndexRef = useRef(new Map());

  function extractStableSentences(text, startIndex) {
    const slice = (text || '').slice(startIndex || 0);
    // Split on sentence terminators; keep only fully terminated sentences
    const parts = slice.split(/([.!?])\s+/);
    if (parts.length <= 1) return { sentences: [], nextIndex: startIndex || 0 };
    const sentences = [];
    let acc = '';
    for (let i = 0; i < parts.length; i++) {
      const seg = parts[i];
      if (!seg) continue;
      acc += (acc ? ' ' : '') + seg.trim();
      // When we hit a terminator in the regex capture, finalize the sentence
      if (seg.match(/^[.!?]$/)) {
        const s = acc.trim();
        if (s.length > 0) sentences.push(s);
        acc = '';
      }
    }
    // Compute new index relative to original text for consumed content
    const consumed = (sentences.join(' ') + ' ').length; // approximate including one space
    const nextIndex = (startIndex || 0) + consumed;
    return { sentences, nextIndex };
  }

  async function enqueueTts(text, messageId) {
    if (!text) return;
    ttsQueueRef.current.push({ text, messageId });
    if (!isTtsBusyRef.current) {
      isTtsBusyRef.current = true;
      try {
        while (ttsQueueRef.current.length > 0) {
          const job = ttsQueueRef.current.shift();
          // Skip if muted mid-queue
          if (isMuted) { ttsQueueRef.current.length = 0; break; }
          const ttsReqStart = performance.now();
          const result = await apiService.textToSpeech(job.text);
          try { console.debug('[TTS synth ms]', Math.round(performance.now() - ttsReqStart), 'len=', job.text.length); } catch(_){}
          if (!(result && result.success && result.audio_data)) continue;
          // Stop any current audio
          if (currentAudio) {
            try { currentAudio.pause(); currentAudio.currentTime = 0; } catch(_){ }
          }
          const audioBlob = new Blob([Uint8Array.from(atob(result.audio_data), c => c.charCodeAt(0))], { type: 'audio/mpeg' });
          const audioUrl = URL.createObjectURL(audioBlob);
          const audio = new Audio(audioUrl);
          setCurrentAudio(audio);
          const playbackStart = performance.now();
          await new Promise((resolve) => {
            audio.onplay = () => { setIsSpeaking(true); if (job.messageId) setCurrentSpeakingMessageId(job.messageId); };
            audio.onended = () => { setIsSpeaking(false); setCurrentAudio(null); URL.revokeObjectURL(audioUrl); try { console.debug('[TTS playback ms]', Math.round(performance.now() - playbackStart)); } catch(_){} resolve(); };
            audio.onerror = () => { setIsSpeaking(false); setCurrentAudio(null); URL.revokeObjectURL(audioUrl); try { console.debug('[TTS playback error ms]', Math.round(performance.now() - playbackStart)); } catch(_){} resolve(); };
            audio.play().catch(() => resolve());
          });
          // Mark message as partially spoken by advancing index; do not mark fully spoken here
        }
      } finally {
        isTtsBusyRef.current = false;
      }
    }
  }

  const handleVoiceInput = useCallback(async () => {
    if (isRecording) {
      setIsRecording(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      const audioChunks = [];
      const sttStartTs = performance.now();

      // Setup simple VAD using WebAudio analyser
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 2048;
      const dataArray = new Uint8Array(analyser.fftSize);
      source.connect(analyser);
      let silenceMs = 0;
      let lastTick = performance.now();
      const SILENCE_THRESHOLD = 0.02; // RMS ~2%
      const SILENCE_HOLD_MS = 900;    // stop after ~0.9s silence
      let rafId = null;
      const vadLoop = () => {
        analyser.getByteTimeDomainData(dataArray);
        // Compute RMS
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          const v = (dataArray[i] - 128) / 128;
          sum += v * v;
        }
        const rms = Math.sqrt(sum / dataArray.length);
        const now = performance.now();
        const dt = now - lastTick;
        lastTick = now;
        if (rms < SILENCE_THRESHOLD) {
          silenceMs += dt;
          if (silenceMs >= SILENCE_HOLD_MS && mediaRecorder.state === 'recording') {
            try { mediaRecorder.stop(); } catch(_){ }
          }
        } else {
          silenceMs = 0;
        }
        if (mediaRecorder.state === 'recording') rafId = requestAnimationFrame(vadLoop);
      };

      mediaRecorder.ondataavailable = (event) => {
        // Collect for final transcript
        audioChunks.push(event.data);
        // Emit partials periodically using small chunks
        if (event.data && event.data.size > 0 && isRecording) {
          const partialBlob = event.data;
          // Fire-and-forget partial STT; update composer on success
          (async () => {
            try {
              const result = await apiService.speechToText(partialBlob);
              if (result && result.success && result.transcript) {
                window.dispatchEvent(new CustomEvent('stt:transcript_partial', { detail: { transcript: result.transcript } }));
              }
            } catch(_){ }
          })();
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        try {
          const result = await apiService.speechToText(audioBlob);
          if (result.success && result.transcript) {
            // Return transcript via custom event for consumers
            window.dispatchEvent(new CustomEvent('stt:transcript', { detail: { transcript: result.transcript } }));
          } else {
            alert('Speech recognition failed: ' + (result.error || 'Unknown error'));
          }
        } catch (error) {
          alert('Speech recognition error: ' + error.message);
        }
        setIsRecording(false);
        try { console.debug('[STT total ms]', Math.round(performance.now() - sttStartTs)); } catch(_){ }
        try { if (rafId) cancelAnimationFrame(rafId); } catch(_){ }
        try { source.disconnect(); } catch(_){ }
        try { analyser.disconnect(); } catch(_){ }
        try { audioCtx.close(); } catch(_){ }
        stream.getTracks().forEach(track => track.stop());
      };

      // Start recorder with timeslice to trigger ondataavailable regularly for partials
      mediaRecorder.start(800);
      setIsRecording(true);
      // Kick off VAD monitoring
      rafId = requestAnimationFrame(vadLoop);
      // Safety timeout
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          try { mediaRecorder.stop(); } catch(_){ }
          stream.getTracks().forEach(track => track.stop());
        }
      }, 15000);
    } catch (error) {
      alert('Microphone access denied: ' + error.message);
      setIsRecording(false);
    }
  }, [isRecording]);

  const speakText = useCallback(async (text, messageId = null) => {
    if (isMuted) return;
    // If entire message already spoken, skip
    if (messageId && spokenMessageIds.has(messageId)) return;

    try {
      let cleanText = text
        .replace(/\n+/g, ' ')
        .replace(/\s+/g, ' ')
        .replace(/Sources?:.*$/i, '')
        .replace(/References?:.*$/i, '')
        .replace(/\[EVENT\].*$/g, '')
        .replace(/```.*?```/gs, '')
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/`(.*?)`/g, '$1')
        .replace(/\[(.*?)\]\(.*?\)/g, '$1')
        .replace(/#{1,6}\s+/g, '')
        .trim();

      // Identify new stable sentences since last spoken index
      const prevIndex = messageId ? (lastSpokenIndexRef.current.get(messageId) || 0) : 0;
      const { sentences, nextIndex } = extractStableSentences(cleanText, prevIndex);
      if (sentences.length > 0) {
        // Enqueue each sentence as a separate TTS job
        for (const s of sentences) {
          await enqueueTts(s, messageId);
        }
        if (messageId) {
          lastSpokenIndexRef.current.set(messageId, nextIndex);
        }
      }
    } catch (error) {
      alert('Text-to-speech error: ' + error.message);
    }
  }, [isMuted, spokenMessageIds, currentAudio]);

  const stopSpeaking = useCallback(() => {
    if (isMuted) {
      setIsMuted(false);
      return;
    }
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      setCurrentAudio(null);
    }
    // Clear any queued TTS jobs
    if (ttsQueueRef.current && ttsQueueRef.current.length) ttsQueueRef.current.length = 0;
    const audioElements = document.querySelectorAll('audio');
    audioElements.forEach(audio => { audio.pause(); audio.currentTime = 0; });
    setIsSpeaking(false);
    setCurrentSpeakingMessageId(null);
    setIsMuted(true);
  }, [isMuted, currentAudio]);

  return {
    // states
    isRecording, isSpeaking, isMuted,
    currentAudio, spokenMessageIds, currentSpeakingMessageId,
    lastProcessedMessageRef,
    // actions
    handleVoiceInput, speakText, stopSpeaking,
    setIsMuted, setCurrentSpeakingMessageId, setSpokenMessageIds
  };
}

// Export globally for non-bundled usage
window.useVoice = useVoice;
})();


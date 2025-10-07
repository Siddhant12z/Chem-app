/**
 * useStreamingVoice - Simplified TTS playback
 * Just plays audio chunks sent from backend (no sentence extraction)
 */

;(function(){
const { useState, useRef, useCallback } = React;

function useStreamingVoice() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  
  const audioQueueRef = useRef([]);
  const currentAudioRef = useRef(null);
  const isProcessingRef = useRef(false);
  
  /**
   * Play audio from base64 data
   * Called when backend sends audio event
   */
  const playAudio = useCallback((audioBase64) => {
    if (isMuted) {
      console.log('[Streaming Voice] Skipped audio - muted');
      return;
    }
    
    if (!audioBase64) {
      console.warn('[Streaming Voice] No audio data provided');
      return;
    }
    
    try {
      const queueLength = audioQueueRef.current.length;
      console.log('[Streaming Voice] Received audio, queue length:', queueLength, 'isSpeaking:', isSpeaking);
      
      // Convert base64 to blob
      const audioBlob = new Blob(
        [Uint8Array.from(atob(audioBase64), c => c.charCodeAt(0))], 
        { type: 'audio/mpeg' }
      );
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.preload = 'auto';
      
      // Add to queue
      audioQueueRef.current.push({ audio, audioUrl });
      
      // Start processing queue if not already processing
      if (!isProcessingRef.current) {
        console.log('[Streaming Voice] Starting queue processing');
        processAudioQueue();
      } else {
        console.log('[Streaming Voice] Queued (processing in progress)');
      }
      
    } catch (error) {
      console.error('[Streaming Voice] Error preparing audio:', error);
    }
  }, [isMuted]);
  
  /**
   * Process audio queue sequentially
   */
  function processAudioQueue() {
    // Prevent multiple simultaneous processing
    if (isProcessingRef.current) {
      console.log('[Streaming Voice] Already processing queue');
      return;
    }
    
    isProcessingRef.current = true;
    console.log('[Streaming Voice] Starting queue processing, queue length:', audioQueueRef.current.length);
    
    playNextInQueue();
  }
  
  function playNextInQueue() {
    // Check if queue is empty
    if (audioQueueRef.current.length === 0) {
      console.log('[Streaming Voice] Queue empty - stopping processing');
      setIsSpeaking(false);
      currentAudioRef.current = null;
      isProcessingRef.current = false;
      return;
    }
    
    const { audio, audioUrl } = audioQueueRef.current.shift();
    
    console.log('[Streaming Voice] Playing audio, remaining in queue:', audioQueueRef.current.length);
    
    currentAudioRef.current = audio;
    setIsSpeaking(true);
    
    const playStart = performance.now();
    
    // Set up event handlers
    audio.onended = () => {
      const duration = Math.round(performance.now() - playStart);
      console.log('[Streaming Voice] Audio ended after', duration + 'ms');
      URL.revokeObjectURL(audioUrl);
      currentAudioRef.current = null;
      
      // Continue to next after small gap
      setTimeout(() => {
        playNextInQueue();
      }, 200);
    };
    
    audio.onerror = (e) => {
      console.error('[Streaming Voice] Playback error:', e);
      URL.revokeObjectURL(audioUrl);
      currentAudioRef.current = null;
      
      // Continue to next
      setTimeout(() => {
        playNextInQueue();
      }, 200);
    };
    
    // Start playback
    audio.play().then(() => {
      console.log('[Streaming Voice] Playing...');
    }).catch((e) => {
      console.error('[Streaming Voice] Failed to play:', e);
      URL.revokeObjectURL(audioUrl);
      currentAudioRef.current = null;
      
      // Try next
      setTimeout(() => {
        playNextInQueue();
      }, 200);
    });
  }
  
  /**
   * Stop all audio and clear queue
   */
  const stopSpeaking = useCallback(() => {
    console.log('[Streaming Voice] Stop speaking, isMuted:', isMuted);
    
    if (isMuted) {
      // Unmute
      setIsMuted(false);
      return;
    }
    
    // Stop current audio
    if (currentAudioRef.current) {
      try {
        currentAudioRef.current.pause();
        currentAudioRef.current.currentTime = 0;
        currentAudioRef.current.src = '';
      } catch (e) {
        console.error('[Streaming Voice] Error stopping:', e);
      }
      currentAudioRef.current = null;
    }
    
    // Clear queue
    audioQueueRef.current.forEach(({ audioUrl }) => {
      try { URL.revokeObjectURL(audioUrl); } catch (_) {}
    });
    audioQueueRef.current = [];
    
    // Reset processing state
    isProcessingRef.current = false;
    setIsSpeaking(false);
    setIsMuted(true);
    
    console.log('[Streaming Voice] Stopped and muted');
  }, [isMuted]);
  
  /**
   * Voice input (STT) - reuse existing logic
   */
  const handleVoiceInput = useCallback(async () => {
    if (isRecording) {
      setIsRecording(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      const audioChunks = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        try {
          const result = await apiService.speechToText(audioBlob);
          if (result.success && result.transcript) {
            window.dispatchEvent(new CustomEvent('stt:transcript', { 
              detail: { transcript: result.transcript } 
            }));
          } else {
            alert('Speech recognition failed: ' + (result.error || 'Unknown error'));
          }
        } catch (error) {
          alert('Speech recognition error: ' + error.message);
        }
        setIsRecording(false);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      
      // Auto-stop after 15 seconds
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop();
        }
      }, 15000);
      
    } catch (error) {
      alert('Microphone access denied: ' + error.message);
      setIsRecording(false);
    }
  }, [isRecording]);
  
  return {
    isSpeaking,
    isMuted,
    isRecording,
    playAudio,
    stopSpeaking,
    handleVoiceInput,
    setIsMuted
  };
}

// Export globally
window.useStreamingVoice = useStreamingVoice;
})();


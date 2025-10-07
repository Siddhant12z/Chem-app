/**
 * useBrowserTTS - Browser SpeechSynthesis fallback
 * Free offline TTS when OpenAI API is unavailable
 */

;(function(){
const { useState, useRef, useCallback } = React;

function useBrowserTTS() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isAvailable, setIsAvailable] = useState(false);
  
  const utteranceRef = useRef(null);
  const queueRef = useRef([]);
  const isProcessingRef = useRef(false);
  
  // Check if SpeechSynthesis is available
  React.useEffect(() => {
    const available = 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
    setIsAvailable(available);
    
    if (available) {
      console.log('[Browser TTS] SpeechSynthesis API available');
      
      // Get available voices for debugging
      const voices = speechSynthesis.getVoices();
      console.log('[Browser TTS] Available voices:', voices.length);
      
      // Log voices that might support multiple languages
      const multilingualVoices = voices.filter(v => 
        v.lang.includes('en') || v.lang.includes('hi') || v.lang.includes('ne')
      );
      console.log('[Browser TTS] Multilingual voices:', multilingualVoices.map(v => ({ name: v.name, lang: v.lang })));
    } else {
      console.warn('[Browser TTS] SpeechSynthesis API not available');
    }
  }, []);
  
  /**
   * Speak text using browser SpeechSynthesis
   */
  const speakText = useCallback((text) => {
    if (!isAvailable || isMuted || !text?.trim()) {
      console.log('[Browser TTS] Skipped - not available, muted, or no text');
      return;
    }
    
    try {
      console.log('[Browser TTS] Speaking text:', text.substring(0, 50) + '...');
      
      // Add to queue
      queueRef.current.push(text.trim());
      
      // Start processing if not already processing
      if (!isProcessingRef.current) {
        processQueue();
      }
      
    } catch (error) {
      console.error('[Browser TTS] Error preparing speech:', error);
    }
  }, [isAvailable, isMuted]);
  
  /**
   * Process speech queue sequentially
   */
  function processQueue() {
    if (isProcessingRef.current || queueRef.current.length === 0) {
      return;
    }
    
    isProcessingRef.current = true;
    
    const text = queueRef.current.shift();
    
    try {
      // Stop any current speech
      speechSynthesis.cancel();
      
      // Create new utterance
      const utterance = new SpeechSynthesisUtterance(text);
      utteranceRef.current = utterance;
      
      // Configure utterance
      utterance.rate = 0.9;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      
      // Try to select a good voice
      const voices = speechSynthesis.getVoices();
      if (voices.length > 0) {
        // Prefer voices that might support multiple languages
        const preferredVoice = voices.find(v => 
          v.name.toLowerCase().includes('google') || 
          v.name.toLowerCase().includes('microsoft') ||
          v.lang.includes('en-US')
        ) || voices[0];
        
        utterance.voice = preferredVoice;
        console.log('[Browser TTS] Using voice:', preferredVoice.name, preferredVoice.lang);
      }
      
      // Set language
      utterance.lang = 'en-US';
      
      // Set up event handlers
      utterance.onstart = () => {
        console.log('[Browser TTS] Speech started');
        setIsSpeaking(true);
      };
      
      utterance.onend = () => {
        console.log('[Browser TTS] Speech ended');
        utteranceRef.current = null;
        setIsSpeaking(false);
        
        // Process next in queue after small delay
        setTimeout(() => {
          isProcessingRef.current = false;
          processQueue();
        }, 100);
      };
      
      utterance.onerror = (event) => {
        console.error('[Browser TTS] Speech error:', event.error);
        utteranceRef.current = null;
        setIsSpeaking(false);
        
        // Continue with next in queue
        setTimeout(() => {
          isProcessingRef.current = false;
          processQueue();
        }, 100);
      };
      
      // Start speaking
      speechSynthesis.speak(utterance);
      
    } catch (error) {
      console.error('[Browser TTS] Error in processQueue:', error);
      isProcessingRef.current = false;
      setIsSpeaking(false);
    }
  }
  
  /**
   * Stop all speech
   */
  const stopSpeaking = useCallback(() => {
    console.log('[Browser TTS] Stop speaking');
    
    if (isMuted) {
      // Unmute
      setIsMuted(false);
      return;
    }
    
    // Stop speech synthesis
    speechSynthesis.cancel();
    
    // Clear queue
    queueRef.current = [];
    utteranceRef.current = null;
    isProcessingRef.current = false;
    
    setIsSpeaking(false);
    setIsMuted(true);
  }, [isMuted]);
  
  /**
   * Get available voices
   */
  const getVoices = useCallback(() => {
    if (!isAvailable) return [];
    
    const voices = speechSynthesis.getVoices();
    return voices.map(v => ({
      name: v.name,
      lang: v.lang,
      default: v.default,
      localService: v.localService
    }));
  }, [isAvailable]);
  
  return {
    isSpeaking,
    isMuted,
    isAvailable,
    speakText,
    stopSpeaking,
    setIsMuted,
    getVoices
  };
}

// Export globally
window.useBrowserTTS = useBrowserTTS;
})();

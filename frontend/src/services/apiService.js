/**
 * API service for handling all backend communications
 */

class ApiService {
  constructor() {
    this.baseUrl = 'http://localhost:8000';
    this.defaultHeaders = {
      'Content-Type': 'application/json'
    };
    this.defaultTimeoutMs = 30000; // 30s default
    this.defaultRetries = 2;       // retry transient failures
  }

  // Generic fetch wrapper with error handling
  async request(endpoint, options = {}, controls = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: this.defaultHeaders,
      ...options
    };
    const timeoutMs = controls.timeoutMs ?? this.defaultTimeoutMs;
    const retries = controls.retries ?? this.defaultRetries;

    // For FormData, do not send Content-Type; browser sets it
    if (config.body instanceof FormData) {
      const { headers, ...rest } = config;
      config.headers = { ...(headers || {}) };
      delete config.headers['Content-Type'];
    }

    let attempt = 0;
    let lastErr;
    while (attempt <= retries) {
      const controller = new AbortController();
      const timer = timeoutMs && !config.stream ? setTimeout(() => controller.abort(), timeoutMs) : null;
      try {
        const response = await fetch(url, { ...config, signal: controller.signal });
        if (timer) clearTimeout(timer);
        if (!response.ok) {
          const isStream = !!config.stream;
          const status = response.status;
          // Try to parse error json; if fails, build generic
          let errorText;
          try { errorText = await response.text(); } catch (_) { errorText = ''; }
          const shouldRetry = [429, 500, 502, 503, 504].includes(status);
          const err = new Error(this._formatHttpError(endpoint, status, response.statusText, errorText));
          if (shouldRetry && attempt < retries && !isStream) {
            await this._sleep(this._backoff(attempt));
            attempt++;
            lastErr = err;
            continue;
          }
          throw err;
        }
        return response;
      } catch (error) {
        if (timer) clearTimeout(timer);
        const isAbort = error?.name === 'AbortError';
        const isNetwork = !isAbort && (error instanceof TypeError || (error?.message || '').includes('Network'));
        if ((isAbort || isNetwork) && attempt < retries && !config.stream) {
          await this._sleep(this._backoff(attempt));
          attempt++;
          lastErr = error;
          continue;
        }
        console.error(`API request failed for ${endpoint}:`, error);
        throw error;
      }
    }
    throw lastErr || new Error('Unknown API error');
  }

  _formatHttpError(endpoint, status, statusText, bodyText) {
    let msg = `HTTP ${status}: ${statusText} at ${endpoint}`;
    if (bodyText) {
      // Try to surface server error string
      try {
        const parsed = JSON.parse(bodyText);
        if (parsed && parsed.error) msg += ` - ${parsed.error}`;
        else msg += ` - ${bodyText.substring(0, 200)}`;
      } catch (_) {
        msg += ` - ${bodyText.substring(0, 200)}`;
      }
    }
    return msg;
  }

  _sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
  _backoff(attempt) { return 500 * Math.pow(2, attempt); }

  // Chat API
  async sendChatMessage(messages, model = null) {
    const response = await this.request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        messages,
        model
      })
    });
    return response;
  }

  // RAG Chat API with memory management
  async sendRagMessage(messages, chatId, model = null, k = 3) {
    const response = await this.request('/api/rag-chat', {
      method: 'POST',
      body: JSON.stringify({
        messages,
        chat_id: chatId,
        model,
        k
      }),
      // mark as streaming to skip timeouts/retries during open stream
      stream: true
    }, { retries: 0, timeoutMs: 0 });
    return response;
  }

  // Text-to-Speech API
  async textToSpeech(text, voiceId = null) {
    const response = await this.request('/api/tts', {
      method: 'POST',
      body: JSON.stringify({
        text,
        voice_id: voiceId
      })
    });
    return response.json();
  }

  // Speech-to-Text API
  async speechToText(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    
    const response = await this.request('/api/stt', {
      method: 'POST',
      headers: {}, // Remove Content-Type for FormData
      body: formData
    });
    return response.json();
  }

  // Molecule drawing API
  async drawMolecule(smiles, name = '', format = 'svg', width = 300, height = 300) {
    const response = await this.request('/api/draw-molecule', {
      method: 'POST',
      body: JSON.stringify({
        smiles,
        name,
        format,
        width,
        height
      })
    });
    
    if (format === 'svg') {
      return response.text();
    } else {
      return response.text();
    }
  }

  // Molecule info API
  async getMoleculeInfo(smiles) {
    const response = await this.request('/api/molecule-info', {
      method: 'POST',
      body: JSON.stringify({ smiles })
    });
    return response.json();
  }

  // Get available voices
  async getVoices() {
    const response = await this.request('/api/voices');
    return response.json();
  }

  // Test API connectivity
  async testConnection() {
    const response = await this.request('/api/test');
    return response.json();
  }
}

// Create singleton instance
const apiService = new ApiService();

// Export for use in components
window.apiService = apiService;

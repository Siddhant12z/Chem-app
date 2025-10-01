# Voice Features Implementation

## Overview
The chat UI now includes full voice functionality with Speech-to-Text (SST) and Text-to-Speech (TTS) capabilities.

## Features Implemented

### 🎤 Speech-to-Text (Voice Input)
- Click the microphone button to start recording your question
- The system will automatically convert your speech to text
- The transcribed text appears in the input field
- Click the microphone again or wait for the recording to complete

### 🔊 Text-to-Speech (Voice Output)
- Assistant responses are automatically spoken aloud
- Click the speaker button to stop the current speech
- The speaker button shows visual feedback when speaking

### 🎨 Visual Feedback
- Microphone button turns red and pulses when recording
- Speaker button turns green and pulses when speaking
- Hover effects on both buttons for better UX

## Browser Compatibility

### Speech Recognition (SST)
- **Chrome/Edge**: Full support
- **Firefox**: Limited support
- **Safari**: Limited support
- **Mobile browsers**: Varies by device

### Speech Synthesis (TTS)
- **All modern browsers**: Full support
- **Mobile devices**: Full support

## Usage Instructions

1. **Start the servers**:
   ```bash
   # Terminal 1: Start the backend server
   cd server
   python ollama_proxy.py
   
   # Terminal 2: Start the frontend server
   cd chat-ui
   python -m http.server 3000
   ```

2. **Open the application**:
   - Navigate to `http://localhost:3000` in your browser
   - Allow microphone permissions when prompted

3. **Use voice features**:
   - Click the 🎤 button to speak your chemistry question
   - The AI will respond both in text and voice
   - Click the 🔊 button to stop speech if needed

## Technical Implementation

### Speech Recognition
- Uses Web Speech API (`webkitSpeechRecognition`)
- Configured for English (en-US)
- Single utterance mode (not continuous)
- Error handling for unsupported browsers

### Speech Synthesis
- Uses Web Speech API (`speechSynthesis`)
- Automatic text cleaning (removes markdown formatting)
- Configurable speech rate, pitch, and volume
- Auto-speaks assistant responses with 500ms delay

### State Management
- React state for recording/speaking status
- Visual feedback through CSS classes
- Proper cleanup and error handling

## Troubleshooting

### Microphone Not Working
1. Check browser permissions for microphone access
2. Ensure you're using HTTPS (required for microphone access)
3. Try refreshing the page and allowing permissions again

### Speech Not Playing
1. Check your system volume
2. Ensure no other applications are using the audio output
3. Try clicking the speaker button to manually stop/start

### Browser Compatibility Issues
- Use Chrome or Edge for best compatibility
- Some features may not work in private/incognito mode
- Mobile browsers may have different behavior

## Future Enhancements
- Language selection for speech recognition
- Voice command shortcuts
- Customizable speech settings (rate, pitch, voice)
- Offline speech recognition support

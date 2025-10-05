/**
 * Composer area component with text input, voice controls, and quick actions
 */

;(function(){
const { useState } = React;

function ComposerArea({ prefill, setPrefill, onSend, isRecording, onVoiceInput, isSpeaking, onStopSpeaking, isMuted }) {
  const quickChips = [
    { label: 'What is organic chemistry?' },
    { label: 'What is ions?' },
    { label: 'Draw diagram of water' },
    { label: 'Draw diagram of benzene' },
  ];

  return (
    <div className="composer-area">
      <div className="quick-actions">
        <div className="quick-title">Quick Test Questions:</div>
        <QuickActionsChips chips={quickChips} onPick={(t) => setPrefill(t)} />
      </div>
      <div className="composer-row">
        <MicButton isRecording={isRecording} onToggle={onVoiceInput} />
        <TextComposer value={prefill} onChange={setPrefill} placeholder="Type Question" onSend={onSend} />
        <SpeakerButton isSpeaking={isSpeaking} onToggle={onStopSpeaking} isMuted={isMuted} />
        <div className="mic-helper">Click microphone to speak your question</div>
      </div>
    </div>
  );
}

function QuickActionsChips({ chips, onPick }) {
  return (
    <div className="chip-row">
      {chips.map((c, idx) => (
        <QuickActionChip key={idx} label={c.label} index={idx} onClick={() => onPick(c.label)} />
      ))}
    </div>
  );
}

function QuickActionChip({ label, index, onClick }) {
  const colorClass = index < 2 ? 'chip-blue' : 'chip-green';
  return (
    <button className={`chip ${colorClass}`} onClick={onClick}>
      {label}
    </button>
  );
}

function TextComposer({ value, onChange, placeholder, onSend }) {
  return (
    <div className="composer-input-wrap">
      <input
        className="text-input"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter') onSend(); }}
        aria-label="Type Question"
      />
      <button className="btn btn-primary" onClick={onSend}>
        Send
      </button>
    </div>
  );
}

function MicButton({ isRecording, onToggle }) {
  return (
    <button 
      className={`mic-button ${isRecording ? 'recording' : ''}`} 
      onClick={onToggle} 
      title={isRecording ? 'Stop Recording' : 'Start Recording'}
    >
      {isRecording ? '⏹️' : '🎤'}
    </button>
  );
}

function SpeakerButton({ isSpeaking, onToggle, isMuted }) {
  const getButtonState = () => {
    if (isMuted) return { icon: '🔇', title: 'Unmute (TTS is muted)', className: 'muted' };
    if (isSpeaking) return { icon: '🔇', title: 'Stop Speaking', className: 'speaking' };
    return { icon: '🔊', title: 'Speaker', className: '' };
  };
  
  const { icon, title, className } = getButtonState();
  return (
    <button 
      className={`speaker-button ${className}`} 
      onClick={onToggle} 
      title={title}
    >
      {icon}
    </button>
  );
}

// Export for use in main HTML file
window.ComposerArea = ComposerArea;
window.QuickActionsChips = QuickActionsChips;
window.QuickActionChip = QuickActionChip;
window.TextComposer = TextComposer;
window.MicButton = MicButton;
window.SpeakerButton = SpeakerButton;
})();

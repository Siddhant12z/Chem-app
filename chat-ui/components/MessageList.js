/**
 * Message list component with markdown rendering and molecule attachments
 */

;(function(){
const { useState, useRef, useEffect, memo, useMemo } = React;

const MessageItem = memo(function MessageItem({ m, onSpeak }) {
  return (
    <div className={"message " + m.role}>
      <div className="avatar">{m.role === 'user' ? '🧑' : '🧪'}</div>
      {m.role === 'assistant'
        ? (
            <div className="bubble md">
              {m.text && m.text.trim().length > 0
                ? (() => {
                    const { answerText, references, plainText } = parseAssistantContent(m.text);
                    return (
                      <>
                        <div dangerouslySetInnerHTML={{ __html: renderMarkdown(answerText) }} />
                        {references.length > 0 && <ReferencesPanel items={references} />}
                        {plainText && (
                          <div className="speak-row">
                            <button 
                              className="speak-inline" 
                              onClick={() => onSpeak && onSpeak(plainText, m.id)} 
                              title="Speak this answer"
                            >
                              🔊 Speak
                            </button>
                          </div>
                        )}
                      </>
                    );
                  })()
                : (
                    <span className="thinking" aria-live="polite" aria-busy="true">
                      <span className="spinner" />
                      <span className="thinking-text">Thinking...</span>
                    </span>
                  )}
              {Array.isArray(m.attachments) && m.attachments.map((att, i) => (
                att.kind === 'molecule' ? <MoleculeCard key={i} name={att.name} smiles={att.smiles} /> : null
              ))}
            </div>
          )
        : (
            <div className="bubble">{m.text}</div>
          )}
    </div>
  );
});

function MessageList({ messages, onSpeak }) {
  const items = useMemo(() => messages, [messages]);
  return (
    <div className="message-list">
      {items.map((m) => (
        <MessageItem key={m.id} m={m} onSpeak={onSpeak} />
      ))}
    </div>
  );
}

function ReferencesPanel({ items }) {
  return (
    <div className="refs-panel">
      <div className="refs-title">📚 References:</div>
      <ul className="refs-list">
        {items.map((it, idx) => (
          <li key={idx}>
            {it.href ? (
              <a href={it.href} target="_blank" rel="noreferrer noopener">
                {it.label}
              </a>
            ) : (
              it.label
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

// Simple molecule name to SMILES mapping
const moleculeSmiles = {
  'benzene': 'c1ccccc1',
  'water': 'O',
  'methane': 'C',
  'ethanol': 'CCO',
  'acetic acid': 'CC(=O)O',
  'phosphoric acid': 'OP(=O)(O)O',
  'ammonia': 'N',
  'carbon dioxide': 'O=C=O',
  'glucose': 'C([C@@H]1[C@H]([C@@H]([C@H]([C@H](O1)O)O)O)O)O',
  'caffeine': 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C',
  'nitric acid': 'O[N+]([O-])=O',
  'sulfuric acid': 'OS(=O)(=O)O',
  'hydrochloric acid': 'Cl',
  'sodium chloride': '[Na+].[Cl-]',
  'carbon monoxide': '[C-]#[O+]',
  'methanol': 'CO',
  'formaldehyde': 'C=O',
  'acetone': 'CC(=O)C',
  'toluene': 'Cc1ccccc1',
  'phenol': 'Oc1ccccc1',
  'citric acid': 'C(C(=O)O)C(CC(=O)O)(C(=O)O)O',
  'nitrous acid': 'ON=O',
  'hydrogen peroxide': 'OO'
};

function MoleculeCard({ name, smiles, width = 220, height = 160 }) {
  const ref = useRef(null);
  const [actualSmiles, setActualSmiles] = useState(smiles);
  const [error, setError] = useState(null);
  const [isRendering, setIsRendering] = useState(false);
  
  useEffect(() => {
    if (!actualSmiles && name) {
      const resolved = moleculeSmiles[name.toLowerCase()];
      if (resolved) {
        setActualSmiles(resolved);
      }
    }
  }, [name, actualSmiles]);

  useEffect(() => {
    if (!actualSmiles) return;
    
    setIsRendering(true);
    setError(null);
    
    const renderMolecule = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/draw-molecule', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            smiles: actualSmiles,
            name: name,
            format: 'svg',
            width: width,
            height: height
          })
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const svgContent = await response.text();
        
        if (ref.current) {
          ref.current.innerHTML = svgContent;
        }
        setError(null);
        
      } catch (err) {
        setError('Backend rendering failed. Using simple diagram.');
        if (ref.current) {
          ref.current.innerHTML = createSimpleMoleculeSVG(name, actualSmiles);
        }
      } finally {
        setIsRendering(false);
      }
    };
    
    renderMolecule();
  }, [actualSmiles, name, width, height]);
  
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>
        {name}{actualSmiles ? ` — ${actualSmiles}` : ' (SMILES not found)'}
        {isRendering && <span style={{ color: '#3b82f6' }}> (rendering...)</span>}
        {error && (
          <span style={{ color: '#ef4444' }}>
            ({error})
            {error.includes('Backend rendering failed') && (
              <button 
                onClick={() => {
                  setError(null);
                  setIsRendering(true);
                  const event = new Event('retry-render');
                  window.dispatchEvent(event);
                }} 
                style={{ 
                  marginLeft: '8px', 
                  padding: '2px 6px', 
                  fontSize: '10px', 
                  background: '#3b82f6', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '3px',
                  cursor: 'pointer'
                }}
              >
                Retry
              </button>
            )}
          </span>
        )}
      </div>
      <div 
        ref={ref} 
        style={{ 
          width, 
          height, 
          background: '#fff', 
          border: '1px solid #e5e7eb',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }} 
      />
    </div>
  );
}

// Simple SVG molecule renderer for common molecules
function createSimpleMoleculeSVG(name, smiles) {
  const molecules = {
    'benzene': {
      svg: `
        <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
          <circle cx="100" cy="100" r="60" fill="none" stroke="#333" stroke-width="3"/>
          <circle cx="100" cy="40" r="8" fill="#333"/>
          <circle cx="140" cy="70" r="8" fill="#333"/>
          <circle cx="140" cy="130" r="8" fill="#333"/>
          <circle cx="100" cy="160" r="8" fill="#333"/>
          <circle cx="60" cy="130" r="8" fill="#333"/>
          <circle cx="60" cy="70" r="8" fill="#333"/>
          <line x1="100" y1="40" x2="140" y2="70" stroke="#333" stroke-width="2"/>
          <line x1="140" y1="70" x2="140" y2="130" stroke="#333" stroke-width="2"/>
          <line x1="140" y1="130" x2="100" y2="160" stroke="#333" stroke-width="2"/>
          <line x1="100" y1="160" x2="60" y2="130" stroke="#333" stroke-width="2"/>
          <line x1="60" y1="130" x2="60" y2="70" stroke="#333" stroke-width="2"/>
          <line x1="60" y1="70" x2="100" y2="40" stroke="#333" stroke-width="2"/>
          <text x="100" y="190" text-anchor="middle" font-family="Arial" font-size="12" fill="#666">Benzene (C₆H₆)</text>
        </svg>
      `
    },
    'water': {
      svg: `
        <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
          <circle cx="100" cy="100" r="12" fill="#FF6B6B"/>
          <circle cx="80" cy="80" r="6" fill="#4ECDC4"/>
          <circle cx="120" cy="80" r="6" fill="#4ECDC4"/>
          <line x1="100" y1="100" x2="80" y2="80" stroke="#333" stroke-width="2"/>
          <line x1="100" y1="100" x2="120" y2="80" stroke="#333" stroke-width="2"/>
          <text x="100" y="140" text-anchor="middle" font-family="Arial" font-size="12" fill="#666">Water (H₂O)</text>
        </svg>
      `
    },
    'methane': {
      svg: `
        <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
          <circle cx="100" cy="100" r="10" fill="#333"/>
          <circle cx="100" cy="60" r="6" fill="#4ECDC4"/>
          <circle cx="140" cy="100" r="6" fill="#4ECDC4"/>
          <circle cx="100" cy="140" r="6" fill="#4ECDC4"/>
          <circle cx="60" cy="100" r="6" fill="#4ECDC4"/>
          <line x1="100" y1="100" x2="100" y2="60" stroke="#333" stroke-width="2"/>
          <line x1="100" y1="100" x2="140" y2="100" stroke="#333" stroke-width="2"/>
          <line x1="100" y1="100" x2="100" y2="140" stroke="#333" stroke-width="2"/>
          <line x1="100" y1="100" x2="60" y2="100" stroke="#333" stroke-width="2"/>
          <text x="100" y="170" text-anchor="middle" font-family="Arial" font-size="12" fill="#666">Methane (CH₄)</text>
        </svg>
      `
    },
    'ethanol': {
      svg: `
        <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
          <circle cx="80" cy="100" r="8" fill="#333"/>
          <circle cx="120" cy="100" r="8" fill="#333"/>
          <circle cx="80" cy="60" r="6" fill="#4ECDC4"/>
          <circle cx="80" cy="140" r="6" fill="#4ECDC4"/>
          <circle cx="60" cy="100" r="6" fill="#4ECDC4"/>
          <circle cx="120" cy="60" r="6" fill="#4ECDC4"/>
          <circle cx="120" cy="140" r="6" fill="#4ECDC4"/>
          <circle cx="140" cy="100" r="6" fill="#4ECDC4"/>
          <circle cx="120" cy="40" r="6" fill="#FF6B6B"/>
          <line x1="80" y1="100" x2="120" y2="100" stroke="#333" stroke-width="2"/>
          <line x1="80" y1="100" x2="80" y2="60" stroke="#333" stroke-width="2"/>
          <line x1="80" y1="100" x2="80" y2="140" stroke="#333" stroke-width="2"/>
          <line x1="80" y1="100" x2="60" y2="100" stroke="#333" stroke-width="2"/>
          <line x1="120" y1="100" x2="120" y2="60" stroke="#333" stroke-width="2"/>
          <line x1="120" y1="100" x2="120" y2="140" stroke="#333" stroke-width="2"/>
          <line x1="120" y1="100" x2="140" y2="100" stroke="#333" stroke-width="2"/>
          <line x1="120" y1="60" x2="120" y2="40" stroke="#333" stroke-width="2"/>
          <text x="100" y="180" text-anchor="middle" font-family="Arial" font-size="12" fill="#666">Ethanol (C₂H₅OH)</text>
        </svg>
      `
    }
  };
  
  const molecule = molecules[name.toLowerCase()];
  if (molecule) {
    return molecule.svg;
  }
  
  return `
    <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
      <rect x="50" y="50" width="100" height="100" fill="none" stroke="#ccc" stroke-width="2" stroke-dasharray="5,5"/>
      <text x="100" y="100" text-anchor="middle" font-family="Arial" font-size="14" fill="#666">${name}</text>
      <text x="100" y="120" text-anchor="middle" font-family="Arial" font-size="10" fill="#999">${smiles}</text>
      <text x="100" y="140" text-anchor="middle" font-family="Arial" font-size="10" fill="#999">Structure not available</text>
    </svg>
  `;
}

// Markdown rendering helper
function renderMarkdown(text) {
  if (!text) return '';
  try {
    const cleaned = text.replace(/```(?:json)?\s*\{[^}]*"tool"[^}]*\}\s*```/g, '');
    const html = marked.parse(cleaned, { breaks: true });
    return DOMPurify.sanitize(html);
  } catch (_) {
    return text;
  }
}

// Parse assistant content into answer and up to 2 references
function parseAssistantContent(raw) {
  const text = (raw || '').trim();
  if (!text) return { answerText: '', references: [], plainText: '' };

  const headerRegex = /(\n|\r|^)\s*(Sources?:|References?:)\s*\n/i;
  let answerPart = text;
  let refsPart = '';
  const match = text.match(headerRegex);
  if (match) {
    const idx = text.toLowerCase().lastIndexOf(match[2].toLowerCase());
    if (idx >= 0) {
      answerPart = text.slice(0, idx).trim();
      refsPart = text.slice(idx).replace(headerRegex, '').trim();
    }
  }

  const lines = refsPart
    .split(/\n+/)
    .map(l => l.replace(/^[-*\d\s\[\]]+/, '').trim())
    .filter(l => l.length > 0)
    .slice(0, 2);

  const urlRegex = /(https?:\/\/[^\s)]+)|(www\.[^\s)]+)/i;
  const references = lines.map(l => {
    const m = l.match(urlRegex);
    const href = m ? (m[0].startsWith('http') ? m[0] : `https://${m[0]}`) : undefined;
    const label = l.length > 150 ? (l.slice(0, 147) + '…') : l;
    return { label, href };
  });

  const plainText = answerPart
    .replace(/#{1,6}\s+/g, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/`(.*?)`/g, '$1')
    .replace(/\[(.*?)\]\(.*?\)/g, '$1')
    .replace(/\n+/g, ' ')
    .trim();

  return { answerText: answerPart, references, plainText };
}

// Export for use in main HTML file
window.MessageList = MessageList;
window.ReferencesPanel = ReferencesPanel;
window.MoleculeCard = MoleculeCard;
})();

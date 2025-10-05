/**
 * Sidebar component with chat list and navigation
 */

;(function(){
const { useState } = React;

function Sidebar({ chats, selectedChatId, onNewChat, onSelectChat, onDeleteChat }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <NewChatButton onClick={onNewChat} />
      </div>
      <ConversationList 
        chats={chats} 
        selectedChatId={selectedChatId} 
        onSelectChat={onSelectChat} 
        onDeleteChat={onDeleteChat} 
      />
      <div className="sidebar-footer">
        <AppFooterVersion versionText="Chem Tutor v2.0" />
      </div>
    </aside>
  );
}

function NewChatButton({ onClick }) {
  return (
    <button className="btn btn-primary btn-new-chat" onClick={onClick}>
      <span className="icon">+</span>
      <span>New Chat</span>
    </button>
  );
}

function ConversationList({ chats, selectedChatId, onSelectChat, onDeleteChat }) {
  return (
    <div className="conversation-list">
      {chats.map((c) => (
        <ConversationListItem
          key={c.id}
          title={c.title || 'New Chat'}
          subtitle={`${c.messages?.length || 0} messages`}
          selected={c.id === selectedChatId}
          onClick={() => onSelectChat(c.id)}
          onDelete={() => onDeleteChat(c.id)}
        />
      ))}
    </div>
  );
}

function ConversationListItem({ title, subtitle, selected, onClick, onDelete }) {
  return (
    <div 
      className={"conversation-item" + (selected ? " selected" : "")} 
      onClick={onClick} 
      style={{ cursor: 'pointer' }}
    >
      <div className="conversation-icon">💬</div>
      <div className="conversation-texts">
        <div className="conversation-title">{title}</div>
        <div className="conversation-subtitle">{subtitle}</div>
      </div>
      <div className="conversation-actions">
        <button 
          className="icon-btn delete-btn" 
          title="Delete chat" 
          aria-label="Delete chat" 
          onClick={(e) => { 
            e.stopPropagation(); 
            onDelete && onDelete(); 
          }}
        >
          🗑️
        </button>
      </div>
    </div>
  );
}

function AppFooterVersion({ versionText }) {
  return <div className="version-text">{versionText}</div>;
}

// Export for use in main HTML file
window.Sidebar = Sidebar;
window.NewChatButton = NewChatButton;
window.ConversationList = ConversationList;
window.ConversationListItem = ConversationListItem;
window.AppFooterVersion = AppFooterVersion;
})();

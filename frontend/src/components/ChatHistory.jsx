import React, { useState } from 'react';
import { IoCopyOutline, IoDownloadOutline, IoTrashOutline, IoArrowBackOutline, IoSearchOutline } from "react-icons/io5";

const ChatHistory = ({ chatHistory, onGoBack, onDeleteChat }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedChat, setSelectedChat] = useState(null);

  const filteredChats = chatHistory.filter(chat =>
    chat.query.toLowerCase().includes(searchTerm.toLowerCase()) ||
    chat.response.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    console.log("Copied code to clipboard");
  };

  const downloadCode = (code, chatId) => {
    const element = document.createElement("a");
    const file = new Blob([code], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = `st_code_${chatId}.st`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const truncateText = (text, maxLength = 100) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  if (selectedChat) {
    return (
      <div className="app-container">
        <div className="card">
          <div className="chat-detail-header">
            <button onClick={() => setSelectedChat(null)} className="btn btn-secondary">
              <IoArrowBackOutline /> Back to List
            </button>
            <button onClick={onGoBack} className="btn btn-secondary">
              Back to Main
            </button>
          </div>

          <div className="chat-detail">
            <div className="chat-timestamp">
              Generated on: {formatTimestamp(selectedChat.timestamp)}
            </div>

            <div className="chat-section">
              <h3 className="section-title">Original Query:</h3>
              <div className="query-box">
                {selectedChat.query}
              </div>
            </div>

            {selectedChat.feedback && (
              <div className="chat-section">
                <h3 className="section-title">Feedback Provided:</h3>
                <div className="feedback-box">
                  {selectedChat.feedback}
                </div>
              </div>
            )}

            <div className="chat-section">
              <div className="code-header">
                <h3 className="section-title">Generated ST Code:</h3>
                <div className="code-actions">
                  <button onClick={() => copyCode(selectedChat.response)} className="btn-primary btn-icon" title="Copy Code">
                    <IoCopyOutline />
                  </button>
                  <button onClick={() => downloadCode(selectedChat.response, selectedChat.id)} className="btn-primary btn-icon" title="Download Code">
                    <IoDownloadOutline />
                  </button>
                  <button onClick={() => onDeleteChat(selectedChat.id)} className="btn-danger btn-icon" title="Delete Chat">
                    <IoTrashOutline />
                  </button>
                </div>
              </div>
              <div className="code-editor">
                <pre className="code-block">
                  <code>{selectedChat.response}</code>
                </pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <div className="card">
        <div className="history-header">
          <button onClick={onGoBack} className="btn btn-secondary">
            <IoArrowBackOutline /> Back to Main
          </button>
          <h1 className="title">Chat History</h1>
        </div>

        <div className="search-container">
          <div className="search-input-wrapper">
            <IoSearchOutline className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search in chat history..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="chat-list">
          {filteredChats.length === 0 ? (
            <div className="no-chats-message">
              {chatHistory.length === 0 ? 'No chat history available.' : 'No chats match your search.'}
            </div>
          ) : (
            filteredChats.map((chat) => (
              <div key={chat.id} className="chat-item">
                <div className="chat-item-header">
                  <div className="chat-timestamp-small">
                    {formatTimestamp(chat.timestamp)}
                  </div>
                  <div className="chat-item-actions">
                    <button onClick={() => copyCode(chat.response)} className="btn-icon btn-small" title="Copy Code">
                      <IoCopyOutline />
                    </button>
                    <button onClick={() => downloadCode(chat.response, chat.id)} className="btn-icon btn-small" title="Download Code">
                      <IoDownloadOutline />
                    </button>
                    <button onClick={() => onDeleteChat(chat.id)} className="btn-icon btn-small btn-danger" title="Delete Chat">
                      <IoTrashOutline />
                    </button>
                  </div>
                </div>
                
                <div className="chat-item-content">
                  <div className="chat-query">
                    <strong>Query:</strong> {truncateText(chat.query)}
                  </div>
                  {chat.feedback && (
                    <div className="chat-feedback-preview">
                      <strong>Feedback:</strong> {truncateText(chat.feedback, 50)}
                    </div>
                  )}
                  <div className="chat-response-preview">
                    <strong>Response:</strong> {truncateText(chat.response, 80)}
                  </div>
                </div>

                <button
                  onClick={() => setSelectedChat(chat)}
                  className="btn btn-primary btn-view-full"
                >
                  View Full Chat
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatHistory;
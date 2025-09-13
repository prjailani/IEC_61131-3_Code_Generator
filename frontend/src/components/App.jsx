import React, { useState, useEffect } from 'react';
import Users from './users.jsx';
import ChatHistory from './ChatHistory.jsx';
import { 
  IoCopyOutline, 
  IoDownloadOutline, 
  IoSendOutline, 
  IoSaveOutline, 
  IoChatboxOutline 
} from "react-icons/io5";
import LOGO from '../assets/logo.png';

export default function App({ onLogout }) {
  const [currentPage, setCurrentPage] = useState('main');
  const [narrativeText, setNarrativeText] = useState('');
  const [generatedCode, setGeneratedCode] = useState('');
  const [feedback, setFeedback] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [error, setError] = useState(null);
  const [interCode, setInterCode] = useState([])
    const [refinedQuery, setRefinedQuery] = useState('')



const user = JSON.parse(localStorage.getItem('user') || '{}');
const userId = user.id;  

console.log(userId)
  // Fetch chat history when page loads
  useEffect(() => {
    async function loadHistory() {
      try {
        const res = await fetch(`http://127.0.0.1:8000/chat-history/${userId}`);
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const data = await res.json();
        setChatHistory(data.chatHistory || []);
      } catch (err) {
        console.error('Error fetching history:', err);
      }
    }
    loadHistory();
  }, [userId]);

  // === API Calls ===
  async function saveChatEntry(narrative, code, feedbackText) {
    try {
      const res = await fetch('http://127.0.0.1:8000/save-chat-entry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          query: 'Your : '+narrative +"\nRefine Query : "+refinedQuery,
          response: code,
          feedback: feedbackText
          
        })
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      return data.chatEntry;
    } catch (err) {
      console.error('Error saving chat entry:', err);
    }
  }

  // === Helpers ===
  const copier = () => {
    navigator.clipboard.writeText(generatedCode);
  };

  const downloadCode = () => {
    const element = document.createElement("a");
    const file = new Blob([generatedCode], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = "generated_st_code.st";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  // === Main Actions ===
  const handleGenerateCode = async () => {
    if (!narrativeText.trim()) return;
    setIsLoading(true);
    setError(null);
    setGeneratedCode('');
    setRefinedQuery('');

      ([])

    try {
      const response = await fetch('http://127.0.0.1:8000/generate-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ narrative: narrativeText })
      });
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      if (data.code) {
        setGeneratedCode(data.code);
        setInterCode(data.interCode);
        setRefinedQuery(data.Refine);
      } else {
        setError('No code returned from API.');
      }
    } catch (e) {
      setError(`Failed to generate code`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerateWithFeedback = async () => {
    if (!feedback.trim()) return;
    setIsRegenerating(true);
    setError(null);
    setRefinedQuery('')


    const combinedQuery = `$Feedback for improvement: ${feedback}`;
    try {
      const response = await fetch('http://127.0.0.1:8000/regenerate-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: narrativeText,feedback: combinedQuery , intermediateCode : interCode})
      });
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      if (data.code) {
        setGeneratedCode(data.code);
        setInterCode(data.interCode);
        setRefinedQuery(data.Refine)

        setFeedback('');
      } else {
        setError('No regenerated code returned from API.');
      }
    } catch (e) {
      setError(`Failed to regenerate code`);
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleSaveChat = async () => {
    if (!narrativeText.trim() || !generatedCode.trim()) {
      setError('Both query and generated code required.');
      return;
    }
    const newChat = await saveChatEntry(narrativeText, generatedCode, feedback || null);
    if (newChat) {
      setChatHistory(prev => [newChat, ...prev]);
      setError('Chat saved successfully!');
      setTimeout(() => setError(null), 2000);
    }
  };

  // === Render pages ===
  if (currentPage === 'users') {
    return <Users onGoBack={() => setCurrentPage('main')} />;
  }

  if (currentPage === 'history') {
    return (
      <ChatHistory
        chatHistory={chatHistory}
        onGoBack={() => setCurrentPage('main')}
        onDeleteChat={async (chatId) => {
          try {
            const response = await fetch(`http://127.0.0.1:8000/delete-chat/${chatId}`, {
              method: 'DELETE'
            });
            if (response.ok) {
              setChatHistory(prev => prev.filter(chat => chat.id !== chatId));
            } else {
              setChatHistory(prev => prev.filter(chat => chat.id !== chatId));
            }
          } catch (error) {
            setChatHistory(prev => prev.filter(chat => chat.id !== chatId));
          }
        }}
      />
    );
  }

  return (
    <div className="app-container">
      <div className='logo_container'>
        <div className="logoplaceholder">
          <img src={LOGO} alt="Logo" />
        </div>
      </div>

      <div className="card">
        <div className="switch-container">
          <button onClick={() => setCurrentPage('users')} className="btn btn-secondary">
            Go to Variables
          </button>
          <button onClick={() => setCurrentPage('history')} className="btn btn-secondary">
            <IoChatboxOutline /> Chat History
          </button>
          <button onClick={onLogout} className="btn btn-secondary">Logout</button>
        </div>

        <h1 className="title">
          Txt2PLC - IEC 61131-3 Code Generator
        </h1>

        <div>
          <textarea
            className="input-textarea"
            placeholder="Describe your automation logic..."
            value={narrativeText}
            onChange={(e) => setNarrativeText(e.target.value)}
          />
        </div>

        <div className="generate-button-container">
          <button
            onClick={handleGenerateCode}
            disabled={isLoading || !narrativeText.trim()}
            className="btn btn-primary btn-generate"
          >
            {isLoading ? 'Generating...' : 'Generate Code'}
          </button>
        </div>

        {error && (
          <div className={`error-box ${error.includes('success') ? 'success-box' : ''}`}>
            <p className="error-message">{error}</p>
          </div>
        )}

        {generatedCode && (
          <>
            <div className="code-box">
              <div className="code-header">
                <h2 className="code-title">Generated IEC 61131-3 Structured Text</h2>
                <div className="code-actions">
                  <button onClick={copier} className='btn-primary btn-icon' title="Copy Code">
                    <IoCopyOutline />
                  </button>
                  <button onClick={downloadCode} className='btn-primary btn-icon' title="Download Code">
                    <IoDownloadOutline />
                  </button>
                  <button onClick={handleSaveChat} className='btn-primary btn-icon' title="Save Chat">
                    <IoSaveOutline />
                  </button>
                </div>
              </div>
              <div className="code-editor">
                <pre className="code-block">
                  <code className="codeBox">{generatedCode}</code>
                </pre>
              </div>
            </div>

            <div className="feedback-container">
              <h3 className="feedback-title">Need improvements? Share your feedback:</h3>
              <div className="feedback-input-container">
                <textarea
                  className="feedback-textarea"
                  placeholder="Your feedback here..."
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                />
                <button
                  onClick={handleRegenerateWithFeedback}
                  disabled={isRegenerating || !feedback.trim()}
                  className="btn btn-primary btn-send"
                  title="Regenerate with Feedback"
                >
                  {isRegenerating ? 'Regenerating...' : <IoSendOutline />}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

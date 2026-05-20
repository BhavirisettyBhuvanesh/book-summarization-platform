import { useState, useEffect } from 'react';
import { Routes, Route, Link, useNavigate, Navigate } from 'react-router-dom';
import { BookOpen, FileText, History as HistoryIcon, LogOut, Search, User } from 'lucide-react';
import './index.css';
import DocumentUploader from './components/DocumentUploader';
import QueryInterface from './components/QueryInterface';
import Dashboard from './components/Dashboard';
import Auth from './components/Auth';
import History from './components/History';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [userEmail, setUserEmail] = useState(localStorage.getItem('userEmail'));
  const [currentDoc, setCurrentDoc] = useState(null);
  const [queryResult, setQueryResult] = useState(null);
  const navigate = useNavigate();

  const handleLoginSuccess = (newToken, email) => {
    setToken(newToken);
    setUserEmail(email);
    navigate('/');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userEmail');
    setToken(null);
    setUserEmail(null);
    navigate('/login');
  };

  const handleUploadSuccess = (doc_id, file_name) => {
    setCurrentDoc({ id: doc_id, name: file_name });
    setQueryResult(null);
  };

  const handleQueryResult = (data) => {
    setQueryResult(data);
  };

  // Protected Layout Component
  const MainApp = () => (
    <div className="container" style={{ paddingBottom: '5rem' }}>
      <header className="flex-center" style={{ flexDirection: 'column', gap: '1rem', marginTop: '2rem' }}>
        <div className="glass-panel flex-center" style={{ padding: '1rem', borderRadius: '50%' }}>
          <BookOpen size={40} color="var(--accent-blue)" />
        </div>
        <h1 className="gradient-text" style={{ fontSize: '3rem', fontWeight: 'bold' }}>
          Intel Summarization
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          AI-Powered Book Analysis & RAG Pipeline Comparison
        </p>
      </header>
      
      <main style={{ marginTop: '3rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem' }}>
        {!currentDoc ? (
          <DocumentUploader onUploadSuccess={handleUploadSuccess} />
        ) : (
          <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem' }}>
            <div className="glass-panel" style={{ padding: '1rem 2rem', display: 'flex', alignItems: 'center', gap: '12px', border: '1px solid var(--accent-purple)' }}>
               <FileText color="var(--accent-purple)" />
               <span>Active Document: <strong>{currentDoc.name}</strong></span>
            </div>
            <QueryInterface docId={currentDoc.id} onQueryResult={handleQueryResult} />
          </div>
        )}

        {queryResult && (
          <Dashboard data={queryResult} />
        )}
      </main>
    </div>
  );

  return (
    <div style={{ minHeight: '100vh' }}>
      {/* Navbar */}
      {token && (
        <nav style={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          background: 'rgba(15, 23, 42, 0.8)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
          padding: '0.8rem 2rem'
        }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
              <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'white', textDecoration: 'none', fontWeight: '700' }}>
                <BookOpen size={20} color="var(--accent-blue)" />
                <span>RAG.AI</span>
              </Link>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem' }}>
                  <Search size={16} /> Search
                </Link>
                <Link to="/history" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem' }}>
                  <HistoryIcon size={16} /> History
                </Link>
              </div>
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#94a3b8', fontSize: '0.85rem' }}>
                <User size={16} /> {userEmail}
              </div>
              <button 
                onClick={handleLogout}
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  color: '#fca5a5',
                  padding: '0.5rem 1rem',
                  borderRadius: '0.5rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontSize: '0.85rem'
                }}
              >
                <LogOut size={16} /> Logout
              </button>
            </div>
          </div>
        </nav>
      )}

      <Routes>
        <Route path="/login" element={!token ? <Auth onLoginSuccess={handleLoginSuccess} /> : <Navigate to="/" />} />
        <Route path="/" element={token ? <MainApp /> : <Navigate to="/login" />} />
        <Route path="/history" element={token ? <History /> : <Navigate to="/login" />} />
      </Routes>
    </div>
  );
}

export default App;

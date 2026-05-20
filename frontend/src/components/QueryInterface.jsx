import { useState } from 'react';
import { Send, Loader2, Sparkles } from 'lucide-react';
import axios from 'axios';

export default function QueryInterface({ docId, onQueryResult }) {
  const [question, setQuestion] = useState('');
  const [isQuerying, setIsQuerying] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim() || !docId) return;

    setIsQuerying(true);
    setError('');
    
    // Clear the previous results on the screen before starting the new query
    onQueryResult(null);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post('http://localhost:8001/query', {
        doc_id: docId,
        question: question.trim()
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      onQueryResult(response.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to analyze document. Please try again.');
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <div className="glass-panel" style={{ width: '100%', maxWidth: '800px', margin: '0 auto', padding: '1.5rem' }}>
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        
        <div style={{ flexGrow: 1, position: 'relative' }}>
          <Sparkles 
            size={20} 
            color="var(--accent-purple)" 
            style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)' }} 
          />
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about the document..."
            disabled={isQuerying}
            style={{
              width: '100%',
              padding: '1rem 1rem 1rem 3.5rem',
              borderRadius: '12px',
              border: '1px solid var(--glass-border)',
              background: 'rgba(0,0,0,0.2)',
              color: 'var(--text-primary)',
              fontSize: '1rem',
              outline: 'none'
            }}
          />
        </div>

        <button 
          type="submit"
          disabled={isQuerying || !question.trim()}
          style={{
            background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))',
            color: 'white',
            border: 'none',
            padding: '1rem 2rem',
            borderRadius: '12px',
            fontSize: '1rem',
            fontWeight: 'bold',
            cursor: (isQuerying || !question.trim()) ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            opacity: (isQuerying || !question.trim()) ? 0.7 : 1,
            transition: 'opacity 0.2s'
          }}
        >
          {isQuerying ? (
            <><Loader2 className="animate-spin" size={20} /> Analyzing...</>
          ) : (
            <><Send size={20} /> Ask AI</>
          )}
        </button>

      </form>

      {error && (
        <p style={{ color: '#f87171', marginTop: '1rem', textAlign: 'center' }}>{error}</p>
      )}
    </div>
  );
}

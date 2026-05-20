import { useState, useEffect } from 'react';
import { Clock, MessageSquare, ChevronRight, BarChart3, AlertCircle } from 'lucide-react';

const History = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch('http://localhost:8001/history', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setHistory(data);
      } else {
        setError('Failed to load history');
      }
    } catch (err) {
      setError('Connection error');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return '#10b981'; // Green
    if (score >= 0.5) return '#f59e0b'; // Amber
    return '#ef4444'; // Red
  };

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '3rem' }}>
      <p style={{ color: '#94a3b8' }}>Loading your history...</p>
    </div>
  );

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
        <Clock size={28} color="#818cf8" />
        <h1 style={{ fontSize: '1.8rem', fontWeight: '700' }}>Query History</h1>
      </div>

      {error && (
        <div className="glass-panel" style={{ padding: '1rem', color: '#fca5a5', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {history.length === 0 ? (
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
          <MessageSquare size={48} color="#334155" style={{ marginBottom: '1rem' }} />
          <p style={{ color: '#94a3b8' }}>No history found. Ask your first question to see it here!</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {history.map((item) => (
            <div key={item.id} className="glass-panel" style={{ 
              padding: '1.5rem', 
              borderRadius: '1rem',
              transition: 'transform 0.2s, border-color 0.2s',
              cursor: 'pointer',
              border: '1px solid rgba(255,255,255,0.05)'
            }}
            onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateX(10px)';
              e.currentTarget.style.borderColor = 'rgba(129, 140, 248, 0.4)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateX(0)';
              e.currentTarget.style.borderColor = 'rgba(255,255,255,0.05)';
            }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: expandedId === item.id ? '1rem' : '0' }}>
                <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                  <ChevronRight 
                    size={20} 
                    color="#818cf8" 
                    style={{ 
                      transform: expandedId === item.id ? 'rotate(90deg)' : 'rotate(0deg)',
                      transition: 'transform 0.2s ease-in-out',
                      marginTop: '0.2rem'
                    }} 
                  />
                  <div>
                    <p style={{ color: '#818cf8', fontSize: '0.75rem', fontWeight: '600', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                      {new Date(item.timestamp).toLocaleDateString()} at {new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </p>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0', color: '#f1f5f9' }}>
                      {item.question}
                    </h3>
                  </div>
                </div>
                <div style={{ 
                  background: 'rgba(129, 140, 248, 0.1)', 
                  padding: '0.4rem 0.8rem', 
                  borderRadius: '2rem',
                  fontSize: '0.75rem',
                  color: '#818cf8',
                  fontWeight: '600',
                  border: '1px solid rgba(129, 140, 248, 0.2)'
                }}>
                  {item.pipeline_used.replace('_', ' ').toUpperCase()}
                </div>
              </div>

              {expandedId === item.id && (
                <div style={{ marginTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '1.5rem' }}>
                  {item.answer && (
                    <div style={{ 
                      background: 'rgba(15, 23, 42, 0.5)', 
                      padding: '1rem', 
                      borderRadius: '0.5rem',
                      borderLeft: '4px solid #818cf8',
                      marginBottom: '1.5rem'
                    }}>
                      <p style={{ color: '#cbd5e1', fontSize: '0.9rem', lineHeight: '1.5' }}>
                        {item.answer}
                      </p>
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                    {Object.entries(item.scores).filter(([key]) => key !== 'overall_score').map(([key, value]) => (
                      <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: getScoreColor(value) }}></div>
                        <span style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'capitalize' }}>
                          {key.replace('_', ' ')}: 
                          <strong style={{ color: '#f1f5f9', marginLeft: '0.3rem' }}>{(value * 100).toFixed(0)}%</strong>
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default History;

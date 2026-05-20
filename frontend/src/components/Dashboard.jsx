import { useState } from 'react';
import { Trophy, Clock, CheckCircle2, Zap, BarChart3, ShieldCheck, Layers, FileText, Activity } from 'lucide-react';

export default function Dashboard({ data }) {
  const [activeTab, setActiveTab] = useState('summary'); // 'summary' or 'performance'
  
  if (!data) return null;

  const pipelines = [
    { id: 'basic_rag', title: 'Basic RAG', color: '#4ade80', icon: <CheckCircle2 color="#4ade80" /> },
    { id: 'page_index_rag', title: 'Page-Index RAG', color: '#3b82f6', icon: <Zap color="#3b82f6" /> },
    { id: 'hybrid_rag', title: 'Hybrid RAG', color: '#a855f7', icon: <Trophy color="#a855f7" /> }
  ];

  const performanceData = Object.entries(data.results).map(([id, res]) => ({
    name: id.replace(/_/g, ' ').toUpperCase(),
    time: res.response_time_seconds,
    color: id === 'hybrid_rag' ? '#a855f7' : (id === 'page_index_rag' ? '#3b82f6' : '#4ade80')
  }));
  const maxTime = Math.max(...performanceData.map(d => d.time));

  return (
    <div style={{ width: '100%', maxWidth: '1200px', margin: '2rem auto', padding: '0 1rem' }}>
      
      {/* Top Winner Banner */}
      <div className="glass-panel" style={{ 
        padding: '2rem', 
        marginBottom: '1rem', 
        textAlign: 'center', 
        border: '1px solid var(--accent-blue)',
        background: 'linear-gradient(180deg, rgba(59, 130, 246, 0.1) 0%, transparent 100%)'
      }}>
        <h2 style={{ fontSize: '1.4rem', marginBottom: '0.8rem', color: 'var(--text-secondary)', fontWeight: 'normal' }}>Analysis for: <span style={{ color: 'var(--text-primary)' }}>"{data.question}"</span></h2>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', color: 'var(--accent-purple)' }}>
          <Trophy size={28} />
          <span style={{ fontSize: '1.5rem', fontWeight: 'bold', letterSpacing: '1.5px' }}>
             {data.best_pipeline.replace(/_/g, ' ').toUpperCase()} WINS ON QUALITY
          </span>
        </div>
      </div>

      {/* TAB SWITCHER */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginBottom: '2rem' }}>
        <button 
          onClick={() => setActiveTab('summary')}
          style={{ 
            padding: '0.8rem 1.5rem', 
            borderRadius: '12px', 
            border: activeTab === 'summary' ? '1px solid var(--accent-blue)' : '1px solid var(--glass-border)',
            background: activeTab === 'summary' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.05)',
            color: activeTab === 'summary' ? 'white' : 'var(--text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.3s ease'
          }}>
          <FileText size={18} /> Summary Insights
        </button>
        <button 
          onClick={() => setActiveTab('performance')}
          style={{ 
            padding: '0.8rem 1.5rem', 
            borderRadius: '12px', 
            border: activeTab === 'performance' ? '1px solid var(--accent-purple)' : '1px solid var(--glass-border)',
            background: activeTab === 'performance' ? 'rgba(168, 85, 247, 0.2)' : 'rgba(255,255,255,0.05)',
            color: activeTab === 'performance' ? 'white' : 'var(--text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.3s ease'
          }}>
          <Activity size={18} /> Performance Evaluation
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        
        {activeTab === 'summary' ? (
          /* TAB 1: SUMMARY INSIGHTS */
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '1.5rem' }}>
            {pipelines.map(pipe => {
              const result = data.results[pipe.id];
              const isWinner = data.best_pipeline === pipe.id;
              const scores = result.scores;
              
              return (
                <div key={pipe.id} className="glass-panel" style={{ 
                  padding: '1.5rem', 
                  border: isWinner ? '2px solid var(--accent-purple)' : '1px solid var(--glass-border)',
                  background: isWinner ? 'rgba(168, 85, 247, 0.05)' : 'rgba(255,255,255,0.02)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1.2rem'
                }}>
                  {/* Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                     <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        {pipe.icon}
                        <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{pipe.title}</h3>
                     </div>
                     {isWinner && <span style={{ background: 'var(--accent-purple)', padding: '2px 10px', borderRadius: '10px', fontSize: '0.65rem', fontWeight: 'bold' }}>QUALITY LEADER</span>}
                  </div>

                  {/* Response Preview */}
                  <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.3)', borderRadius: '12px', fontSize: '0.9rem', minHeight: '100px', border: '1px solid rgba(255,255,255,0.05)' }}>
                     {result.answer}
                  </div>

                  {/* Footer Speed */}
                  <div style={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                     <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={14} /> {result.response_time_seconds}s
                     </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          /* TAB 2: PERFORMANCE EVALUATION */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
             
             {/* QUALITY HISTOGRAM COMPARISON */}
             <div className="glass-panel" style={{ padding: '2rem', border: '1px solid rgba(168, 85, 247, 0.2)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '2rem' }}>
                  <Layers size={24} color="var(--accent-purple)" />
                  <h3 style={{ margin: 0 }}>RAG Quality Histogram (Side-by-Side)</h3>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2rem' }}>
                   {/* Metric 1: Faithfulness */}
                   <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                      <div style={{ textAlign: 'center', fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--text-secondary)' }}>FAITHFULNESS (%)</div>
                      <div style={{ height: '150px', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', gap: '10px', paddingBottom: '10px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                         {pipelines.map(p => (
                            <div key={p.id} style={{ 
                               width: '30px', 
                               height: `${(data.results[p.id].scores?.faithfulness || 0) * 100}%`, 
                               background: p.color, 
                               borderRadius: '4px 4px 0 0',
                               position: 'relative',
                               transition: 'height 0.5s ease'
                            }}>
                               <span style={{ position: 'absolute', top: '-20px', left: '50%', transform: 'translateX(-50%)', fontSize: '0.7rem', fontWeight: 'bold' }}>
                                  {((data.results[p.id].scores?.faithfulness || 0) * 100).toFixed(0)}
                               </span>
                            </div>
                         ))}
                      </div>
                   </div>

                   {/* Metric 2: Relevance */}
                   <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                      <div style={{ textAlign: 'center', fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--text-secondary)' }}>RELEVANCY (%)</div>
                      <div style={{ height: '150px', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', gap: '10px', paddingBottom: '10px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                         {pipelines.map(p => (
                            <div key={p.id} style={{ 
                               width: '30px', 
                               height: `${(data.results[p.id].scores?.answer_relevancy || 0) * 100}%`, 
                               background: p.color, 
                               borderRadius: '4px 4px 0 0',
                               position: 'relative',
                               transition: 'height 0.5s ease'
                            }}>
                               <span style={{ position: 'absolute', top: '-20px', left: '50%', transform: 'translateX(-50%)', fontSize: '0.7rem', fontWeight: 'bold' }}>
                                  {((data.results[p.id].scores?.answer_relevancy || 0) * 100).toFixed(0)}
                               </span>
                            </div>
                         ))}
                      </div>
                   </div>

                   {/* Metric 3: Diversity */}
                   <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                      <div style={{ textAlign: 'center', fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--text-secondary)' }}>DIVERSITY (%)</div>
                      <div style={{ height: '150px', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', gap: '10px', paddingBottom: '10px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                         {pipelines.map(p => (
                            <div key={p.id} style={{ 
                               width: '30px', 
                               height: `${(data.results[p.id].scores?.retrieval_diversity || 0) * 100}%`, 
                               background: p.color, 
                               borderRadius: '4px 4px 0 0',
                               position: 'relative',
                               transition: 'height 0.5s ease'
                            }}>
                               <span style={{ position: 'absolute', top: '-20px', left: '50%', transform: 'translateX(-50%)', fontSize: '0.7rem', fontWeight: 'bold' }}>
                                  {((data.results[p.id].scores?.retrieval_diversity || 0) * 100).toFixed(0)}
                               </span>
                            </div>
                         ))}
                      </div>
                   </div>
                </div>
                
                {/* Legend */}
                <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', marginTop: '1.5rem', fontSize: '0.8rem' }}>
                   {pipelines.map(p => (
                      <div key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                         <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: p.color }}></div>
                         <span style={{ color: 'var(--text-secondary)', fontWeight: '500' }}>{p.title}</span>
                      </div>
                   ))}
                </div>
             </div>

             {/* PERFORMANCE ANALYTICS */}
             <div className="glass-panel" style={{ padding: '2rem', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '2rem' }}>
                <BarChart3 size={24} color="var(--accent-blue)" />
                <h3 style={{ margin: 0 }}>Efficiency Benchmark (Latency)</h3>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
                  {performanceData.map(d => (
                    <div key={d.name}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                        <span>{d.name}</span>
                        <span style={{ fontWeight: 'bold' }}>{d.time}s</span>
                      </div>
                      <div style={{ height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${(d.time / maxTime) * 100}%`, background: d.color }} />
                      </div>
                    </div>
                  ))}
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '1rem', padding: '1rem', borderLeft: '1px solid rgba(255,255,255,0.1)' }}>
                   <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                      <Zap size={16} color="var(--accent-blue)" style={{ display: 'inline', marginRight: '5px' }} />
                      Note: While <strong>Basic RAG</strong> is faster, <strong>Hybrid RAG</strong> often provides higher <em>Faithfulness</em> by combining multiple search strategies.
                   </p>
                </div>
              </div>
            </div>
          </div>
        )}
        
      </div>
    </div>
  );
}

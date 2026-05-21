import { useState } from 'react';
import { UploadCloud, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import axios from 'axios';

export default function DocumentUploader({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // 'idle' | 'uploading' | 'success' | 'error'
  const [errorMessage, setErrorMessage] = useState('');

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus('idle');
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setStatus('uploading');
    setErrorMessage('');

    // Prepare the file to be sent via HTTP POST
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      // Send the file to our FastAPI backend
      const response = await axios.post('https://book-summarization-platform.onrender.com/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        },
        timeout: 300000 // 5 minutes
      });

      setStatus('success');
      // Pass the doc_id back to App.jsx
      onUploadSuccess(response.data.doc_id, file.name);

    } catch (error) {
      console.error(error);
      setStatus('error');
      setErrorMessage(error.response?.data?.detail || 'Failed to upload document');
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', width: '100%', maxWidth: '600px', margin: '0 auto' }}>

      {/* File Selection Zone */}
      <div
        style={{
          border: '2px dashed var(--glass-border)',
          borderRadius: '12px',
          padding: '3rem 2rem',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          backgroundColor: file ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
          marginBottom: '1.5rem'
        }}
        onClick={() => document.getElementById('file-input').click()}
      >
        <input
          type="file"
          id="file-input"
          accept=".pdf"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />

        <UploadCloud size={48} color={file ? "var(--accent-blue)" : "var(--text-secondary)"} style={{ marginBottom: '1rem' }} />

        {file ? (
          <h3 style={{ color: 'var(--text-primary)' }}>Selected: {file.name}</h3>
        ) : (
          <div>
            <h3 style={{ color: 'var(--text-primary)' }}>Click to upload a PDF</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
              Only PDF format is supported.
            </p>
          </div>
        )}
      </div>

      {/* Upload Button & Status */}
      {file && status !== 'success' && (
        <button
          onClick={handleUpload}
          disabled={status === 'uploading'}
          style={{
            background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '8px',
            fontSize: '1rem',
            fontWeight: 'bold',
            cursor: status === 'uploading' ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            width: '100%',
            opacity: status === 'uploading' ? 0.7 : 1
          }}
        >
          {status === 'uploading' ? (
            <><Loader2 className="animate-spin" size={20} /> Processing Document...</>
          ) : (
            'Upload & Analyze'
          )}
        </button>
      )}

      {/* Success Message */}
      {status === 'success' && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', color: '#4ade80', padding: '1rem' }}>
          <CheckCircle size={24} />
          <span>Upload successful! The document is ready for queries.</span>
        </div>
      )}

      {/* Error Message */}
      {status === 'error' && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', color: '#f87171', padding: '1rem' }}>
          <AlertCircle size={24} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Global CSS for the spinning loader */}
      <style>{`
        .animate-spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

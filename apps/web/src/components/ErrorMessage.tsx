'use client';

import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorMessageProps {
  code: string;
  message: string;
  onReset: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ code, message, onReset }) => {
  const getTitle = (errCode: string) => {
    switch (errCode) {
      case 'INVALID_IMAGE':
        return 'Invalid Image Content';
      case 'NO_FACE':
        return 'No Face Detected';
      case 'MULTIPLE_FACES':
        return 'Multiple Faces Detected';
      case 'FACE_TOO_SMALL':
        return 'Face Resolution Too Small';
      case 'LOW_IMAGE_QUALITY':
        return 'Low Image Quality';
      default:
        return 'Processing Request Failed';
    }
  };

  return (
    <div
      className="glass-card"
      style={{
        maxWidth: '640px',
        margin: '0 auto',
        borderColor: 'rgba(239, 68, 68, 0.4)',
        background: 'rgba(30, 15, 25, 0.85)',
        textAlign: 'center',
        padding: '2.5rem 2rem',
      }}
    >
      <div
        style={{
          background: 'rgba(239, 68, 68, 0.15)',
          padding: '1rem',
          borderRadius: '50%',
          width: 'fit-content',
          margin: '0 auto 1.25rem auto',
          display: 'flex',
        }}
      >
        <AlertTriangle size={32} color="#f87171" />
      </div>

      <div className="badge badge-warning" style={{ marginBottom: '1rem', background: 'rgba(239, 68, 68, 0.15)', color: '#f87171', borderColor: 'rgba(239, 68, 68, 0.3)' }}>
        Error Code: {code}
      </div>

      <h3 style={{ fontSize: '1.35rem', fontWeight: 700, color: '#fecaca', marginBottom: '0.5rem' }}>
        {getTitle(code)}
      </h3>

      <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginBottom: '1.75rem' }}>
        {message}
      </p>

      <button onClick={onReset} className="btn-primary" style={{ background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' }}>
        <RefreshCw size={18} />
        <span>Try Another Photo</span>
      </button>
    </div>
  );
};

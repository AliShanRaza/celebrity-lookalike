import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer style={{ borderTop: '1px solid var(--border-glass)', padding: '2.5rem 0', marginTop: '4rem', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
      <div className="container flex-between" style={{ flexDirection: 'column', gap: '1rem', textAlign: 'center' }}>
        <p>
          <strong>Entertainment Notice:</strong> Similarity scores are visual entertainment resemblance scores calibrated between 0% and 100%. They do not represent identity verification probabilities or biometric authentication.
        </p>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
          © {new Date().getFullYear()} Celebrity Look-Alike Monorepo | Built with Next.js, FastAPI, PostgreSQL & pgvector.
        </p>
      </div>
    </footer>
  );
};

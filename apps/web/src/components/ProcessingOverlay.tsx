'use client';

import React from 'react';
import { Cpu, ShieldCheck } from 'lucide-react';

export const ProcessingOverlay: React.FC = () => {
  return (
    <div style={{ maxWidth: '960px', margin: '0 auto' }}>
      {/* High-Load Queue Status Banner */}
      <div
        style={{
          background: 'rgba(234, 179, 8, 0.12)',
          border: '1px solid rgba(234, 179, 8, 0.3)',
          color: '#fde047',
          padding: '0.75rem 1.25rem',
          borderRadius: '0.75rem',
          fontSize: '0.875rem',
          fontWeight: 600,
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <span>High Traffic Queue: Active demand on recognition engine</span>
        <span className="badge" style={{ background: 'rgba(234, 179, 8, 0.25)', color: '#ffffff' }}>
          Queue Position #1
        </span>
      </div>

      {/* Animated Processing Status Card */}
      <div className="glass-card" style={{ textAlign: 'center', padding: '3rem 2rem', marginBottom: '2.5rem' }}>
        <div style={{ position: 'relative', width: '72px', height: '72px', margin: '0 auto 1.25rem auto', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ position: 'absolute', width: '100%', height: '100%', borderRadius: '50%', border: '3px solid var(--accent-primary)', borderTopColor: 'transparent', animation: 'spin 1s linear infinite' }} />
          <Cpu size={32} color="var(--accent-cyan)" />
        </div>

        <h3 style={{ fontSize: '1.35rem', fontWeight: 700, marginBottom: '0.5rem' }} className="gradient-text">
          Analyzing Facial Points & Computing Resemblance
        </h3>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
          Step 1: Validating portrait image &nbsp;&bull;&nbsp; Step 2: Detecting eyebrows, eyes, nose & mouth landmarks &nbsp;&bull;&nbsp; Step 3: Neural similarity vector search...
        </p>

        <div className="badge badge-success" style={{ padding: '0.4rem 0.9rem' }}>
          <ShieldCheck size={16} />
          <span>Transient Processing: Zero persistent image storage</span>
        </div>
      </div>

      {/* Loading Skeletons */}
      <div className="grid-cols-3">
        {[1, 2, 3].map((item) => (
          <div key={item} className="glass-card" style={{ opacity: 0.6, animation: 'pulse 1.5s ease-in-out infinite' }}>
            <div style={{ width: '100%', height: '200px', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '0.75rem', marginBottom: '1rem' }} />
            <div style={{ width: '65%', height: '20px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '0.25rem', marginBottom: '0.5rem' }} />
            <div style={{ width: '40%', height: '14px', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '0.25rem', marginBottom: '1rem' }} />
            <div style={{ width: '100%', height: '8px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '9999px' }} />
          </div>
        ))}
      </div>

      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
};

'use client';

import React from 'react';
import { Upload, Scan, Sparkles } from 'lucide-react';

export const ThreeStepGuide: React.FC = () => {
  return (
    <div style={{ maxWidth: '960px', margin: '0 auto 3rem auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'var(--font-display)', fontStyle: 'italic', textTransform: 'uppercase' }}>
          HOW IT WORKS IN 3 SIMPLE STEPS <span style={{ color: 'var(--accent-neon-yellow)', fontStyle: 'normal' }}>✦</span>
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginTop: '0.35rem' }}>
          StarByFace methodology for facial point extraction & neural celebrity similarity matching
        </p>
      </div>

      <div className="grid-cols-3" style={{ gap: '1.5rem' }}>
        {/* Step 1 */}
        <div
          className="glass-card"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            position: 'relative',
            padding: '2rem 1.5rem',
            borderTop: '4px solid var(--accent-neon-yellow)',
            background: '#12141A',
            borderRadius: '20px',
          }}
        >
          <div
            style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              background: 'var(--accent-neon-yellow)',
              color: '#000000',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1.25rem',
            }}
          >
            <Upload size={24} />
          </div>

          <div
            style={{
              position: 'absolute',
              top: '14px',
              right: '16px',
              fontWeight: 800,
              fontSize: '0.8rem',
              color: 'var(--accent-neon-yellow)',
            }}
          >
            STEP 1
          </div>

          <h3 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '0.5rem' }}>
            Upload Portrait Photo
          </h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
            Select or drag & drop a clear single portrait photo (JPEG, PNG, WebP) or paste an image URL.
          </p>
        </div>

        {/* Step 2 */}
        <div
          className="glass-card"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            position: 'relative',
            padding: '2rem 1.5rem',
            borderTop: '4px solid var(--bg-card-mint)',
            background: '#12141A',
            borderRadius: '20px',
          }}
        >
          <div
            style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              background: 'var(--bg-card-mint)',
              color: '#000000',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1.25rem',
            }}
          >
            <Scan size={24} />
          </div>

          <div
            style={{
              position: 'absolute',
              top: '14px',
              right: '16px',
              fontWeight: 800,
              fontSize: '0.8rem',
              color: 'var(--bg-card-mint)',
            }}
          >
            STEP 2
          </div>

          <h3 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '0.5rem' }}>
            Detect Face & Landmarks
          </h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
            System detects facial landmarks including eyebrows, eyes, nose, mouth, and face contour position.
          </p>
        </div>

        {/* Step 3 */}
        <div
          className="glass-card"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            position: 'relative',
            padding: '2rem 1.5rem',
            borderTop: '4px solid var(--accent-purple)',
            background: '#12141A',
            borderRadius: '20px',
          }}
        >
          <div
            style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              background: 'var(--accent-purple)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1.25rem',
            }}
          >
            <Sparkles size={24} />
          </div>

          <div
            style={{
              position: 'absolute',
              top: '14px',
              right: '16px',
              fontWeight: 800,
              fontSize: '0.8rem',
              color: 'var(--accent-purple)',
            }}
          >
            STEP 3
          </div>

          <h3 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '0.5rem' }}>
            Neural Similarity Match
          </h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
            Neural network compares face embedding against curated celebrity database to return Best Pair & matches.
          </p>
        </div>
      </div>
    </div>
  );
};

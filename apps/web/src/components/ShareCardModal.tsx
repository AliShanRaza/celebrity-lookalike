'use client';

import React, { useRef } from 'react';
import { MatchResultResponse, CelebrityMatchItem, getImageUrl } from '@/lib/api-client';
import { FacialLandmarksOverlay } from './FacialLandmarksOverlay';
import { X, Download, Share2, Sparkles, Lock, ShieldCheck } from 'lucide-react';

interface ShareCardModalProps {
  results: MatchResultResponse;
  userImageUrl?: string | null;
  onClose: () => void;
}

export const ShareCardModal: React.FC<ShareCardModalProps> = ({
  results,
  userImageUrl,
  onClose,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const bestMatch: CelebrityMatchItem | null =
    results.best_pair?.male_match || results.overall_matches[0] || null;

  const handleDownloadCard = () => {
    // Generate simple share card JSON / blob download
    const cardData = {
      title: 'StarByFace Celebrity Look-Alike Result',
      top_match: bestMatch?.name,
      resemblance_score: `${bestMatch?.resemblance_score}%`,
      best_pair: results.best_pair
        ? `${results.best_pair.male_match?.name || 'N/A'} & ${results.best_pair.female_match?.name || 'N/A'}`
        : 'N/A',
      processed_at: results.processed_at,
      privacy_note: 'Uploaded photo was processed in-memory and destroyed after recognition.',
    };

    const blob = new Blob([JSON.stringify(cardData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `celebrity-lookalike-share-card.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(8px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="share-card-title"
    >
      <div
        className="glass-card"
        style={{
          maxWidth: '540px',
          width: '100%',
          position: 'relative',
          padding: '2rem',
          border: '2px solid var(--border-glow)',
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 27, 75, 0.95))',
        }}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          aria-label="Close Share Card Modal"
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            background: 'rgba(255, 255, 255, 0.1)',
            border: 'none',
            color: '#ffffff',
            borderRadius: '50%',
            padding: '8px',
            cursor: 'pointer',
            display: 'flex',
          }}
        >
          <X size={18} />
        </button>

        {/* Card Header */}
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div className="badge" style={{ marginBottom: '0.5rem', background: 'rgba(99, 102, 241, 0.2)' }}>
            <Sparkles size={14} color="var(--accent-cyan)" />
            <span>Official Celebrity Look-Alike Card</span>
          </div>
          <h3 id="share-card-title" style={{ fontSize: '1.5rem', fontWeight: 800 }} className="gradient-text">
            My Celebrity Look-Alike
          </h3>
        </div>

        {/* Printable/Shareable Card Body */}
        <div
          ref={cardRef}
          style={{
            background: 'rgba(0, 0, 0, 0.4)',
            border: '1px solid var(--border-glass)',
            borderRadius: '1rem',
            padding: '1.5rem',
            marginBottom: '1.5rem',
          }}
        >
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
            {/* User Photo Box with Facial Points Overlay */}
            <div style={{ textAlign: 'center' }}>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem', fontWeight: 600 }}>
                MY PORTRAIT & LANDMARKS
              </p>
              <div
                style={{
                  position: 'relative',
                  width: '100%',
                  height: '140px',
                  borderRadius: '0.75rem',
                  overflow: 'hidden',
                  background: '#1a1d2e',
                  border: '1px solid var(--accent-cyan)',
                }}
              >
                {userImageUrl ? (
                  /* eslint-disable-next-line @next/next/no-img-element */
                  <img src={userImageUrl} alt="My Portrait" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)' }}>
                    Portrait
                  </div>
                )}
                {results.landmarks && <FacialLandmarksOverlay landmarks={results.landmarks} />}
              </div>
            </div>

            {/* Top Celebrity Match Box */}
            <div style={{ textAlign: 'center' }}>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem', fontWeight: 600 }}>
                TOP CELEBRITY MATCH
              </p>
              <div
                style={{
                  width: '100%',
                  height: '140px',
                  borderRadius: '0.75rem',
                  overflow: 'hidden',
                  background: '#1a1d2e',
                  border: '1px solid var(--accent-primary)',
                }}
              >
                {bestMatch?.image_url ? (
                  /* eslint-disable-next-line @next/next/no-img-element */
                  <img src={getImageUrl(bestMatch.image_url)} alt={bestMatch.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)' }}>
                    Celebrity
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Match Score Summary */}
          {bestMatch && (
            <div
              style={{
                textAlign: 'center',
                padding: '0.75rem',
                background: 'rgba(99, 102, 241, 0.1)',
                borderRadius: '0.75rem',
                border: '1px solid rgba(99, 102, 241, 0.25)',
              }}
            >
              <p style={{ fontSize: '1.1rem', fontWeight: 800, color: '#ffffff' }}>
                {bestMatch.name}
              </p>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Resemblance Score:</span>
                <span style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                  {bestMatch.resemblance_score}%
                </span>
              </div>
            </div>
          )}

          {/* Privacy Note inside Card */}
          <div style={{ marginTop: '1rem', textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.35rem' }}>
            <Lock size={12} color="#34d399" />
            <span>Privacy Note: Uploaded image destroyed after matching. Sharing is opt-in.</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={handleDownloadCard}
            className="btn-primary"
            style={{ flex: 1, justifyContent: 'center' }}
          >
            <Download size={18} />
            <span>Download Result Card</span>
          </button>

          <button
            onClick={onClose}
            className="btn-secondary"
            style={{ padding: '0.75rem 1.25rem' }}
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};

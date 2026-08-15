'use client';

import React, { useState, useRef } from 'react';
import { MatchResultResponse, CelebrityMatchItem, getImageUrl } from '@/lib/api-client';
import { FacialLandmarksOverlay } from './FacialLandmarksOverlay';
import { ShareCardModal } from './ShareCardModal';
import { Award, User, RefreshCw, Sparkles, ShieldCheck, Heart, Share2, Scan } from 'lucide-react';

interface ResultsDisplayProps {
  results: MatchResultResponse;
  userImageUrl?: string | null;
  onReset: () => void;
}

export const ResultsDisplay: React.FC<ResultsDisplayProps> = ({
  results,
  userImageUrl,
  onReset,
}) => {
  const defaultTab = results.primary_target_gender === 'female' ? 'female' : results.primary_target_gender === 'male' ? 'male' : 'best_pair';
  const [activeTab, setActiveTab] = useState<'best_pair' | 'overall' | 'male' | 'female'>(defaultTab);
  const [showShareModal, setShowShareModal] = useState<boolean>(false);
  const [showLandmarks, setShowLandmarks] = useState<boolean>(true);
  const restartButtonRef = useRef<HTMLButtonElement>(null);

  const getMatchesForTab = (): CelebrityMatchItem[] => {
    switch (activeTab) {
      case 'male':
        return results.male_matches;
      case 'female':
        return results.female_matches;
      case 'overall':
        return results.overall_matches;
      case 'best_pair':
      default:
        return results.overall_matches;
    }
  };

  const matches = getMatchesForTab();

  const handleKeyDownTab = (e: React.KeyboardEvent, targetTab: 'best_pair' | 'overall' | 'male' | 'female') => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setActiveTab(targetTab);
    }
  };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto 3rem auto' }}>
      {/* User Portrait Preview with Interactive Facial Landmarks Overlay */}
      {userImageUrl && (
        <div
          className="glass-card"
          style={{
            marginBottom: '2rem',
            display: 'flex',
            alignItems: 'center',
            gap: '1.5rem',
            padding: '1.25rem 1.5rem',
            flexWrap: 'wrap',
            background: '#12141A',
            borderRadius: '20px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <div
            style={{
              position: 'relative',
              width: '90px',
              height: '90px',
              borderRadius: '1rem',
              overflow: 'hidden',
              background: '#161821',
              border: '2px solid var(--accent-neon-yellow)',
              boxShadow: '0 0 20px rgba(226, 255, 56, 0.25)',
              flexShrink: 0,
            }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={userImageUrl}
              alt="Uploaded Portrait Preview"
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
            {showLandmarks && results.landmarks && (
              <FacialLandmarksOverlay landmarks={results.landmarks} />
            )}
          </div>

          <div style={{ flex: 1, minWidth: '220px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <Sparkles size={18} color="var(--accent-neon-yellow)" />
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800 }}>
                Facial Landmark Points Extracted
              </h3>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Eyebrows, eyes, nose, mouth, and position landmarks detected successfully.
            </p>
          </div>

          {results.landmarks && (
            <button
              onClick={() => setShowLandmarks(!showLandmarks)}
              className="btn-outline-pill"
              style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
            >
              <Scan size={14} />
              <span>{showLandmarks ? 'Hide Landmarks' : 'Show Landmarks'}</span>
            </button>
          )}
        </div>
      )}

      {/* Results Header & Category Tabs */}
      <div className="glass-card" style={{ marginBottom: '2rem', textAlign: 'center', background: '#12141A', borderRadius: '24px', padding: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
          <Sparkles color="var(--accent-neon-yellow)" size={28} />
          <h2 style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'var(--font-display)', fontStyle: 'italic', textTransform: 'uppercase' }}>
            Celebrity Look-Alike Results ✦
          </h2>
        </div>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginBottom: '1.5rem' }}>
          Model Version: <code style={{ color: 'var(--accent-neon-yellow)' }}>{results.model_version}</code> | Score Version: <code style={{ color: 'var(--accent-purple)' }}>{results.score_version}</code>
        </p>

        {/* 4-Tab Keyboard-Accessible Navigation */}
        <div
          role="tablist"
          aria-label="Celebrity Look-Alike Result Categories"
          style={{
            display: 'inline-flex',
            background: 'rgba(0, 0, 0, 0.6)',
            padding: '0.4rem',
            borderRadius: '9999px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            gap: '0.35rem',
            flexWrap: 'wrap',
            justifyContent: 'center',
          }}
        >
          <button
            role="tab"
            id="tab-best-pair"
            aria-selected={activeTab === 'best_pair'}
            aria-controls="tabpanel-results"
            tabIndex={activeTab === 'best_pair' ? 0 : -1}
            onClick={() => setActiveTab('best_pair')}
            onKeyDown={(e) => handleKeyDownTab(e, 'best_pair')}
            style={{
              padding: '0.65rem 1.35rem',
              borderRadius: '9999px',
              border: 'none',
              fontWeight: 700,
              cursor: 'pointer',
              background: activeTab === 'best_pair' ? 'var(--accent-neon-yellow)' : 'transparent',
              color: activeTab === 'best_pair' ? '#000000' : 'var(--text-muted)',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <Heart size={16} color={activeTab === 'best_pair' ? '#000000' : 'currentColor'} />
            <span>Best Pair</span>
          </button>

          <button
            role="tab"
            id="tab-overall"
            aria-selected={activeTab === 'overall'}
            aria-controls="tabpanel-results"
            tabIndex={activeTab === 'overall' ? 0 : -1}
            onClick={() => setActiveTab('overall')}
            onKeyDown={(e) => handleKeyDownTab(e, 'overall')}
            style={{
              padding: '0.65rem 1.35rem',
              borderRadius: '9999px',
              border: 'none',
              fontWeight: 700,
              cursor: 'pointer',
              background: activeTab === 'overall' ? 'var(--accent-neon-yellow)' : 'transparent',
              color: activeTab === 'overall' ? '#000000' : 'var(--text-muted)',
              transition: 'all 0.2s ease',
            }}
          >
            Overall ({results.overall_matches.length})
          </button>

          <button
            role="tab"
            id="tab-male"
            aria-selected={activeTab === 'male'}
            aria-controls="tabpanel-results"
            tabIndex={activeTab === 'male' ? 0 : -1}
            onClick={() => setActiveTab('male')}
            onKeyDown={(e) => handleKeyDownTab(e, 'male')}
            style={{
              padding: '0.65rem 1.35rem',
              borderRadius: '9999px',
              border: 'none',
              fontWeight: 700,
              cursor: 'pointer',
              background: activeTab === 'male' ? 'var(--accent-neon-yellow)' : 'transparent',
              color: activeTab === 'male' ? '#000000' : 'var(--text-muted)',
              transition: 'all 0.2s ease',
            }}
          >
            Male ({results.male_matches.length})
          </button>

          <button
            role="tab"
            id="tab-female"
            aria-selected={activeTab === 'female'}
            aria-controls="tabpanel-results"
            tabIndex={activeTab === 'female' ? 0 : -1}
            onClick={() => setActiveTab('female')}
            onKeyDown={(e) => handleKeyDownTab(e, 'female')}
            style={{
              padding: '0.65rem 1.35rem',
              borderRadius: '9999px',
              border: 'none',
              fontWeight: 700,
              cursor: 'pointer',
              background: activeTab === 'female' ? 'var(--accent-neon-yellow)' : 'transparent',
              color: activeTab === 'female' ? '#000000' : 'var(--text-muted)',
              transition: 'all 0.2s ease',
            }}
          >
            Female ({results.female_matches.length})
          </button>
        </div>
      </div>

      {/* Tab Panel Content */}
      <div id="tabpanel-results" role="tabpanel" aria-labelledby={`tab-${activeTab}`}>
        {activeTab === 'best_pair' && (
          <div className="glass-card" style={{ marginBottom: '2.5rem', padding: '2rem', border: '2px solid rgba(226, 255, 56, 0.3)', background: '#12141A', borderRadius: '24px' }}>
            <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(226, 255, 56, 0.15)', color: 'var(--accent-neon-yellow)', padding: '0.4rem 1rem', borderRadius: '9999px', fontSize: '0.85rem', fontWeight: 800, marginBottom: '0.75rem' }}>
                <Heart size={16} />
                <span>TOP MALE & FEMALE LOOK-ALIKE PAIR</span>
              </div>
              <h3 style={{ fontSize: '1.6rem', fontWeight: 800 }}>Your Best Pair Matches</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
                Overall Pair Resemblance Score: <strong style={{ color: 'var(--accent-neon-yellow)' }}>{results.best_pair?.pair_score || 0}%</strong>
              </p>
            </div>

            <div className="grid-cols-2" style={{ gap: '1.5rem' }}>
              {/* Male Match Card */}
              {results.best_pair?.male_match ? (
                <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', background: '#161821', borderRadius: '20px' }}>
                  <div style={{ background: 'rgba(6, 182, 212, 0.2)', color: '#06b6d4', padding: '0.3rem 0.75rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 800, width: 'fit-content', marginBottom: '0.85rem' }}>
                    TOP MALE LOOK-ALIKE
                  </div>
                  <div style={{ width: '100%', height: '220px', borderRadius: '1rem', overflow: 'hidden', marginBottom: '1rem', background: '#090a0d' }}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={getImageUrl(results.best_pair.male_match.image_url)} alt={results.best_pair.male_match.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  </div>
                  <h4 style={{ fontSize: '1.3rem', fontWeight: 800 }}>{results.best_pair.male_match.name}</h4>
                  <div className="flex-between" style={{ marginTop: '0.75rem', fontSize: '0.95rem' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Resemblance:</span>
                    <span style={{ fontWeight: 900, color: 'var(--accent-neon-yellow)' }}>{results.best_pair.male_match.resemblance_score}%</span>
                  </div>
                </div>
              ) : (
                <div className="glass-card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  No male match available
                </div>
              )}

              {/* Female Match Card */}
              {results.best_pair?.female_match ? (
                <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', background: '#161821', borderRadius: '20px' }}>
                  <div style={{ background: 'rgba(236, 72, 153, 0.2)', color: '#ec4899', padding: '0.3rem 0.75rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 800, width: 'fit-content', marginBottom: '0.85rem' }}>
                    TOP FEMALE LOOK-ALIKE
                  </div>
                  <div style={{ width: '100%', height: '220px', borderRadius: '1rem', overflow: 'hidden', marginBottom: '1rem', background: '#090a0d' }}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={getImageUrl(results.best_pair.female_match.image_url)} alt={results.best_pair.female_match.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  </div>
                  <h4 style={{ fontSize: '1.3rem', fontWeight: 800 }}>{results.best_pair.female_match.name}</h4>
                  <div className="flex-between" style={{ marginTop: '0.75rem', fontSize: '0.95rem' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Resemblance:</span>
                    <span style={{ fontWeight: 900, color: 'var(--accent-neon-yellow)' }}>{results.best_pair.female_match.resemblance_score}%</span>
                  </div>
                </div>
              ) : (
                <div className="glass-card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  No female match available
                </div>
              )}
            </div>
          </div>
        )}

        {/* OVERALL / MALE / FEMALE RANKED GRID */}
        {matches.length === 0 ? (
          <div className="glass-card" style={{ textAlign: 'center', padding: '3.5rem 2rem', color: 'var(--text-muted)', background: '#12141A', borderRadius: '24px' }}>
            <p style={{ fontSize: '1.15rem', marginBottom: '0.5rem' }}>No celebrity matches found for this category.</p>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Try uploading a different portrait to see matches across all categories.</p>
          </div>
        ) : (
          <div className="results-grid">
            {matches.map((item, idx) => (
              <div key={item.celebrity_id + idx} className="glass-card" style={{ display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden', background: '#12141A', borderRadius: '24px', border: '1px solid rgba(255,255,255,0.08)' }}>
                {/* Rank Badge */}
                <div
                  style={{
                    position: 'absolute',
                    top: '14px',
                    left: '14px',
                    background: idx === 0 ? 'var(--accent-neon-yellow)' : 'rgba(0, 0, 0, 0.85)',
                    color: idx === 0 ? '#000000' : '#ffffff',
                    fontWeight: 800,
                    fontSize: '0.8rem',
                    padding: '0.35rem 0.75rem',
                    borderRadius: '9999px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem',
                    zIndex: 10,
                  }}
                >
                  <Award size={14} />
                  <span>#{idx + 1} Match</span>
                </div>

                {/* Celebrity Image */}
                <div style={{ width: '100%', height: '230px', borderRadius: '1rem', overflow: 'hidden', marginBottom: '1rem', background: '#161821', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                  {item.image_url ? (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img src={getImageUrl(item.image_url)} alt={`Photo of ${item.name}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  ) : (
                    <User size={64} color="var(--text-muted)" />
                  )}
                </div>

                {/* Celebrity Details */}
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '0.25rem' }}>{item.name}</h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'capitalize', marginBottom: '1rem' }}>
                  Category: {item.gender}
                </p>

                {/* Resemblance Score Bar */}
                <div style={{ marginTop: 'auto', paddingTop: '0.85rem', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
                  <div className="flex-between" style={{ marginBottom: '0.4rem', fontSize: '0.85rem' }}>
                    <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Look-alike Score</span>
                    <span style={{ fontWeight: 900, color: 'var(--accent-neon-yellow)', fontSize: '1.1rem' }}>{item.resemblance_score}%</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${item.resemblance_score}%`,
                        height: '100%',
                        background: 'var(--accent-neon-yellow)',
                        borderRadius: '9999px',
                        transition: 'width 0.6s ease',
                      }}
                    />
                  </div>
                </div>

                {item.bio && (
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.75rem', lineHeight: 1.4 }}>
                    {item.bio}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Action Footer Bar */}
      <div className="glass-card" style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem', background: '#12141A', borderRadius: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          <ShieldCheck size={16} color="var(--accent-neon-yellow)" />
          <span>Uploaded photos are deleted after recognition unless you elect to share results.</span>
        </div>

        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
          <button
            onClick={() => setShowShareModal(true)}
            className="btn-neon-pill"
          >
            <Share2 size={18} />
            <span>Share My Results</span>
          </button>

          <button
            ref={restartButtonRef}
            onClick={onReset}
            className="btn-outline-pill"
            aria-label="Try Another Photo"
          >
            <RefreshCw size={18} />
            <span>Try Another Photo</span>
          </button>
        </div>
      </div>

      {/* Share Card Modal */}
      {showShareModal && (
        <ShareCardModal
          results={results}
          userImageUrl={userImageUrl}
          onClose={() => setShowShareModal(false)}
        />
      )}
    </div>
  );
};

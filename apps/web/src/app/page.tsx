'use client';

import React, { useState, useRef } from 'react';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { UploadDropzone } from '@/components/UploadDropzone';
import { ThreeStepGuide } from '@/components/ThreeStepGuide';
import { ProcessingOverlay } from '@/components/ProcessingOverlay';
import { ResultsDisplay } from '@/components/ResultsDisplay';
import { ErrorMessage } from '@/components/ErrorMessage';
import { HealthStatus } from '@/components/HealthStatus';
import { HeroIllustration } from '@/components/HeroIllustration';
import { BrandLogosBar } from '@/components/BrandLogosBar';
import { findCelebrityMatches, MatchResultResponse, ApiError } from '@/lib/api-client';
import { Lock, Sparkles, ShieldCheck, Cpu } from 'lucide-react';

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<{ code: string; message: string } | null>(null);
  const [results, setResults] = useState<MatchResultResponse | null>(null);

  const uploadSectionRef = useRef<HTMLDivElement>(null);

  const scrollToUpload = () => {
    uploadSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleFileSelected = (file: File) => {
    setSelectedFile(file);
    setError(null);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleSubmit = async (file: File, targetGender: string, targetOrigin: string) => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      const data = await findCelebrityMatches(file, targetGender, targetOrigin);
      setResults(data);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError({ code: err.code, message: err.message });
      } else {
        setError({ code: 'UNKNOWN_ERROR', message: err.message || 'Failed to process portrait' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setIsLoading(false);
    setError(null);
    setResults(null);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Top Floating Glass Header */}
      <Header onGetStartedClick={scrollToUpload} />

      <main style={{ flex: 1, paddingBottom: '4rem' }}>
        <div className="container">
          
          {/* SECTION 1: Dark Hero Card Container (Direct Visual Parity with Reference Image Card 1) */}
          <section className="hero-card" id="hero">
            {/* Purple side glow indicator */}
            <div className="hero-card-side-indicator" />

            <div className="hero-content-grid">
              {/* Left Column: Headlines & Action Pills */}
              <div>
                <div className="hero-tag-serif">Apply Now!</div>

                <h1 className="hero-headline-display">
                  DISCOVER YOUR<br />
                  CELEBRITY<br />
                  LOOK-ALIKE<span className="hero-star-accent">✦</span>MATCHES
                </h1>

                <p className="hero-subtext">
                  StarByFace facial resemblance engine with instant neural recognition and zero persistent image storage.
                </p>

                <div className="hero-action-group">
                  <button onClick={scrollToUpload} className="btn-neon-pill">
                    Let&apos;s Started
                  </button>
                  <button onClick={scrollToUpload} className="btn-outline-pill">
                    Apply Now
                  </button>
                </div>
              </div>

              {/* Right Column: Purple 3D Graphic Illustration */}
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <HeroIllustration />
              </div>
            </div>

            {/* Bottom Brand Logos Bar */}
            <BrandLogosBar />
          </section>

          {/* Privacy Guarantee Note */}
          <div
            style={{
              maxWidth: '720px',
              margin: '0 auto 2.5rem auto',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.75rem',
              background: 'rgba(61, 243, 196, 0.08)',
              border: '1px solid rgba(61, 243, 196, 0.2)',
              color: '#3DF3C4',
              padding: '0.75rem 1.5rem',
              borderRadius: '1.25rem',
              fontSize: '0.9rem',
              fontWeight: 600,
              textAlign: 'center',
            }}
          >
            <Lock size={18} />
            <span>
              <strong>Privacy Promise:</strong> Uploaded photos are processed strictly in-memory and deleted immediately after recognition.
            </span>
          </div>

          {/* Interactive Workflow Area */}
          <div ref={uploadSectionRef} id="upload-section">
            {isLoading ? (
              <ProcessingOverlay />
            ) : error ? (
              <ErrorMessage code={error.code} message={error.message} onReset={handleReset} />
            ) : results ? (
              <ResultsDisplay
                results={results}
                userImageUrl={previewUrl}
                onReset={handleReset}
              />
            ) : (
              <UploadDropzone
                onFileSelected={handleFileSelected}
                onSubmit={handleSubmit}
                isLoading={isLoading}
              />
            )}
          </div>

          {/* SECTION 2: Secondary Mint Green Container Card (Visual Parity with Reference Image Card 2) */}
          <section className="mint-card" id="features">
            <div className="mint-card-grid">
              {/* Left Column: Embedded Dark Facial AI Scanner Graphic Card */}
              <div
                style={{
                  background: '#090a0d',
                  borderRadius: '24px',
                  padding: '2rem',
                  color: '#ffffff',
                  boxShadow: '0 15px 35px rgba(0, 0, 0, 0.3)',
                  position: 'relative',
                  overflow: 'hidden',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                    <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--accent-neon-yellow)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#000000', fontWeight: 900, fontSize: '0.9rem' }}>
                      ✦
                    </div>
                    <span style={{ fontWeight: 800, fontSize: '1.1rem', letterSpacing: '-0.01em' }}>AI Scanner</span>
                  </div>

                  <div style={{ display: 'flex', gap: '4px' }}>
                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-neon-yellow)' }} />
                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#3DF3C4' }} />
                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#8B3DFF' }} />
                  </div>
                </div>

                <div style={{ fontSize: '2.4rem', fontWeight: 900, fontStyle: 'italic', textTransform: 'uppercase', letterSpacing: '-0.02em', lineHeight: 1.1, marginBottom: '1.5rem' }}>
                  FACIAL AI<br />NEURAL ENGINE
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', background: 'rgba(255, 255, 255, 0.06)', padding: '0.85rem 1.25rem', borderRadius: '16px' }}>
                  <Cpu color="var(--accent-neon-yellow)" size={24} />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700 }}>512-D Embedding Vectors</div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Fast pgvector similarity index</div>
                  </div>
                </div>
              </div>

              {/* Right Column: Mint Card Headline */}
              <div>
                <h2 className="mint-headline-display">
                  SMART AI FOR<br />
                  CELEBRITY MATCHING
                </h2>
                <p style={{ fontSize: '1.05rem', color: '#1a2e28', marginTop: '1.25rem', lineHeight: 1.6, fontWeight: 500 }}>
                  Extract deep facial landmarks including eyes, nose, lips, and face outline contour to calculate calibrated similarity percentages in milliseconds.
                </p>
              </div>
            </div>
          </section>

          {/* 3-Step Guide and Health Status */}
          <div id="how-it-works">
            <ThreeStepGuide />
          </div>

          <div id="health" style={{ marginTop: '3rem' }}>
            <HealthStatus />
          </div>

        </div>
      </main>

      <Footer />
    </div>
  );
}

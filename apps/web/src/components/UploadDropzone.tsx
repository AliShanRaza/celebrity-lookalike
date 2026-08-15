'use client';

import React, { useState, useRef } from 'react';
import { UploadCloud, Image as ImageIcon, X, Sparkles, User, Globe, RefreshCw } from 'lucide-react';

interface UploadDropzoneProps {
  onFileSelected: (file: File) => void;
  onSubmit: (file: File, targetGender: string, targetOrigin: string) => void;
  isLoading: boolean;
}

export type StepState = 'select_gender' | 'select_upload' | 'select_origin' | 'ready_to_submit';

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({
  onFileSelected,
  onSubmit,
  isLoading,
}) => {
  const [targetGender, setTargetGender] = useState<'female' | 'male' | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [targetOrigin, setTargetOrigin] = useState<'bollywood' | 'hollywood' | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Compute current state machine step
  let currentStep: StepState = 'select_gender';
  if (!targetGender) {
    currentStep = 'select_gender';
  } else if (!selectedFile) {
    currentStep = 'select_upload';
  } else if (!targetOrigin) {
    currentStep = 'select_origin';
  } else {
    currentStep = 'ready_to_submit';
  }

  const handleGenderSelect = (gender: 'female' | 'male') => {
    setTargetGender(gender);
  };

  const handleFileChange = (file: File | null) => {
    if (!file) return;
    setSelectedFile(file);
    onFileSelected(file);

    if (previewUrl && typeof window !== 'undefined' && window.URL && typeof window.URL.revokeObjectURL === 'function') {
      try { URL.revokeObjectURL(previewUrl); } catch (_) {}
    }

    let url = 'mock-preview-url';
    if (typeof window !== 'undefined' && window.URL && typeof window.URL.createObjectURL === 'function') {
      try { url = URL.createObjectURL(file); } catch (_) {}
    }
    setPreviewUrl(url);
  };

  const handleOriginSelect = (origin: 'bollywood' | 'hollywood') => {
    setTargetOrigin(origin);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  // State Resets
  const resetToGender = () => {
    setTargetGender(null);
    if (previewUrl && typeof window !== 'undefined' && window.URL && typeof window.URL.revokeObjectURL === 'function') {
      try { URL.revokeObjectURL(previewUrl); } catch (_) {}
    }
    setPreviewUrl(null);
    setSelectedFile(null);
    setTargetOrigin(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const resetToUpload = () => {
    if (previewUrl && typeof window !== 'undefined' && window.URL && typeof window.URL.revokeObjectURL === 'function') {
      try { URL.revokeObjectURL(previewUrl); } catch (_) {}
    }
    setPreviewUrl(null);
    setSelectedFile(null);
    setTargetOrigin(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const resetToOrigin = () => {
    setTargetOrigin(null);
  };

  const isSubmitDisabled = isLoading || currentStep !== 'ready_to_submit' || !selectedFile || !targetGender || !targetOrigin;

  return (
    <div className="glass-card" style={{ maxWidth: '680px', margin: '0 auto 2.5rem auto', textAlign: 'center', position: 'relative', background: '#12141A', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '24px', padding: '2.25rem' }}>
      <input
        type="file"
        ref={fileInputRef}
        accept="image/jpeg,image/png,image/webp"
        style={{ display: 'none' }}
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            handleFileChange(e.target.files[0]);
          }
        }}
      />

      {/* Workflow Step Progress Indicator Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.75rem', paddingBottom: '1rem', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
        <div style={{ display: 'flex', gap: '0.65rem', alignItems: 'center' }}>
          <div
            style={{
              padding: '0.3rem 0.8rem',
              borderRadius: '9999px',
              fontSize: '0.75rem',
              fontWeight: 800,
              background: 'var(--accent-neon-yellow)',
              color: '#000000'
            }}
          >
            {currentStep === 'select_gender' ? 'STEP 1 / 3' : currentStep === 'select_upload' ? 'STEP 2 / 3' : 'STEP 3 / 3'}
          </div>
          <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-muted)' }}>
            {currentStep === 'select_gender' ? 'Select Celebrity Gender' : currentStep === 'select_upload' ? 'Upload Portrait Photo' : 'Select Celebrity Origin'}
          </span>
        </div>

        {targetGender && (
          <button
            type="button"
            onClick={resetToGender}
            className="btn-outline-pill"
            style={{ fontSize: '0.8rem', padding: '0.35rem 0.85rem' }}
            aria-label="Start over from Step 1"
          >
            <RefreshCw size={13} />
            <span>Start Over</span>
          </button>
        )}
      </div>

      {/* Completed Step Summary Badges */}
      {targetGender && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', justifyContent: 'center', marginBottom: '1.5rem' }}>
          {/* Step 1 Summary */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '0.75rem',
              padding: '0.4rem 0.85rem',
              fontSize: '0.85rem',
            }}
          >
            <User size={14} color={targetGender === 'female' ? '#ec4899' : '#06b6d4'} />
            <span>Gender: <strong style={{ textTransform: 'capitalize', color: '#fff' }}>{targetGender}</strong></span>
            <button
              type="button"
              onClick={resetToGender}
              style={{ background: 'none', border: 'none', color: 'var(--accent-neon-yellow)', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer', padding: '0 0.2rem', textDecoration: 'underline' }}
              aria-label="Change gender selection"
            >
              Change
            </button>
          </div>

          {/* Step 2 Summary */}
          {selectedFile && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '0.75rem',
                padding: '0.4rem 0.85rem',
                fontSize: '0.85rem',
              }}
            >
              <ImageIcon size={14} color="#3DF3C4" />
              <span>Photo: <strong style={{ color: '#fff' }}>{selectedFile.name.length > 18 ? selectedFile.name.substring(0, 15) + '...' : selectedFile.name}</strong></span>
              <button
                type="button"
                onClick={resetToUpload}
                style={{ background: 'none', border: 'none', color: 'var(--accent-neon-yellow)', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer', padding: '0 0.2rem', textDecoration: 'underline' }}
                aria-label="Change uploaded photo"
              >
                Change
              </button>
            </div>
          )}

          {/* Step 3 Summary */}
          {targetOrigin && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '0.75rem',
                padding: '0.4rem 0.85rem',
                fontSize: '0.85rem',
              }}
            >
              <Globe size={14} color={targetOrigin === 'bollywood' ? '#f59e0b' : '#8b3dff'} />
              <span>Origin: <strong style={{ textTransform: 'capitalize', color: '#fff' }}>{targetOrigin}</strong></span>
              <button
                type="button"
                onClick={resetToOrigin}
                style={{ background: 'none', border: 'none', color: 'var(--accent-neon-yellow)', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer', padding: '0 0.2rem', textDecoration: 'underline' }}
                aria-label="Change origin selection"
              >
                Change
              </button>
            </div>
          )}
        </div>
      )}

      {/* STEP 1: GENDER SELECTION */}
      {currentStep === 'select_gender' && (
        <div data-testid="step-gender-container" style={{ padding: '0.5rem 0' }}>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '0.5rem', fontFamily: 'var(--font-display)', fontStyle: 'italic', textTransform: 'uppercase' }}>
            Choose Target Gender Category ✦
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginBottom: '2rem' }}>
            Select a gender category to filter celebrity matches.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', maxWidth: '520px', margin: '0 auto' }}>
            {/* Female Selection Card */}
            <button
              type="button"
              data-testid="gender-female-btn"
              onClick={() => handleGenderSelect('female')}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleGenderSelect('female'); }}
              aria-label="Select Female Category"
              style={{
                background: 'rgba(236, 72, 153, 0.1)',
                border: '2px solid rgba(236, 72, 153, 0.4)',
                borderRadius: '1.25rem',
                padding: '2rem 1.25rem',
                cursor: 'pointer',
                transition: 'all 0.25s ease',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '0.75rem',
                outline: 'none',
              }}
            >
              <div style={{ background: '#ec4899', width: '56px', height: '56px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 20px rgba(236, 72, 153, 0.4)' }}>
                <User size={28} color="#ffffff" />
              </div>
              <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff' }}>Female</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Match female celebrities</span>
            </button>

            {/* Male Selection Card */}
            <button
              type="button"
              data-testid="gender-male-btn"
              onClick={() => handleGenderSelect('male')}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleGenderSelect('male'); }}
              aria-label="Select Male Category"
              style={{
                background: 'rgba(6, 182, 212, 0.1)',
                border: '2px solid rgba(6, 182, 212, 0.4)',
                borderRadius: '1.25rem',
                padding: '2rem 1.25rem',
                cursor: 'pointer',
                transition: 'all 0.25s ease',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '0.75rem',
                outline: 'none',
              }}
            >
              <div style={{ background: '#06b6d4', width: '56px', height: '56px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 20px rgba(6, 182, 212, 0.4)' }}>
                <User size={28} color="#ffffff" />
              </div>
              <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff' }}>Male</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Match male celebrities</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: UPLOAD INTERFACE */}
      {currentStep === 'select_upload' && (
        <div data-testid="step-upload-container">
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '0.5rem', fontFamily: 'var(--font-display)', fontStyle: 'italic', textTransform: 'uppercase' }}>
            Upload Your Portrait Photo ✦
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Select or drag & drop a clear front-facing portrait photo.
          </p>

          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            aria-label="Upload portrait photo dropzone"
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                fileInputRef.current?.click();
              }
            }}
            style={{
              border: isDragging ? '2px dashed var(--accent-neon-yellow)' : '2px dashed rgba(255, 255, 255, 0.2)',
              background: isDragging ? 'rgba(226, 255, 56, 0.08)' : 'rgba(255, 255, 255, 0.02)',
              borderRadius: '1.25rem',
              padding: '3rem 1.5rem',
              cursor: 'pointer',
              transition: 'all 0.25s ease',
              outline: 'none',
            }}
          >
            <div style={{ background: 'var(--accent-neon-yellow)', padding: '1rem', borderRadius: '50%', width: 'fit-content', margin: '0 auto 1.25rem auto', display: 'flex', color: '#000000' }}>
              <UploadCloud size={36} />
            </div>

            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '0.5rem' }}>
              Drag & Drop Your Portrait Photo
            </h3>

            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
              Supports JPEG, PNG, or WebP (Max 10MB, exactly 1 face)
            </p>

            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255, 255, 255, 0.08)', padding: '0.5rem 1.25rem', borderRadius: '9999px', fontSize: '0.85rem', fontWeight: 600 }}>
              <ImageIcon size={14} color="var(--accent-neon-yellow)" />
              <span>Click to Browse Files</span>
            </div>
          </div>
        </div>
      )}

      {/* STEP 3 & 4: ORIGIN SELECTION & SUBMISSION */}
      {(currentStep === 'select_origin' || currentStep === 'ready_to_submit') && (
        <div data-testid="step-origin-container">
          {previewUrl && (
            <div style={{ position: 'relative', width: '180px', height: '180px', margin: '0 auto 1.5rem auto', borderRadius: '1.25rem', overflow: 'hidden', border: '2px solid var(--accent-neon-yellow)', boxShadow: '0 8px 30px rgba(226, 255, 56, 0.2)' }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={previewUrl}
                alt="Selected user portrait preview"
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
              <button
                onClick={resetToUpload}
                aria-label="Remove selected image"
                type="button"
                style={{
                  position: 'absolute',
                  top: '8px',
                  right: '8px',
                  background: 'rgba(0, 0, 0, 0.85)',
                  border: 'none',
                  color: '#fff',
                  borderRadius: '50%',
                  padding: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                }}
              >
                <X size={16} />
              </button>
            </div>
          )}

          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '0.5rem', fontFamily: 'var(--font-display)', fontStyle: 'italic', textTransform: 'uppercase' }}>
            Choose Celebrity Origin ✦
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Select which dataset to match your facial features against.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', maxWidth: '520px', margin: '0 auto 2rem auto' }}>
            {/* Bollywood Card */}
            <button
              type="button"
              data-testid="origin-bollywood-btn"
              onClick={() => handleOriginSelect('bollywood')}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleOriginSelect('bollywood'); }}
              aria-label="Select Bollywood Dataset"
              style={{
                background: targetOrigin === 'bollywood' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(245, 158, 11, 0.08)',
                border: targetOrigin === 'bollywood' ? '2px solid #f59e0b' : '2px solid rgba(245, 158, 11, 0.25)',
                borderRadius: '1.25rem',
                padding: '1.5rem 1rem',
                cursor: 'pointer',
                transition: 'all 0.25s ease',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '0.65rem',
                outline: 'none',
                boxShadow: targetOrigin === 'bollywood' ? '0 0 20px rgba(245, 158, 11, 0.3)' : 'none'
              }}
            >
              <div style={{ background: '#f59e0b', width: '48px', height: '48px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 15px rgba(245, 158, 11, 0.4)' }}>
                <Globe size={24} color="#ffffff" />
              </div>
              <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#ffffff' }}>Bollywood</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Indian Cinema Stars</span>
            </button>

            {/* Hollywood Card */}
            <button
              type="button"
              data-testid="origin-hollywood-btn"
              onClick={() => handleOriginSelect('hollywood')}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleOriginSelect('hollywood'); }}
              aria-label="Select Hollywood Dataset"
              style={{
                background: targetOrigin === 'hollywood' ? 'rgba(139, 61, 255, 0.2)' : 'rgba(139, 61, 255, 0.08)',
                border: targetOrigin === 'hollywood' ? '2px solid var(--accent-purple)' : '2px solid rgba(139, 61, 255, 0.25)',
                borderRadius: '1.25rem',
                padding: '1.5rem 1rem',
                cursor: 'pointer',
                transition: 'all 0.25s ease',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '0.65rem',
                outline: 'none',
                boxShadow: targetOrigin === 'hollywood' ? '0 0 20px rgba(139, 61, 255, 0.3)' : 'none'
              }}
            >
              <div style={{ background: 'var(--accent-purple)', width: '48px', height: '48px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 15px rgba(139, 61, 255, 0.4)' }}>
                <Globe size={24} color="#ffffff" />
              </div>
              <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#ffffff' }}>Hollywood</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Global Film Stars</span>
            </button>
          </div>

          {/* Submit Action Button */}
          <button
            type="button"
            data-testid="submit-matches-btn"
            onClick={() => selectedFile && targetGender && targetOrigin && onSubmit(selectedFile, targetGender, targetOrigin)}
            disabled={isSubmitDisabled}
            className="btn-neon-pill"
            style={{
              width: '100%',
              justifyContent: 'center',
              padding: '1rem',
              fontSize: '1.05rem',
              borderRadius: '1.25rem',
              opacity: isSubmitDisabled ? 0.5 : 1,
              cursor: isSubmitDisabled ? 'not-allowed' : 'pointer',
              transition: 'all 0.25s ease',
            }}
          >
            <Sparkles size={20} />
            <span>
              {isLoading
                ? 'Processing Portrait...'
                : !targetOrigin
                ? 'Select Origin Category Above'
                : 'Find My Celebrity Look-Alikes'}
            </span>
          </button>
        </div>
      )}
    </div>
  );
};

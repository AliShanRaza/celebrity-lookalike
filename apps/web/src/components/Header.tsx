'use client';

import React from 'react';
import Link from 'next/link';

interface HeaderProps {
  onGetStartedClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onGetStartedClick }) => {
  return (
    <div className="header-wrapper">
      <div className="container">
        <header className="header-container">
          {/* Logo */}
          <Link href="/" className="nav-logo">
            <div className="logo-badge">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L3 7V17L12 22L21 17V7L12 2Z" stroke="#000000" strokeWidth="2.5" strokeLinejoin="round"/>
                <path d="M12 6L7 12L12 18L17 12L12 6Z" fill="#000000"/>
              </svg>
            </div>
            <span style={{ fontWeight: 800, fontSize: '1.2rem', letterSpacing: '-0.02em' }}>
              Celebrity Look-Alike
            </span>
          </Link>

          {/* Navigation Links */}
          <nav>
            <ul className="nav-links">
              <li><a href="#hero">Home</a></li>
              <li><a href="#features">Pages</a></li>
              <li><a href="#how-it-works">Project</a></li>
              <li><a href="#privacy">Blog</a></li>
              <li><a href="#health">Contact</a></li>
            </ul>
          </nav>

          {/* Call to Action Button */}
          <button
            onClick={onGetStartedClick}
            className="btn-neon-pill"
          >
            Let&apos;s Started
          </button>
        </header>
      </div>
    </div>
  );
};

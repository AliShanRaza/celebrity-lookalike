'use client';

import React from 'react';

export const HeroIllustration: React.FC = () => {
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: '380px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 520 460"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ overflow: 'visible' }}
      >
        <defs>
          {/* Gradients */}
          <linearGradient id="purpleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#A855F7" />
            <stop offset="100%" stopColor="#6D28D9" />
          </linearGradient>

          <linearGradient id="neonYellowGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#EFFE54" />
            <stop offset="100%" stopColor="#CBEA00" />
          </linearGradient>

          <filter id="purpleGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="15" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          <filter id="dropShadow" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="12" stdDeviation="16" floodColor="#000000" floodOpacity="0.6" />
          </filter>
        </defs>

        {/* Ambient Purple Background Glow */}
        <circle cx="360" cy="200" r="140" fill="#8B3DFF" opacity="0.25" filter="url(#purpleGlow)" />

        {/* 3D Purple Torus / Spiral Spring Coil (Reference Image) */}
        <g stroke="#9333EA" strokeWidth="14" strokeLinecap="round">
          <path d="M 330 110 C 370 70, 440 80, 450 140 C 460 200, 380 230, 360 270 C 340 310, 410 370, 470 340" fill="none" opacity="0.9" />
        </g>
        <g stroke="#A855F7" strokeWidth="10" strokeLinecap="round">
          <path d="M 325 112 C 365 72, 435 82, 445 142 C 455 202, 375 232, 355 272 C 335 312, 405 372, 465 342" fill="none" />
        </g>

        {/* Floating Neon Yellow Credit Card on top left of Phone */}
        <g transform="translate(290, 110) rotate(-18)" filter="url(#dropShadow)">
          <rect x="0" y="0" width="110" height="70" rx="12" fill="url(#neonYellowGradient)" stroke="#000000" strokeWidth="2.5" />
          <rect x="14" y="16" width="22" height="16" rx="4" fill="#000000" />
          <circle cx="85" cy="50" r="10" fill="#000000" opacity="0.8" />
          <circle cx="73" cy="50" r="10" fill="#000000" opacity="0.4" />
        </g>

        {/* Floating 3D Coin Badge with $ Symbol on top right */}
        <g transform="translate(430, 90)" filter="url(#dropShadow)">
          <ellipse cx="25" cy="25" rx="25" ry="25" fill="#8B3DFF" stroke="#000000" strokeWidth="2.5" />
          <ellipse cx="25" cy="20" rx="25" ry="25" fill="#A855F7" stroke="#000000" strokeWidth="2.5" />
          <text x="25" y="28" fill="#EFFE54" fontSize="22" fontWeight="900" textAnchor="middle" fontFamily="sans-serif">$</text>
        </g>

        {/* Smartphone Device Frame */}
        <g transform="translate(370, 140) rotate(14)" filter="url(#dropShadow)">
          {/* Phone Shell Outer */}
          <rect x="0" y="0" width="165" height="290" rx="30" fill="#18181B" stroke="#000000" strokeWidth="4" />
          {/* Phone Screen Inner */}
          <rect x="8" y="8" width="149" height="274" rx="24" fill="#09090B" />

          {/* Notch Header */}
          <rect x="52" y="14" width="60" height="12" rx="6" fill="#18181B" />

          {/* Screen Content: Spendings Header */}
          <text x="20" y="52" fill="#9CA3AF" fontSize="10" fontWeight="600" fontFamily="sans-serif">SCANNING</text>
          <text x="20" y="68" fill="#FFFFFF" fontSize="14" fontWeight="800" fontFamily="sans-serif">Face Match ✦</text>

          {/* Screen Content: Neon Yellow Coins Stack Graphic */}
          <g transform="translate(20, 85)">
            <rect x="0" y="0" width="109" height="110" rx="16" fill="rgba(168, 85, 247, 0.2)" stroke="rgba(168, 85, 247, 0.4)" strokeWidth="1" />
            {/* Coins / Face scan target */}
            <circle cx="54.5" cy="45" r="28" fill="none" stroke="#EFFE54" strokeWidth="3" strokeDasharray="6 4" />
            <circle cx="54.5" cy="45" r="14" fill="#EFFE54" />
            <rect x="15" y="88" width="79" height="8" rx="4" fill="#A855F7" />
          </g>

          {/* Overview Button Pill on phone screen */}
          <g transform="translate(20, 215)">
            <rect x="0" y="0" width="109" height="32" rx="16" fill="#000000" stroke="#333333" strokeWidth="1" />
            <text x="54.5" y="20" fill="#FFFFFF" fontSize="11" fontWeight="700" textAnchor="middle" fontFamily="sans-serif">Overview ›</text>
          </g>
        </g>

        {/* 3D Purple % Badge Icon floating near phone base (Matching reference) */}
        <g transform="translate(290, 340) rotate(-12)" filter="url(#dropShadow)">
          <rect x="0" y="0" width="75" height="55" rx="16" fill="#7C3AED" stroke="#000000" strokeWidth="2.5" />
          <text x="37.5" y="36" fill="#EFFE54" fontSize="26" fontWeight="900" textAnchor="middle" fontFamily="sans-serif">%</text>
        </g>

        {/* Stylized Vector Hand holding Phone (Reference Style) */}
        <g transform="translate(420, 300)" opacity="0.95">
          <path d="M 70 80 C 40 40, 20 20, -20 50 C -40 70, -10 110, 30 130 Z" fill="#FFFFFF" stroke="#000000" strokeWidth="3" />
          <path d="M 60 40 C 30 10, 0 10, -30 30" stroke="#000000" strokeWidth="3" fill="none" strokeLinecap="round" />
        </g>

        {/* Small floating stars / sparks */}
        <path d="M 270 90 L 273 98 L 281 101 L 273 104 L 270 112 L 267 104 L 259 101 L 267 98 Z" fill="#EFFE54" />
        <path d="M 400 390 L 402 396 L 408 398 L 402 400 L 400 406 L 398 400 L 392 398 L 398 396 Z" fill="#A855F7" />
      </svg>
    </div>
  );
};

'use client';

import React, { useEffect, useState } from 'react';
import { fetchVersionInfo, VersionInfo } from '@/lib/api-client';
import { Users, Film, Cpu, ShieldCheck } from 'lucide-react';

export const BrandLogosBar: React.FC = () => {
  const [versionInfo, setVersionInfo] = useState<VersionInfo | null>(null);

  useEffect(() => {
    fetchVersionInfo().then((info) => {
      setVersionInfo(info);
    });
  }, []);

  const totalCelebs = versionInfo?.total_celebrities || 300;
  const rawProvider = versionInfo?.recognition_provider || 'insightface';
  const providerLabel = rawProvider.toLowerCase() === 'insightface' ? 'InsightFace' : rawProvider.toUpperCase();

  return (
    <div className="brand-logos-section">
      <div className="brand-join-text">
        Compare your face against {totalCelebs}+ Bollywood &amp; Hollywood celebrities in real time
      </div>

      <div className="honest-badges-row">
        <div className="honest-badge-item">
          <Users size={16} className="honest-badge-icon" />
          <span>{totalCelebs}+ Celebrities</span>
        </div>

        <div className="honest-badge-item">
          <Film size={16} className="honest-badge-icon" />
          <span>Bollywood &amp; Hollywood</span>
        </div>

        <div className="honest-badge-item">
          <Cpu size={16} className="honest-badge-icon" />
          <span>{providerLabel} Neural Model</span>
        </div>

        <div className="honest-badge-item">
          <ShieldCheck size={16} className="honest-badge-icon" />
          <span>Zero Persistent Upload Storage</span>
        </div>
      </div>
    </div>
  );
};

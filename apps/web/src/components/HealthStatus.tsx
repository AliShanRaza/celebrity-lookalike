'use client';

import React, { useEffect, useState } from 'react';
import { Activity, Server, Cpu, Database } from 'lucide-react';

interface HealthData {
  status: string;
  database: string;
  environment: string;
}

interface VersionData {
  app_version: string;
  recognition_provider: string;
  model_version: string;
  embedding_dimension: number;
}

export const HealthStatus: React.FC = () => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [version, setVersion] = useState<VersionData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    async function fetchStatus() {
      try {
        const [healthRes, versionRes] = await Promise.all([
          fetch(`${apiUrl}/api/v1/health`),
          fetch(`${apiUrl}/api/v1/version`)
        ]);

        if (!healthRes.ok || !versionRes.ok) {
          throw new Error('Failed to reach API endpoints');
        }

        const healthJson = await healthRes.json();
        const versionJson = await versionRes.json();

        setHealth(healthJson);
        setVersion(versionJson);
      } catch (err: any) {
        setError(err.message || 'API connection failed');
      } finally {
        setLoading(false);
      }
    }

    fetchStatus();
  }, [apiUrl]);

  return (
    <div className="glass-card" style={{ marginTop: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <Activity color="var(--accent-cyan)" size={24} />
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>System Health & Infrastructure Monitor</h2>
      </div>

      {loading ? (
        <div style={{ color: 'var(--text-muted)' }}>Connecting to backend service...</div>
      ) : error ? (
        <div className="badge badge-warning" style={{ padding: '0.75rem 1rem' }}>
          ⚠️ Backend Status: Offline / Connecting ({error})
        </div>
      ) : (
        <div className="grid-cols-3">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
              <Server size={18} />
              <span>API Gateway Status</span>
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#34d399' }}>
              {health?.status.toUpperCase()} ({health?.environment})
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Version: v{version?.app_version}</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
              <Database size={18} />
              <span>Postgres + pgvector DB</span>
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#34d399' }}>
              {health?.database.toUpperCase()}
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>HNSW Index Ready</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
              <Cpu size={18} />
              <span>Recognition Provider</span>
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--accent-secondary)' }}>
              {version?.recognition_provider.toUpperCase()} ({version?.model_version})
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Dim: {version?.embedding_dimension}d vector</span>
          </div>
        </div>
      )}
    </div>
  );
};

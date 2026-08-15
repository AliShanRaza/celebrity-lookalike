import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom';
import { HealthStatus } from '../HealthStatus';

describe('HealthStatus Component', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders loading state initially', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})));
    render(<HealthStatus />);
    expect(screen.getByText(/Connecting to backend service.../i)).toBeInTheDocument();
  });

  it('renders healthy status when API calls succeed', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string) => {
        if (url.includes('/health')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ status: 'healthy', database: 'connected', environment: 'development' }),
          });
        }
        if (url.includes('/version')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ app_version: '0.1.0', recognition_provider: 'fake', model_version: 'fake_v1', embedding_dimension: 512 }),
          });
        }
        return Promise.reject(new Error('Unknown URL'));
      })
    );

    render(<HealthStatus />);

    await waitFor(() => {
      expect(screen.getByText(/System Health & Infrastructure Monitor/i)).toBeInTheDocument();
      expect(screen.getByText(/HEALTHY \(development\)/i)).toBeInTheDocument();
      expect(screen.getByText(/CONNECTED/i)).toBeInTheDocument();
      expect(screen.getByText(/FAKE \(fake_v1\)/i)).toBeInTheDocument();
    });
  });
});

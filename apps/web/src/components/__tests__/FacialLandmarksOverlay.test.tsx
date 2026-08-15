import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import { FacialLandmarksOverlay } from '../FacialLandmarksOverlay';
import { FacialLandmarks } from '@/lib/api-client';

describe('FacialLandmarksOverlay Component Tests', () => {
  const sampleLandmarks: FacialLandmarks = {
    eyebrows: [{ x: 0.35, y: 0.30 }, { x: 0.65, y: 0.30 }],
    left_eye: [{ x: 0.38, y: 0.38 }],
    right_eye: [{ x: 0.62, y: 0.38 }],
    nose: [{ x: 0.50, y: 0.52 }],
    mouth: [{ x: 0.40, y: 0.65 }, { x: 0.60, y: 0.65 }],
    contour: [{ x: 0.25, y: 0.42 }, { x: 0.50, y: 0.68 }, { x: 0.75, y: 0.42 }],
  };

  it('Renders SVG overlay when landmarks are provided and hides when null', () => {
    const { rerender } = render(<FacialLandmarksOverlay landmarks={null} />);
    expect(screen.queryByTestId('facial-landmarks-svg')).not.toBeInTheDocument();

    rerender(<FacialLandmarksOverlay landmarks={sampleLandmarks} />);
    expect(screen.getByTestId('facial-landmarks-svg')).toBeInTheDocument();
  });

  it('Asserts all rendered landmark circles remain bounded within [0%, 100%] container space across 3 aspect ratios', () => {
    const aspectRatios = [1.0, 0.8, 1.777]; // Square 1:1, Portrait 4:5, Landscape 16:9

    aspectRatios.forEach((aspectRatio) => {
      const { unmount } = render(
        <FacialLandmarksOverlay
          landmarks={sampleLandmarks}
          imageAspectRatio={aspectRatio}
          containerAspectRatio={1.0}
        />
      );

      const circles = screen.getByTestId('facial-landmarks-svg').querySelectorAll('circle');
      expect(circles.length).toBeGreaterThan(0);

      circles.forEach((circle) => {
        const cxStr = circle.getAttribute('cx') || '0%';
        const cyStr = circle.getAttribute('cy') || '0%';

        const cxVal = parseFloat(cxStr.replace('%', ''));
        const cyVal = parseFloat(cyStr.replace('%', ''));

        // All points must be bounded strictly within container viewport [0%, 100%]
        expect(cxVal).toBeGreaterThanOrEqual(0);
        expect(cxVal).toBeLessThanOrEqual(100);
        expect(cyVal).toBeGreaterThanOrEqual(0);
        expect(cyVal).toBeLessThanOrEqual(100);

        // All points must stay within face bounding box (Y <= 85%)
        expect(cyVal).toBeLessThanOrEqual(85);
      });

      unmount();
    });
  });
});

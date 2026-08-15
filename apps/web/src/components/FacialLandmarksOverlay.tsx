'use client';

import React from 'react';
import { FacialLandmarks, LandmarkPoint } from '@/lib/api-client';

interface FacialLandmarksOverlayProps {
  landmarks?: FacialLandmarks | null;
  imageAspectRatio?: number; // width / height of original image (default 1.0)
  containerAspectRatio?: number; // width / height of container (default 1.0 square)
}

export const FacialLandmarksOverlay: React.FC<FacialLandmarksOverlayProps> = ({
  landmarks,
  imageAspectRatio = 1.0,
  containerAspectRatio = 1.0,
}) => {
  if (!landmarks) return null;

  // 1. Calculate facial feature bounding box from core landmarks (eyebrows, eyes, nose, mouth)
  const corePoints = [
    ...(landmarks.eyebrows || []),
    ...(landmarks.left_eye || []),
    ...(landmarks.right_eye || []),
    ...(landmarks.nose || []),
    ...(landmarks.mouth || []),
  ];

  let minX = 0.1, maxX = 0.9, minY = 0.1, maxY = 0.9;
  if (corePoints.length > 0) {
    const xs = corePoints.map((p) => p.x);
    const ys = corePoints.map((p) => p.y);
    minX = Math.max(0.02, Math.min(...xs) - 0.15);
    maxX = Math.min(0.98, Math.max(...xs) + 0.15);
    minY = Math.max(0.02, Math.min(...ys) - 0.15);
    maxY = Math.min(0.98, Math.max(...ys) + 0.20);
  }

  // 2. Object-fit: cover Coordinate Transform
  // Transforms normalized (x,y) relative to uncropped image into (rx, ry) relative to container viewport
  const transformPoint = (pt: LandmarkPoint): { x: number; y: number } => {
    // Safety clamp within facial feature bounding box
    const clampedX = Math.max(minX, Math.min(maxX, pt.x));
    const clampedY = Math.max(minY, Math.min(maxY, pt.y));

    let rx = clampedX;
    let ry = clampedY;

    if (imageAspectRatio && containerAspectRatio) {
      const R_img = imageAspectRatio;
      const R_box = containerAspectRatio;

      if (R_img < R_box) {
        // Image is taller than container: height is scaled up, top & bottom cropped
        // rx stays center-aligned, ry scales around vertical center 0.5
        const scaleY = R_img / R_box;
        ry = (clampedY - 0.5) * scaleY + 0.5;
      } else if (R_img > R_box) {
        // Image is wider than container: width is scaled up, left & right cropped
        const scaleX = R_box / R_img;
        rx = (clampedX - 0.5) * scaleX + 0.5;
      }
    }

    return {
      x: Math.max(0.0, Math.min(1.0, rx)),
      y: Math.max(0.0, Math.min(1.0, ry)),
    };
  };

  const renderGroup = (points: LandmarkPoint[], color: string, groupKey: string, isClosed: boolean = false) => {
    if (!points || points.length === 0) return null;

    const transformedPoints = points.map(transformPoint);

    const pathData =
      transformedPoints
        .map((pt, idx) => `${idx === 0 ? 'M' : 'L'} ${pt.x * 100} ${pt.y * 100}`)
        .join(' ') + (isClosed ? ' Z' : '');

    return (
      <g key={groupKey}>
        {/* Connecting Landmark Skeleton Lines */}
        <path
          d={pathData}
          fill="none"
          stroke={color}
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.85"
        />

        {/* Individual Landmark Feature Keypoints */}
        {transformedPoints.map((pt, idx) => (
          <circle
            key={idx}
            cx={`${pt.x * 100}%`}
            cy={`${pt.y * 100}%`}
            r="3"
            fill={color}
            stroke="#ffffff"
            strokeWidth="1"
            style={{ filter: `drop-shadow(0 0 4px ${color})` }}
          />
        ))}
      </g>
    );
  };

  return (
    <svg
      viewBox="0 0 100 100"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
      }}
      data-testid="facial-landmarks-svg"
    >
      {/* 1. Face Contour / Jawline (Bounded strictly around chin) */}
      {renderGroup(landmarks.contour, '#38bdf8', 'contour', false)}

      {/* 2. Eyebrows (Cyan) */}
      {renderGroup(landmarks.eyebrows, '#06b6d4', 'eyebrows', false)}

      {/* 3. Eyes (Bright Green) */}
      {renderGroup(landmarks.left_eye, '#34d399', 'left_eye', true)}
      {renderGroup(landmarks.right_eye, '#34d399', 'right_eye', true)}

      {/* 4. Nose Bridge & Tip (Gold Yellow) */}
      {renderGroup(landmarks.nose, '#f59e0b', 'nose', false)}

      {/* 5. Mouth & Lips (Pink Magenta) */}
      {renderGroup(landmarks.mouth, '#ec4899', 'mouth', true)}
    </svg>
  );
};

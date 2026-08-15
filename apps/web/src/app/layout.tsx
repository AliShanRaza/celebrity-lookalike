import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Celebrity Look-Alike | Privacy-First Face Matcher',
  description: 'AI-powered celebrity look-alike matching web app with privacy guarantees and calibrated resemblance scoring.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400;1,600&family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,700;1,800&family=Syne:wght@700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body>
        <div className="ambient-background">
          <div className="ambient-orb-1" />
          <div className="ambient-orb-2" />
        </div>
        {children}
      </body>
    </html>
  );
}


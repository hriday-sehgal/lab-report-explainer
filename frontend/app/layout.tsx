import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'CarePulse OS — Clinical Laboratory Diagnostics & Agentic Explainer',
  description: 'Clinical Care Operating System by Hriday Sehgal with Google ADK 2.0 and Gemini Flash',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-100 text-slate-900 min-h-screen antialiased flex flex-col">
        {children}
      </body>
    </html>
  );
}

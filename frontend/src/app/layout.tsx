import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "QuantPulse TSX | Paper Trading & Sentiment IA",
  description: "Plateforme Next.js + FastAPI de Paper Trading Bourse de Toronto Large Cap avec indicateurs de Momentum (RSI+MACD), Recharts et Gemini IA.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className={`${inter.variable} font-sans`}>
      <body className="antialiased min-h-screen text-slate-100">{children}</body>
    </html>
  );
}

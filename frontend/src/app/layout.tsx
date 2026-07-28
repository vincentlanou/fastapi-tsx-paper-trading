import type { Metadata } from "next";
import "./globals.css";

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
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}

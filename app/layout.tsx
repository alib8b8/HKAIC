import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HKAIC - AI Drone Flight Intelligence Platform",
  description: "HKAIC is a modern AI-powered SaaS platform for drone flight intelligence.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

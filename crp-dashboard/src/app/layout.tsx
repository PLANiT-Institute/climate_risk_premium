import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "https://crp-dashboard.vercel.app"
  ),
  title: "CRP Dashboard — Samcheok Blue Power",
  description:
    "Climate Risk Premium analysis for the 2,100MW Samcheok Blue Power coal-fired plant",
  openGraph: {
    title: "CRP Dashboard — Samcheok Blue Power",
    description:
      "Climate Risk Premium Model Results for 2,100MW Samcheok Coal-Fired Power Plant",
    siteName: "CRP Dashboard",
    images: [{ url: "/og-image.png", width: 1200, height: 630 }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "CRP Dashboard — Samcheok Blue Power",
    description:
      "Climate Risk Premium Model Results for 2,100MW Samcheok Coal-Fired Power Plant",
    images: ["/og-image.png"],
  },
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css"
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-slate-50`}
      >
        <Sidebar />
        <main className="ml-64 min-h-screen">
          <div className="max-w-7xl mx-auto px-6 py-8">{children}</div>
        </main>
      </body>
    </html>
  );
}
